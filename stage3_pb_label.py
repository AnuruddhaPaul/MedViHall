"""
Pillar B labeling driver -- labels every Pillar B response that has no core label yet, by running the SAME
validated pipeline as Pillar D (stage1_extract_claims -> Layer 1 -> stage3_layer2_judge) through
stage3_pd_label.py with its output directory switched to medvihall_outputs/pillar_b_stage3/.

Responses covered
  RAG, contrastive        all 8,395 each (labelled regardless of whether a confidence was stated: SMHR does not need it)
  baseline llava_med      the 1,679 rerun responses (pillar_b_baseline_llava_med_fixed.jsonl)
  baseline, other models  NOT relabelled: the core run already labelled them (medvihall_outputs/layer2_judge.jsonl)
Any response byte-identical to the core response for the same (model, image, query) reuses the core label.
Each distinct response gets a pseudo-model key "<model>__<sha1[:12]>" exactly as in Pillar D.

Usage (project root; resume-safe, every phase rescans its output files):
  python stage3_pb_label.py [--require-complete] [--sample N]
"""
import os
import sys
import json
import argparse
from pathlib import Path

os.environ.setdefault('PD_STAGE3_DIR', 'pillar_b_stage3')          # must be set before importing the Pillar D driver
import stage3_pd_label as L                              # noqa: E402

OUT = Path('medvihall_outputs')
RAG = OUT / 'pillar_b_rag.jsonl'
CONTRASTIVE = OUT / 'pillar_b_contrastive.jsonl'
BASE_LLAVA_MED = OUT / 'pillar_b_baseline_llava_med_fixed.jsonl'
EXPECT = {RAG: 8395, CONTRASTIVE: 8395, BASE_LLAVA_MED: 1679}


def load_unique(path):
    rows = {}
    for r in L._iter_jsonl(path):
        rows[(r['model'], r['image_id'], r['query_type'])] = r
    return rows


def build_worklist(sample=0):
    L.OUT_DIR.mkdir(parents=True, exist_ok=True)
    core = L.load_core_responses()
    items, seen, reused, skipped_empty = [], set(), 0, 0
    for path in (RAG, CONTRASTIVE, BASE_LLAVA_MED):
        for (m, img, qt), r in sorted(load_unique(path).items()):
            resp = r['response']
            if not resp.strip() or resp.strip() == '[EMPTY]' or resp.startswith('[ERROR]'):
                skipped_empty += 1
                continue
            if core.get((m, img, qt)) == resp:
                reused += 1
                continue
            pm = L.pseudo_model(m, resp)
            if (pm, img, qt) in seen:
                continue
            seen.add((pm, img, qt))
            items.append({'model': pm, 'image_id': img, 'modality': r['modality'], 'query_type': qt, 'response': resp})
    if sample:
        import random
        random.Random(1).shuffle(items)
        items = items[:sample]
    tmp = L.WORKLIST.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    tmp.replace(L.WORKLIST)
    print(f'worklist: {len(items)} responses to label | reused core labels: {reused} | empty/error skipped: {skipped_empty}'
          f' -> {L.WORKLIST}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--require-complete', action='store_true')
    ap.add_argument('--sample', type=int, default=0)
    args = ap.parse_args()
    if args.require_complete:
        for p, n in EXPECT.items():
            have = len(load_unique(p)) if p.exists() else 0
            if have < n:
                raise SystemExit(f'{p.name} incomplete ({have}/{n}); not labelling yet')
    if not L.WORKLIST.exists():
        build_worklist(args.sample)
    L.sub(sys.executable, ['module', 'stage1_extract_claims'])
    L.sub(sys.executable, ['module', 'stage2_radiology_chexbert'])
    L.sub(L.PY312, ['module', 'stage2_other_modalities'])
    L.merge_layer1()
    L.sub(sys.executable, ['module', 'stage3_layer2_judge'])
    print('\nPillar B labeling complete.')


if __name__ == '__main__':
    main()
