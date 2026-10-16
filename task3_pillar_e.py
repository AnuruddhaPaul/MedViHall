"""
Task 3 (Pillar E, RQ5): cross-modal safety transfer.

For each of the 6 modality pairs, Spearman-correlate model SMHR rankings
across the 12 models. Separately, do the same for SRI rankings among just
the 3 medical specialists. Significance is assessed via the standard t-test
for Spearman's rho (t = r*sqrt((n-2)/(1-r^2)), compared against the
two-tailed critical t at alpha=0.05) rather than a fixed |r| cutoff.
"""
import json
import math
from pathlib import Path
from itertools import combinations

from task2_pillar_c import spearman

METRICS_FILE = Path('medvihall_outputs/metrics_summary.json')
OUT_FILE = Path('medvihall_outputs/pillar_e_cross_modal_transfer.json')

# Two-tailed critical t values at alpha=0.05 for small df (n-2), standard table.
T_CRIT_005 = {1: 12.706, 2: 4.303, 3: 3.182, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201}


def significance(r, n):
    if r is None:
        return None, None, 'n/a'
    df = n - 2
    if df <= 0:
        return r, None, 'insufficient sample (n<=2)'
    if abs(r) >= 1.0:
        return r, float('inf'), 'significant (perfect correlation)'
    t = r * math.sqrt(df / (1 - r ** 2))
    crit = T_CRIT_005.get(df)
    if crit is None:
        crit = 2.228  # fall back to df=10 critical value as a reasonable approximation
    label = 'significant (p<0.05)' if abs(t) > crit else 'not significant (p>=0.05)'
    return r, t, label


def main():
    summary = json.loads(METRICS_FILE.read_text(encoding='utf-8'))
    models = sorted(summary['models'])
    modalities = sorted({mod for m in models for mod in summary['models'][m]['by_modality']})
    specialists = sorted(m for m in models if summary['models'][m]['is_medical'])

    smhr_by_modality = {
        mod: {m: summary['models'][m]['by_modality'][mod]['smhr'] for m in models
              if mod in summary['models'][m]['by_modality']}
        for mod in modalities
    }
    sri = summary['sri']  # specialist -> modality -> {sri, ...}

    pairs = list(combinations(modalities, 2))
    smhr_matrix = {}
    smhr_results = []
    for a, b in pairs:
        common = [m for m in models if m in smhr_by_modality[a] and m in smhr_by_modality[b]]
        xa = [smhr_by_modality[a][m] for m in common]
        xb = [smhr_by_modality[b][m] for m in common]
        r = spearman(xa, xb)
        rho, t, label = significance(r, len(common))
        smhr_matrix[(a, b)] = rho
        smhr_results.append({'modality_a': a, 'modality_b': b, 'n_models': len(common),
                              'spearman_r': rho, 't_stat': t, 'significance': label})

    sri_results = []
    for a, b in pairs:
        common = [s for s in specialists if a in sri.get(s, {}) and b in sri.get(s, {})]
        xa = [sri[s][a]['sri'] for s in common]
        xb = [sri[s][b]['sri'] for s in common]
        r = spearman(xa, xb) if len(common) >= 2 else None
        rho, t, label = significance(r, len(common))
        sri_results.append({'modality_a': a, 'modality_b': b, 'n_specialists': len(common),
                             'spearman_r': rho, 't_stat': t, 'significance': label,
                             'note': 'n=3 specialists -- correlation is coarse/low-power at this sample size'})

    results = {
        'modalities': modalities,
        'smhr_cross_modal_correlation': smhr_results,
        'sri_cross_modal_correlation_specialists_only': sri_results,
    }
    OUT_FILE.write_text(json.dumps(results, indent=2), encoding='utf-8')

    print('=== SMHR cross-modal Spearman correlation matrix (12 models) ===')
    header = '            ' + ''.join(f'{m:>16}' for m in modalities)
    print(header)
    for a in modalities:
        row = f'{a:<12}'
        for b in modalities:
            if a == b:
                row += f'{"1.0000":>16}'
            else:
                key = (a, b) if (a, b) in smhr_matrix else (b, a)
                v = smhr_matrix.get(key)
                row += f'{v:>16.4f}' if v is not None else f'{"n/a":>16}'
        print(row)

    print('\n=== SMHR cross-modal pairs, significance ===')
    for r in smhr_results:
        print(f'  {r["modality_a"]:<15} x {r["modality_b"]:<15} rho={r["spearman_r"]:+.4f}  t={r["t_stat"]:+.3f}  {r["significance"]}')

    print('\n=== SRI cross-modal pairs (3 specialists only) ===')
    for r in sri_results:
        rho_str = f'{r["spearman_r"]:+.4f}' if r["spearman_r"] is not None else 'n/a'
        print(f'  {r["modality_a"]:<15} x {r["modality_b"]:<15} rho={rho_str}  {r["significance"]}  ({r["note"]})')

    n_sig_pos = sum(1 for r in smhr_results if r['spearman_r'] and r['spearman_r'] > 0 and 'not significant' not in r['significance'])
    n_pairs = len(smhr_results)
    print(f'\n=== Summary ===')
    print(f'{n_sig_pos}/{n_pairs} modality pairs show a statistically significant positive SMHR correlation.')
    print(f'Saved to {OUT_FILE}')


if __name__ == '__main__':
    main()
