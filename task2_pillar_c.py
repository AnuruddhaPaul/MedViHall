"""
Task 2 (Pillar C, RQ9): CREST and MediHall Score, computed over the same
classified claims as SMHR (layer2_judge.jsonl + layer1_verdicts.jsonl
omissions folded in), then Spearman-correlated against SMHR rankings.

Formula sources (looked up, not guessed):
- CREST ("Clinically-Informed Framework for Evaluating VLMs in Radiology
  Report Generation", PMC12919594): CREST = (1/N) * sum(r(e_i)) over the N
  erroneous claims, r(e_i) in {1=Low, 2=Medium, 3=High} clinical risk.
- MediHall Score (Med-HallMark / "Detecting and Evaluating Medical
  Hallucinations in Large Vision Language Models", arXiv:2406.10185):
  per-claim Hi in {0.0=Catastrophic, 0.2=Critical, 0.4=Attribute,
  0.6=Prompt-induced, 0.8=Minor, 1.0=Correct}, score = mean(Hi) over ALL
  claims (report/answer-level average).

Both papers use their own error taxonomies, which don't line up 1:1 with
this project's 7-class taxonomy. Mapped by preserving the existing
clinician severity ranking (1=2=1.0 > 3=0.7 > 7=0.6 > 4=0.5 > 5=0.4 > 6=0.1)
onto each paper's tiers -- documented explicitly here rather than silently:

  CREST risk tier:      class 1,2 -> High(3);  class 3,7 -> Medium(2);  class 4,5,6 -> Low(1)
  MediHall Hi:          class 1,2 -> 0.0 (Catastrophic -- matches the paper's OWN
                                            definition: "omissions or fabrications")
                         class 3   -> 0.2 (Critical -- matches "misjudging disease type")
                         class 7   -> 0.4 (Attribute)
                         class 4   -> 0.6 (Prompt-induced)
                         class 5,6 -> 0.8 (Minor)
                         not-hallucination -> 1.0 (Correct)

Note the key structural difference this preserves: CREST's denominator (N)
is the ERROR count only, while MediHall Score's and SMHR's denominator is
ALL claims -- so CREST measures "how bad are the errors when they happen"
while SMHR/MediHall measure "how much of the output is bad overall". A
model with few-but-severe errors will show high CREST but modest SMHR;
that's the divergence pattern this task asks to find, not a bug.
"""
import json
import math
from pathlib import Path
from collections import defaultdict

LAYER2_FILE = Path('medvihall_outputs/layer2_judge.jsonl')
LAYER1_FILE = Path('medvihall_outputs/layer1_verdicts.jsonl')
OUT_FILE = Path('medvihall_outputs/pillar_c_metric_concordance.json')

CREST_RISK = {1: 3, 2: 3, 3: 2, 7: 2, 4: 1, 5: 1, 6: 1}
MEDIHALL_HI = {1: 0.0, 2: 0.0, 3: 0.2, 7: 0.4, 4: 0.6, 5: 0.8, 6: 0.8}
NOT_HALLUCINATION_HI = 1.0


