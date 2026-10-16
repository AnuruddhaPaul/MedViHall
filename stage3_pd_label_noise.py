"""
Label-noise check: compare the labels from the 1,000-response relabel
(pillar_d_stage3_noise: shuffled order, different batch size) against the
original Stage 3 labels for the same distinct responses. Reports the flip rate
of the strict and claim-level labels with Wilson 95% intervals.
"""
import json
import math
from pathlib import Path
from collections import Counter

import stage3_pd_label as L
import stage3_pd_ece as E

NOISE = Path('medvihall_outputs/pillar_d_stage3_noise')
orig = E.load_labels(Path('medvihall_outputs/pillar_d_stage3/layer2_judge.jsonl'),
                     Path('medvihall_outputs/pillar_d_stage3/layer1_verdicts.jsonl'))
new = E.load_labels(NOISE / 'layer2_judge.jsonl', NOISE / 'layer1_verdicts.jsonl')
mod = {}
for r in L._iter_jsonl(NOISE / 'pd_results.jsonl'):
    mod[(r['model'], r['image_id'], r['query_type'])] = r['modality']


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


keys = [k for k in new if k in orig]
print(f'responses relabeled: {len(new)} | comparable (labeled in both): {len(keys)} | '
      f'unlabeled in new: {len(mod) - len(new)} | unlabeled in orig: {len([k for k in mod if k not in orig])}')
for name, fn in (('strict', lambda l: l['claims_ok'] and l['n_omissions'] == 0), ('claims-only', lambda l: l['claims_ok'])):
    flips = [k for k in keys if fn(orig[k]) != fn(new[k])]
    lo, hi = wilson(len(flips), len(keys))
    to_bad = sum(1 for k in flips if fn(orig[k]) and not fn(new[k]))
    print(f'\n{name}: flips {len(flips)}/{len(keys)} = {len(flips)/len(keys):.3%}  (95% CI {lo:.3%}-{hi:.3%})'
          f' | correct->incorrect {to_bad}, incorrect->correct {len(flips) - to_bad}')
    by = Counter(); tot = Counter()
    for k in keys:
        tot[mod[k]] += 1
        by[mod[k]] += fn(orig[k]) != fn(new[k])
    print('   by modality:', {m: f'{by[m]}/{tot[m]}' for m in tot})
# Layer 1 omissions are deterministic given the text, so strict-label flips come from the LLM judge
om = sum(1 for k in keys if orig[k]['n_omissions'] != new[k]['n_omissions'])
print(f'\nLayer 1 omission-count differences: {om}/{len(keys)} (expected 0; Layer 1 is deterministic)')
