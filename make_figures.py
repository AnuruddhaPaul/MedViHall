"""
Regenerate every MedViHall paper figure, table, figure_manifest.md and figure_checks.md.

    python make_figures.py            # uses the cached judged-record table if the inputs are unchanged
    python make_figures.py --rebuild  # re-derive the record table from layer2_judge/layer1_verdicts first

Style/venue sizes live in fig_style.py.  Figure code: figs_a.py (Figs 1-5), figs_b.py (Figs 6-12);
tables: tables.py; shared context, checks and saving: fig_common.py; data layer: fig_data.py.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import fig_style as st
import fig_data as fd
import fig_common as fc
import figs_a
import figs_b
import tables

ROOT = Path(__file__).resolve().parent

FIGURES = [('Fig 1', figs_a.fig01), ('Fig 2', figs_a.fig02), ('Fig 3', figs_a.fig03), ('Fig 4', figs_a.fig04), ('Fig 5', figs_a.fig05),
           ('Fig 6', figs_b.fig06), ('Fig 7', figs_b.fig07), ('Fig 8', figs_b.fig08), ('Fig 9', figs_b.fig09),
           ('Fig 10', figs_b.fig10), ('Fig 11', figs_b.fig11), ('Fig 12', figs_b.fig12)]
TABLES = [('T1', tables.t1), ('T2', tables.t2), ('T3', tables.t3), ('T4', tables.t4), ('T5', tables.t5)]

# (placement, reason) -- the reasons are judgements made after looking at the computed results.
PLACEMENT = {
    1: ('main', 'introduces the pipeline; no data'),
    2: ('main', 'headline ranking; the rank-range column makes the CI caveat visible'),
    3: ('main', 'modality dependence plus class composition in one figure'),
    4: ('main', 'the specialisation paradox is the central claim; all 12 SRI intervals sit above 1'),
    5: ('appendix', 'direction of the normal-vs-abnormal gap is not uniform (ophthalmology: normal lower; others mixed); only the Q4 effect is clear, and it fits one sentence in the text'),
    6: ('appendix', '3 of 6 pairs significant, radiology transfers weakly; one sentence plus the appendix figure is enough'),
    7: ('appendix', 'MediHall agreement is near-definitional (rho = -1); CREST rho can be quoted in text'),
    8: ('appendix', 'calibration is a secondary pillar; quote ECE range and rank stability in text'),
    9: ('main', 'mitigation is a headline contribution, but note it covers 5 models on a 500-image subset and no fine-tuning arm'),
    10: ('main (recommended) -- NOT AVAILABLE', 'no Pillar A result file exists'),
    11: ('appendix -- NOT AVAILABLE', 'no Pillar H result file exists'),
    12: ('appendix', 'only valid if labelled as simulated annotators; must not be placed as clinician validation'),
}


# ------------------------------------------------------------------ extra data-driven checks
def llava_med_decoder_check(ctx):
    """Quantify the known llava_med chopped-start decoding issue in the core run."""
    ctx.current = 'core'
    fixed = fd.OUT / 'pillar_b_baseline_llava_med_fixed.jsonl'
    res = fd.OUT / 'medvihall_results_deduped.jsonl'
    mit = fd.OUT / 'pillar_b_mitigation_results.json'
    try:
        fd.need(fixed), fd.need(res), fd.need(mit)
    except fd.MissingData as e:
        ctx.note(f'llava_med decoder check skipped: {e}')
        return
    keys = set()
    with open(fixed, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            keys.add((r['image_id'], r['query_type']))
    d = ctx.df[ctx.df['model'] == 'llava_med']
    d = d[[(i, q) in keys for i, q in zip(d['image_id'], d['query_type'])]]
    core_sub = d['w'].sum() / d['claims'].sum()
    fixed_smhr = fd.load_json(mit)['smhr']['baseline']['llava_med']['smhr']
    tot = chop = 0
    with open(res, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            t = (r['response'] or '').lstrip()
            if r['model'] != 'llava_med' or r['query_type'] != 'Q1' or not t:
                continue
            tot += 1
            chop += t[0].islower() or t[0] in ',.;:)'
    other = 0
    n_o = 0
    with open(res, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            t = (r['response'] or '').lstrip()
            if r['model'] == 'llava_med' or r['query_type'] != 'Q1' or not t:
                continue
            n_o += 1
            other += t[0].islower() or t[0] in ',.;:)'
    ctx.decoder = dict(chop=chop / tot, n=tot, other=other / max(n_o, 1), core_sub=core_sub, fixed=fixed_smhr, n_keys=len(keys),
                       claims_core=float(d['claims'].mean()))
    ctx.check('X01', False, 'DECISION NEEDED: llava_med core-run responses are affected by the chopped-start decoder bug',
              f'{chop / tot:.1%} of {tot:,} llava_med Q1 responses start mid-sentence (lower-case/punctuation first character) vs {other / max(n_o, 1):.1%} for the other 11 models; '
              f'on the same {len(keys):,} (image, query) keys llava_med SMHR is {core_sub:.3f} in the core run but {fixed_smhr:.3f} with the fixed decoder (Pillar B baseline). '
              f'Figs 2-5, 7 and Tables T3 use the core-run value ({ctx.cell("llava_med")["point"]:.3f}); llava_med\'s ranking and SRI may be overstated.')
    ctx.note(f'llava_med core-run SMHR ({core_sub:.3f} on the Pillar B subset keys) vs decoder-fixed rerun ({fixed_smhr:.3f}): difference {core_sub - fixed_smhr:+.3f}. '
             f'Core-run llava_med averages {d["claims"].mean():.2f} claims per response on those keys. '
             'This is not corrected in any figure; the core-run numbers are plotted as saved (they match the sanity values).', fig='Figs 2-5, 7, T3')


def write_checks(ctx, started, stop=None):
    n_pass = sum(1 for c in ctx.checks if c[1] == 'PASS')
    fails = [c for c in ctx.checks if c[1] == 'FAIL']
    L = ['# Figure checks', '',
         f'Generated by `make_figures.py` on {time.strftime("%Y-%m-%d %H:%M")} ({time.time() - started:.0f} s).', '']
    if stop:
        L += ['## STOPPED', '', stop, '', 'No figure was plotted after the core check failed.', '']
    L += ['## Summary', '',
          f'- Assertions: {n_pass} passed, {len(fails)} flagged (FAIL rows below; those with id `X..` are findings that need your decision, not code errors).',
          f'- Figures written: {len(ctx.manifest)} of 12; tables written: {len(ctx.tables)} of 5.',
          f'- Bootstrap: {ctx.boot.B:,} resamples of IMAGES (never claims), stratified by the 13 design strata, fixed seed {ctx.boot.seed}, percentile 95% intervals; '
          'the same resampled images are used for every model and metric (paired). SRI keeps the point-estimate best-general model fixed. '
          'Mitigation deltas and calibration intervals are read from the saved Pillar B / D files (2,000 resamples, images/responses as documented there).', '']
    L += ['## Findings that need your decision', '']
    for c in fails:
        if c[0].startswith('X'):
            L += [f'- **{c[2]}.** {c[3]}']
    L += ['- **AI-persona annotators.** `human_annotations/` holds Claude-generated persona outputs that were renamed; Fig 12 and T5 are therefore labelled "simulated annotators" and must not be cited as clinician validation (see `annotation_report.md`).',
          '- **Hard-coded Hugging Face token** in `MedViHall_Phase3_Phase4_v4.ipynb` (cell 5, `HF_TOKEN`). It was not read into any output here, but it should be rotated and removed before the repo is shared.',
          '- **Judge/extractor overlap.** Claims are extracted and judged by Qwen2.5-7B-Instruct while four evaluated models are Qwen-family and occupy the top of the ranking; a judge self-preference effect is untested.', '']
    L += ['## Figures not generated', '']
    for k, why in ctx.not_generated:
        L += [f'- **{k}**: {why}']
    L += ['- **Fig 9 fine-tuning arm**: no fine-tuning result file exists in `medvihall_outputs/`; Fig 9 shows RAG and contrastive decoding only.',
          '- **Pillar F / Pillar G**: intentionally not made (removed / on hold).', '']
    L += ['## Where the text must not claim a ranking (overlapping intervals)', '']
    for fig, t in ctx.overlaps:
        L += [f'- **{fig}**: {t}']
    L += ['']
    L += ['## Numbers that looked odd or need a caveat', '']
    for fig, t in ctx.notes:
        L += [f'- **{fig}**: {t}']
    L += ['', '## All assertions', '', '| id | result | assertion | detail |', '|---|---|---|---|']
    for cid, status, desc, det in ctx.checks:
        L += [f'| {cid} | {status} | {desc} | {str(det).replace("|", "/").replace(chr(10), " ")[:300]} |']
    (ROOT / 'figure_checks.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def write_manifest(ctx):
    L = ['# Figure manifest', '',
         'Each entry lists the source result files, the script and function, the claim the figure supports, and a draft caption '
         '(two sentences, sample size and meaning of the error bars stated). Source data for every figure sits beside it as `<name>.csv`; '
         'vector PDF and 300 dpi PNG are in `paper_figures/`. Regenerate everything with `python make_figures.py`.', '',
         f'Venue sizes (fig_style.py): single column {st.COLUMN_WIDTH_IN} in, double column {st.DOUBLE_COLUMN_IN} in, text height {st.TEXT_HEIGHT_IN} in (placeholder until the venue is chosen).', '']
    caveat = getattr(ctx, 'decoder', None)
    for e in sorted(ctx.manifest, key=lambda x: x['num']):
        n = e['num']
        L += [f'## Fig {n} -- `{e["name"]}`', '',
              f'- **Files:** `paper_figures/{e["name"]}.pdf`, `.png`, `.csv`',
              '- **Source result files:** ' + '; '.join(f'`{s}`' if '(' not in s else s for s in e['sources']),
              f'- **Script / function:** `{e["func"]}` (run via `make_figures.py`)',
              f'- **Claim supported:** {e["claim"]}',
              f'- **Draft caption:** {e["caption"]}',
              f'- **Size:** {e["width_in"]:.2f} x {e["height_in"]:.2f} in']
        cav = [t for f, t in ctx.overlaps if f in (f'Fig {n}',)]
        if cav:
            L += ['- **Ranking caveat:** ' + ' '.join(cav)]
        if caveat and n in (2, 3, 4, 5, 7):
            L += [f'- **Caveat (llava_med decoder):** {caveat["chop"]:.0%} of core-run llava_med Q1 responses start mid-sentence; its core SMHR is {caveat["core_sub"]:.3f} vs {caveat["fixed"]:.3f} with the fixed decoder on the same responses\' keys. See figure_checks.md.']
        if n == 12:
            L += ['- **Caveat (provenance):** annotators are AI personas, not clinicians; say so in the caption (the draft caption does).']
        L += ['']
    L += ['## Tables', '']
    for t in ctx.tables:
        L += [f'### {t["name"]}', f'- Files: `paper_tables/{t["name"]}.tex`, `paper_tables/{t["name"]}.csv`',
              '- Source: ' + '; '.join(f'`{s}`' for s in t['sources']), f'- Function: `{t["func"]}`', f'- Supports: {t["claim"]}', f'- Draft caption: {t["caption"]}', '']
    # page budget
    L += ['## Page budget and main/appendix split', '',
          f'Heights below are at the sizes set in `fig_style.py` (page text height {st.TEXT_HEIGHT_IN:.1f} in; two single-column figures can sit side by side).', '',
          '| Fig | Width x height (in) | Space | Placement | Why |', '|---|---|---|---|---|']
    by = {e['num']: e for e in ctx.manifest}
    main_full = main_single = 0.0
    for n in range(1, 13):
        pl, why = PLACEMENT[n]
        if n in by:
            e = by[n]
            wide = e['width_in'] > st.COLUMN_WIDTH_IN + 0.3
            space = f'{e["height_in"] / st.TEXT_HEIGHT_IN:.0%} of a page (full width)' if wide else f'{e["height_in"] / st.TEXT_HEIGHT_IN:.0%} of a column'
            L += [f'| {n} | {e["width_in"]:.1f} x {e["height_in"]:.1f} | {space} | {pl} | {why} |']
            if pl == 'main':
                if wide:
                    main_full += e['height_in']
                else:
                    main_single += e['height_in']
        else:
            L += [f'| {n} | -- | -- | {pl} | {why} |']
    L += ['', f'Main-paper figures made here (1, 2, 3, 4, 9) need about {(main_full + main_single / 2) / st.TEXT_HEIGHT_IN:.1f} pages '
              f'({main_full:.1f} in of full-width figures plus {main_single:.1f} in of single-column figures that pair up). '
              'Your recommended main set (1, 2, 3, 4, 9, 10) holds, except that Fig 10 (Pillar A) cannot be made, so the main paper currently has five figures. '
              'To save space: place Fig 2 and Fig 4 side by side as one full-width strip, and keep 5-8 and 12 in the appendix.', '']
    (ROOT / 'figure_manifest.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def main():
    started = time.time()
    force = '--rebuild' in sys.argv
    ctx = fc.Ctx(force_rebuild=force)
    stop = None
    try:
        ctx.run_core_checks()
    except fc.StopFigures as e:
        stop = str(e)
        write_checks(ctx, started, stop)
        print('STOPPED:', stop)
        sys.exit(1)
    llava_med_decoder_check(ctx)
    for label, fn in FIGURES:
        fc.safe_run(ctx, label, fn)
    for label, fn in TABLES:
        fc.safe_run(ctx, label, fn)
    for e in ctx.manifest:
        ok = all((fc.FIG_DIR / f'{e["name"]}.{x}').exists() and (fc.FIG_DIR / f'{e["name"]}.{x}').stat().st_size > 0 for x in ('pdf', 'png', 'csv'))
        ctx.check(f'F{e["num"]:02d}_files', ok, f'Fig {e["num"]}: PDF, PNG and source CSV written')
    write_manifest(ctx)
    write_checks(ctx, started)
    print(f'{len(ctx.manifest)} figures, {len(ctx.tables)} tables written; {len(ctx.not_generated)} not generated.')
    for k, why in ctx.not_generated:
        print(' not generated:', k, '--', why[:110])
    for c in ctx.checks:
        if c[1] == 'FAIL':
            print(' FLAG', c[0], c[2][:100])


if __name__ == '__main__':
    main()