def spearman(x, y):
    """Spearman rank correlation, no scipy dependency needed."""
    n = len(x)
    def rank(vals):
        order = sorted(range(n), key=lambda i: vals[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks
    rx, ry = rank(x), rank(y)
    mean_rx, mean_ry = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    var_x = sum((v - mean_rx) ** 2 for v in rx)
    var_y = sum((v - mean_ry) ** 2 for v in ry)
    if var_x == 0 or var_y == 0:
        return None
    return cov / math.sqrt(var_x * var_y)


def load_layer1_omissions():
    out = {}
    with open(LAYER1_FILE, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            key = (r['model'], r['image_id'], r['query_type'])
            out[key] = len(r.get('omissions', []))
    return out


def main():
    omissions = load_layer1_omissions()

    # (model, modality) -> list of (is_hallucination, class_or_None)
    points = defaultdict(list)

    with open(LAYER2_FILE, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r.get('_parse_error'):
                continue
            key = (r['model'], r['image_id'], r['query_type'])
            mk = (r['model'], r['modality'])

            n_om = omissions.get(key, 0)
            for _ in range(n_om):
                points[mk].append((True, 2))

            for j in r['claim_judgments']:
                cls = j.get('hallucination_class')
                is_hall = bool(j.get('is_hallucination')) and cls in CREST_RISK
                points[mk].append((is_hall, cls if is_hall else None))

    models = sorted({m for (m, _mod) in points})
    modalities = sorted({mod for (_m, mod) in points})

    per_model_modality = {}
    per_model_overall = defaultdict(list)  # model -> pooled points across modalities

    for m in models:
        per_model_modality[m] = {}
        for mod in modalities:
            pts = points.get((m, mod), [])
            if not pts:
                continue
            per_model_modality[m][mod] = pts
            per_model_overall[m].extend(pts)

    def compute_crest_medihall(pts):
        total = len(pts)
        if total == 0:
            return None, None, 0, 0
        errors = [cls for (is_h, cls) in pts if is_h]
        n_errors = len(errors)
        crest = (sum(CREST_RISK[c] for c in errors) / n_errors) if n_errors else None
        medihall_sum = sum(MEDIHALL_HI[c] if is_h else NOT_HALLUCINATION_HI for (is_h, c) in pts)
        medihall = medihall_sum / total
        return crest, medihall, total, n_errors

    results = {'models': {}}
    for m in models:
        results['models'][m] = {'overall': {}, 'by_modality': {}}
        crest, medihall, total, n_err = compute_crest_medihall(per_model_overall[m])
        results['models'][m]['overall'] = {
            'crest': crest, 'medihall_score': medihall, 'n_claims': total, 'n_errors': n_err,
        }
        for mod in modalities:
            pts = per_model_modality[m].get(mod, [])
            crest, medihall, total, n_err = compute_crest_medihall(pts)
            results['models'][m]['by_modality'][mod] = {
                'crest': crest, 'medihall_score': medihall, 'n_claims': total, 'n_errors': n_err,
            }

    # Load SMHR for correlation + divergence analysis.
    metrics_summary = json.loads(Path('medvihall_outputs/metrics_summary.json').read_text(encoding='utf-8'))
    smhr_overall = {m: metrics_summary['models'][m]['smhr_overall'] for m in models}

    crest_overall = {m: results['models'][m]['overall']['crest'] for m in models}
    medihall_overall = {m: results['models'][m]['overall']['medihall_score'] for m in models}

    smhr_vals = [smhr_overall[m] for m in models]
    crest_vals = [crest_overall[m] for m in models]
    medihall_vals = [medihall_overall[m] for m in models]

    correlations = {
        'smhr_vs_crest': spearman(smhr_vals, crest_vals),
        'smhr_vs_medihall': spearman(smhr_vals, medihall_vals),
        'crest_vs_medihall': spearman(crest_vals, medihall_vals),
    }
    results['spearman_correlations_overall'] = correlations

    # Divergence: z-score SMHR and CREST at model x modality granularity, flag |diff| > 1 SD.
    mm_smhr, mm_crest = {}, {}
    for m in models:
        for mod in modalities:
            s = metrics_summary['models'][m]['by_modality'].get(mod, {}).get('smhr')
            c = results['models'][m]['by_modality'].get(mod, {}).get('crest')
            if s is not None and c is not None:
                mm_smhr[(m, mod)] = s
                mm_crest[(m, mod)] = c

    def zscores(d):
        vals = list(d.values())
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        return {k: (v - mean) / std if std else 0.0 for k, v in d.items()}, mean, std

    z_smhr, smhr_mean, smhr_std = zscores(mm_smhr)
    z_crest, crest_mean, crest_std = zscores(mm_crest)

    divergences = []
    for key in mm_smhr:
        diff = z_smhr[key] - z_crest[key]
        if abs(diff) > 1.0:
            m, mod = key
            pts = per_model_modality[m].get(mod, [])
            n_claims = len(pts)
            n_errors = sum(1 for (is_h, _) in pts if is_h)
            hallucination_rate = n_errors / n_claims if n_claims else 0
            divergences.append({
                'model': m, 'modality': mod,
                'smhr': mm_smhr[key], 'crest': mm_crest[key],
                'z_smhr': z_smhr[key], 'z_crest': z_crest[key], 'z_diff': diff,
                'n_claims': n_claims, 'n_errors': n_errors, 'hallucination_rate': hallucination_rate,
                'pattern': (
                    'high SMHR-vs-CREST (frequent but comparatively mild errors)' if diff > 0
                    else 'high CREST-vs-SMHR (rare but severe errors)'
                ),
            })
    divergences.sort(key=lambda d: -abs(d['z_diff']))
    results['smhr_crest_divergences'] = divergences

    OUT_FILE.write_text(json.dumps(results, indent=2), encoding='utf-8')

    print('=== Spearman correlations across 12 models (overall) ===')
    for k, v in correlations.items():
        print(f'  {k}: {v:.4f}' if v is not None else f'  {k}: n/a')

    print('\n=== SMHR / CREST / MediHall Score rankings (sorted by SMHR ascending) ===')
    print(f'{"model":<12}{"SMHR":>10}{"CREST":>10}{"MediHall":>10}')
    for m in sorted(models, key=lambda m: smhr_overall[m]):
        print(f'{m:<12}{smhr_overall[m]:>10.4f}{crest_overall[m]:>10.4f}{medihall_overall[m]:>10.4f}')

    print(f'\n=== SMHR vs CREST divergences (>1 SD in z-score), {len(divergences)} found ===')
    for d in divergences:
        print(f'  {d["model"]:<12} {d["modality"]:<15} SMHR={d["smhr"]:.4f} CREST={d["crest"]:.4f} '
              f'z_diff={d["z_diff"]:+.2f}  n_claims={d["n_claims"]} hallucination_rate={d["hallucination_rate"]:.3f}  {d["pattern"]}')

    print(f'\nSaved to {OUT_FILE}')


if __name__ == '__main__':
    main()
