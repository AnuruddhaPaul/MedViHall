"""
Pillar B (RQ8) Stage 4 -- SMHR per model per strategy (baseline / RAG / contrastive), comparison, results draft.

SMHR / CHR are computed exactly as compute_model_metrics.py does for the core run:
  record_weighted = n_layer1_omissions * w[2] + sum(w[class] over Layer-2 hallucinated claims)
  record_claims   = n_layer2_claims + n_layer1_omissions
  SMHR            = sum(record_weighted) / sum(record_claims)       (CLASS_WEIGHTS below)
  CHR             = share of records with any Class 1/2 hallucination (incl. omissions)
Labels: baseline (all models but llava_med) = core labels; baseline llava_med = rerun with the decoding fix;
RAG / contrastive = pillar_b_stage3 labels (stage3_pb_label.py). A response byte-identical to the core response
reuses the core label. Unparseable judge outputs are unlabeled and excluded (counted).

Comparisons use the PAIRED set of (image, query) keys labelled under both baseline and the strategy, with a
cluster bootstrap over images (n_boot resamples) for the SMHR difference.
SRI(specialist, modality, condition) = SMHR(specialist) / SMHR(best general VLM in that modality and condition).

Outputs: medvihall_outputs/pillar_b_mitigation_results.json and pillar_b_results_section.md (data-filled draft).
Usage: python pillar_b_stage4.py [--conditions baseline rag contrastive] [--n-boot 2000]
"""
import json
import argparse
import hashlib
import collections
from pathlib import Path

import numpy as np

OUT = Path('medvihall_outputs')
CORE_L2, CORE_L1 = OUT / 'layer2_judge.jsonl', OUT / 'layer1_verdicts.jsonl'
PB_DIR = OUT / 'pillar_b_stage3'
CORE_RESULTS = OUT / 'medvihall_results_deduped.jsonl'
FILES = {'baseline': OUT / 'pillar_b_baseline.jsonl', 'rag': OUT / 'pillar_b_rag.jsonl',
         'contrastive': OUT / 'pillar_b_contrastive.jsonl'}
BASE_LLAVA_MED = OUT / 'pillar_b_baseline_llava_med_fixed.jsonl'
RESULT_JSON = OUT / 'pillar_b_mitigation_results.json'
RESULT_MD = OUT / 'pillar_b_results_section.md'
MODELS = ['qwen25vl', 'llava16', 'chexagent', 'huatuogpt', 'llava_med']
SPECIALISTS = ['chexagent', 'huatuogpt', 'llava_med']
GENERALS = ['qwen25vl', 'llava16']
MODALITIES = ['radiology', 'dermatology', 'histopathology', 'ophthalmology']
CLASS_WEIGHTS = {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.5, 5: 0.4, 6: 0.1, 7: 0.6}
MIN_CLAIMS_CELL = 100


