"""
Stage 1 -- proportionally stratified 500-image subset of manifest_3500.json.

Note: the manifest has 13 strata (S1-S4, DS1-DS3, HS1-HS3, OS1-OS3), not the
12 the task description assumed -- proceeding with the actual 13.

Each stratum's target count = round(current_count * 500/3500), using the
largest-remainder method (round down all fractional parts, then give the +1
back to the strata with the largest remainders until the total is exactly
500) so the total lands exactly on 500 without ad-hoc manual adjustment.

Fixed seed (42) for reproducible per-stratum sampling without replacement.
"""
import json
import random
from pathlib import Path
from collections import Counter, defaultdict

SEED = 42
TARGET_TOTAL = 500
MANIFEST_IN = Path('medvihall_data/data/ground_truth/manifest_3500.json')
MANIFEST_OUT = Path('medvihall_data/data/ground_truth/manifest_500_representative.json')


def largest_remainder_allocation(counts, total_target):
    grand_total = sum(counts.values())
    scale = total_target / grand_total
    raw = {k: v * scale for k, v in counts.items()}
    floor_alloc = {k: int(v) for k, v in raw.items()}
    remainder = total_target - sum(floor_alloc.values())
    # Give the remaining seats to the strata with the largest fractional remainders.
    fractional = sorted(raw.keys(), key=lambda k: raw[k] - floor_alloc[k], reverse=True)
    for k in fractional[:remainder]:
        floor_alloc[k] += 1
    return floor_alloc


def main():
    manifest = json.loads(MANIFEST_IN.read_text(encoding='utf-8'))
    by_stratum = defaultdict(list)
    for r in manifest:
        by_stratum[r['stratum']].append(r)

    counts = {k: len(v) for k, v in by_stratum.items()}
    print(f'Strata found: {len(counts)} (instructions assumed 12; manifest actually has {len(counts)})')

    allocation = largest_remainder_allocation(counts, TARGET_TOTAL)

    rng = random.Random(SEED)
    subset = []
    print(f'\n{"stratum":<8}{"n_3500":>10}{"n_500":>10}')
    for stratum in sorted(counts):
        n = allocation[stratum]
        pool = by_stratum[stratum][:]
        rng.shuffle(pool)
        subset.extend(pool[:n])
        print(f'{stratum:<8}{counts[stratum]:>10}{n:>10}')

    print(f'{"TOTAL":<8}{sum(counts.values()):>10}{len(subset):>10}')
    assert len(subset) == TARGET_TOTAL, f'Expected {TARGET_TOTAL}, got {len(subset)}'

    MANIFEST_OUT.write_text(json.dumps(subset, indent=2), encoding='utf-8')
    print(f'\nSaved {len(subset)} images to {MANIFEST_OUT}')


if __name__ == '__main__':
    main()
