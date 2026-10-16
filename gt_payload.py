"""
Shared ground-truth payload construction for Stage 3 (LLM-as-judge).

Builds the richest-available GROUND_TRUTH JSON per modality/record, per the
design confirmed against the actual GT schemas (see gt_coverage_notes.json
for the full class-coverage rationale).
"""
import json
from pathlib import Path

GT_DIR = Path('medvihall_data/data/ground_truth')

GT_FILES = {
    'radiology':      GT_DIR / 'radiology_gt_merged.json',
    'dermatology':     GT_DIR / 'dermatology_gt_merged.json',
    'histopathology':  GT_DIR / 'histopathology_gt_merged.json',
    'ophthalmology':   GT_DIR / 'ophthalmology_gt_merged.json',
}


def load_gt_index():
    """modality -> {image_id: record}"""
    index = {}
    for modality, path in GT_FILES.items():
        with open(path, encoding='utf-8') as f:
            records = json.load(f)
        index[modality] = {r['image_id']: r for r in records}
    return index


def build_gt_payload(modality, gt_record):
    """
    Richest-available GT payload per modality, for embedding into the
    Stage 3 judge prompt as GROUND_TRUTH JSON.
    """
    if gt_record is None:
        return {}

    if modality == 'radiology':
        return {
            'positive_labels': gt_record.get('positive_labels', []),
            'negative_labels': gt_record.get('negative_labels', []),
            'no_finding':      gt_record.get('no_finding'),
            'n_positive':      gt_record.get('n_positive'),
        }

    if modality == 'dermatology':
        return {
            'diagnosis':        gt_record.get('diagnosis'),
            'malignant':        gt_record.get('malignant'),
            'anatomical_site':  gt_record.get('anatomical_site'),
        }

    if modality == 'histopathology':
        # Richest-available: NCT-CRC subset has a genuine 3-class tissue_class
        # (STR/TUM/DEB); PatchCamelyon subset only has a constant tissue_type
        # ('breast') and binary tumor_present. Use tissue_class/tissue_full
        # when present (multi-class), else fall back to the binary fields.
        payload = {
            'tumor_present':    gt_record.get('tumor_present'),
            'expert_verified':  gt_record.get('expert_verified'),
            'ambiguous':        gt_record.get('ambiguous'),
        }
        if gt_record.get('tissue_class') is not None:
            payload['tissue_class'] = gt_record.get('tissue_class')
            payload['tissue_full']  = gt_record.get('tissue_full')
        else:
            payload['tissue_type'] = gt_record.get('tissue_type')
        return payload

    if modality == 'ophthalmology':
        return {
            'glaucoma':         gt_record.get('glaucoma'),
            'cup_disc_ratio':   gt_record.get('cup_disc_ratio'),
            'cdr_suspicious':   gt_record.get('cdr_suspicious'),
        }

    return {}
