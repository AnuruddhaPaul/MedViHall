"""
Stage 4 -- final metrics: SMHR, CHR (already computed per-model/per-modality
in stage3_metrics_by_model.json) plus SRI (Specialist Ratio Index), computed
per specialist model per modality:

    SRI(specialist, modality) = SMHR(specialist, modality) / SMHR(best general VLM, modality)

"Best general VLM" = lowest SMHR (least hallucination) among non-specialist
models in that modality. Specialist identity comes from the is_medical flag
already present in medvihall_results_deduped.jsonl -- not hardcoded.

An SRI < 1.0 means the specialist model hallucinates less than the best
general VLM in that modality (specialization helping); SRI > 1.0 means it
hallucinates more despite being domain-specific.

Saves medvihall_outputs/metrics_summary.json and prints a summary table.
"""
import json
from pathlib import Path

PER_MODEL_FILE = Path('medvihall_outputs/stage3_metrics_by_model.json')
RESULTS_FILE = Path('medvihall_outputs/medvihall_results_deduped.jsonl')
OUT_FILE = Path('medvihall_outputs/metrics_summary.json')


def load_is_medical_map():
    m = {}
    with open(RESULTS_FILE, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            m[r['model']] = r['is_medical']
    return m


def main():
    per_model = json.loads(PER_MODEL_FILE.read_text(encoding='utf-8'))
    is_medical = load_is_medical_map()

    specialists = sorted(m for m in per_model if is_medical.get(m))
    generals = sorted(m for m in per_model if not is_medical.get(m))
    print(f'Specialists (is_medical=True): {specialists}')
    print(f'General VLMs: {generals}')

    modalities = sorted({m for r in per_model.values() for m in r['by_modality']})

    # Best general VLM per modality = lowest SMHR among generals.
    best_general = {}
    for modality in modalities:
        candidates = [(m, per_model[m]['by_modality'][modality]['smhr'])
                      for m in generals if modality in per_model[m]['by_modality']]
        best_model, best_smhr = min(candidates, key=lambda x: x[1])
        best_general[modality] = {'model': best_model, 'smhr': best_smhr}

    sri = {}  # specialist -> modality -> value
    for spec in specialists:
        sri[spec] = {}
        for modality in modalities:
            if modality not in per_model[spec]['by_modality']:
                continue
            spec_smhr = per_model[spec]['by_modality'][modality]['smhr']
            base = best_general[modality]['smhr']
            sri[spec][modality] = {
                'sri': spec_smhr / base if base else None,
                'specialist_smhr': spec_smhr,
                'best_general_model': best_general[modality]['model'],
                'best_general_smhr': base,
            }

    summary = {
        'models': {
            m: {
                'is_medical': is_medical.get(m, False),
                'smhr_overall': r['smhr_overall'],
                'chr_overall': r['chr_overall'],
                'n_records': r['n_records'],
                'n_parse_errors': r['n_parse_errors'],
                'by_modality': {
                    mod: {'smhr': s['smhr'], 'chr': s['chr'], 'records': s['records'], 'claims': s['claims']}
                    for mod, s in r['by_modality'].items()
                },
            }
            for m, r in per_model.items()
        },
        'best_general_vlm_by_modality': best_general,
        'sri': sri,
    }
    OUT_FILE.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    print(f'\n=== Overall SMHR / CHR (sorted by SMHR, ascending = safer) ===')
    print(f'{"model":<12} {"specialist":<11} {"SMHR":>8} {"CHR":>8}')
    for m in sorted(per_model, key=lambda m: per_model[m]['smhr_overall']):
        r = per_model[m]
        print(f'{m:<12} {str(is_medical.get(m,False)):<11} {r["smhr_overall"]:>8.4f} {r["chr_overall"]:>8.4f}')

    print(f'\n=== Best general VLM per modality ===')
    for modality, info in best_general.items():
        print(f'  {modality}: {info["model"]} (SMHR={info["smhr"]:.4f})')

    print(f'\n=== SRI (specialist SMHR / best-general SMHR) per modality ===')
    print(f'{"specialist":<12}' + ''.join(f'{m:>16}' for m in modalities))
    for spec in specialists:
        row = f'{spec:<12}'
        for modality in modalities:
            v = sri[spec].get(modality, {}).get('sri')
            row += f'{v:>16.4f}' if v is not None else f'{"n/a":>16}'
        print(row)

    print(f'\nSaved to {OUT_FILE}')


if __name__ == '__main__':
    main()
