"""
Human/AI annotation sample for Pillar B.

Draws a stratified, model-balanced sample of generations for blind annotation:
  unit  = (image_id, query_type) "key"; every sampled key contributes ONE response from every
          model x every condition (baseline / RAG / contrastive), so each model (and each model x
          condition cell) is represented by exactly the same number of items and the same
          images/questions are paired across models and mitigation strategies.
  strata = modality x query type (16 cells), --keys-per-cell keys per cell (default 3 ->
          48 keys -> 720 items, 144 per model; raise it for a bigger sample), spread across
          the image strata (S1..S4, DS1.. etc.) round-robin inside each cell.
  filter = a response is INVALID if it is empty/[ERROR]/[EMPTY], has fewer than --min-words words
          (single word / fragment) or starts mid-sentence (chopped start: first char lowercase or
          punctuation). Repetition loops are kept but flagged (--exclude-degenerate drops them).
          A key is eligible only if all its responses are valid. Exception ("whole model has that kind of thing"): when a model's valid rate in
          a condition is below --chronic-threshold, the filter is waived for that model x condition
          so the model is still represented; those cells are listed in the report.
  blind  = the annotator sheet has random item ids and no model/condition column and shows the
          plain question (retrieval context stripped); annotation_key.csv maps ids back.

Outputs (default medvihall_outputs/annotation/):
  annotation_sheet.csv        blind sheet to annotate (human and AI annotators use the same one)
  annotation_key.csv          item_id -> model, condition, image, stratum, validity flags
  annotation_sample_report.json   counts, exclusion reasons, waived cells, parameters
  DONE.txt                    written last, only on success

Usage:
  python build_annotation_sample.py                              # needs all 3 conditions complete
  python build_annotation_sample.py --conditions baseline rag --outdir <dir>   # dry run on partial data
"""
import csv
import json
import random
import argparse
import collections
from pathlib import Path

OUT = Path('medvihall_outputs')
MANIFEST = Path('medvihall_data/data/ground_truth/manifest_500_representative.json')
FILES = {'baseline': OUT / 'pillar_b_baseline.jsonl', 'rag': OUT / 'pillar_b_rag.jsonl',
         'contrastive': OUT / 'pillar_b_contrastive.jsonl'}
MODELS = ['qwen25vl', 'llava16', 'chexagent', 'huatuogpt', 'llava_med']
QTS = ['Q1', 'Q2', 'Q3', 'Q4']
MODALITIES = ['radiology', 'dermatology', 'histopathology', 'ophthalmology']
SEED = 20261008


def load(path):
    rows = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows[(r['model'], r['image_id'], r['query_type'])] = r
    return rows


