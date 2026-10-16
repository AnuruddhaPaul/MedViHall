"""Figures 6-12 (Pillars E, C, D, B, A, H and the annotation analysis)."""
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats

import fig_style as st
from fig_common import Ctx, ci_overlap, spread_labels, fmt_ci
from fig_data import OUT, ROOT, MissingData, load_json, need

SCRIPT = 'figs_b.py'
ANN = ROOT / 'annotation_results'


def _parse_ci(s):
    m = re.match(r'\s*(-?[\d.]+(?:e-?\d+)?)\s*\.\.\s*(-?[\d.]+(?:e-?\d+)?)\s*$', str(s))
    if not m:
        return np.nan, np.nan
    return float(m.group(1)), float(m.group(2))


def _holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


# =========================================================================== Fig 6
def fig06(ctx: Ctx):
    d = load_json(OUT / 'pillar_e_cross_modal_transfer.json')
    mods = st.MODALITY_ORDER
    pairs = d['smhr_cross_modal_correlation']
    p_raw = []
    for r in pairs:
        n = r['n_models']
        p_raw.append(2 * stats.t.sf(abs(r['t_stat']), n - 2))
    p_holm = _holm(p_raw)
    # recompute rho from the per-model per-modality SMHR in metrics_summary.json
    for r in pairs:
        a = [ctx.ms['models'][m]['by_modality'][r['modality_a']]['smhr'] for m in ctx.models]
        b = [ctx.ms['models'][m]['by_modality'][r['modality_b']]['smhr'] for m in ctx.models]
        rho = stats.spearmanr(a, b).statistic
        ctx.check(f'F06_{r["modality_a"][:4]}_{r["modality_b"][:4]}', abs(rho - r['spearman_r']) < 1e-9,
                  f'Fig6 rho {r["modality_a"]}-{r["modality_b"]} recomputed from SMHR == pillar_e file',
                  f'{rho:.4f} vs {r["spearman_r"]:.4f}')
        sig_file = r['significance'].startswith('significant')
    rows, M = [], np.full((4, 4), np.nan)
    marks = {}
    for r, pr, ph in zip(pairs, p_raw, p_holm):
        i, j = mods.index(r['modality_a']), mods.index(r['modality_b'])
        M[i, j] = M[j, i] = r['spearman_r']
        mk = ('*' if pr < 0.05 else '') + ('†' if ph < 0.05 else '')
        marks[(i, j)] = marks[(j, i)] = mk
        ctx.check(f'F06s_{i}{j}', (pr < 0.05) == r['significance'].startswith('significant'),
                  f'Fig6 significance mark {r["modality_a"]}-{r["modality_b"]} agrees with the file label', f'p={pr:.4f}')
        rows.append(dict(modality_a=r['modality_a'], modality_b=r['modality_b'], n_models=r['n_models'], spearman_rho=r['spearman_r'],
                         t_stat=r['t_stat'], p_uncorrected=pr, p_holm_6_tests=ph, mark=mk))
    fig, ax = plt.subplots(figsize=(st.COLUMN_WIDTH_IN, 3.05))
    im = ax.imshow(np.ma.masked_invalid(M), cmap='RdBu_r', vmin=-1, vmax=1)
    for i in range(4):
        for j in range(4):
            if i == j:
                ax.text(j, i, '1', ha='center', va='center', fontsize=st.FS_BASE, color='#808080')
            else:
                v = M[i, j]
                ax.text(j, i, f'{v:.2f}{marks[(i, j)]}', ha='center', va='center', fontsize=st.FS_BASE,
                        color='white' if abs(v) > 0.6 else 'black', fontweight='bold' if marks[(i, j)] else 'normal')
    ax.set_xticks(range(4))
    ax.set_xticklabels([st.MODALITY_ABBR[m] for m in mods])
    ax.set_yticks(range(4))
    ax.set_yticklabels([st.MODALITY_SHORT[m] for m in mods])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.03)
    cb.set_label('Spearman ρ of model SMHR', fontsize=st.FS_BASE)
    cb.ax.tick_params(labelsize=st.FS_BASE, length=2)
    cb.outline.set_linewidth(0.4)
    fig.text(0.5, -0.02, '* p<0.05 uncorrected;  † p<0.05 after Holm (6 pairs);\nn = 12 models per pair', ha='center', va='top', fontsize=st.FS_BASE)
    weak = [(r['modality_a'], r['modality_b'], r['spearman_r']) for r in pairs if r['spearman_r'] < 0.5]
    ctx.note('Rankings transfer between dermatology, histopathology and ophthalmology but radiology transfers weakly (rho: ' +
             ', '.join(f'{a[:5]}-{b[:5]} {v:.2f}' for a, b, v in weak) + '). With 12 models a rho of about 0.58 is the p=0.05 threshold, so the intervals around these rhos are wide.', fig='Fig 6')
    n_sig, n_holm = sum(p < 0.05 for p in p_raw), int((p_holm < 0.05).sum())
    ctx.note(f'{n_sig}/6 pairs are significant uncorrected and {n_holm}/6 survive Holm correction; the Specialist-only SRI transfer (n=3) in the same file is not plotted because rho on 3 points is not informative.', fig='Fig 6')
    meta = ctx.save(fig, 'fig06_cross_modal_transfer', pd.DataFrame(rows))
    ctx.add_manifest(
        num=6, name='fig06_cross_modal_transfer', func=f'{SCRIPT}:fig06',
        sources=['medvihall_outputs/pillar_e_cross_modal_transfer.json', 'medvihall_outputs/metrics_summary.json (rho recomputed)'],
        claim='A model\'s SMHR rank in one modality predicts its rank in the other modalities only partly; radiology transfers worst.',
        caption=(f'Spearman correlation between the 12 models\' SMHR rankings in each pair of modalities (n = 12 models; each SMHR from the full {len(ctx.images):,}-image benchmark). '
                 f'Marks show p < 0.05 without (*) and with (†) Holm correction for six pairs; no confidence interval is drawn, so with n = 12 weaker correlations should be read as inconclusive.'),
        **meta)


