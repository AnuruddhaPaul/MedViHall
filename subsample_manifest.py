"""
subsample_manifest.py
─────────────────────
Cuts MedViHall's full manifest (9,346 images) down to 3,500 stratified images.
Outputs: medvihall_data/data/ground_truth/manifest_3500.json

Target strata:
  Radiology    : S1=300, S2=300, S3=300, S4=300      total=1200
  Dermatology  : DS1=400, DS2=200, DS3=300            total=900
  Histopathology: HS1=300, HS2=200, HS3=300           total=800
  Ophthalmology: OS1=250, OS2=200, OS3=150            total=600
  ─────────────────────────────────────────────────────────────
  TOTAL                                               = 3,500

Run ONCE before starting inference:
  python subsample_manifest.py

Seed=42 for reproducibility. Idempotent — re-running produces identical output.
"""

import json, random, sys
from pathlib import Path
from collections import Counter, defaultdict

# ── Config ────────────────────────────────────────────────────────────────
SEED       = 42
DATA_DIR   = Path('./medvihall_data')
GT_DIR     = DATA_DIR / 'data' / 'ground_truth'
OUTPUT     = GT_DIR / 'manifest_3500.json'

GT_FILES = {
    'radiology':      GT_DIR / 'radiology_gt_merged.json',
    'dermatology':    GT_DIR / 'dermatology_gt_merged.json',
    'histopathology': GT_DIR / 'histopathology_gt_merged.json',
    'ophthalmology':  GT_DIR / 'ophthalmology_gt_merged.json',
}

# Target N per stratum — total = 3,500
TARGETS = {
    # Radiology (anchor modality — dense for fine-tuning paradox confirmation)
    'S1':  300, 'S2':  300, 'S3':  300, 'S4':  300,
    # Dermatology
    'DS1': 400, 'DS2': 200, 'DS3': 300,
    # Histopathology
    'HS1': 300, 'HS2': 200, 'HS3': 300,
    # Ophthalmology (OS3=150 thin — in limitations)
    'OS1': 250, 'OS2': 200, 'OS3': 150,
}

MODALITY_STRATA = {
    'radiology':      ['S1','S2','S3','S4'],
    'dermatology':    ['DS1','DS2','DS3'],
    'histopathology': ['HS1','HS2','HS3'],
    'ophthalmology':  ['OS1','OS2','OS3'],
}

# ── Load full manifest ────────────────────────────────────────────────────
print('Loading full manifest from GT files ...')
full_manifest = []
for modality, gt_file in GT_FILES.items():
    if not gt_file.exists():
        print(f'  ⚠ Missing: {gt_file} — skipping {modality}')
        continue
    with open(gt_file) as f:
        records = json.load(f)
    for rec in records:
        img_path = rec.get('validated_path')
        if not img_path:
            # Try to find by filename
            for p in (DATA_DIR / 'data' / 'raw').rglob(rec.get('filename', '')):
                img_path = str(p)
                break
        if img_path and Path(img_path).exists():
            full_manifest.append({
                'image_id':   rec['image_id'],
                'modality':   modality,
                'stratum':    rec.get('stratum', ''),
                'image_path': img_path,
                'source':     rec.get('source', ''),
            })

print(f'Full manifest: {len(full_manifest)} images')
by_stratum = defaultdict(list)
for item in full_manifest:
    by_stratum[item['stratum']].append(item)

print('\nAvailable vs targets:')
print(f'  {"Stratum":<8}  {"Available":>10}  {"Target":>8}  {"Status":>10}')
print(f'  {"-"*44}')
for stratum, target in TARGETS.items():
    avail = len(by_stratum[stratum])
    status = '✓' if avail >= target else f'⚠ SHORTFALL ({avail})'
    print(f'  {stratum:<8}  {avail:>10}  {target:>8}  {status}')

# ── Stratified sampling ───────────────────────────────────────────────────
random.seed(SEED)
subsampled = []
actual_counts = {}

print('\nSampling ...')
for modality in ['radiology', 'dermatology', 'histopathology', 'ophthalmology']:
    mod_strata = MODALITY_STRATA[modality]
    mod_total  = 0
    for stratum in mod_strata:
        pool   = by_stratum[stratum]
        target = TARGETS[stratum]
        n      = min(target, len(pool))   # take all if pool < target
        chosen = random.sample(pool, n)
        subsampled.extend(chosen)
        actual_counts[stratum] = n
        mod_total += n
    print(f'  {modality:<16} {mod_total} images')

print(f'\nTotal subsampled: {len(subsampled)} images (target: 3500)')

# ── Final count summary ───────────────────────────────────────────────────
print('\nFinal strata counts:')
by_mod = defaultdict(int)
for item in subsampled:
    by_mod[item['modality']] += 1
for modality, strata in MODALITY_STRATA.items():
    sc = {s: actual_counts.get(s, 0) for s in strata}
    print(f'  {modality:<20} {by_mod[modality]:>5}  {sc}')

# ── Write output ──────────────────────────────────────────────────────────
if OUTPUT.exists():
    print(f'\n⚠ {OUTPUT} already exists — overwriting')
GT_DIR.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, 'w') as f:
    json.dump(subsampled, f, indent=2, ensure_ascii=False)
print(f'\n✓ Saved: {OUTPUT}  ({OUTPUT.stat().st_size/1024:.1f} KB)')

# ── Estimate GPU time ─────────────────────────────────────────────────────
NORMAL_STRATA = {'S1','DS1','HS1','OS1'}
normal_count  = sum(1 for e in subsampled if e['stratum'] in NORMAL_STRATA)
q4_calls      = normal_count
total_calls   = len(subsampled) * 3 + q4_calls   # Q1+Q2+Q3 all, Q4 normal only
est_hrs_model = total_calls * 17 / 3600           # avg 17s/call with per-QT limits
est_hrs_all   = est_hrs_model * 15

print(f'\nGPU time estimates (per-QT limits, avg 17s/call):')
print(f'  Calls per model : {total_calls:,}  (Q4 only on {normal_count} normal strata)')
print(f'  Per model       : {est_hrs_model:.1f} h  ({est_hrs_model/24:.1f} days)')
print(f'  15 models total : {est_hrs_all:.0f} h = {est_hrs_all/24:.1f} days GPU')
print(f'\nNow run the inference notebook with manifest_3500.json loaded.')
