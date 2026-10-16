"""
Stage 3 (Pillar D) -- ECE / ACE per model per config, plus rank stability.

Correctness label (per spec): a response is "correct" iff it contains zero
Class 1-7 hallucinations. Primary label ("strict") counts Layer 2 claim
hallucinations (classes 1,3-7) AND Layer 1 omissions (class 2), matching how
compute_model_metrics.py folds omissions back in. A claim-level-only variant
("claims") is reported as a sensitivity check.

Confidence = the parsed 0-100 confidence field; responses with no stated
confidence cannot enter ECE/ACE and are counted as coverage loss per cell.
Label source per response: byte-identical to the core response -> core Layer
1/2 labels; otherwise -> fresh Pillar D labels (pillar_d_stage3/).

ECE: 10 equal-width bins, bin-size-weighted. ACE: 10 equal-mass bins,
unweighted mean |accuracy - confidence| (binary single-class case).

Usage (project root):  python stage3_pd_ece.py [--boot 500]
"""
import json
import sys
import argparse
from pathlib import Path
from itertools import combinations

import numpy as np

import stage3_pd_label as L

CORE_L2 = Path('medvihall_outputs/layer2_judge.jsonl')
CORE_L1 = Path('medvihall_outputs/layer1_verdicts.jsonl')
OUT_JSON = Path('medvihall_outputs/pillar_d_calibration_results.json')

MODELS = ['qwen25vl', 'llava16', 'chexagent', 'huatuogpt', 'llava_med']
CONFIGS = ['temp0.0_greedy', 'temp0.0_nucleus', 'temp0.3_greedy',
           'temp0.3_nucleus', 'temp0.7_greedy', 'temp0.7_nucleus']
MIN_N = 50
N_BINS = 10


def load_labels(l2_path, l1_path):
    """(model, image, qt) -> {'claims_ok': bool, 'n_omissions': int}; unparseable judge -> absent."""
    omissions = {}
    for r in L._iter_jsonl(l1_path):
        omissions[(r['model'], r['image_id'], r['query_type'])] = len(r.get('omissions', []))
    out = {}
    for r in L._iter_jsonl(l2_path):
        if r.get('_parse_error'):
            continue
        k = (r['model'], r['image_id'], r['query_type'])
        hall = any(j.get('is_hallucination') and j.get('hallucination_class') in (1, 2, 3, 4, 5, 6, 7)
                   for j in r.get('claim_judgments', []) if isinstance(j, dict))
        out[k] = {'claims_ok': not hall, 'n_omissions': omissions.get(k, 0)}
    return out


def ece_ace(conf, correct, rng_key=None):
    n = len(conf)
    if n == 0:
        return None, None
    conf = np.asarray(conf, float)
    correct = np.asarray(correct, float)
    idx = np.minimum((conf * N_BINS).astype(int), N_BINS - 1)
    ece = 0.0
    for b in range(N_BINS):
        m = idx == b
        if m.any():
            ece += m.sum() / n * abs(correct[m].mean() - conf[m].mean())
    order = np.argsort(conf, kind='stable')
    chunks = np.array_split(order, N_BINS)
    ace = float(np.mean([abs(correct[c].mean() - conf[c].mean()) for c in chunks if len(c)]))
    return float(ece), ace


def boot_ci(conf, correct, n_boot, seed=0):
    rng = np.random.default_rng(seed)
    conf = np.asarray(conf, float)
    correct = np.asarray(correct, float)
    n = len(conf)
    vals = []
    for _ in range(n_boot):
        s = rng.integers(0, n, n)
        vals.append(ece_ace(conf[s], correct[s])[0])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def rank(values):
    order = np.argsort(values, kind='stable')
    ranks = np.empty(len(values))
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float('nan')
    return float(np.corrcoef(ra, rb)[0, 1])


def stability(table, models, configs):
    """table[(model, config)] = ECE. Pairwise Spearman of model rankings across configs."""
    present = [m for m in models if all(table.get((m, c)) is not None for c in configs)]
    if len(present) < 3:
        return None
    vecs = {c: [table[(m, c)] for m in present] for c in configs}
    rhos = {f'{a} vs {b}': spearman(vecs[a], vecs[b]) for a, b in combinations(configs, 2)}
    vals = [v for v in rhos.values() if v == v]
    return {'models': present, 'pairwise_rho': rhos,
            'mean_rho': float(np.mean(vals)) if vals else None,
            'min_rho': float(np.min(vals)) if vals else None,
            'rankings': {c: [present[i] for i in np.argsort(vecs[c], kind='stable')] for c in configs}}