def jl(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def pseudo_model(model, response):
    return f'{model}__{hashlib.sha1(response.encode("utf-8")).hexdigest()[:12]}'


def load_labels(l2_path, l1_path):
    """(model_key, image, qt) -> (weighted, claims, has_class12) ; parse errors absent."""
    om = {}
    if Path(l1_path).exists():
        for r in jl(l1_path):
            om[(r['model'], r['image_id'], r['query_type'])] = len(r.get('omissions', []))
    out = {}
    for r in jl(l2_path):
        if r.get('_parse_error'):
            continue
        k = (r['model'], r['image_id'], r['query_type'])
        n_om = om.get(k, 0)
        weighted, claims, c12 = n_om * CLASS_WEIGHTS[2], len(r['claim_judgments']) + n_om, n_om > 0
        for j in r['claim_judgments']:
            if j.get('is_hallucination'):
                weighted += CLASS_WEIGHTS.get(j.get('hallucination_class'), 0)
                c12 = c12 or j.get('hallucination_class') in (1, 2)
        out[k] = (weighted, claims, c12)
    return out


def chopped(t):
    t = t.strip()
    return bool(t) and (t[0].islower() or t[0] in ',.;:)%]')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conditions', nargs='*', default=['baseline', 'rag', 'contrastive'])
    ap.add_argument('--n-boot', type=int, default=2000)
    args = ap.parse_args()
    conds = args.conditions
    rng = np.random.default_rng(7)

    core_lab = load_labels(CORE_L2, CORE_L1)
    pb_lab = load_labels(PB_DIR / 'layer2_judge.jsonl', PB_DIR / 'layer1_verdicts.jsonl') if PB_DIR.exists() else {}
    core_resp = {(r['model'], r['image_id'], r['query_type']): r['response'] for r in jl(CORE_RESULTS)}
    print(f'core labels {len(core_lab)} | pillar B labels {len(pb_lab)}')

    # ---- records per condition -> {(model, img, qt): (modality, weighted, claims, c12, response)}
    cell = {}
    quality = {}
    for c in conds:
        rows = {}
        for r in jl(FILES[c]):
            rows[(r['model'], r['image_id'], r['query_type'])] = r
        if c == 'baseline' and BASE_LLAVA_MED.exists():
            for r in jl(BASE_LLAVA_MED):
                rows[(r['model'], r['image_id'], r['query_type'])] = r
        d = {}
        unlabeled = collections.Counter()
        for (m, img, qt), r in rows.items():
            resp = r['response']
            lab = None
            if c == 'baseline' and not (m == 'llava_med' and BASE_LLAVA_MED.exists()):
                lab = core_lab.get((m, img, qt))
            else:
                lab = pb_lab.get((pseudo_model(m, resp), img, qt))
                if lab is None and core_resp.get((m, img, qt)) == resp:
                    lab = core_lab.get((m, img, qt))
            if lab is None:
                unlabeled[m] += 1
                continue
            d[(m, img, qt)] = (r['modality'],) + lab + (resp,)
        cell[c] = d
        quality[c] = {m: {'records': sum(1 for k in rows if k[0] == m),
                          'unlabeled': unlabeled[m],
                          'null_confidence_rate': round(float(np.mean([rows[k].get('confidence') is None
                                                                       for k in rows if k[0] == m])), 4),
                          'chopped_start_rate': round(float(np.mean([chopped(rows[k]['response'])
                                                                     for k in rows if k[0] == m])), 4),
                          'median_words': float(np.median([len(rows[k]['response'].split())
                                                           for k in rows if k[0] == m]))} for m in MODELS}

    def agg(items):
        w = sum(i[1] for i in items)
        n = sum(i[2] for i in items)
        return {'records': len(items), 'claims': n, 'smhr': (w / n) if n else None,
                'chr': (sum(1 for i in items if i[3]) / len(items)) if items else None}

    results = {'parameters': {'conditions': conds, 'n_boot': args.n_boot, 'class_weights': CLASS_WEIGHTS,
                              'min_claims_per_cell_for_ranking': MIN_CLAIMS_CELL},
               'smhr': {}, 'paired_vs_baseline': {}, 'data_quality': quality}
    for c in conds:
        results['smhr'][c] = {}
        for m in MODELS:
            items = [v for (mm, _, _), v in cell[c].items() if mm == m]
            res = agg(items)
            res['by_modality'] = {mod: agg([i for i in items if i[0] == mod]) for mod in MODALITIES}
            results['smhr'][c][m] = res

    # ---- paired comparison vs baseline, cluster bootstrap over images
    if 'baseline' in conds:
        for c in [x for x in conds if x != 'baseline']:
            results['paired_vs_baseline'][c] = {}
            for m in MODELS:
                keys = sorted(set(k for k in cell['baseline'] if k[0] == m) & set(k for k in cell[c] if k[0] == m))
                if not keys:
                    continue
                imgs = sorted({k[1] for k in keys})
                ix = {im: i for i, im in enumerate(imgs)}
                arr = np.zeros((len(imgs), 4))        # base_w, base_n, cond_w, cond_n
                for k in keys:
                    b, t = cell['baseline'][k], cell[c][k]
                    arr[ix[k[1]]] += [b[1], b[2], t[1], t[2]]
                tot = arr.sum(axis=0)
                b_s, c_s = tot[0] / tot[1], tot[2] / tot[3]
                deltas = np.empty(args.n_boot)
                for i in range(args.n_boot):
                    s = arr[rng.integers(0, len(imgs), len(imgs))].sum(axis=0)
                    deltas[i] = s[2] / s[3] - s[0] / s[1]
                lo, hi = np.percentile(deltas, [2.5, 97.5])
                results['paired_vs_baseline'][c][m] = {
                    'n_paired_keys': len(keys), 'baseline_smhr': b_s, 'strategy_smhr': c_s, 'delta': c_s - b_s,
                    'delta_ci95': [float(lo), float(hi)], 'relative_change': (c_s - b_s) / b_s if b_s else None,
                    'significant': bool(lo > 0 or hi < 0)}

    # ---- (a)-(d)
    ans = {}
    strategies = [c for c in conds if c != 'baseline']
    if strategies and 'baseline' in conds:
        ans['a_best_strategy_per_model'] = {}
        for m in MODELS:
            opts = {c: results['paired_vs_baseline'][c][m] for c in strategies if m in results['paired_vs_baseline'].get(c, {})}
            if not opts:
                continue
            best = min(opts, key=lambda c: opts[c]['delta'])
            ans['a_best_strategy_per_model'][m] = {
                'best': best if opts[best]['delta'] < 0 else 'none (no strategy lowered SMHR)',
                'delta': opts[best]['delta'], 'delta_ci95': opts[best]['delta_ci95'], 'significant': opts[best]['significant'],
                'all': {c: {'delta': o['delta'], 'significant': o['significant']} for c, o in opts.items()}}
        bests = {m: v['best'] for m, v in ans['a_best_strategy_per_model'].items()}
        ans['b_best_differs_by_model'] = {
            'best_by_model': bests, 'same_for_all_models': len(set(bests.values())) == 1,
            'specialists': {m: bests.get(m) for m in SPECIALISTS}, 'generals': {m: bests.get(m) for m in GENERALS}}
        ans['d_strategies_that_increase_smhr'] = [
            {'model': m, 'strategy': c, 'delta': o['delta'], 'delta_ci95': o['delta_ci95'], 'significant': o['significant']}
            for c in strategies for m, o in results['paired_vs_baseline'].get(c, {}).items() if o['delta'] > 0]

    # ---- (c) SRI per condition
    sri = {}
    for c in conds:
        sri[c] = {}
        for mod in MODALITIES:
            gen = {g: results['smhr'][c][g]['by_modality'][mod] for g in GENERALS}
            gen = {g: v for g, v in gen.items() if v['smhr'] is not None and v['claims'] >= MIN_CLAIMS_CELL}
            if not gen:
                continue
            bg = min(gen, key=lambda g: gen[g]['smhr'])
            for s in SPECIALISTS:
                sv = results['smhr'][c][s]['by_modality'][mod]
                if sv['smhr'] is None or sv['claims'] < MIN_CLAIMS_CELL:
                    continue
                sri[c].setdefault(s, {})[mod] = {'sri': sv['smhr'] / gen[bg]['smhr'], 'best_general': bg}
        vals = [v['sri'] for s in sri[c].values() for v in s.values()]
        sri[c]['_mean_sri'] = float(np.mean(vals)) if vals else None
    results['sri'] = sri
    if 'baseline' in conds and sri['baseline'].get('_mean_sri'):
        b = sri['baseline']['_mean_sri']
        ans['c_specialist_vs_general_gap'] = {'baseline_mean_sri': b, 'by_strategy': {}}
        for c in strategies:
            v = sri[c].get('_mean_sri')
            if v is None:
                continue
            ans['c_specialist_vs_general_gap']['by_strategy'][c] = {
                'mean_sri': v, 'change_vs_baseline': v - b,
                'direction': 'narrows' if abs(v - 1) < abs(b - 1) else 'widens' if abs(v - 1) > abs(b - 1) else 'unchanged',
                'note': 'SRI > 1: specialists hallucinate more than the best general VLM; gap narrows when mean SRI moves toward 1'}
    results['answers'] = ans
    RESULT_JSON.write_text(json.dumps(results, indent=2, default=float), encoding='utf-8')
    print(f'wrote {RESULT_JSON}')

    # ---- markdown draft
    L = ['# Pillar B (RQ8): comparative mitigation efficacy -- results draft (auto-filled; edit prose before use)', '',
         'SMHR per model and strategy (class-weighted hallucinated claims / claims incl. Layer-1 omissions; lower is safer).',
         'Greedy decoding throughout; baseline = unmitigated prompt; RAG = top-3 modality reference snippets; '
         'contrastive = visual contrastive decoding (alpha=1.0, beta=0.1, diffusion-noise t=500).', '',
         '| Model | ' + ' | '.join(f'{c} SMHR' for c in conds) + ' | ' + ' | '.join(f'Δ {c} [95% CI]' for c in strategies) + ' |',
         '|---|' + '---|' * (len(conds) + len(strategies))]
    for m in MODELS:
        row = [f"{results['smhr'][c][m]['smhr']:.3f}" if results['smhr'][c][m]['smhr'] is not None else 'n/a' for c in conds]
        dl = []
        for c in strategies:
            o = results['paired_vs_baseline'].get(c, {}).get(m)
            dl.append('n/a' if not o else f"{o['delta']:+.3f} [{o['delta_ci95'][0]:+.3f}, {o['delta_ci95'][1]:+.3f}]{'*' if o['significant'] else ''}")
        L.append(f'| {m} | ' + ' | '.join(row) + ' | ' + ' | '.join(dl) + ' |')
    L += ['', '\\* = bootstrap 95% CI (resampling images, paired on the same image/query keys) excludes 0.', '']
    if 'a_best_strategy_per_model' in ans:
        L += ['**(a) Best strategy per model:** ' + '; '.join(
            f"{m}: {v['best']} ({v['delta']:+.3f})" for m, v in ans['a_best_strategy_per_model'].items()) + '.',
              f"**(b) Differs by model:** {'no, one strategy is best for all' if ans['b_best_differs_by_model']['same_for_all_models'] else 'yes'}"
              f" (specialists: {ans['b_best_differs_by_model']['specialists']}; generals: {ans['b_best_differs_by_model']['generals']}).",
              '**(c) Specialist-vs-general gap (mean SRI, baseline %.2f):** ' % ans.get('c_specialist_vs_general_gap', {}).get('baseline_mean_sri', float('nan')) +
              '; '.join(f"{c}: {v['mean_sri']:.2f} ({v['direction']})" for c, v in
                        ans.get('c_specialist_vs_general_gap', {}).get('by_strategy', {}).items()) + '.',
              '**(d) Strategies that increased SMHR:** ' + ('; '.join(
                  f"{o['model']}+{o['strategy']} ({o['delta']:+.3f}{', significant' if o['significant'] else ', n.s.'})"
                  for o in ans['d_strategies_that_increase_smhr']) or 'none') + '.', '']
    L += ['Data-quality notes: see `data_quality` in pillar_b_mitigation_results.json (missing-confidence, chopped-start and unlabeled rates per cell).']
    RESULT_MD.write_text('\n'.join(L), encoding='utf-8')
    print(f'wrote {RESULT_MD}')
    for c in conds:
        print(c, {m: (round(results['smhr'][c][m]['smhr'], 3) if results['smhr'][c][m]['smhr'] is not None else None) for m in MODELS})


if __name__ == '__main__':
    main()