def invalid_reasons(text, min_words):
    t = (text or '').strip()
    if not t or t == '[EMPTY]':
        return ['empty']
    if t.startswith('[ERROR]'):
        return ['error']
    out = []
    toks = t.split()
    if len(toks) < min_words:
        out.append('too_short')
    if t[0].islower() or t[0] in ',.;:)%]':
        out.append('chopped_start')
    run = best = 1
    for a, b in zip(toks, toks[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    if best >= 8 or (len(toks) >= 40 and len(set(toks)) / len(toks) < 0.25):
        out.append('degenerate_repetition')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conditions', nargs='*', default=['baseline', 'rag', 'contrastive'])
    ap.add_argument('--keys-per-cell', type=int, default=3)
    ap.add_argument('--min-words', type=int, default=8)
    ap.add_argument('--chronic-threshold', type=float, default=0.30)
    ap.add_argument('--exclude-degenerate', action='store_true',
                    help='also exclude repetition-loop outputs (default: keep and flag them; they are real model behaviour)')
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--outdir', default=str(OUT / 'annotation'))
    ap.add_argument('--require-complete', action='store_true',
                    help='abort unless every selected condition has all 8,395 calls')
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    conds = args.conditions

    manifest = {m['image_id']: m for m in json.loads(MANIFEST.read_text(encoding='utf-8'))}
    data = {c: load(FILES[c]) for c in conds}
    fixed = OUT / 'pillar_b_baseline_llava_med_fixed.jsonl'      # decoding-fix rerun replaces the chopped llava_med baseline
    if 'baseline' in data and fixed.exists():
        fx = load(fixed)
        if args.require_complete and len(fx) < 1679:
            raise SystemExit(f'llava_med fixed baseline incomplete ({len(fx)}/1679)')
        data['baseline'].update(fx)
        print(f'baseline: llava_med rows replaced by the fixed rerun ({fixed.name})')
    elif args.require_complete and 'baseline' in data:
        raise SystemExit('llava_med fixed baseline rerun not finished yet')
    for c in conds:
        print(f'{c}: {len(data[c])} records')
        if args.require_complete and len(data[c]) < 8395:
            raise SystemExit(f'{c} incomplete ({len(data[c])}/8395); not building the list yet')

    # ---- validity per response and per model x condition
    reasons, valid_rate = {}, {}
    exclusion = collections.defaultdict(collections.Counter)
    for c in conds:
        for m in MODELS:
            n = nv = 0
            for (mm, img, qt), r in data[c].items():
                if mm != m:
                    continue
                rs = invalid_reasons(r['response'], args.min_words)
                reasons[(c, mm, img, qt)] = rs
                n += 1
                nv += not [x for x in rs if args.exclude_degenerate or x != 'degenerate_repetition']
                for x in rs:
                    exclusion[f'{m}|{c}'][x] += 1
            valid_rate[(m, c)] = nv / n if n else 0.0
    waived = {(m, c) for (m, c), v in valid_rate.items() if v < args.chronic_threshold}

    def ok(c, m, img, qt):
        if (c, m, img, qt) not in reasons:
            return False                      # response missing
        rs = reasons[(c, m, img, qt)]
        if not args.exclude_degenerate:
            rs = [x for x in rs if x != 'degenerate_repetition']
        return (m, c) in waived or not rs

    # ---- eligible keys per cell
    keys = set()
    for c in conds:
        keys |= {(img, qt) for (_, img, qt) in data[c]}
    eligible = collections.defaultdict(list)
    n_candidates = collections.Counter()
    for img, qt in sorted(keys):
        mod = manifest[img]['modality']
        n_candidates[(mod, qt)] += 1
        if all(ok(c, m, img, qt) for c in conds for m in MODELS):
            eligible[(mod, qt)].append((img, qt))

    rng = random.Random(args.seed)
    chosen, shortfall = [], {}
    for mod in MODALITIES:
        for qt in QTS:
            pool = eligible.get((mod, qt), [])
            by_stratum = collections.defaultdict(list)
            for k in pool:
                by_stratum[manifest[k[0]]['stratum']].append(k)
            strata = sorted(by_stratum)
            rng.shuffle(strata)
            for s in strata:
                rng.shuffle(by_stratum[s])
            pick = []
            while len(pick) < args.keys_per_cell and any(by_stratum[s] for s in strata):
                for s in strata:
                    if by_stratum[s] and len(pick) < args.keys_per_cell:
                        pick.append(by_stratum[s].pop())
            if len(pick) < args.keys_per_cell:
                shortfall[f'{mod}|{qt}'] = {'wanted': args.keys_per_cell, 'got': len(pick), 'eligible': len(pool)}
            chosen += pick

    # backfill: cells short of eligible keys are topped up from the cells with surplus (model balance is
    # unaffected because every key carries one response per model x condition)
    target = args.keys_per_cell * len(MODALITIES) * len(QTS)
    taken = set(chosen)
    spare = {cell: [k for k in pool if k not in taken] for cell, pool in eligible.items()}
    for v in spare.values():
        rng.shuffle(v)
    backfilled = 0
    while len(chosen) < target and any(spare.values()):
        cell = max(spare, key=lambda c: len(spare[c]))
        chosen.append(spare[cell].pop())
        backfilled += 1

    # ---- build items (random ids, shuffled order, blind sheet)
    items = [(c, m, img, qt) for img, qt in chosen for c in conds for m in MODELS]
    rng.shuffle(items)
    sheet_rows, key_rows = [], []
    for i, (c, m, img, qt) in enumerate(items, 1):
        r = data[c][(m, img, qt)]
        base_prompt = data['baseline'][(m, img, qt)]['prompt'] if 'baseline' in data else r['prompt']
        iid = f'A{i:04d}'
        img_rec = manifest[img]
        sheet_rows.append({'item_id': iid, 'image_path': img_rec['image_path'], 'modality': img_rec['modality'],
                           'question': base_prompt, 'response': r['response'],
                           'hallucination_present (Y/N)': '', 'hallucination_types / notes': '',
                           'severity (0-3)': '', 'annotator': ''})
        key_rows.append({'item_id': iid, 'model': m, 'condition': c, 'image_id': img, 'query_type': qt,
                         'modality': img_rec['modality'], 'stratum': img_rec['stratum'],
                         'filter_waived': (m, c) in waived, 'flags': ';'.join(reasons[(c, m, img, qt)]),
                         'confidence': r.get('confidence'), 'pair_key': f'{img}|{qt}'})

    def write_csv(path, rows):
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    write_csv(outdir / 'annotation_sheet.csv', sheet_rows)
    write_csv(outdir / 'annotation_key.csv', key_rows)

    cnt = lambda f: dict(collections.Counter(f(k) for k in key_rows))
    report = {
        'parameters': vars(args), 'n_keys': len(chosen), 'n_items': len(items),
        'items_per_model': cnt(lambda k: k['model']), 'items_per_condition': cnt(lambda k: k['condition']),
        'items_per_model_condition': cnt(lambda k: f"{k['model']}|{k['condition']}"),
        'items_per_modality': cnt(lambda k: k['modality']), 'items_per_query_type': cnt(lambda k: k['query_type']),
        'items_per_image_stratum': cnt(lambda k: k['stratum']),
        'valid_rate_before_filter': {f'{m}|{c}': round(v, 4) for (m, c), v in sorted(valid_rate.items())},
        'filter_waived_cells (valid rate below threshold)': sorted(f'{m}|{c}' for m, c in waived),
        'invalid_reason_counts': {k: dict(v) for k, v in sorted(exclusion.items())},
        'candidate_keys_vs_eligible_per_cell': {f'{m}|{q}': {'candidates': n_candidates[(m, q)],
                                                             'eligible_all_valid': len(eligible.get((m, q), []))}
                                                for m in MODALITIES for q in QTS},
        'shortfall_cells': shortfall, 'backfilled_keys': backfilled,
        'note': 'Keys are kept only if every model x condition response is valid (or its cell is waived), so '
                'annotation hallucination rates are conditional on well-formed outputs; the pre-filter validity '
                'rates above quantify what was excluded.',
    }
    (outdir / 'annotation_sample_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (outdir / 'DONE.txt').write_text(f'{len(items)} items / {len(chosen)} keys written', encoding='utf-8')
    print(f"\nANNOTATION LIST COMPLETE: {len(items)} items ({len(chosen)} keys x {len(conds)} conditions x {len(MODELS)} models)")
    print('per model:', report['items_per_model'])
    print('waived cells:', report['filter_waived_cells (valid rate below threshold)'])
    print('shortfall cells:', shortfall or 'none')
    print('valid rates:', report['valid_rate_before_filter'])


if __name__ == '__main__':
    main()
