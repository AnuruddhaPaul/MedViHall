"""
Robustness checks for the Pillar D (RQ10) rank-stability verdict. CPU only.
All checks use the strict label (zero Class 1-7 hallucinations incl. omissions)
and report mean pairwise Spearman rho across configs ("all6" = every config,
"distinct4" = greedy + the three nucleus settings, since the three greedy
configs are the same decoding).

  A. ECE binning: 5 / 10 / 15 / 20 bins
  B. By modality (each modality analysed separately)
  C. Common-coverage subset: only (image, query) items where all 5 models
     stated a confidence in that config
  D. Label-noise simulation: flip labels at the measured judge flip rate,
     one draw per distinct response (identical text -> identical judgment)
  E. Leave-one-model-out

Usage (project root):  python stage3_pd_robustness.py
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import stage3_pd_label as L
import stage3_pd_ece as E

OUT = Path('medvihall_outputs/pillar_d_robustness.json')
MODELS, CONFIGS = E.MODELS, E.CONFIGS
DISTINCT4 = ['temp0.0_greedy', 'temp0.0_nucleus', 'temp0.3_nucleus', 'temp0.7_nucleus']


def build_rows():
    runs, _, _ = L.load_effective_runs()
    core = L.load_core_responses()
    core_labels = E.load_labels(E.CORE_L2, E.CORE_L1)
    fresh_labels = E.load_labels(L.L2, L.L1_ALL)
    rows = defaultdict(list)
    for (m, cfg, img, qt), r in runs.items():
        if r.get('confidence') is None:
            continue
        resp = r['response']
        if core.get((m, img, qt)) == resp:
            lab = core_labels.get((m, img, qt))
        else:
            lab = fresh_labels.get((L.pseudo_model(m, resp), img, qt))
        if lab is None:
            continue
        rows[(m, cfg)].append({
            'img': img, 'qt': qt, 'mod': r['modality'],
            'conf': min(max(float(r['confidence']), 0.0), 100.0) / 100.0,
            'ok': bool(lab['claims_ok'] and lab['n_omissions'] == 0),
            'rid': (m, img, qt, L.response_hash(resp)),
        })
    return rows


def ece_table(rows, min_n=50, n_bins=10):
    E.N_BINS = n_bins
    table = {}
    for m in MODELS:
        for c in CONFIGS:
            rs = rows.get((m, c), [])
            table[(m, c)] = (E.ece_ace([x['conf'] for x in rs], [x['ok'] for x in rs])[0]
                             if len(rs) >= min_n else None)
    return table


def rho_summary(table, models=MODELS):
    out = {}
    for name, cfgs in (('all6', CONFIGS), ('distinct4', DISTINCT4)):
        st = E.stability(table, models, cfgs)
        out[name] = None if st is None else {'mean_rho': st['mean_rho'], 'min_rho': st['min_rho'],
                                             'n_models': len(st['models'])}
    return out


def fmt(s):
    return ' | '.join(f'{k}: ' + ('n/a' if v is None else f'{v["mean_rho"]:.2f} (min {v["min_rho"]:.2f}, {v["n_models"]} models)')
                      for k, v in s.items())


def main():
    rows = build_rows()
    result = {}

    print('A. ECE bin count')
    result['A_bins'] = {}
    for k in (5, 10, 15, 20):
        s = rho_summary(ece_table(rows, n_bins=k))
        result['A_bins'][k] = s
        print(f'  {k:2d} bins -> {fmt(s)}')
    E.N_BINS = 10

    print('B. By modality')
    result['B_modality'] = {}
    for mod in ('radiology', 'dermatology', 'histopathology', 'ophthalmology'):
        sub = {k: [x for x in v if x['mod'] == mod] for k, v in rows.items()}
        tab = ece_table(sub, min_n=40)
        present = [m for m in MODELS if all(tab.get((m, c)) is not None for c in CONFIGS)]
        s = rho_summary(tab, present) if len(present) >= 3 else None
        n = {m: min((len(sub.get((m, c), [])) for c in CONFIGS)) for m in MODELS}
        result['B_modality'][mod] = {'models_used': present, 'min_n_per_model': n,
                                     'rho': s, 'ece_greedy': {m: tab[(m, 'temp0.0_greedy')] for m in MODELS}}
        print(f'  {mod:15s} models={present} -> {fmt(s) if s else "insufficient data"}')
        print('      ECE@greedy:', {m: (None if v is None else round(v, 3)) for m, v in result['B_modality'][mod]['ece_greedy'].items()},
              ' min n:', n)

    print('C. Common-coverage subset (all 5 models stated a confidence)')
    common = {}
    for c in CONFIGS:
        sets = [{(x['img'], x['qt']) for x in rows.get((m, c), [])} for m in MODELS]
        common[c] = set.intersection(*sets) if all(sets) else set()
    sub = {(m, c): [x for x in rows.get((m, c), []) if (x['img'], x['qt']) in common[c]]
           for m in MODELS for c in CONFIGS}
    n_common = {c: len(common[c]) for c in CONFIGS}
    s = rho_summary(ece_table(sub, min_n=30))
    result['C_common_coverage'] = {'n_items_per_config': n_common, 'rho': s}
    print(f'  common items per config: {n_common}')
    print(f'  {fmt(s)}')

    print('D. Label-noise simulation (200 reps per rate; flip per distinct response)')
    rid_index = {}
    for rs in rows.values():
        for x in rs:
            rid_index.setdefault(x['rid'], len(rid_index))
    cells = {}
    for key, rs in rows.items():
        if len(rs) >= 50:
            cells[key] = (np.array([x['conf'] for x in rs]), np.array([x['ok'] for x in rs]),
                          np.array([rid_index[x['rid']] for x in rs]))
    base = rho_summary(ece_table(rows))
    result['D_noise'] = {'baseline': base}
    print(f'  baseline (no flips): {fmt(base)}')
    rng = np.random.default_rng(7)
    E.N_BINS = 10
    for p in (0.05, 0.13, 0.20):
        res = {'all6': [], 'distinct4': []}
        for _ in range(200):
            flip = rng.random(len(rid_index)) < p
            table = {k: E.ece_ace(conf, ok ^ flip[idx])[0] for k, (conf, ok, idx) in cells.items()}
            s = rho_summary(table)
            for name in res:
                if s[name]:
                    res[name].append(s[name]['mean_rho'])
        summ = {name: {'mean': float(np.mean(v)), 'p05': float(np.percentile(v, 5)),
                       'frac_ge_0.8': float(np.mean(np.array(v) >= 0.8))} for name, v in res.items()}
        result['D_noise'][str(p)] = summ
        print(f'  flip {p:.2f}: ' + ' | '.join(
            f'{n}: mean {x["mean"]:.2f}, 5th pct {x["p05"]:.2f}, P(rho>=0.8)={x["frac_ge_0.8"]:.2f}' for n, x in summ.items()))

    print('E. Leave-one-model-out')
    base_table = ece_table(rows)
    result['E_leave_one_out'] = {}
    for drop in MODELS:
        s = rho_summary(base_table, [m for m in MODELS if m != drop])
        result['E_leave_one_out'][drop] = s
        print(f'  without {drop:10s} -> {fmt(s)}')

    OUT.write_text(json.dumps(result, indent=1, default=str), encoding='utf-8')
    print(f'\nsaved -> {OUT}')


if __name__ == '__main__':
    main()
