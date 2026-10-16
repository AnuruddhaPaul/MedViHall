"""
Stage 2, Layer 1 -- dermatology / histopathology / ophthalmology automated
detection using scispaCy NER (via an EntityRuler over a controlled keyword
lexicon -- see stage2_lexicons.py) + negspaCy negation detection.

Runs on the Python 3.12 environment (scispaCy/negspaCy need spaCy<3.9,
which has no Python 3.13 wheels -- see project notes).

For every non-radiology record in medvihall_results_deduped.jsonl, matches
each modality's canonical-class keywords in the VLM response, negates them
via negspaCy, and compares the resulting presence/absence calls against the
ground truth to flag fabrications/omissions/matches, mirroring the radiology
CheXbert script's output shape so both feed the same downstream metrics code.

Resume-safe: same pattern as stage1/stage2-radiology -- output file is the
source of truth for "already done", re-scanned on start.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from stage2_lexicons import (
    DERM_DIAGNOSIS_TO_CANONICAL, DERM_KEYWORDS,
    HISTO_TISSUE_TO_CANONICAL, HISTO_KEYWORDS,
    OPHTH_KEYWORDS,
)

RESULTS_FILE = Path('medvihall_outputs/medvihall_results_deduped.jsonl')
GT_DIR = Path('medvihall_data/data/ground_truth')
OUT_FILE = Path('medvihall_outputs/layer1_other_verdicts.jsonl')
PROGRESS_FILE = Path('medvihall_outputs/layer1_other_progress.json')

CHECKPOINT_EVERY_N = 500
MODALITIES = ['dermatology', 'histopathology', 'ophthalmology']


def load_gt_indexes():
    derm = {r['image_id']: r for r in json.load(open(GT_DIR / 'dermatology_gt_merged.json', encoding='utf-8'))}
    histo = {r['image_id']: r for r in json.load(open(GT_DIR / 'histopathology_gt_merged.json', encoding='utf-8'))}
    # NCT subset carries the richer tissue_class; merge it in by image_id.
    nct = {r['image_id']: r for r in json.load(open(GT_DIR / 'histopathology_nct_gt.json', encoding='utf-8'))}
    for image_id, r in nct.items():
        if image_id in histo:
            histo[image_id]['tissue_class'] = r.get('tissue_class')
    ophth = {r['image_id']: r for r in json.load(open(GT_DIR / 'ophthalmology_gt_merged.json', encoding='utf-8'))}
    return {'dermatology': derm, 'histopathology': histo, 'ophthalmology': ophth}


def load_source_records():
    records = []
    with open(RESULTS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r['modality'] in MODALITIES:
                records.append(r)
    return records


def load_done_keys():
    done = set()
    if not OUT_FILE.exists():
        return done
    with open(OUT_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            done.add((rec['model'], rec['image_id'], rec['query_type']))
    return done


def save_progress(n_done, n_total, started_at):
    PROGRESS_FILE.write_text(json.dumps({
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'started_at': started_at,
        'records_done': n_done,
        'records_total': n_total,
    }, indent=2), encoding='utf-8')


def build_nlp():
    import spacy
    from negspacy.negation import Negex

    nlp = spacy.load('en_core_sci_md', disable=['parser'])
    nlp.add_pipe('sentencizer')

    ruler = nlp.add_pipe('entity_ruler', before='ner')
    patterns = []
    for modality, kw_map in (('DERM', DERM_KEYWORDS), ('HISTO', HISTO_KEYWORDS), ('OPHTH', OPHTH_KEYWORDS)):
        for canonical, phrases in kw_map.items():
            label = f'{modality}::{canonical}'
            for phrase in phrases:
                patterns.append({'label': label, 'pattern': phrase})
    ruler.add_patterns(patterns)

    nlp.add_pipe('negex', config={'ent_types': [p['label'] for p in patterns]})
    return nlp


def extract_findings(nlp, text, prefix):
    """Returns {canonical_class: 'positive'|'negated'} for entities with the given label prefix."""
    if not text.strip():
        text = '[EMPTY]'
    doc = nlp(text)
    findings = {}
    for ent in doc.ents:
        if not ent.label_.startswith(prefix + '::'):
            continue
        canonical = ent.label_.split('::', 1)[1]
        status = 'negated' if ent._.negex else 'positive'
        # If any mention is positive, prefer positive (a later negated repeat shouldn't erase an earlier finding).
        if findings.get(canonical) != 'positive':
            findings[canonical] = status
    return findings


def verdict_dermatology(findings, gt):
    fabrications, omissions, matches = [], [], []
    diagnosis_raw = str(gt.get('diagnosis', '')).strip().lower()
    canonical_gt = DERM_DIAGNOSIS_TO_CANONICAL.get(diagnosis_raw)
    malignant = gt.get('malignant')

    for canonical, status in findings.items():
        if canonical in ('malignant_generic', 'benign_generic'):
            continue
        if status != 'positive':
            continue
        if canonical_gt is not None:
            if canonical == canonical_gt:
                matches.append(canonical)
            else:
                fabrications.append(canonical)
    if canonical_gt is not None and canonical_gt not in [c for c, s in findings.items() if s == 'positive']:
        omissions.append(canonical_gt)

    # Malignant/benign cross-check (independent of specific diagnosis class).
    if malignant is True and findings.get('malignant_generic') != 'positive' and canonical_gt is None:
        omissions.append('malignant_generic')
    if malignant is False and findings.get('malignant_generic') == 'positive':
        fabrications.append('malignant_generic')
    return fabrications, omissions, matches


def verdict_histopathology(findings, gt):
    fabrications, omissions, matches = [], [], []
    tissue_class = gt.get('tissue_class')  # only present for NCT subset
    tumor_present = gt.get('tumor_present')

    if tissue_class is not None:
        canonical_gt = HISTO_TISSUE_TO_CANONICAL.get(tissue_class)
        for canonical in ('tumor', 'stroma', 'debris'):
            status = findings.get(canonical)
            if status == 'positive':
                if canonical == canonical_gt:
                    matches.append(canonical)
                else:
                    fabrications.append(canonical)
        if canonical_gt and findings.get(canonical_gt) != 'positive':
            omissions.append(canonical_gt)
    else:
        # PatchCamelyon subset: binary tumor_present only.
        tumor_found = findings.get('tumor') == 'positive'
        if tumor_present is True and not tumor_found:
            omissions.append('tumor')
        if tumor_present is False and tumor_found:
            fabrications.append('tumor')
        if tumor_present is True and tumor_found:
            matches.append('tumor')
    return fabrications, omissions, matches


def verdict_ophthalmology(findings, gt):
    fabrications, omissions, matches = [], [], []
    glaucoma = gt.get('glaucoma')
    cdr_suspicious = gt.get('cdr_suspicious')

    glaucoma_found = findings.get('glaucoma') == 'positive'
    if glaucoma is True and not glaucoma_found:
        omissions.append('glaucoma')
    if glaucoma is False and glaucoma_found:
        fabrications.append('glaucoma')
    if glaucoma is True and glaucoma_found:
        matches.append('glaucoma')

    cdr_found = findings.get('cdr_elevated') == 'positive'
    if cdr_suspicious is True and not cdr_found:
        omissions.append('cdr_elevated')
    if cdr_suspicious is False and cdr_found:
        fabrications.append('cdr_elevated')
    if cdr_suspicious is True and cdr_found:
        matches.append('cdr_elevated')
    return fabrications, omissions, matches


def main():
    print(f'[{datetime.now().isoformat()}] Loading GT indexes ...')
    gt_indexes = load_gt_indexes()
    for m, idx in gt_indexes.items():
        print(f'  {m}: {len(idx)} GT records')

    print(f'[{datetime.now().isoformat()}] Loading source records ...')
    records = load_source_records()
    print(f'  {len(records)} records total across {MODALITIES}')

    print(f'[{datetime.now().isoformat()}] Scanning {OUT_FILE} for done keys ...')
    done_keys = load_done_keys()
    print(f'  {len(done_keys)} already done')

    todo = [r for r in records if (r['model'], r['image_id'], r['query_type']) not in done_keys]
    print(f'  {len(todo)} remaining')

    if not todo:
        print('Stage 2 other-modalities already complete.')
        return

    print(f'[{datetime.now().isoformat()}] Loading spaCy + scispaCy + negspaCy pipeline ...')
    nlp = build_nlp()
    print('  Loaded.')

    prefix_by_modality = {'dermatology': 'DERM', 'histopathology': 'HISTO', 'ophthalmology': 'OPHTH'}
    verdict_fn = {
        'dermatology': verdict_dermatology,
        'histopathology': verdict_histopathology,
        'ophthalmology': verdict_ophthalmology,
    }

    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    n_done = 0
    n_no_gt = 0

    out_f = open(OUT_FILE, 'a', encoding='utf-8')
    try:
        for r in todo:
            modality = r['modality']
            gt = gt_indexes[modality].get(r['image_id'])
            findings = extract_findings(nlp, r['response'], prefix_by_modality[modality])

            if gt is None:
                fabrications, omissions, matches = [], [], []
                n_no_gt += 1
            else:
                fabrications, omissions, matches = verdict_fn[modality](findings, gt)

            rec_out = {
                'model': r['model'], 'image_id': r['image_id'], 'modality': modality,
                'query_type': r['query_type'],
                'findings': findings,
                'gt_found': gt is not None,
                'fabrications': fabrications, 'omissions': omissions, 'matches': matches,
            }
            out_f.write(json.dumps(rec_out, ensure_ascii=False) + '\n')
            n_done += 1

            if n_done % CHECKPOINT_EVERY_N == 0:
                out_f.flush()
                os.fsync(out_f.fileno())
                save_progress(len(done_keys) + n_done, len(records), started_at)
                elapsed = time.time() - t0
                rate = n_done / elapsed
                eta_h = (len(todo) - n_done) / rate / 3600 if rate > 0 else float('inf')
                print(f'  [{n_done}/{len(todo)}] elapsed={elapsed/60:.1f}min rate={rate:.2f}rec/s '
                      f'no_gt={n_no_gt} ETA={eta_h:.2f}h')
    finally:
        out_f.close()
        save_progress(len(done_keys) + n_done, len(records), started_at)

    print(f'\n[{datetime.now().isoformat()}] Stage 2 other-modalities run finished. Processed: {n_done}, no_gt={n_no_gt}')
    print(f'  Total done overall: {len(done_keys) + n_done} / {len(records)}')


if __name__ == '__main__':
    main()