def verdict(mean_rho):
    if mean_rho is None:
        return 'insufficient data'
    if mean_rho >= 0.8:
        return 'STABLE -- calibration ranking is a weights property'
    if mean_rho <= 0.4:
        return 'SHIFTS -- calibration ranking is a decoding artifact'
    return 'PARTIALLY STABLE -- inconclusive (0.4 < mean rho < 0.8)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boot', type=int, default=500)
    args = ap.parse_args()

    runs, excluded, regenerated = L.load_effective_runs()
    core = L.load_core_responses()
    core_labels = load_labels(CORE_L2, CORE_L1)
    fresh_labels = load_labels(L.L2, L.L1_ALL)
    print(f'effective runs {len(runs)} (excluded capped llava16 {excluded}, regenerated {regenerated}); '
          f'core labels {len(core_labels)}, fresh labels {len(fresh_labels)}')

    cells = {}
    cov = {}
    for (m, cfg, img, qt), r in runs.items():
        c = cov.setdefault((m, cfg), {'total': 0, 'with_conf': 0, 'labeled': 0, 'unlabeled': 0})
        c['total'] += 1
        if r.get('confidence') is None:
            continue
        c['with_conf'] += 1
        resp = r['response']
        if core.get((m, img, qt)) == resp:
            lab = core_labels.get((m, img, qt))
        else:
            lab = fresh_labels.get((L.pseudo_model(m, resp), img, qt))
        if lab is None:
            c['unlabeled'] += 1
            continue
        c['labeled'] += 1
        conf = min(max(float(r['confidence']), 0.0), 100.0) / 100.0
        cells.setdefault((m, cfg), []).append(
            (conf, lab['claims_ok'] and lab['n_omissions'] == 0, lab['claims_ok']))

    results = {}
    for (m, cfg), rows in sorted(cells.items()):
        conf = [x[0] for x in rows]
        out = {'coverage': cov[(m, cfg)], 'mean_conf': float(np.mean(conf))}
        for name, col in (('strict', 1), ('claims', 2)):
            corr = [x[col] for x in rows]
            e, a = ece_ace(conf, corr)
            cell = {'n': len(rows), 'accuracy': float(np.mean(corr)), 'ece': e, 'ace': a}
            if len(rows) >= MIN_N:
                lo, hi = boot_ci(conf, corr, args.boot)
                cell.update(ece_ci95=[lo, hi])
            else:
                cell.update(ece=None, ace=None)
            out[name] = cell
        results[f'{m}|{cfg}'] = out

    summary = {}
    for name in ('strict', 'claims'):
        table = {(m, c): results.get(f'{m}|{c}', {}).get(name, {}).get('ece') for m in MODELS for c in CONFIGS}
        eff = ['temp0.0_greedy', 'temp0.0_nucleus', 'temp0.3_nucleus', 'temp0.7_nucleus']
        summary[name] = {
            'all_6_configs': stability(table, MODELS, CONFIGS),
            'distinct_4_settings': stability(table, MODELS, eff),
            'all_6_configs_excl_llava16': stability(table, [m for m in MODELS if m != 'llava16'], CONFIGS),
            'distinct_4_settings_excl_llava16': stability(table, [m for m in MODELS if m != 'llava16'], eff),
        }
        for k, v in summary[name].items():
            if v:
                v['verdict'] = verdict(v['mean_rho'])

    OUT_JSON.write_text(json.dumps({'cells': results, 'rank_stability': summary,
                                    'notes': {'excluded_capped_llava16': excluded,
                                              'regenerated_llava16': regenerated, 'min_n': MIN_N}},
                                   indent=1), encoding='utf-8')

    for name in ('strict', 'claims'):
        print(f'\n=== label = {name} ===  ECE / ACE  (n)')
        print(f'{"model":10s}' + ''.join(f'{c.replace("temp", "t"):>24s}' for c in CONFIGS))
        for m in MODELS:
            row = f'{m:10s}'
            for c in CONFIGS:
                cell = results.get(f'{m}|{c}', {}).get(name)
                if not cell or cell['ece'] is None:
                    row += f'{"n/a":>24s}'
                else:
                    row += f'{cell["ece"]:.3f}/{cell["ace"]:.3f} ({cell["n"]})'.rjust(24)
            print(row)
        for k, v in summary[name].items():
            if v:
                print(f'  {k:34s} mean rho={v["mean_rho"]:.3f} min={v["min_rho"]:.3f} -> {v["verdict"]}')
    print(f'\nfull results -> {OUT_JSON}')


if __name__ == '__main__':
    main()
