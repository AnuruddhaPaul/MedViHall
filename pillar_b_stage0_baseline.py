"""
Pillar B (RQ8), Stage 0 -- "no mitigation" baseline. No new inference: filter the
core results (medvihall_results_deduped.jsonl) to the 5 representative_subset
models x the 500 manifest_500_representative image_ids x all query types, save
as medvihall_outputs/pillar_b_baseline.jsonl, and verify it against the exact
call list Pillar D used (Q1-Q3 for every image, Q4 only for NORMAL_STRATA).
"""
import json
import collections
from pathlib import Path

import stage2_pillar_d_calibration as S

OUT = Path('medvihall_outputs')
CORE = OUT / 'medvihall_results_deduped.jsonl'
SUBSET = OUT / 'representative_subset.json'
BASELINE = OUT / 'pillar_b_baseline.jsonl'

models = json.loads(SUBSET.read_text(encoding='utf-8'))['representative_subset']
manifest = json.loads(S.MANIFEST_FILE.read_text(encoding='utf-8'))
img_ids = {i['image_id'] for i in manifest}
expected = {(i['image_id'], qt) for i, qt in S.build_call_list(manifest)}
print(f'models: {models}')
print(f'subset images: {len(img_ids)} | expected calls per model: {len(expected)} | x{len(models)} = {len(expected) * len(models)}')

rows, dup = {}, 0
with open(CORE, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r['model'] in models and r['image_id'] in img_ids:
            k = (r['model'], r['image_id'], r['query_type'])
            if k in rows:
                dup += 1
            rows[k] = r

with open(BASELINE, 'w', encoding='utf-8') as f:
    for k in sorted(rows):
        f.write(json.dumps(rows[k], ensure_ascii=False) + '\n')

print(f'\nbaseline records written: {len(rows)} -> {BASELINE} (duplicate keys in source: {dup})')
extra = collections.Counter()
for m in models:
    have = {(i, q) for (mm, i, q) in rows if mm == m}
    missing = sorted(expected - have)
    unexpected = sorted(have - expected)
    extra[m] = len(unexpected)
    bad = [r for (mm, i, q), r in rows.items() if mm == m and (not r['response'].strip() or '[ERROR]' in r['response'] or r['response'].strip() == '[EMPTY]')]
    conf = sum(1 for (mm, i, q), r in rows.items() if mm == m and r.get('confidence') is not None)
    print(f'  {m:10s} have={len(have):5d} expected={len(expected)} missing={len(missing):4d} '
          f'unexpected(extra)={len(unexpected):3d} empty/error={len(bad):3d} with_confidence={conf}')
    if missing:
        byq = collections.Counter(q for _, q in missing)
        print(f'             missing by query type: {dict(byq)}  e.g. {missing[:3]}')

print(f'\nTOTAL in baseline: {len(rows)} (target {len(expected) * len(models)}); gap = {len(expected) * len(models) - sum(len({(i, q) for (mm, i, q) in rows if mm == m} & expected) for m in models)}')