# =========================================================================== Fig 7
def fig07(ctx: Ctx):
    d = load_json(OUT / 'pillar_c_metric_concordance.json')
    mods = st.MODALITY_ORDER
    cells = []
    for m in ctx.models:
        for mod in mods:
            c = d['models'][m]['by_modality'][mod]
            sm = ctx.ms['models'][m]['by_modality'][mod]['smhr']
            cells.append(dict(model=m, modality=mod, smhr=sm, crest=c['crest'], medihall=c['medihall_score'], n_claims=c['n_claims']))
    cdf = pd.DataFrame(cells)
    over = d['spearman_correlations_overall']
    for key, col in (('smhr_vs_crest', 'crest'), ('smhr_vs_medihall', 'medihall_score')):
        rho = stats.spearmanr([ctx.ms['models'][m]['smhr_overall'] for m in ctx.models],
                              [d['models'][m]['overall'][col] for m in ctx.models]).statistic
        ctx.check(f'F07_{key}', abs(rho - over[key]) < 1e-9, f'Fig7 12-model rho {key} recomputed == file', f'{rho:.4f} vs {over[key]:.4f}')
    rho_cell = {c: stats.spearmanr(cdf['smhr'], cdf[c]).statistic for c in ('crest', 'medihall')}
    z = lambda x: (x - x.mean()) / x.std(ddof=0)
    cdf['z_smhr'] = z(cdf['smhr'])
    cdf['z_crest'] = z(cdf['crest'])
    cdf['z_neg_medihall'] = z(-cdf['medihall'])
    cdf['zdiff_crest'] = cdf['z_smhr'] - cdf['z_crest']
    cdf['zdiff_medihall'] = cdf['z_smhr'] - cdf['z_neg_medihall']
    file_div = d['smhr_crest_divergences']
    # cross-check my z-diff against the file's list
    top_file = [(x['model'], x['modality']) for x in file_div[:6]]
    top_mine = [(r.model, r.modality) for r in cdf.reindex(cdf['zdiff_crest'].abs().sort_values(ascending=False).index).head(6).itertuples()]
    ctx.check('F07_div', top_file == top_mine, 'Fig7 six largest SMHR-vs-CREST divergences recomputed == pillar_c file', f'{top_mine}')

    fig, axes = plt.subplots(1, 2, figsize=(st.DOUBLE_COLUMN_IN, 3.2), gridspec_kw=dict(wspace=0.28, left=0.07, right=0.985, top=0.96, bottom=0.17))
    for ax, col, zcol, xl, lab in ((axes[0], 'crest', 'zdiff_crest', 'CREST (higher = riskier errors)', 'a'),
                                   (axes[1], 'medihall', 'zdiff_medihall', 'MediHall Score (higher = better)', 'b')):
        for m in ctx.models:
            s = cdf[cdf['model'] == m]
            ax.scatter(s['smhr'], s[col], marker=st.MODEL_MARKERS[m], color=st.MODEL_COLORS[m], edgecolor='black', linewidth=0.3,
                       s=26 if st.MODEL_MARKERS[m] != '*' else 44, zorder=3)
        top = cdf.reindex(cdf[zcol].abs().sort_values(ascending=False).index).head(6)
        if top[zcol].abs().max() >= 0.5:
            keylines = []
            for k, r in enumerate(top.itertuples(), 1):
                ax.annotate(str(k), xy=(r.smhr, getattr(r, col)), xytext=(5, 5), textcoords='offset points', fontsize=st.FS_BASE,
                            fontweight='bold', ha='left', va='bottom')
                keylines.append(f'{k}  {st.MODEL_SHORT[r.model]}, {st.MODALITY_SHORT[r.modality]}')
            ax.text(0.98, 0.03, 'largest disagreements:\n' + '\n'.join(keylines), transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=st.FS_BASE, linespacing=1.2)
        else:
            ax.text(0.03, 0.03, f'no cell disagrees: max |z diff| = {top[zcol].abs().max():.2f}', transform=ax.transAxes, ha='left', va='bottom', fontsize=st.FS_BASE)
        key = 'smhr_vs_crest' if col == 'crest' else 'smhr_vs_medihall'
        ax.text(0.03 if col == 'crest' else 0.97, 0.97, f'ρ (12 models) = {over[key]:.2f}\nρ (48 cells) = {rho_cell[col]:.2f}',
                transform=ax.transAxes, va='top', ha='left' if col == 'crest' else 'right', fontsize=st.FS_BASE)
        ax.set_xlabel('SMHR (lower is safer)')
        ax.set_ylabel(xl)
        st.panel_label(ax, lab, dx=-0.15)
    ctx.note(f'MediHall Score vs SMHR: rho = {over["smhr_vs_medihall"]:.2f} across 12 models and {rho_cell["medihall"]:.2f} across the 48 cells (MediHall is higher-is-better, so -1 means an identical ordering). '
             'Both are class-weighted means over all claims with monotone class mappings, so this agreement is largely by construction and is weak evidence of independent validation (it should not be presented as a surprising concordance).', fig='Fig 7')
    ctx.note(f'CREST vs SMHR: rho = {over["smhr_vs_crest"]:.2f} (12 models), {rho_cell["crest"]:.2f} (48 cells). CREST averages risk only over erroneous claims, so the two measure different things.', fig='Fig 7')
    ctx.note('Labelled "disagreement" cells are the six largest |z(SMHR) - z(other metric)| among the 48 cells (an effect-size heuristic, no significance test; the CREST panel reproduces the list in the Pillar C file, the MediHall panel is computed here with the same rule).', fig='Fig 7')
    src = cdf.rename(columns={'medihall': 'medihall_score'})
    meta = ctx.save(fig, 'fig07_metric_concordance', src)
    ctx.add_manifest(
        num=7, name='fig07_metric_concordance', func=f'{SCRIPT}:fig07',
        sources=['medvihall_outputs/pillar_c_metric_concordance.json', 'medvihall_outputs/metrics_summary.json (SMHR per cell)'],
        claim='SMHR agrees with MediHall Score and partly with CREST on model rankings; individual model-by-modality cells disagree.',
        caption=(f'SMHR against (a) CREST and (b) MediHall Score for 12 models in 4 modalities (48 cells, {len(ctx.images):,} images; one marker per cell, marker shape identifies the model as in Fig. 2). '
                 f'Spearman ρ is shown for the 12 model-level values and for the 48 cells, numbered cells are the six largest standardised SMHR-versus-CREST disagreements (none exist for MediHall), and no confidence intervals are shown.'),
        **meta)


