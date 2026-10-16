"""
Computes SMHR/CHR for a single model from layer2_judge.jsonl + layer1_verdicts.jsonl,
and saves/updates the running per-model summary at
medvihall_outputs/stage3_metrics_by_model.json.

Usage: python compute_model_metrics.py <model_name>
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

CLASS_WEIGHTS = {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.5, 5: 0.4, 6: 0.1, 7: 0.6}
SUMMARY_FILE = Path('medvihall_outputs/stage3_metrics_by_model.json')


def compute_for_model(model):
    layer1_omissions = {}
    with open('medvihall_outputs/layer1_verdicts.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r['model'] != model:
                continue
            key = (r['model'], r['image_id'], r['query_type'])
            layer1_omissions[key] = len(r.get('omissions', []))

    total_weighted = 0.0
    total_claims = 0
    n_records = 0
    n_records_with_hallucination = 0
    n_parse_errors = 0
    by_modality = defaultdict(lambda: {'weighted': 0.0, 'claims': 0, 'records': 0, 'chr_records': 0})

    with open('medvihall_outputs/layer2_judge.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r['model'] != model:
                continue
            key = (r['model'], r['image_id'], r['query_type'])
            n_records += 1
            m = r['modality']
            by_modality[m]['records'] += 1

            if r.get('_parse_error'):
                n_parse_errors += 1
                continue

            n_om = layer1_omissions.get(key, 0)
            record_weighted = n_om * CLASS_WEIGHTS[2]
            record_claims = len(r['claim_judgments']) + n_om
            has_class12 = n_om > 0

            for j in r['claim_judgments']:
                if j.get('is_hallucination'):
                    w = CLASS_WEIGHTS.get(j.get('hallucination_class'), 0)
                    record_weighted += w
                    if j.get('hallucination_class') in (1, 2):
                        has_class12 = True

            total_weighted += record_weighted
            total_claims += record_claims
            by_modality[m]['weighted'] += record_weighted
            by_modality[m]['claims'] += record_claims
            if has_class12:
                n_records_with_hallucination += 1
                by_modality[m]['chr_records'] += 1

    result = {
        'model': model,
        'n_records': n_records,
        'n_parse_errors': n_parse_errors,
        'total_claims': total_claims,
        'smhr_overall': total_weighted / total_claims if total_claims else None,
        'chr_overall': n_records_with_hallucination / n_records if n_records else None,
        'by_modality': {},
    }
    for m, s in by_modality.items():
        result['by_modality'][m] = {
            'records': s['records'],
            'claims': s['claims'],
            'smhr': s['weighted'] / s['claims'] if s['claims'] else None,
            'chr': s['chr_records'] / s['records'] if s['records'] else None,
        }
    return result


def main():
    model = sys.argv[1]
    result = compute_for_model(model)

    summary = {}
    if SUMMARY_FILE.exists():
        summary = json.loads(SUMMARY_FILE.read_text(encoding='utf-8'))
    summary[model] = result
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    print(f'=== {model} ===')
    print(f'records={result["n_records"]} parse_errors={result["n_parse_errors"]} total_claims={result["total_claims"]}')
    print(f'SMHR={result["smhr_overall"]:.4f}  CHR={result["chr_overall"]:.4f}')
    for m, s in result['by_modality'].items():
        print(f'  {m}: records={s["records"]} claims={s["claims"]} SMHR={s["smhr"]:.4f} CHR={s["chr"]:.4f}')
    print(f'Saved to {SUMMARY_FILE}')


if __name__ == '__main__':
    main()
