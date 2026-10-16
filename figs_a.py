"""Figures 1-5 (benchmark overview and core core-run results)."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

import fig_style as st
from fig_common import Ctx, ci_overlap, spread_labels, fmt_ci
from fig_data import pct_ci, OUT, load_json, need

SCRIPT = 'figs_a.py'


def _style_model_ticklabels(ax, models, axis='y'):
    labels = ax.get_yticklabels() if axis == 'y' else ax.get_xticklabels()
    for lab, m in zip(labels, models):
        if m in st.SPECIALISTS:
            lab.set_fontweight('bold')
            lab.set_color('#7F2704')


# =========================================================================== Fig 1
def fig01(ctx: Ctx):
    df = ctx.df
    n_img = len(ctx.images)
    n_models = df['model'].nunique()
    n_gen = sum(1 for m in ctx.models if not ctx.is_medical[m])
    n_spec = n_models - n_gen
    per_model = int((df['model'] == ctx.models[0]).sum())
    n_claims = int(df['claims'].sum())
    n_strata = ctx.images['stratum'].nunique()
    qts = sorted(df['query_type'].unique())

    fig, ax = plt.subplots(figsize=(st.DOUBLE_COLUMN_IN, 2.35))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 33)
    ax.axis('off')

    def box(x, y, w, h, head, body, fc='#F2F2F2', ec='#404040'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.25,rounding_size=1.2',
                                    fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h - 1.4, head, ha='center', va='top', fontsize=st.FS_LABEL, fontweight='bold')
        ax.text(x + w / 2, y + h - 5.0, body, ha='center', va='top', fontsize=st.FS_BASE, linespacing=1.25)

    def arrow(x0, y0, x1, y1):
        ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle='-|>', lw=1.0, color='#404040', shrinkA=0, shrinkB=0))

    w = 17.0
    xs = [0.8, 21.2, 41.6, 62.0, 82.4]
    y0, h = 8.5, 22.0
    box(xs[0], y0, w, h, 'Images',
        f'{n_img:,} images\n4 modalities\n{n_strata} strata\n(normal, abnormal)\nwith GT labels', fc='#E8F1FA')
    box(xs[1], y0, w, h, 'VLMs',
        f'{n_models} VLMs\n{n_gen} general,\n{n_spec} medical\n{len(qts)} prompts Q1-Q4\n{per_model:,} resp./model', fc='#E8F1FA')
    box(xs[2], y0, w, h, 'Claims',
        f'LLM splits each\nresponse into\natomic claims\n{n_claims:,} claims\n(incl. omissions)', fc='#EEF6EE')
    # Layer 1 / Layer 2 stacked in column 4
    box(xs[3], 18.0, w, 12.5, 'Layer 1', 'rule-based vs. GT:\nCheXbert (radiol.),\nscispaCy (others)', fc='#FFF4E0')
    box(xs[3], 3.0, w, 12.5, 'Layer 2', 'LLM judge assigns\neach claim one of\n7 classes (below)', fc='#FFF4E0')
    wts = ctx.W
    box(xs[4], y0, w, h, 'Metrics',
        'SMHR = sum(w n)/N\nCHR, SRI\nweights ' + f'{min(wts.values()):.1f}-{max(wts.values()):.1f}\n'
        'bootstrap CIs\nover images', fc='#FBE9E7')
    for i in range(3):
        arrow(xs[i] + w + 0.4, y0 + h / 2, xs[i + 1] - 0.4, y0 + h / 2)
    arrow(xs[2] + w + 0.4, y0 + h / 2 + 3, xs[3] - 0.4, 24.0)
    arrow(xs[2] + w + 0.4, y0 + h / 2 - 3, xs[3] - 0.4, 9.0)
    arrow(xs[3] + w + 0.4, 24.0, xs[4] - 0.4, y0 + h / 2 + 3)
    arrow(xs[3] + w + 0.4, 9.0, xs[4] - 0.4, y0 + h / 2 - 3)
    names = [f'{k} {st.CLASS_NAMES[k].lower()}' for k in st.CLASS_IDS]
    ax.text(50, 0.4, 'Classes: ' + '; '.join(names), ha='center', va='bottom', fontsize=st.FS_BASE, color='#404040')

    src = pd.DataFrame([
        ('images', n_img), ('modalities', ctx.images['modality'].nunique()), ('strata', n_strata),
        ('vlms', n_models), ('general_vlms', n_gen), ('specialist_vlms', n_spec),
        ('prompts', len(qts)), ('responses_per_model', per_model), ('claims_total_incl_omissions', n_claims),
        *[(f'class_weight_{k}', v) for k, v in wts.items()]], columns=['item', 'value'])
    meta = ctx.save(fig, 'fig01_overview', src)
    ctx.add_manifest(
        num=1, name='fig01_overview', func=f'{SCRIPT}:fig01',
        sources=['medvihall_data/data/ground_truth/manifest_3500.json (image/stratum counts)',
                 'medvihall_outputs/layer2_judge.jsonl, layer1_verdicts.jsonl (response/claim counts)',
                 'compute_model_metrics.py (class weights)'],
        claim='The benchmark is a two-layer, claim-level pipeline whose output is a severity-weighted rate.',
        caption=(f'Overview of MedViHall: {n_img:,} images from four modalities are shown to {n_models} VLMs, responses are split into '
                 f'claims, checked by an automated Layer 1 and an LLM-judge Layer 2, and aggregated into severity-weighted metrics (SMHR). '
                 f'Counts are read from the result files; the pipeline description follows the stage scripts.'),
        **meta)


# =========================================================================== Fig 2
def fig02(ctx: Ctx):
    models = ctx.models
    n_img = len(ctx.images)
    cells = {m: ctx.cell(m) for m in models}
    boots = np.column_stack([cells[m]['boots'] for m in models])
    ranks = boots.argsort(axis=1).argsort(axis=1) + 1
    rank_pt = pd.Series({m: cells[m]['point'] for m in models}).rank().astype(int)
    cu = {m: ctx.boot_u.ratio(m)[1] for m in models}

    fig, ax = plt.subplots(figsize=(st.COLUMN_WIDTH_IN, 3.0))
    ypos = {m: len(models) - 1 - i for i, m in enumerate(models)}
    spec_y = [ypos[m] for m in models if m in st.SPECIALISTS]
    ax.axhspan(min(spec_y) - 0.5, max(spec_y) + 0.5, color='#FBE9D8', lw=0, zorder=0)
    rows = []
    for m in models:
        c = cells[m]
        ax.hlines(ypos[m], c['lo'], c['hi'], color=st.MODEL_COLORS[m], lw=1.6, zorder=2)
        ax.plot(c['point'], ypos[m], marker=st.MODEL_MARKERS[m], color=st.MODEL_COLORS[m], mec='black', mew=0.4,
                ms=st.MS + (2 if st.MODEL_MARKERS[m] in '*' else 0), zorder=3, ls='none')
        r_lo, r_hi = np.quantile(ranks[:, models.index(m)], [0.025, 0.975])
        ax.text(1.02, ypos[m], f'{int(r_lo)}' if r_lo == r_hi else f'{int(r_lo)}-{int(r_hi)}',
                transform=ax.get_yaxis_transform(), ha='left', va='center', fontsize=st.FS_BASE)
        u_lo, u_hi = pct_ci(cu[m])
        rows.append(dict(model=m, group='specialist' if m in st.SPECIALISTS else 'general', smhr=c['point'],
                         ci_lo=c['lo'], ci_hi=c['hi'], ci_lo_unstratified=u_lo, ci_hi_unstratified=u_hi,
                         rank_point=int(rank_pt[m]), rank_lo=int(r_lo), rank_hi=int(r_hi),
                         n_images=n_img, n_responses=int((ctx.df['model'] == m).sum()),
                         n_claims=int(ctx.df.loc[ctx.df['model'] == m, 'claims'].sum())))
    ax.set_yticks([ypos[m] for m in models])
    ax.set_yticklabels([ctx.name(m) for m in models])
    _style_model_ticklabels(ax, models)
    ax.set_ylim(-0.6, len(models) - 0.4)
    lo = min(r['ci_lo'] for r in rows)
    hi = max(r['ci_hi'] for r in rows)
    ax.set_xlim(np.floor(lo * 20) / 20 - 0.01, np.ceil(hi * 20) / 20 + 0.01)
    ax.set_xlabel('SMHR (severity-weighted hallucinated\nclaims per claim; lower is safer)')
    ax.text(1.02, len(models) - 0.35, 'rank\nrange', transform=ax.get_yaxis_transform(), ha='left', va='bottom',
            fontsize=st.FS_BASE, color=st.NEUTRAL)
    ax.text(ax.get_xlim()[0] + 0.006, np.mean(spec_y), 'medical\nspecialists', fontsize=st.FS_BASE, color='#7F2704',
            va='center', ha='left', style='italic')
    ax.grid(axis='x', lw=0.4)
    src = pd.DataFrame(rows)

    # ranking caveats: marginal CI overlap and paired differences between neighbours
    over_s, over_u, notsig = [], [], []
    for a, b in zip(models[:-1], models[1:]):
        ca, cb = cells[a], cells[b]
        if ci_overlap(ca['lo'], ca['hi'], cb['lo'], cb['hi']):
            over_s.append(f'{a}~{b}')
        ua, ub = pct_ci(cu[a]), pct_ci(cu[b])
        if ci_overlap(*ua, *ub):
            over_u.append(f'{a}~{b}')
        d_lo, d_hi = pct_ci(cells[b]['boots'] - cells[a]['boots'])
        if d_lo <= 0 <= d_hi:
            notsig.append(f'{a} vs {b} (diff {fmt_ci(cells[b]["point"] - cells[a]["point"], d_lo, d_hi)})')
    ctx.overlap_note('Adjacent models whose 95% CIs overlap (stratified bootstrap): ' + (', '.join(over_s) or 'none') +
                     '. Under the more conservative unstratified bootstrap: ' + (', '.join(over_u) or 'none') +
                     '. The paper should not claim a strict order inside these runs.')
    ctx.overlap_note('Adjacent pairs whose PAIRED difference CI contains 0 (cannot be separated): ' + ('; '.join(notsig) or 'none'))
    all_pairs_sep = 0
    tot = 0
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            tot += 1
            d_lo, d_hi = pct_ci(cells[models[j]]['boots'] - cells[models[i]]['boots'])
            all_pairs_sep += not (d_lo <= 0 <= d_hi)
    ctx.overlap_note(f'{all_pairs_sep} of {tot} model pairs have a paired-difference CI that excludes 0.')
    gen_max = max(cells[m]['hi'] for m in st.GENERALS)
    spec_min = min(cells[m]['lo'] for m in st.SPECIALISTS)
    ctx.note(f'Worst general model ({st.MODEL_SHORT[max(st.GENERALS, key=lambda m: cells[m]["point"])]}) has upper CI {gen_max:.3f}; '
             f'best specialist has lower CI {spec_min:.3f}. '
             + ('Specialist and general intervals are disjoint at the extremes.' if spec_min > gen_max else
                'Specialist and general intervals overlap, so "all specialists worse than all generals" needs care.'))
    ctx.note('The claim extractor and Layer-2 judge are Qwen2.5-7B-Instruct, the same family as the evaluated Qwen2.5-VL/Qwen2-VL/Qwen3-VL/Qwen3.5 '
             'models; the family also occupies the top of the ranking, so judge self-preference cannot be ruled out from these files.')
    meta = ctx.save(fig, 'fig02_smhr_ranking', src)
    ctx.add_manifest(
        num=2, name='fig02_smhr_ranking', func=f'{SCRIPT}:fig02',
        sources=['medvihall_outputs/layer2_judge.jsonl', 'medvihall_outputs/layer1_verdicts.jsonl',
                 'medvihall_outputs/metrics_summary.json (cross-check)', 'medvihall_data/data/ground_truth/manifest_3500.json'],
        claim='Medical specialists have higher SMHR than most general VLMs; neighbouring ranks are not always separable.',
        caption=(f'SMHR of 12 VLMs on {n_img:,} images ({int((ctx.df["model"] == models[0]).sum()):,} responses per model); lower is safer, and medical '
                 f'specialists are shaded. Bars are 95% image-level bootstrap intervals ({ctx.boot.B:,} resamples, seed {ctx.boot.seed}), and the right-hand column '
                 f'gives each model\'s 95% bootstrap rank range, so models with overlapping ranges are not ordered.'),
        **meta)


# =========================================================================== Fig 3
def fig03(ctx: Ctx):
    models = ctx.models
    mods = st.MODALITY_ORDER
    fig = plt.figure(figsize=(st.DOUBLE_COLUMN_IN, 3.1))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.55, left=0.12, right=0.80, top=0.92, bottom=0.17)
    ax = fig.add_subplot(gs[0])
    M = np.array([[ctx.cell(m, mod)['point'] for mod in mods] for m in models])
    im = ax.imshow(M, cmap='YlOrRd', vmin=0.3, vmax=1.0, aspect='auto')
    rows = []
    for i, m in enumerate(models):
        for j, mod in enumerate(mods):
            c = ctx.cell(m, mod)
            ax.text(j, i, f'{c["point"]:.2f}', ha='center', va='center', fontsize=st.FS_BASE,
                    color='white' if c['point'] > 0.72 else 'black')
            rows.append(dict(panel='a_heatmap', row=m, col=mod, value=c['point'], ci_lo=c['lo'], ci_hi=c['hi'],
                             n_images=int(ctx.boot.mask(mod).sum()),
                             n_claims=int(ctx.df[(ctx.df['model'] == m) & (ctx.df['modality'] == mod)]['claims'].sum())))
    ax.set_xticks(range(len(mods)))
    ax.set_xticklabels([st.MODALITY_ABBR[k] for k in mods])
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([ctx.name(m) for m in models])
    _style_model_ticklabels(ax, models)
    ax.axhline(len(st.GENERALS) - 0.5, color='black', lw=1.0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    cax = fig.add_axes([0.12, 0.07, 0.22, 0.025])
    cb = fig.colorbar(im, cax=cax, orientation='horizontal')
    cb.set_label('SMHR (lower is safer)', fontsize=st.FS_BASE)
    cb.ax.tick_params(labelsize=st.FS_BASE, length=2)
    cb.outline.set_linewidth(0.4)
    st.panel_label(ax, 'a', dx=-0.38)

    # class shares of flagged hallucinations (pooled over models)
    ax2 = fig.add_subplot(gs[1])
    ccols = [f'c{k}' for k in st.CLASS_IDS]
    tot = ctx.df.groupby('modality')[ccols].sum().loc[mods]
    share = tot.div(tot.sum(axis=1), axis=0)
    # consistency: class counts x weights == weighted numerators
    for mod in mods:
        lhs = sum(tot.loc[mod, f'c{k}'] * ctx.W[k] for k in st.CLASS_IDS)
        rhs = ctx.df.loc[ctx.df['modality'] == mod, 'w'].sum()
        ctx.check(f'F03_{mod}', abs(lhs - rhs) < 1e-6, f'Fig3 {mod}: sum_c w_c*n_c == summed weighted numerator', f'{lhs:.2f} vs {rhs:.2f}')
    bottom = np.zeros(len(mods))
    x = np.arange(len(mods))
    mids = {}
    for k in st.CLASS_IDS:
        v = share[f'c{k}'].values
        ax2.bar(x, v, bottom=bottom, width=0.62, color=st.CLASS_COLORS[k], hatch=st.CLASS_HATCH[k], edgecolor='white', lw=0.5)
        mids[k] = bottom[-1] + v[-1] / 2
        for j, mod in enumerate(mods):
            rows.append(dict(panel='b_class_share', row=st.CLASS_NAMES[k], col=mod, value=v[j],
                             ci_lo=np.nan, ci_hi=np.nan, n_images=int(ctx.boot.mask(mod).sum()),
                             n_claims=int(tot.loc[mod, f'c{k}'])))
        bottom += v
    ax2.set_xticks(x)
    ax2.set_xticklabels([st.MODALITY_ABBR[k] for k in mods])
    ax2.set_ylim(0, 1)
    ax2.set_yticks([0, .25, .5, .75, 1])
    ax2.set_yticklabels(['0', '25', '50', '75', '100'])
    ax2.set_ylabel('Share of flagged hallucinations (%)')
    ax2.set_xlim(-0.5, len(mods) - 0.5)
    ys = spread_labels([mids[k] for k in st.CLASS_IDS], 0.075, 0.03, 0.97)
    for k, yy in zip(st.CLASS_IDS, ys):
        ax2.annotate(f'{k} {st.CLASS_NAMES[k]}', xy=(len(mods) - 0.5 - 0.19, mids[k]), xytext=(len(mods) - 0.5 + 0.12, yy),
                     fontsize=st.FS_BASE, va='center', ha='left', color='black', annotation_clip=False,
                     arrowprops=dict(arrowstyle='-', lw=0.4, color='#808080', shrinkA=0, shrinkB=0))
    st.panel_label(ax2, 'b', dx=-0.2)
    dom = share.idxmax(axis=1)
    ctx.note('Class shares are pooled over the 12 models (verbose models contribute more flagged claims); Layer-1 omissions are counted as class 2. '
             'Dominant class per modality: ' + ', '.join(f'{k}={st.CLASS_NAMES[int(v[1:])]} ({share.loc[k, v]:.0%})' for k, v in dom.items()) + '.',
             fig='Fig 3')
    meta = ctx.save(fig, 'fig03_modality_fingerprints', pd.DataFrame(rows))
    sp = M[[models.index(m) for m in st.SPECIALISTS]].mean()
    ctx.add_manifest(
        num=3, name='fig03_modality_fingerprints', func=f'{SCRIPT}:fig03',
        sources=['medvihall_outputs/layer2_judge.jsonl', 'medvihall_outputs/layer1_verdicts.jsonl', 'medvihall_outputs/metrics_summary.json (cross-check)'],
        claim='Hallucination burden depends on modality (radiology is hardest for most models) and is dominated by a few classes.',
        caption=(f'(a) SMHR by model and modality (cell CIs in the source CSV). (b) Share of flagged hallucinations by class within each modality, pooled over the '
                 f'12 models ({int(tot.values.sum()):,} flagged claims/omissions on {len(ctx.images):,} images). The thick line separates general VLMs (above) from medical specialists (below).'),
        **meta)


# =========================================================================== Fig 4
def fig04(ctx: Ctx):
    mods = st.MODALITY_ORDER
    best = ctx.ms['best_general_vlm_by_modality']
    sri_file = ctx.ms['sri']
    rows = []
    fig, ax = plt.subplots(figsize=(st.COLUMN_WIDTH_IN, 2.9))
    offs = {'huatuogpt': -0.24, 'chexagent': 0.0, 'llava_med': 0.24}
    ymap = {mod: len(mods) - 1 - i for i, mod in enumerate(mods)}
    ax.axvspan(0.0, 1.0, color='#E3F1E3', lw=0, zorder=0)
    ax.axvline(1.0, color='black', lw=0.9, ls='--', zorder=1)
    stab = []
    for mod in mods:
        g = best[mod]['model']
        mask = ctx.boot.mask(mod)
        pg, bg = ctx.boot.ratio(g, mask=mask)
        gen_boots = np.column_stack([ctx.boot.ratio(x, mask=mask)[1] for x in st.GENERALS])
        stab.append((mod, g, float((gen_boots.argmin(axis=1) == st.GENERALS.index(g)).mean())))
        for s in st.SPECIALISTS:
            ps, bs = ctx.boot.ratio(s, mask=mask)
            sri = ps / pg
            lo, hi = pct_ci(bs / bg)
            ctx.check(f'F04_{s}_{mod}', abs(sri - sri_file[s][mod]['sri']) < 1e-9,
                      f'Fig4 SRI {s}/{mod} recomputed == metrics_summary.json', f'{sri:.4f}')
            y = ymap[mod] + offs[s]
            ax.hlines(y, lo, hi, color=st.MODEL_COLORS[s], lw=1.6, zorder=2)
            ax.plot(sri, y, marker=st.MODEL_MARKERS[s], color=st.MODEL_COLORS[s], mec='black', mew=0.4,
                    ms=st.MS + (2 if s == 'huatuogpt' else 0), ls='none', zorder=3)
            rows.append(dict(modality=mod, specialist=s, reference_model=g, sri=sri, ci_lo=lo, ci_hi=hi,
                             specialist_smhr=ps, reference_smhr=pg, ci_excludes_1=bool(lo > 1 or hi < 1),
                             n_images=int(mask.sum())))
    ax.set_yticks([ymap[m] for m in mods])
    ax.set_yticklabels([f'{st.MODALITY_SHORT[m]}\nvs {ctx.name(best[m]["model"])}' for m in mods])
    ax.set_ylim(-0.6, len(mods) - 0.35)
    xmax = max(r['ci_hi'] for r in rows)
    ax.set_xlim(0.8, xmax + 0.12)
    ax.set_xlabel('SRI = SMHR(specialist) / SMHR(best general VLM)')
    ax.text(0.99, 1.0, 'safer', transform=ax.get_xaxis_transform(), ha='right', va='bottom', fontsize=st.FS_BASE, color='#2E7D32')
    ax.text(1.01, 1.0, 'worse', transform=ax.get_xaxis_transform(), ha='left', va='bottom', fontsize=st.FS_BASE, color='#7F2704')
    ax.legend([Line2D([], [], marker=st.MODEL_MARKERS[s_], color=st.MODEL_COLORS[s_], mec='black', mew=0.4, ls='-', lw=1.6,
                      ms=st.MS + (2 if s_ == 'huatuogpt' else 0)) for s_ in st.SPECIALISTS],
              [st.MODEL_SHORT[s_] for s_ in st.SPECIALISTS], loc='upper right', frameon=False, handlelength=1.4,
              handletextpad=0.4, borderaxespad=0.2, fontsize=st.FS_BASE)
    src = pd.DataFrame(rows)
    n_above = int(src['ci_excludes_1'].sum())
    ctx.check('F04_all_above_1', bool((src['ci_lo'] > 1).all()), f'Fig4: all 12 specialist-by-modality SRI intervals lie above 1',
              f'{int((src["ci_lo"] > 1).sum())}/12 above 1; {n_above}/12 exclude 1')
    unstable = [f'{m}: {g} is lowest-SMHR general in {p:.0%} of resamples' for m, g, p in stab if p < 0.9]
    ctx.note('Reference model (best general VLM) is fixed to the point-estimate identity in every resample. ' +
             ('Reference unstable in: ' + '; '.join(unstable) if unstable else 'It remains the lowest-SMHR general model in >= 90% of resamples for every modality.'),
             fig='Fig 4')
    near = src[(src['ci_lo'] < 1.05)]
    if len(near):
        ctx.note('SRI intervals with lower bound < 1.05: ' + ', '.join(f"{r.specialist}/{r.modality} ({r.ci_lo:.2f})" for r in near.itertuples()), fig='Fig 4')
    ctx.overlap_note('Within a modality the three specialists\' SRI intervals overlap in several cells (see source CSV); do not rank specialists against each other from Fig 4.', fig='Fig 4')
    meta = ctx.save(fig, 'fig04_specialization_paradox', src)
    ctx.add_manifest(
        num=4, name='fig04_specialization_paradox', func=f'{SCRIPT}:fig04',
        sources=['medvihall_outputs/layer2_judge.jsonl', 'medvihall_outputs/layer1_verdicts.jsonl', 'medvihall_outputs/metrics_summary.json (SRI cross-check, reference model)'],
        claim=f'Every medical specialist has SRI > 1 in every modality: it hallucinates more than the best general VLM ({n_above}/12 intervals exclude 1).',
        caption=(f'Specialist Ratio Index (SRI) per medical specialist and modality; values above 1 mean the specialist hallucinates more than the best general VLM named '
                 f'under each modality. Bars are 95% image-level bootstrap intervals ({ctx.boot.B:,} resamples; reference model held fixed) over {len(ctx.images):,} images '
                 f'({", ".join(f"{int(ctx.boot.mask(m).sum())}" for m in mods)} per modality).'),
        **meta)


# =========================================================================== Fig 5
def fig05(ctx: Ctx):
    models = ctx.models
    mods = st.MODALITY_ORDER
    N = st.NORMAL_STRATA
    allnormal = ctx.boot.mask(strata=N)
    rows = []
    fig, axes = plt.subplots(1, 5, figsize=(st.DOUBLE_COLUMN_IN, 3.35), sharey=True,
                             gridspec_kw=dict(wspace=0.12, left=0.115, right=0.995, top=0.90, bottom=0.19))
    ypos = {m: len(models) - 1 - i for i, m in enumerate(models)}
    summary = {}

    def dumbbell(ax, m, a, b, color_a_open=True):
        # a: filled (first), b: open (second)
        ax.plot([a['point'], b['point']], [ypos[m]] * 2, color=st.MODEL_COLORS[m], lw=0.8, alpha=0.7, zorder=1)
        ax.hlines(ypos[m] + 0.14, a['lo'], a['hi'], color=st.MODEL_COLORS[m], lw=0.8, zorder=2)
        ax.hlines(ypos[m] - 0.14, b['lo'], b['hi'], color=st.MODEL_COLORS[m], lw=0.8, zorder=2)
        ax.plot(a['point'], ypos[m], marker=st.MODEL_MARKERS[m], color=st.MODEL_COLORS[m], mec='black', mew=0.4, ms=st.MS - 0.5, ls='none', zorder=3)
        ax.plot(b['point'], ypos[m], marker=st.MODEL_MARKERS[m], mfc='white', mec=st.MODEL_COLORS[m], mew=1.0, ms=st.MS - 0.5, ls='none', zorder=3)

    def cell(m, mask, qgroup, field='smhr'):
        if field == 'smhr':
            p, b = ctx.boot.ratio(m, mask=mask, qgroup=qgroup)
        else:
            p, b = ctx.boot.ratio(m, 'has12', 'records', mask=mask, qgroup=qgroup)
        lo, hi = pct_ci(b)
        return {'point': p, 'lo': lo, 'hi': hi, 'boots': b}

    for ax, mod in zip(axes[:4], mods):
        mn, ma = ctx.boot.mask(mod, strata=N), ctx.boot.mask(mod, exclude_strata=N)
        hi_normal = lo_normal = 0
        for m in models:
            a, b = cell(m, mn, 'Q123'), cell(m, ma, 'Q123')
            ca, cb = cell(m, mn, 'Q123', 'chr'), cell(m, ma, 'Q123', 'chr')
            d_lo, d_hi = pct_ci(a['boots'] - b['boots'])
            hi_normal += d_lo > 0
            lo_normal += d_hi < 0
            dumbbell(ax, m, a, b)
            rows.append(dict(panel='a_normal_vs_abnormal', modality=mod, model=m, comparison='normal (filled) minus abnormal (open); Q1-Q3',
                             smhr_a=a['point'], smhr_a_lo=a['lo'], smhr_a_hi=a['hi'], smhr_b=b['point'], smhr_b_lo=b['lo'], smhr_b_hi=b['hi'],
                             diff=a['point'] - b['point'], diff_lo=d_lo, diff_hi=d_hi, chr_a=ca['point'], chr_b=cb['point'],
                             n_images_a=int(mn.sum()), n_images_b=int(ma.sum())))
        summary[mod] = (hi_normal, lo_normal)
        ax.text(0.5, 1.01, st.MODALITY_SHORT[mod], transform=ax.transAxes, ha='center', va='bottom', fontsize=st.FS_LABEL)
    ax = axes[4]
    hi_q4 = lo_q4 = 0
    for m in models:
        a, b = cell(m, allnormal, 'Q4'), cell(m, allnormal, 'Q123')
        ca, cb = cell(m, allnormal, 'Q4', 'chr'), cell(m, allnormal, 'Q123', 'chr')
        d_lo, d_hi = pct_ci(a['boots'] - b['boots'])
        hi_q4 += d_lo > 0
        lo_q4 += d_hi < 0
        dumbbell(ax, m, a, b)
        rows.append(dict(panel='b_counterfactual_Q4', modality='all (normal images)', model=m, comparison='Q4 counterfactual (filled) minus Q1-Q3 (open); normal images only',
                         smhr_a=a['point'], smhr_a_lo=a['lo'], smhr_a_hi=a['hi'], smhr_b=b['point'], smhr_b_lo=b['lo'], smhr_b_hi=b['hi'],
                         diff=a['point'] - b['point'], diff_lo=d_lo, diff_hi=d_hi, chr_a=ca['point'], chr_b=cb['point'],
                         n_images_a=int(allnormal.sum()), n_images_b=int(allnormal.sum())))
    ax.text(0.5, 1.01, 'Normal images:\nQ4 vs Q1-Q3', transform=ax.transAxes, ha='center', va='bottom', fontsize=st.FS_LABEL)
    for ax in axes:
        ax.set_xlim(0, 1.05)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(['0', '.25', '.5', '.75', '1'])
        ax.grid(axis='x', lw=0.4)
        ax.set_ylim(-0.6, len(models) - 0.4)
    axes[0].set_yticks([ypos[m] for m in models])
    axes[0].set_yticklabels([ctx.name(m) for m in models])
    _style_model_ticklabels(axes[0], models)
    fig.text(0.555, 0.075, 'SMHR (lower is safer)', ha='center', va='center', fontsize=st.FS_LABEL)
    h = [Line2D([], [], marker='o', color='#404040', mfc='#404040', ls='none', ms=4), Line2D([], [], marker='o', color='#404040', mfc='white', ls='none', ms=4)]
    fig.legend(h, ['filled: normal images (four modality panels) / Q4 prompt (right panel)',
                   'open: abnormal images / Q1-Q3 prompts'], loc='lower center', ncol=2, frameon=False,
               handletextpad=0.2, columnspacing=1.5, fontsize=st.FS_BASE, bbox_to_anchor=(0.555, -0.01))
    src = pd.DataFrame(rows)
    ctx.check('F05_q4_scope', bool(set(ctx.df.loc[ctx.df['query_type'] == 'Q4', 'image_id']) <= set(ctx.images.loc[ctx.images['stratum'].isin(N), 'image_id'])),
              'Q4 (counterfactual) records exist only for normal-stratum images')
    txt = '; '.join(f'{st.MODALITY_SHORT[k]}: normal higher in {a}/12, lower in {b}/12' for k, (a, b) in summary.items())
    ctx.note(f'Normal-vs-abnormal direction is NOT uniform ({txt}; counts of models whose paired-bootstrap difference CI excludes 0). '
             'The paper should not state a single "normal images are harder" claim without modality qualifiers.', fig='Fig 5')
    ctx.note(f'Q4 counterfactual prompt on normal images: SMHR higher than Q1-Q3 in {hi_q4}/12 models and lower in {lo_q4}/12 (CI excludes 0). '
             'Q4 prompts assert a finding that is absent from the (normal) image (false-premise counterfactual), so higher SMHR means the model went along with the premise; Q4 responses also yield more claims per response than Q2/Q3, so claim mix differs between conditions.', fig='Fig 5')
    meta = ctx.save(fig, 'fig05_normal_image_paradox', src)
    ctx.add_manifest(
        num=5, name='fig05_normal_image_paradox', func=f'{SCRIPT}:fig05',
        sources=['medvihall_outputs/layer2_judge.jsonl', 'medvihall_outputs/layer1_verdicts.jsonl', 'medvihall_data/data/ground_truth/manifest_3500.json (strata)'],
        claim='Whether normal images are hallucinated on more or less than abnormal ones depends on the modality; the Q4 counterfactual prompt changes SMHR on normal images.',
        caption=(f'SMHR on normal strata (S1, DS1, HS1, OS1; filled) versus abnormal strata (open) for Q1-Q3 by modality (left four panels; {int(allnormal.sum()):,} normal and '
                 f'{len(ctx.images) - int(allnormal.sum()):,} abnormal images), and on normal images for the false-premise Q4 counterfactual prompt versus Q1-Q3 (right). Bars are 95% image-level '
                 f'bootstrap intervals ({ctx.boot.B:,} resamples).'),
        **meta)