# =========================================================================== Fig 8
def fig08(ctx: Ctx):
    d = load_json(OUT / 'pillar_d_calibration_results.json')
    cells = d['cells']
    models = [m for m in ctx.models if any(k.startswith(m + '|') for k in cells)]
    configs = sorted({k.split('|')[1] for k in cells})
    cfg_lab = {c: ('G' if c.endswith('greedy') else 'N') + '\nT=' + re.search(r'temp([\d.]+)', c).group(1) for c in configs}
    rs = d['rank_stability']['strict']
    ranks6, ranks4 = rs['all_6_configs'], rs['distinct_4_settings']
    # verify mean rho from the rankings
    def mean_rho(block):
        cfgs = list(block['rankings'])
        rr = []
        for i in range(len(cfgs)):
            for j in range(i + 1, len(cfgs)):
                a = [block['rankings'][cfgs[i]].index(m) for m in block['models']]
                b = [block['rankings'][cfgs[j]].index(m) for m in block['models']]
                rr.append(stats.spearmanr(a, b).statistic)
        return float(np.mean(rr))
    for nm, blk in (('6', ranks6), ('4', ranks4)):
        ctx.check(f'F08_rho{nm}', abs(mean_rho(blk) - blk['mean_rho']) < 1e-9, f'Fig8 mean rho ({nm} configs) recomputed from rankings == file', f'{mean_rho(blk):.3f}')
    fig = plt.figure(figsize=(st.DOUBLE_COLUMN_IN, 2.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.55, left=0.075, right=0.86, top=0.95, bottom=0.2)
    ax = fig.add_subplot(gs[0])
    x = np.arange(len(configs))
    rows = []
    ends = []
    for m in models:
        e = [cells[f'{m}|{c}']['strict']['ece'] for c in configs]
        a = [cells[f'{m}|{c}']['strict']['ace'] for c in configs]
        lo = [cells[f'{m}|{c}']['strict']['ece_ci95'][0] for c in configs]
        hi = [cells[f'{m}|{c}']['strict']['ece_ci95'][1] for c in configs]
        ax.errorbar(x, e, yerr=[np.array(e) - lo, np.array(hi) - np.array(e)], color=st.MODEL_COLORS[m], lw=1.0, capsize=1.5, elinewidth=0.7,
                    marker=st.MODEL_MARKERS[m], ms=st.MS - 0.5, mec='black', mew=0.3, zorder=3)
        ax.plot(x, a, ls='none', marker=st.MODEL_MARKERS[m], mfc='none', mec=st.MODEL_COLORS[m], ms=st.MS + 2.5, mew=0.7, zorder=2)
        ends.append(e[-1])
        for c, ee, aa, l, h in zip(configs, e, a, lo, hi):
            cl = cells[f'{m}|{c}']
            rows.append(dict(model=m, config=c, ece=ee, ece_ci_lo=l, ece_ci_hi=h, ace=aa, accuracy=cl['strict']['accuracy'],
                             mean_stated_confidence=cl['mean_conf'], n_labeled=cl['strict']['n'], n_total=cl['coverage']['total'],
                             confidence_coverage=cl['coverage']['with_conf'] / cl['coverage']['total']))
    ys = spread_labels(ends, 0.028, min(ends) - 0.05, max(ends) + 0.05)
    for m, yy, e in zip(models, ys, ends):
        ax.annotate(ctx.name(m), xy=(x[-1] + 0.12, e), xytext=(x[-1] + 0.55, yy), fontsize=st.FS_BASE, va='center', ha='left',
                    color='black', annotation_clip=False, arrowprops=dict(arrowstyle='-', lw=0.4, color='#808080', shrinkA=0, shrinkB=0))
    ax.set_xticks(x)
    ax.set_xticklabels([cfg_lab[c] for c in configs])
    ax.set_xlim(-0.3, len(configs) - 0.4)
    ax.set_ylabel('ECE (filled) and ACE (ring)')
    ax.set_xlabel('G greedy, N nucleus, T temperature')
    ax.grid(axis='y', lw=0.4)
    st.panel_label(ax, 'a', dx=-0.14)
    # panel b: rank trajectories
    ax2 = fig.add_subplot(gs[1])
    rk = ranks6['rankings']
    for m in models:
        yr = [rk[c].index(m) + 1 for c in configs]
        ax2.plot(x, yr, color=st.MODEL_COLORS[m], marker=st.MODEL_MARKERS[m], ms=st.MS - 0.5, mec='black', mew=0.3, lw=1.0)
        ax2.text(x[0] - 0.2, yr[0], ctx.name(m), ha='right', va='center', fontsize=st.FS_BASE)
    ax2.set_ylim(len(models) + 0.5, 0.5)
    ax2.set_yticks(range(1, len(models) + 1))
    ax2.set_xticks(x)
    ax2.set_xticklabels([cfg_lab[c] for c in configs])
    ax2.set_xlim(-0.3, len(configs) - 0.7)
    ax2.set_ylabel('ECE rank (1 = best calibrated)')
    ax2.yaxis.set_label_coords(1.12, 0.5)
    ax2.yaxis.set_label_position('right')
    ax2.yaxis.tick_right()
    ax2.spines['right'].set_visible(True)
    ax2.spines['left'].set_visible(False)
    ax2.text(0.5, 1.0, f'mean ρ = {ranks6["mean_rho"]:.2f} (6 configs), {ranks4["mean_rho"]:.2f} (4 distinct)',
             transform=ax2.transAxes, ha='center', va='bottom', fontsize=st.FS_BASE)
    st.panel_label(ax2, 'b', dx=-0.02, dy=1.08)
    src = pd.DataFrame(rows)
    src['rank_strict_all6'] = [rk[r.config].index(r.model) + 1 for r in src.itertuples()]
    ctx.check('F08_ece', all(abs(r.ece - cells[f'{r.model}|{r.config}']['strict']['ece']) < 1e-12 for r in src.itertuples()), 'Fig8 plotted ECE == pillar_d_calibration_results.json')
    max_gap = float((src['ece'] - src['ace']).abs().max())
    # CI overlap among models for greedy config
    g = src[src['config'] == 'temp0.0_greedy'].sort_values('ece')
    ov = [f'{a.model}~{b.model}' for a, b in zip(g.itertuples(), list(g.itertuples())[1:]) if ci_overlap(a.ece_ci_lo, a.ece_ci_hi, b.ece_ci_lo, b.ece_ci_hi)]
    ctx.overlap_note('Greedy-decoding ECE, adjacent models in ECE order with overlapping 95% CIs: ' + (', '.join(ov) or 'none') +
                     '. The ranking among those models is not supported even though rank stability across configs is high.', fig='Fig 8')
    ctx.note(f'ECE is 0.5-0.73 for every model and accuracy under the strict zero-hallucination label is only {src["accuracy"].min():.0%}-{src["accuracy"].max():.0%}, so ECE mostly measures overconfidence (as the Pillar D write-up states). '
             f'Max |ECE-ACE| = {max_gap:.3f}. Greedy configs are byte-identical for most models, so only 4 of the 6 configurations are independent; the rank-stability rho (0.93 vs 0.90) is computed on both.', fig='Fig 8')
    ctx.note('Rank stability rests on 5 models; rho can only take multiples of 0.1, and dropping huatuogpt lowers it (Pillar D robustness file).', fig='Fig 8')
    meta = ctx.save(fig, 'fig08_calibration', src)
    ctx.add_manifest(
        num=8, name='fig08_calibration', func=f'{SCRIPT}:fig08',
        sources=['medvihall_outputs/pillar_d_calibration_results.json (ECE, ACE, CIs, rank_stability)'],
        claim='Verbalised-confidence calibration error is large for every model but its model ranking changes little across decoding settings.',
        caption=(f'(a) Expected (ECE) and adaptive (ACE) calibration error of stated confidence for five models under six decoding configurations (strict correctness label; '
                 f'{int(src["n_labeled"].min()):,}-{int(src["n_labeled"].max()):,} labelled responses per cell from a 500-image subset); bars are 95% bootstrap CIs on ECE. '
                 f'(b) ECE rank of each model per configuration (mean pairwise Spearman ρ = {ranks6["mean_rho"]:.2f}, five models).'),
        **meta)


# =========================================================================== Fig 9
def fig09(ctx: Ctx):
    d = load_json(OUT / 'pillar_b_mitigation_results.json')
    pv = d['paired_vs_baseline']
    strategies = [s for s in ('rag', 'contrastive') if s in pv]
    models = [m for m in ctx.models if m in pv[strategies[0]]]
    fig, ax = plt.subplots(figsize=(st.COLUMN_WIDTH_IN, 2.75))
    ypos = {m: len(models) - 1 - i for i, m in enumerate(models)}
    offs = {'rag': 0.16, 'contrastive': -0.16}
    ax.axvspan(0, 0.2, color='#FBE3DD', lw=0, zorder=0)
    ax.axvline(0, color='black', lw=0.9, zorder=1)
    rows, increases = [], []
    for s in strategies:
        for m in models:
            r = pv[s][m]
            dl, (lo, hi) = r['delta'], r['delta_ci95']
            ctx.check(f'F09_{s}_{m}', abs(dl - (r['strategy_smhr'] - r['baseline_smhr'])) < 1e-9 and lo <= dl <= hi and (r['significant'] == (lo > 0 or hi < 0)),
                      f'Fig9 {s}/{m}: delta == strategy - baseline, inside its CI, significance flag consistent', f'{dl:+.4f} [{lo:+.4f}, {hi:+.4f}]')
            y = ypos[m] + offs[s]
            up = dl > 0
            ax.hlines(y, lo, hi, color=st.STRATEGY_COLORS[s], lw=1.6, zorder=2)
            ax.plot(dl, y, marker=st.STRATEGY_MARKERS[s], color=st.STRATEGY_COLORS[s], mec='#B22222' if up else 'black', mew=1.4 if up else 0.4,
                    ms=st.MS + 1, ls='none', zorder=3)
            if up:
                increases.append((m, s, dl, r['significant']))
                ax.text(hi + 0.004, y, 'worse' + ('*' if r['significant'] else ''), fontsize=st.FS_BASE, color='#B22222', va='center', ha='left')
            rows.append(dict(model=m, strategy=s, baseline_smhr=r['baseline_smhr'], strategy_smhr=r['strategy_smhr'], delta=dl, ci_lo=lo, ci_hi=hi,
                             ci_excludes_0=bool(r['significant']), increases_smhr=up, n_paired_keys=r['n_paired_keys'],
                             n_boot=d['parameters']['n_boot']))
    ax.set_yticks([ypos[m] for m in models])
    ax.set_yticklabels([ctx.name(m) for m in models])
    _lab = ax.get_yticklabels()
    for lab, m in zip(_lab, models):
        if m in st.SPECIALISTS:
            lab.set_fontweight('bold')
            lab.set_color('#7F2704')
    lo_all, hi_all = min(r['ci_lo'] for r in rows), max(r['ci_hi'] for r in rows)
    ax.set_xlim(lo_all - 0.01, hi_all + 0.035)
    ax.set_ylim(-0.6, len(models) - 0.4)
    ax.set_xlabel('Change in SMHR vs. matched greedy baseline\n(negative = fewer hallucinations)')
    ax.grid(axis='x', lw=0.4)
    ax.legend([Line2D([], [], marker=st.STRATEGY_MARKERS[s], color=st.STRATEGY_COLORS[s], mec='black', mew=0.4, lw=1.6, ms=st.MS + 1) for s in strategies],
              [st.STRATEGY_NAMES[s] for s in strategies], loc='lower center', bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False, fontsize=st.FS_BASE,
              handlelength=1.4, borderaxespad=0.2, handletextpad=0.4, columnspacing=1.2)
    from matplotlib.ticker import MultipleLocator, FormatStrFormatter
    ax.xaxis.set_major_locator(MultipleLocator(0.05))
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ov = []
    for m in models:
        a, b = pv['rag'][m], pv['contrastive'][m]
        if ci_overlap(*a['delta_ci95'], *b['delta_ci95']):
            ov.append(m)
    ctx.overlap_note('RAG and contrastive-decoding delta CIs overlap for: ' + ', '.join(ov) + '. "Best strategy per model" should only be claimed where the two intervals are separated '
                     f'({", ".join(m for m in models if m not in ov) or "none"}); paired-difference between strategies was not computed in the saved results.', fig='Fig 9')
    ctx.note('Fine-tuning (named in the figure request) has no result file in medvihall_outputs; only RAG and contrastive decoding are plotted.', fig='Fig 9')
    ctx.note('Pillar B uses a 500-image subset (about 1,680 responses per model, 5 models), so baselines differ slightly from the core-run SMHR; '
             'llava_med baseline is the decoder-fixed rerun (pillar_b_baseline_llava_med_fixed.jsonl). Strategy-induced changes in response length (RAG answers are longer for several models) change the claim denominator.', fig='Fig 9')
    meta = ctx.save(fig, 'fig09_mitigation', pd.DataFrame(rows))
    sig_up = [f'{m}+{s}' for m, s, dl, sg in increases if sg]
    ctx.add_manifest(
        num=9, name='fig09_mitigation', func=f'{SCRIPT}:fig09',
        sources=['medvihall_outputs/pillar_b_mitigation_results.json (paired_vs_baseline: delta, delta_ci95)'],
        claim=('No strategy helps every model, and RAG raises SMHR for ' + (', '.join(sorted({m for m, s, _, _ in increases if s == 'rag'})) or 'no model') + '.'),
        caption=(f'Change in SMHR relative to the matched greedy baseline for retrieval-augmented generation and contrastive decoding (five models, {int(min(r["n_paired_keys"] for r in rows)):,}-'
                 f'{int(max(r["n_paired_keys"] for r in rows)):,} paired image-query responses on a 500-image subset). Bars are 95% paired image-level bootstrap intervals ({d["parameters"]["n_boot"]:,} resamples); '
                 f'red outlines mark strategies that increase SMHR ({len(increases)} of {len(rows)} model-strategy cells, {len(sig_up)} with an interval excluding 0).'),
        **meta)


# =========================================================================== Fig 10 / 11 (no result files)
def _search(patterns):
    hits = []
    for pat in patterns:
        hits += [p for p in OUT.rglob(pat) if p.is_file() and p.stat().st_size > 0]
    return hits


def fig10(ctx: Ctx):
    hits = _search(['*pillar_a*', '*stage_local*', '*stage_replacement*', '*causal*'])
    if not hits:
        raise MissingData('No Pillar A (causal stage localization) result file exists in medvihall_outputs/ (searched pillar_a*, *stage_local*, '
                          '*stage_replacement*, *causal*). The 2026 claim audit also records "No Pillar A file, script, notebook or text exists in the repository."')
    raise MissingData(f'Pillar A candidate files found ({[h.name for h in hits]}) but no schema is defined for them in figs_b.py; add a loader before plotting.')


def fig11(ctx: Ctx):
    hits = _search(['*pillar_h*', '*occlusion*', '*context_robust*', '*object_only*', '*background_only*'])
    if not hits:
        raise MissingData('No Pillar H (context occlusion) result file exists in medvihall_outputs/ (searched pillar_h*, *occlusion*, '
                          '*context_robust*, *object_only*, *background_only*); no script or notebook for it exists in the repo either.')
    raise MissingData(f'Pillar H candidate files found ({[h.name for h in hits]}) but no schema is defined for them in figs_b.py; add a loader before plotting.')


# =========================================================================== Fig 12
def fig12(ctx: Ctx):
    a3 = pd.read_csv(need(ANN / 'A3_flag_agreement_overall.csv'))
    b1 = pd.read_csv(need(ANN / 'B1_judge_vs_human_per_class.csv'))
    d3 = pd.read_csv(need(ANN / 'D3_annotator_agreement_with_majority_and_judge.csv'))
    key = pd.read_csv(need(OUT / 'annotation' / 'annotation_key.csv'), encoding='utf-8-sig')
    n_items, n_img = len(key), key['image_id'].nunique()
    name2id = {v.upper().replace(' ', '_').replace('-', '_'): k for k, v in st.CLASS_NAMES.items()}
    name2id['CLINICAL_REASONING_ERROR'] = 7
    classes = list(a3['class'])
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(st.DOUBLE_COLUMN_IN, 3.0), gridspec_kw=dict(width_ratios=[1.5, 1], wspace=0.55, left=0.17, right=0.985, top=0.84, bottom=0.2))
    ax = axes[0]
    ypos = {c: len(classes) - 1 - i for i, c in enumerate(classes)}
    for c in classes:
        r3 = a3[a3['class'] == c].iloc[0]
        r1 = b1[b1['class'] == c].iloc[0]
        f_lo, f_hi = _parse_ci(r3['fleiss_kappa_ci'])
        j_lo, j_hi = _parse_ci(r1['kappa_ci'])
        rare = bool(r3['RARE_class_kappa_unstable'])
        y = ypos[c]
        ax.hlines(y + 0.13, f_lo, f_hi, color='#444444', lw=1.4, zorder=2)
        ax.plot(r3['fleiss_kappa'], y + 0.13, marker='o', color='#444444', mfc='white' if rare else '#444444', ms=st.MS, ls='none', zorder=3)
        ax.hlines(y - 0.13, j_lo, j_hi, color='#D55E00', lw=1.4, zorder=2)
        ax.plot(r1['cohen_kappa'], y - 0.13, marker='s', color='#D55E00', ms=st.MS - 0.5, ls='none', zorder=3, mec='black', mew=0.3)
        rows.append(dict(panel='a', row=c, series='inter-annotator Fleiss kappa (6 simulated annotators)', value=r3['fleiss_kappa'], ci_lo=f_lo, ci_hi=f_hi,
                         n=int(r3['n_items']), rare_class_unstable=rare))
        rows.append(dict(panel='a', row=c, series='judge vs annotator majority, Cohen kappa', value=r1['cohen_kappa'], ci_lo=j_lo, ci_hi=j_hi,
                         n=int(r1['n_items']), rare_class_unstable=rare))
    ax.axvline(0, color='black', lw=0.6)
    ax.set_yticks([ypos[c] for c in classes])
    ax.set_yticklabels([f'{name2id[c]} {st.CLASS_NAMES[name2id[c]]}' for c in classes])
    ax.set_xlabel("Cohen's / Fleiss' κ (95% bootstrap CI over items)")
    ax.set_ylim(-0.6, len(classes) - 0.4)
    ax.set_xlim(-0.15, 0.85)
    ax.grid(axis='x', lw=0.4)
    ax.legend([Line2D([], [], marker='o', color='#444444', lw=1.4, ms=st.MS), Line2D([], [], marker='s', color='#D55E00', lw=1.4, ms=st.MS - 0.5, mec='black', mew=0.3),
               Line2D([], [], marker='o', color='#444444', mfc='white', ls='none', ms=st.MS)],
              ['inter-annotator', 'judge vs. majority', 'rare class (unstable)'], loc='lower left', bbox_to_anchor=(-0.02, 1.0),
              ncol=2, frameon=False, fontsize=st.FS_BASE, handlelength=1.2, handletextpad=0.3, columnspacing=0.8, borderaxespad=0.2)
    st.panel_label(ax, 'a', dx=-0.42)
    ax = axes[1]
    d3 = d3.copy()
    d3['label'] = d3['annotator'].str.replace('_', ' ')
    yp = np.arange(len(d3))[::-1]
    kcol = 'kappa_flags_vs_majority_of_other_five_mean_over_classes'
    for y, (_, r) in zip(yp, d3.iterrows()):
        lo, hi = _parse_ci(r['kappa_ci'])
        col = '#009E73'
        ax.hlines(y, lo, hi, color=col, lw=1.4)
        ax.plot(r[kcol], y, marker='D', color=col, ms=st.MS - 0.5, ls='none', mec='black', mew=0.3)
        rows.append(dict(panel='b', row=r['annotator'], series='annotator vs majority of other five (mean kappa over 7 classes)', value=r[kcol], ci_lo=lo, ci_hi=hi,
                         n=int(r['n_items']), rare_class_unstable=False))
    ax.set_yticks(yp)
    ax.set_yticklabels(d3['label'])
    ax.set_xlabel('κ vs. majority of the other five\n(mean over 7 classes)')
    ax.set_xlim(0.4, 0.75)
    ax.grid(axis='x', lw=0.4)
    st.panel_label(ax, 'b', dx=-0.62)
    fig.text(0.985, 0.005, f'All annotators are simulated (AI-persona) annotators, not clinicians; {n_items} items from {n_img} distinct images.',
             ha='right', va='bottom', fontsize=st.FS_BASE, style='italic', color='#7F2704')
    ctx.note('The six annotation sets are AI-persona (Claude-generated) outputs that were renamed "human_annotations" (see annotation_report.md and project provenance notes). '
             'Figure 12 is therefore labelled as simulated annotators. A persona-versus-clinician panel cannot be made: no clinician labels exist in the repository.', fig='Fig 12')
    ctx.note(f'The {n_items} annotated items come from only {n_img} distinct images, so items are clustered and the item-level bootstrap CIs are optimistic.', fig='Fig 12')
    ctx.not_generated.append(('Fig 12 panel (persona vs clinician)', 'No clinician annotation set exists; every annotator in annotation_results/ is an AI persona, so a persona-vs-clinician comparison is impossible. '
                              'Panels (a)-(b) are plotted and labelled as simulated annotators.'))
    meta = ctx.save(fig, 'fig12_annotation_agreement', pd.DataFrame(rows))
    ctx.add_manifest(
        num=12, name='fig12_annotation_agreement', func=f'{SCRIPT}:fig12',
        sources=['annotation_results/A3_flag_agreement_overall.csv', 'annotation_results/B1_judge_vs_human_per_class.csv',
                 'annotation_results/D3_annotator_agreement_with_majority_and_judge.csv', 'medvihall_outputs/annotation/annotation_key.csv (item/image counts)'],
        claim='Simulated annotators agree moderately with each other on most hallucination classes, and the automatic judge agrees with their majority well only for fabrication.',
        caption=(f'(a) Agreement per hallucination class among six simulated (AI-persona) annotators (Fleiss κ) and between the LLM judge and their majority label (Cohen κ), {n_items} items from {n_img} images. '
                 f'(b) Each annotator\'s mean κ with the majority of the other five; bars are 95% item-bootstrap intervals (2,000 resamples), which are optimistic because items share images, and no clinician annotations are included.'),
        **meta)
