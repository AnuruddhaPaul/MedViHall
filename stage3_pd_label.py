"""
Stage 3 (Pillar D) labeling driver -- derives the per-response correctness label
("zero Class 1-7 hallucinations") for every Pillar D response, by running the
SAME validated core pipeline scripts (stage1_extract_claims -> Layer 1 ->
stage3_layer2_judge) against a Pillar D worklist.

Why a worklist keyed by response hash: the core Layer 2 judgments describe the
core pipeline's one response per (model, image, query); Pillar D produced
different text under each decoding config, so a label is only valid for the
exact response it was computed on. Each distinct (model, image, query,
response) gets one pseudo-model name "<model>__<sha1[:12]>", which lets the
unmodified core scripts (keyed on model/image/query) run as-is. Responses
byte-identical to the core response reuse the core labels instead.

llava16 Q1/Q3/Q4 records generated after the 220-token cap was added
(2026-09-26 17:35:45 UTC) are excluded as truncated; regenerated uncapped
replacements, if present in LLAVA16_REGEN_FILE, supersede them.

Usage (run from the project root; every phase is resume-safe):
  python stage3_pd_label.py all                 # build + claims + layer1 + layer2
  python stage3_pd_label.py build [--sample N]  # just (re)build the worklist
  PD_STAGE3_DIR=pillar_d_stage3_test python stage3_pd_label.py all   # test dir
"""
import os
import sys
import json
import random
import hashlib
import argparse
import subprocess
import importlib
from pathlib import Path

OUT_DIR = Path('medvihall_outputs') / os.environ.get('PD_STAGE3_DIR', 'pillar_d_stage3')
PD_RUNS = Path('medvihall_outputs/pillar_d_calibration_runs.jsonl')
LLAVA16_REGEN_FILE = Path('medvihall_outputs/pillar_d_llava16_uncapped.jsonl')
CORE_RESULTS = Path('medvihall_outputs/medvihall_results_deduped.jsonl')

WORKLIST = OUT_DIR / 'pd_results.jsonl'
VALIDATION = OUT_DIR / 'validation_keys.json'
CLAIMS = OUT_DIR / 'claims.jsonl'
CLAIMS_FAIL = OUT_DIR / 'claims_parse_failures.jsonl'
CLAIMS_PROG = OUT_DIR / 'claims_progress.json'
L1_RAD = OUT_DIR / 'layer1_radiology.jsonl'
L1_RAD_PROG = OUT_DIR / 'layer1_radiology_progress.json'
L1_OTHER = OUT_DIR / 'layer1_other.jsonl'
L1_OTHER_PROG = OUT_DIR / 'layer1_other_progress.json'
L1_ALL = OUT_DIR / 'layer1_verdicts.jsonl'
L2 = OUT_DIR / 'layer2_judge.jsonl'
L2_FAIL = OUT_DIR / 'layer2_judge_parse_failures.jsonl'
L2_PROG = OUT_DIR / 'layer2_judge_progress.json'

CAP_TS = '2026-09-26T17:35:45'
CAPPED_QTS = ('Q1', 'Q3', 'Q4')
PY312 = r'C:\Users\PC\AppData\Local\Programs\Python\Python312\python.exe'
N_VALIDATION = 150

MODULE_OVERRIDES = {
    'stage1_extract_claims': {'RESULTS_FILE': WORKLIST, 'CLAIMS_FILE': CLAIMS,
                              'PARSE_FAIL_FILE': CLAIMS_FAIL, 'PROGRESS_FILE': CLAIMS_PROG},
    'stage2_radiology_chexbert': {'RESULTS_FILE': WORKLIST, 'OUT_FILE': L1_RAD,
                                  'PROGRESS_FILE': L1_RAD_PROG},
    'stage2_other_modalities': {'RESULTS_FILE': WORKLIST, 'OUT_FILE': L1_OTHER,
                                'PROGRESS_FILE': L1_OTHER_PROG},
    'stage3_layer2_judge': {'CLAIMS_FILE': CLAIMS, 'LAYER1_FILE': L1_ALL, 'OUT_FILE': L2,
                            'PARSE_FAIL_FILE': L2_FAIL, 'PROGRESS_FILE': L2_PROG},
}


def response_hash(response):
    return hashlib.sha1(response.encode('utf-8')).hexdigest()[:12]


def pseudo_model(model, response, validation=False):
    return f'{model}__{"v" if validation else ""}{response_hash(response)}'


