"""LaTeX (booktabs) + CSV tables T1-T5.  Every number is read from a result file or recomputed from the judged records."""
import re

import numpy as np
import pandas as pd

import fig_style as st
from fig_common import Ctx, TAB_DIR, fmt_ci
from fig_data import OUT, ROOT, MissingData, load_json, need, load_registry, param_billions

SCRIPT = 'tables.py'
ANN = ROOT / 'annotation_results'


def tex_esc(s):
    s = str(s)
    for a, b in (('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('_', r'\_'), ('#', r'\#')):
        s = s.replace(a, b)
    return s


def _ci2(s):
    lo, hi = (float(x) for x in str(s).split('..'))
    return f'{lo:.2f}, {hi:.2f}'


def _tabular(header, rows, colspec, groups=None, size='\\small'):
    """rows: list of lists (already escaped strings); a row equal to ('MID', text) inserts a sub-heading."""
    out = [size, f'\\begin{{tabular}}{{{colspec}}}', '\\toprule', ' & '.join(header) + ' \\\\', '\\midrule']
    for k, r in enumerate(rows):
        if isinstance(r, tuple) and r[0] == 'MID':
            out += (['\\midrule'] if k else []) + [f'\\multicolumn{{{len(header)}}}{{l}}{{\\textit{{{r[1]}}}}} \\\\', '\\midrule']
        elif isinstance(r, tuple) and r[0] == 'RULE':
            out.append('\\midrule')
        else:
            out.append(' & '.join(r) + ' \\\\')
    out += ['\\bottomrule', '\\end{tabular}']
    return '\n'.join(out)


def _write(ctx, name, env, body, caption, label, csv_df, sources, claim, wide=False):
    star = '*' if wide else ''
    tex = f'\\begin{{table{star}}}[t]\n\\centering\n{body}\n\\caption{{{caption}}}\n\\label{{{label}}}\n\\end{{table{star}}}\n'
    (TAB_DIR / f'{name}.tex').write_text(tex, encoding='utf-8')
    csv_df.to_csv(TAB_DIR / f'{name}.csv', index=False)
    ctx.tables.append(dict(name=name, sources=sources, func=f'{SCRIPT}:{env}', claim=claim, caption=caption))


# ------------------------------------------------------------------ T1
def t1(ctx: Ctx):
    img = ctx.images
    rows, csv = [], []
    for mod in st.MODALITY_ORDER:
        for stt in sorted(img.loc[img['modality'] == mod, 'stratum'].unique()):
            g = img[(img['modality'] == mod) & (img['stratum'] == stt)]
            normal = stt in st.NORMAL_STRATA
            n = len(g)
            resp = n * (4 if normal else 3)
            srcs = '; '.join(f'{k} ({v})' for k, v in g['source'].value_counts().items())
            csv.append(dict(modality=mod, stratum=stt, type='normal' if normal else 'abnormal', images=n, responses_per_model=resp, sources=srcs))
            rows.append([st.MODALITY_SHORT[mod], stt, 'normal' if normal else 'abnormal', tex_esc(srcs), f'{n:,}', f'{resp:,}'])
    c = pd.DataFrame(csv)
    rows.append(('RULE',))
    rows.append(['Total', '', '', '', f'{c["images"].sum():,}', f'{c["responses_per_model"].sum():,}'])
    per_model = int((ctx.df['model'] == ctx.models[0]).sum())
    ctx.check('T1_resp', int(c['responses_per_model'].sum()) == per_model,
              'T1: images x (3 prompts, +Q4 for normal strata) == records per model in layer2_judge.jsonl', f'{int(c["responses_per_model"].sum())} vs {per_model}')
    body = _tabular(['Modality', 'Stratum', 'Type', 'Source dataset (images)', 'Images', 'Responses / model'], rows, 'lllp{5.2cm}rr')
    _write(ctx, 'T1_dataset_strata', 't1', body,
           f'Benchmark composition: {len(img):,} images in {img["stratum"].nunique()} design strata. Normal strata receive four prompts (Q1--Q4), abnormal strata three (Q1--Q3).',
           'tab:dataset', c, ['medvihall_data/data/ground_truth/manifest_3500.json'], 'Dataset and strata counts.')


# ------------------------------------------------------------------ T2
def t2(ctx: Ctx):
    reg = load_registry()
    rows, csv = [], []
    for m in ctx.models:
        r = reg[m]
        local = r['repo_id'].split('/')[-1] if r['repo_id'] else None
        # local dir names follow the repo name for the five locally stored models
        pb, src = param_billions(r['label'], local)
        typ = 'Medical specialist' if ctx.is_medical[m] else 'General'
        csv.append(dict(key=m, model=r['label'], type=typ, params_billion=pb, params_source=src, hf_repo=r['repo_id']))
        rows.append([tex_esc(r['label']), typ, f'{pb:g}' if pb else 'n/a', '\\texttt{' + tex_esc(r['repo_id']) + '}'])
    c = pd.DataFrame(csv)
    if c['params_billion'].isna().any():
        ctx.note('Parameter count not recorded for: ' + ', '.join(c.loc[c['params_billion'].isna(), 'key']) + ' (shown as n/a).', fig='T2')
    ctx.note('Parameter counts are taken from the model label in the inference notebook (nominal size) and, for MiniCPM-V-2.6, from the local safetensors metadata; '
             'they are not exact parameter counts of every checkpoint (e.g. vision towers are included only in the safetensors case).', fig='T2')
    body = _tabular(['Model', 'Type', 'Params (B)', 'Checkpoint'], rows, 'llrl')
    _write(ctx, 'T2_models', 't2', body, 'The 12 evaluated VLMs, in the fixed presentation order (general models, then medical specialists).', 'tab:models', c,
           ['MedViHall_Phase3_Phase4_v4.ipynb (MODEL_REGISTRY: label, repo id)', 'medvihall_outputs/metrics_summary.json (is_medical)', 'models/MiniCPM-V-2_6/model.safetensors.index.json'],
           'Model list.')


# ------------------------------------------------------------------ T3
def t3(ctx: Ctx):
    scopes = [None] + st.MODALITY_ORDER
    heads = ['Model', 'Overall'] + [st.MODALITY_ABBR[m] for m in st.MODALITY_ORDER]
    rows, csv = [], []
    for field, title in (('smhr', 'SMHR [95\\% CI] (lower is safer)'), ('chr', 'CHR [95\\% CI]: share of responses with a class 1 or 2 hallucination')):
        rows.append(('MID', title))
        for m in ctx.models:
            line = [tex_esc(ctx.name(m)) + ('$^{\\dagger}$' if m in st.SPECIALISTS else '')]
            for sc in scopes:
                c = ctx.cell(m, sc, field)
                line.append(fmt_ci(c['point'], c['lo'], c['hi']))
                csv.append(dict(model=m, type='specialist' if m in st.SPECIALISTS else 'general', metric=field.upper(), scope=sc or 'overall',
                                value=c['point'], ci_lo=c['lo'], ci_hi=c['hi'],
                                n_images=int(ctx.boot.mask(sc).sum()) if sc else len(ctx.images)))
            rows.append(line)
    body = _tabular(heads, rows, 'lccccc', size='\\scriptsize')
    cap = (f'Core-run results for 12 VLMs on {len(ctx.images):,} images. Intervals are 95\\% image-level bootstrap CIs ({ctx.boot.B:,} resamples, stratified by design stratum, seed {ctx.boot.seed}); '
           '$^{\\dagger}$ medical specialist. CHR = share of responses containing at least one fabrication or omission.')
    _write(ctx, 'T3_main_results', 't3', body, cap, 'tab:main', pd.DataFrame(csv),
           ['medvihall_outputs/layer2_judge.jsonl', 'medvihall_outputs/layer1_verdicts.jsonl', 'medvihall_outputs/metrics_summary.json (cross-check)'],
           'Main SMHR / CHR results.', wide=True)


# ------------------------------------------------------------------ T4
def t4(ctx: Ctx):
    d = load_json(OUT / 'pillar_b_mitigation_results.json')
    pv = d['paired_vs_baseline']
    strategies = [s for s in ('rag', 'contrastive') if s in pv]
    models = [m for m in ctx.models if m in pv[strategies[0]]]
    rows, csv = [], []
    for m in models:
        line = [tex_esc(ctx.name(m)) + ('$^{\\dagger}$' if m in st.SPECIALISTS else ''), f'{d["smhr"]["baseline"][m]["smhr"]:.3f}']
        for s in strategies:
            r = pv[s][m]
            lo, hi = r['delta_ci95']
            mark = ('$^{*}$' if r['significant'] else '') + (' (up)' if r['delta'] > 0 else '')
            line += [f'{r["strategy_smhr"]:.3f}', f'{r["delta"]:+.3f} [{lo:+.3f}, {hi:+.3f}]{mark}']
            csv.append(dict(model=m, strategy=s, baseline_smhr=r['baseline_smhr'], strategy_smhr=r['strategy_smhr'], delta=r['delta'], ci_lo=lo, ci_hi=hi,
                            ci_excludes_0=r['significant'], increases_smhr=r['delta'] > 0, n_paired_keys=r['n_paired_keys'], n_boot=d['parameters']['n_boot']))
        rows.append(line)
    head = ['Model', 'Baseline SMHR'] + sum([[f'{st.STRATEGY_NAMES[s]} SMHR', f'$\\Delta$ vs. baseline'] for s in strategies], [])
    body = _tabular(head, rows, 'lc' + 'cc' * len(strategies), size='\\footnotesize')
    cap = (f'Mitigation results on a 500-image subset (greedy decoding, paired image-query responses). $\\Delta$ = strategy minus matched baseline with 95\\% paired image-level bootstrap CI '
           f'({d["parameters"]["n_boot"]:,} resamples); $^{{*}}$ CI excludes 0, (up) = SMHR increased; $^{{\\dagger}}$ medical specialist. Fine-tuning results are not available.')
    _write(ctx, 'T4_mitigation', 't4', body, cap, 'tab:mitigation', pd.DataFrame(csv), ['medvihall_outputs/pillar_b_mitigation_results.json'],
           'Mitigation deltas.', wide=True)


# ------------------------------------------------------------------ T5
def t5(ctx: Ctx):
    a1 = pd.read_csv(need(ANN / 'A1_score_agreement_overall.csv'))
    a3 = pd.read_csv(need(ANN / 'A3_flag_agreement_overall.csv'))
    b1 = pd.read_csv(need(ANN / 'B1_judge_vs_human_per_class.csv'))
    csv = []
    rowsA = []
    for _, r in a1.iterrows():
        q = r['QWK_mean_pairwise_0.5bins']
        rowsA.append([tex_esc(r['dimension'].replace('_', ' ')), f'{r["ICC2_1"]:.3f} [{r["ICC2_1_ci"].replace("..", ", ")}]', f'{r["ICC2_k"]:.3f}',
                      f'{r["alpha_interval"]:.3f}', f'{q:.3f}'])
        csv.append(dict(part='A_scores', row=r['dimension'], n_items=r['n_items'], icc2_1=r['ICC2_1'], icc2_1_ci=r['ICC2_1_ci'], icc2_k=r['ICC2_k'],
                        krippendorff_alpha=r['alpha_interval'], qwk_mean_pairwise=q))
    tabA = _tabular(['Score (0--5)', 'ICC(2,1) [95\\% CI]', 'ICC(2,k)', 'Alpha', 'QWK'], rowsA, 'lcccc', size='\\small')
    rowsB = []
    for c in a3['class']:
        r3 = a3[a3['class'] == c].iloc[0]
        r1 = b1[b1['class'] == c].iloc[0]
        nm = c.replace('_', ' ').capitalize()
        f1 = f'{r1["F1"]:.2f}' if pd.notna(r1['F1']) else 'undef.'
        rowsB.append([tex_esc(nm) + ('$^{a}$' if bool(r3['RARE_class_kappa_unstable']) else ''), f'{r3["prevalence"]:.2f}', f'{r3["fleiss_kappa"]:.2f} [{_ci2(r3["fleiss_kappa_ci"])}]',
                      f'{r1["cohen_kappa"]:.2f} [{_ci2(r1["kappa_ci"])}]', f1])
        csv.append(dict(part='B_flags', row=c, n_items=int(r3['n_items']), prevalence=r3['prevalence'], fleiss_kappa=r3['fleiss_kappa'], fleiss_kappa_ci=r3['fleiss_kappa_ci'],
                        judge_vs_majority_kappa=r1['cohen_kappa'], judge_vs_majority_kappa_ci=r1['kappa_ci'], judge_vs_majority_f1=r1['F1'],
                        rare_class_unstable=bool(r3['RARE_class_kappa_unstable'])))
    tabB = _tabular(['Hallucination class', 'Prevalence', 'Fleiss $\\kappa$ [95\\% CI]', 'Judge vs. majority $\\kappa$ [95\\% CI]', 'Judge F1'], rowsB, 'lcccc', size='\\small')
    body = tabA + '\n\\par\\medskip\n' + tabB
    cap = ('Agreement among six \\emph{simulated (AI-persona) annotators} on 720 items (48 distinct images), and between the LLM judge and the annotator majority. '
           'No clinician annotations are included. Intervals are 95\\% item-level bootstrap CIs and are optimistic because items share images; $^{a}$ rare class, $\\kappa$ unstable.')
    _write(ctx, 'T5_annotation_agreement', 't5', body, cap, 'tab:annotation', pd.DataFrame(csv),
           ['annotation_results/A1_score_agreement_overall.csv', 'annotation_results/A3_flag_agreement_overall.csv', 'annotation_results/B1_judge_vs_human_per_class.csv'],
           'Annotation agreement (simulated annotators).')