def _iter_jsonl(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def load_effective_runs():
    """key (model, config_label, image_id, query_type) -> record, first occurrence wins.
    Drops llava16 records truncated by the 220-token cap; regenerated ones supersede."""
    runs, excluded = {}, 0
    for r in _iter_jsonl(PD_RUNS):
        k = (r['model'], r['config_label'], r['image_id'], r['query_type'])
        if k in runs:
            continue
        if (r['model'] == 'llava16' and r['query_type'] in CAPPED_QTS
                and r['timestamp'][:19] >= CAP_TS):
            excluded += 1
            continue
        runs[k] = r
    regenerated = 0
    if LLAVA16_REGEN_FILE.exists():
        for r in _iter_jsonl(LLAVA16_REGEN_FILE):
            k = (r['model'], r['config_label'], r['image_id'], r['query_type'])
            if k not in runs:
                regenerated += 1
            runs[k] = r
    return runs, excluded, regenerated


def load_core_responses():
    return {(r['model'], r['image_id'], r['query_type']): r['response']
            for r in _iter_jsonl(CORE_RESULTS)}


def build_worklist(sample=0):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runs, excluded, regenerated = load_effective_runs()
    core = load_core_responses()
    print(f'effective runs: {len(runs)} (excluded capped llava16: {excluded}, regenerated: {regenerated})')

    need, identical = {}, []
    for (m, cfg, img, qt), r in runs.items():
        if r.get('confidence') is None:
            continue
        resp = r['response']
        if core.get((m, img, qt)) == resp:
            identical.append((m, img, qt, resp, r['modality']))
        else:
            need.setdefault((m, img, qt, response_hash(resp)), (m, img, qt, resp, r['modality']))
    identical = sorted(set(identical))
    print(f'usable responses needing a fresh judgment: {len(need)} | identical to core (reuse core labels): {len(identical)}')

    rng = random.Random(42)
    val = rng.sample(identical, min(N_VALIDATION, len(identical)))
    need_items = [(pseudo_model(m, resp), img, qt, resp, mod, None) for (m, img, qt, resp, mod) in need.values()]
    val_items = [(pseudo_model(m, resp, validation=True), img, qt, resp, mod, (m, img, qt))
                 for (m, img, qt, resp, mod) in val]
    if sample:
        rng.shuffle(need_items)
        need_items = need_items[:sample]
        val_items = val_items[:sample // 2]
        print(f'--sample {sample}: {len(need_items)} need-items + {len(val_items)} validation items')
    items = need_items + val_items

    tmp = WORKLIST.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        for pm, img, qt, resp, mod, _ in items:
            f.write(json.dumps({'model': pm, 'image_id': img, 'modality': mod,
                                'query_type': qt, 'response': resp}, ensure_ascii=False) + '\n')
    tmp.replace(WORKLIST)
    VALIDATION.write_text(json.dumps(
        [{'pseudo_model': pm, 'image_id': img, 'query_type': qt, 'core_key': list(ck)}
         for pm, img, qt, _, _, ck in items if ck is not None], indent=1), encoding='utf-8')
    print(f'worklist written: {len(items)} records -> {WORKLIST}')


def build_resample(n, seed=11):
    """Label-noise check: a shuffled random sample of already-labeled responses,
    relabeled in OUT_DIR (use PD_STAGE3_DIR + PD_STAGE3_BATCH so batch composition differs)."""
    src = Path('medvihall_outputs/pillar_d_stage3/pd_results.jsonl')
    items = [r for r in _iter_jsonl(src) if '__v' not in r['model']]
    rng = random.Random(seed)
    rng.shuffle(items)
    items = items[:n]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(WORKLIST, 'w', encoding='utf-8') as f:
        for r in items:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'resample worklist: {len(items)} records -> {WORKLIST}')


def run_module(name, extra_argv):
    mod = importlib.import_module(name)
    for attr, val in MODULE_OVERRIDES[name].items():
        setattr(mod, attr, val)
    if os.environ.get('PD_STAGE3_BATCH') and hasattr(mod, 'BATCH_SIZE'):
        mod.BATCH_SIZE = int(os.environ['PD_STAGE3_BATCH'])
    sys.argv = [name] + extra_argv
    mod.main()


def merge_layer1():
    n = 0
    tmp = L1_ALL.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as out:
        for src in (L1_RAD, L1_OTHER):
            if src.exists():
                for r in _iter_jsonl(src):
                    out.write(json.dumps(r, ensure_ascii=False) + '\n')
                    n += 1
    tmp.replace(L1_ALL)
    print(f'merged layer1 verdicts: {n} records -> {L1_ALL}')


def sub(exe, args):
    print(f'\n>>> {Path(exe).parent.name} {" ".join(args)}', flush=True)
    rc = subprocess.call([exe, 'stage3_pd_label.py'] + args)
    if rc != 0:
        sys.exit(rc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['all', 'build', 'module', 'merge', 'resample'])
    ap.add_argument('module_name', nargs='?')
    ap.add_argument('--sample', type=int, default=0)
    ap.add_argument('--n', type=int, default=1000)
    args, extra = ap.parse_known_args()

    if args.phase == 'resample':
        build_resample(args.n)
    elif args.phase == 'build':
        build_worklist(args.sample)
    elif args.phase == 'module':
        run_module(args.module_name, extra)
    elif args.phase == 'merge':
        merge_layer1()
    else:
        if not WORKLIST.exists():
            build_worklist(args.sample)
        sub(sys.executable, ['module', 'stage1_extract_claims'])
        sub(sys.executable, ['module', 'stage2_radiology_chexbert'])
        sub(PY312, ['module', 'stage2_other_modalities'])
        merge_layer1()
        sub(sys.executable, ['module', 'stage3_layer2_judge'])
        print('\nStage 3 labeling complete.')


if __name__ == '__main__':
    main()
