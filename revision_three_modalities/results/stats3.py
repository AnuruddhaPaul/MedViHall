"""MedViHall, three-modality release: statistics reported in the text.
One bootstrap configuration throughout: 2,000 resamples of images, stratified by design stratum, seed 42,
paired across models. Permutation tests: 20,000 label swaps within image (100,000 for rank correlations).
Run from ~/work3 (filtered, radiology-free copies of the result files)."""
import json, itertools, math, sys, os
import numpy as np
import pandas as pd
import fig_data as fd

W = {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.5, 5: 0.4, 6: 0.1, 7: 0.6}
Wv = np.array([W[k] for k in range(1, 8)])
GEN = ['qwen25vl', 'gemma3', 'internvl3', 'qwen35', 'qwen3vl', 'minicpm', 'idefics3', 'qwen2vl', 'llava16']
SPEC = ['huatuogpt', 'chexagent', 'llava_med']
MODELS = GEN + SPEC
QWEN = {'qwen25vl', 'qwen35', 'qwen3vl', 'qwen2vl'}
NONQ = [g for g in GEN if g not in QWEN]
MODS = ['dermatology', 'histopathology', 'ophthalmology']
NORMAL = ['DS1', 'HS1', 'OS1']
rng = np.random.default_rng(42)
R = {}

df, info = fd.build_record_table(W)
assert set(df['modality']) == set(MODS), set(df['modality'])
df = df.copy()
df['valid'] = (~df['parse_error']).astype(int)
df['chr'] = (df['has12'] & (~df['parse_error'])).astype(int)
df['fab'] = df['c1']
df['omn'] = df['n_om']
df['jw'] = df['w'] - df['n_om'] * W[2]
df['jc'] = df['claims'] - df['n_om']
df['macro'] = np.where(df['claims'] > 0, df['w'] / df['claims'].clip(lower=1), 0.0)
df['macro_n'] = ((df['claims'] > 0) & (~df['parse_error'])).astype(int)
df['err'] = sum(df[f'c{k}'] for k in range(1, 8))
images = fd.load_manifest()
assert set(df['image_id']) <= set(images['image_id'])
b = fd.Boot(df, images)
N, B = b.N, b.B
R['meta'] = dict(n_images=N, n_records=int(len(df)), n_models=len(MODELS), boot=B, seed=42, stratified=True,
                 records_per_model=int(len(df) / 12), parse_errors_total=int(df['parse_error'].sum()))
mask = {md: b.mask(modality=md) for md in MODS}
allm = np.ones(N, bool)
print('images', N, 'records', len(df), 'per model', len(df) / 12)

# ---------------------------------------------------------------- helpers
def rat(m, num, den, msk=None, q='all'):
    return b.ratio(m, num, den, msk if msk is not None else allm, q)

def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]

def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1.0, run)
    return adj

def perm_test(na, da, nb, db, nperm=20000, logratio=False, seed=0):
    r = np.random.default_rng(seed)
    n = len(na)
    tn, td = na.sum() + nb.sum(), da.sum() + db.sum()
    f = (lambda x, y: np.log(x / y)) if logratio else (lambda x, y: x - y)
    obs = f(na.sum() / da.sum(), nb.sum() / db.sum())
    cnt, done = 0, 0
    dn, dd = na - nb, da - db
    while done < nperm:
        k = min(4000, nperm - done)
        S = (r.random((k, n)) < 0.5).astype(np.float64)
        N1 = nb.sum() + S @ dn; D1 = db.sum() + S @ dd
        N2, D2 = tn - N1, td - D1
        st = f(N1 / D1, N2 / D2)
        cnt += int(np.sum(np.abs(st) >= abs(obs) - 1e-12)); done += k
    return float((1 + cnt) / (nperm + 1)), float(obs)

def ranks(x):
    x = np.asarray(x, float); o = np.argsort(x, kind='mergesort'); r = np.empty(len(x)); i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[o[j + 1]] == x[o[i]]:
            j += 1
        r[o[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return r

def spearman(a, c):
    ra, rc = ranks(a), ranks(c); ra -= ra.mean(); rc -= rc.mean()
    return float(ra @ rc / math.sqrt((ra @ ra) * (rc @ rc)))

def fisher(r, n):
    z = math.atanh(r); se = 1 / math.sqrt(n - 3)
    return [math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)]

def spearman_perm(a, c, nperm=100000, seed=1):
    r = np.random.default_rng(seed)
    ra, rc = ranks(a), ranks(c); ra = ra - ra.mean(); rc = rc - rc.mean()
    den = math.sqrt((ra @ ra) * (rc @ rc)); obs = float(ra @ rc / den)
    P = np.argsort(r.random((nperm, len(a))), axis=1)
    rho = (rc[P] @ ra) / den
    return float((1 + np.sum(np.abs(rho) >= abs(obs) - 1e-12)) / (nperm + 1)), obs

# ---------------------------------------------------------------- 1. overall ranking
ov = {}
for m in MODELS:
    p, bs = rat(m, 'w', 'claims')
    pc, bc = rat(m, 'chr', 'valid')
    ov[m] = dict(smhr=p, ci=ci(bs), chr=pc, chr_ci=ci(bc), claims=int(b.vec(m, 'claims').sum()),
                 records=int(b.vec(m, 'records').sum()), parse_err=int(len(df[(df.model == m)]) - b.vec(m, 'valid').sum()),
                 om_share_weighted=float(b.vec(m, 'omn').sum() * W[2] / b.vec(m, 'w').sum()),
                 unweighted=float(b.vec(m, 'err').sum() / b.vec(m, 'claims').sum()))
    ov[m]['_boots'] = bs
M = np.array([ov[m]['_boots'] for m in MODELS])             # 12 x B
rk = np.argsort(np.argsort(M, axis=0), axis=0) + 1
order = sorted(MODELS, key=lambda m: ov[m]['smhr'])
for i, m in enumerate(MODELS):
    ov[m]['rank_point'] = order.index(m) + 1
    ov[m]['rank_ci'] = [float(np.percentile(rk[i], 2.5)), float(np.percentile(rk[i], 97.5))]
    ov[m]['p_rank1'] = float(np.mean(rk[i] == 1))
pairs = []
for i, j in itertools.combinations(range(12), 2):
    d = M[i] - M[j]
    pairs.append(dict(a=MODELS[i], b=MODELS[j], diff=float(ov[MODELS[i]]['smhr'] - ov[MODELS[j]]['smhr']), ci=ci(d),
                      sep=bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0)))
R['ranking'] = dict(order=order, n_pairs=len(pairs), n_sep=sum(p['sep'] for p in pairs),
                    not_separated=[p for p in pairs if not p['sep']],
                    models={m: {k: v for k, v in ov[m].items() if k != '_boots'} for m in MODELS})
top5 = order[:5]
tp = []
for x, y in itertools.combinations(top5, 2):
    na, da = b.vec(x, 'w'), b.vec(x, 'claims'); nb, db = b.vec(y, 'w'), b.vec(y, 'claims')
    p, obs = perm_test(na, da, nb, db, 20000, False, seed=hash((x, y)) % 1000)
    tp.append(dict(a=x, b=y, diff=obs, p=p))
adj = holm([t['p'] for t in tp])
for t, a in zip(tp, adj):
    t['p_holm'] = float(a)
R['top5_pairs'] = dict(top5=top5, tests=tp)
R['smhr_chr_rho'] = dict(rho=spearman([ov[m]['smhr'] for m in MODELS], [ov[m]['chr'] for m in MODELS]),
                         fisher=fisher(spearman([ov[m]['smhr'] for m in MODELS], [ov[m]['chr'] for m in MODELS]), 12),
                         chr_min=min(ov[m]['chr'] for m in MODELS), chr_max=max(ov[m]['chr'] for m in MODELS),
                         lowest_chr=sorted(MODELS, key=lambda m: ov[m]['chr'])[:4],
                         chr_sorted=[(m, ov[m]['chr']) for m in sorted(MODELS, key=lambda m: ov[m]['chr'])])
R['smhr_unweighted_rho'] = spearman([ov[m]['smhr'] for m in MODELS], [ov[m]['unweighted'] for m in MODELS])
print('order', order)

# ---------------------------------------------------------------- 2. SRI machinery
def cellstats(num, den, q='all', refset=GEN):
    out = {}
    for md in MODS:
        pt = {}; bt = {}
        for m in MODELS:
            pt[m], bt[m] = rat(m, num, den, mask[md], q)
        ref = min(refset, key=lambda g: pt[g])
        beaten = {s: int(sum(pt[s] < pt[g] for g in GEN)) for s in SPEC}
        out[md] = dict(ref=ref, ref_value=pt[ref], values=pt, beaten=beaten,
                       sri={s: [pt[s] / pt[ref]] + ci(bt[s] / bt[ref]) for s in SPEC})
    return out

def summarize(cs, spec=SPEC):
    cells = [(md, s) + tuple(cs[md]['sri'][s]) for md in MODS for s in spec]
    pts = [c[2] for c in cells]; lo = [c[3] for c in cells]; hi = [c[4] for c in cells]
    return dict(n_cells=len(cells), range=[min(pts), max(pts)], lowest_lower=min(lo),
                above1=sum(l > 1 for l in lo), below1=sum(h < 1 for h in hi))

main = cellstats('w', 'claims')
R['sri_main'] = main
R['sri_main_summary'] = dict(all9=summarize(main), six=summarize(main, ['huatuogpt', 'llava_med']))
# permutation tests, Holm over 9 and over 6
cells, praw = [], []
for md in MODS:
    ref = main[md]['ref']
    for s in SPEC:
        p, obs = perm_test(b.vec(s, 'w')[mask[md]], b.vec(s, 'claims')[mask[md]], b.vec(ref, 'w')[mask[md]],
                           b.vec(ref, 'claims')[mask[md]], 20000, True, seed=len(cells) + 11)
        cells.append(dict(md=md, model=s, ref=ref, sri=float(math.exp(obs)), p=p)); praw.append(p)
h9 = holm(praw)
idx6 = [i for i, c in enumerate(cells) if c['model'] != 'chexagent']
h6 = holm([praw[i] for i in idx6])
for i, c in enumerate(cells):
    c['p_holm9'] = float(h9[i])
for k, i in enumerate(idx6):
    cells[i]['p_holm6'] = float(h6[k])
R['sri_perm'] = dict(cells=cells, floor9=9 / 20001, floor6=6 / 20001, max_holm9=float(h9.max()), max_holm6=float(h6.max()))

# ---------------------------------------------------------------- 3. controls table
rows = {}
rows['SMHR (as reported)'] = cellstats('w', 'claims')
rows['SMHR without Q4'] = cellstats('w', 'claims', q='Q123')
rows['SMHR per response, averaged'] = cellstats('macro', 'macro_n')
rows['Judged claims only'] = cellstats('jw', 'jc')
rows['Fabrication rate'] = cellstats('fab', 'claims')
rows['Omission rate'] = cellstats('omn', 'claims')
rows['SMHR, non-Qwen reference'] = cellstats('w', 'claims', refset=NONQ)
rows['CHR'] = cellstats('chr', 'valid')
rows['CHR, non-Qwen reference'] = cellstats('chr', 'valid', refset=NONQ)
R['controls'] = {k: dict(summary9=summarize(v), summary6=summarize(v, ['huatuogpt', 'llava_med']),
                         refs={md: v[md]['ref'] for md in MODS}, sri=v) for k, v in rows.items()}
R['ref_by_metric'] = {k: {md: v[md]['ref'] for md in MODS} for k, v in rows.items()}

# ---------------------------------------------------------------- 4. class-count machinery (weights)
X = {}   # (model, md) -> N x 8 (c1..c7, claims) restricted later
for m in MODELS:
    X[m] = np.column_stack([b.vec(m, f'c{k}') for k in range(1, 8)] + [b.vec(m, 'claims')])
def boots_cnt(m, msk):
    return b.counts[:, msk] @ X[m][msk]                       # B x 8
BS = {(m, md): boots_cnt(m, mask[md]) for m in MODELS for md in MODS}
PT = {(m, md): X[m][mask[md]].sum(0) for m in MODELS for md in MODS}
chk = max(abs((PT[(m, md)][:7] @ Wv) / PT[(m, md)][7] - rat(m, 'w', 'claims', mask[md])[0]) for m in MODELS for md in MODS)
print('weight check (should be ~0):', chk)
R['meta']['weight_check_maxdiff'] = float(chk)
SPECROWS = [MODELS.index(s) for s in SPEC]

def eval_w(w, with_boot=False):
    sm_pt = {k: (v[:7] @ w) / v[7] for k, v in PT.items()}
    ov_pt = {m: sum(PT[(m, md)][:7] @ w for md in MODS) / sum(PT[(m, md)][7] for md in MODS) for m in MODELS}
    refs = {md: min(GEN, key=lambda g: sm_pt[(g, md)]) for md in MODS}
    cells = [sm_pt[(s, md)] / sm_pt[(refs[md], md)] for md in MODS for s in SPEC]
    cells6 = [sm_pt[(s, md)] / sm_pt[(refs[md], md)] for md in MODS for s in ['huatuogpt', 'llava_med']]
    top3 = set(sorted(MODELS, key=lambda m: ov_pt[m])[-3:]) == set(SPEC)
    out = dict(cells=cells, min=min(cells), all_gt1=all(c > 1 for c in cells), all6_gt1=all(c > 1 for c in cells6), top3=top3,
               ov=ov_pt, rank=np.argsort(np.argsort([ov_pt[m] for m in MODELS])))
    if with_boot:
        nums = np.stack([sum(BS[(m, md)][:, :7] @ w for md in MODS) for m in MODELS], 1)
        dens = np.stack([sum(BS[(m, md)][:, 7] for md in MODS) for m in MODELS], 1)
        S = nums / dens                                       # B x 12
        t3b = S[:, SPECROWS].min(1) > S[:, :9].max(1)
        allb = np.ones(B, bool)
        for md in MODS:
            ref = refs[md]
            for s in SPEC:
                allb &= (BS[(s, md)][:, :7] @ w / BS[(s, md)][:, 7]) / (BS[(ref, md)][:, :7] @ w / BS[(ref, md)][:, 7]) > 1
        out['top3_b'] = t3b; out['all_b'] = allb
    return out

e0 = eval_w(Wv)
eq = eval_w(np.ones(7), True)
sm_eq = {}
for md in MODS:
    pt = {m: (PT[(m, md)][:7].sum()) / PT[(m, md)][7] for m in MODELS}
    ref = min(GEN, key=lambda g: pt[g])
    sm_eq[md] = {s: [pt[s] / pt[ref]] + ci((BS[(s, md)][:, :7].sum(1) / BS[(s, md)][:, 7]) / (BS[(ref, md)][:, :7].sum(1) / BS[(ref, md)][:, 7])) for s in SPEC}
eqc = [v for md in MODS for v in sm_eq[md].values()]
R['equal_weights'] = dict(range=[min(c[0] for c in eqc), max(c[0] for c in eqc)], lowest_lower=min(c[1] for c in eqc),
                          rho=float(np.corrcoef(eq['rank'], e0['rank'])[0, 1]), cells=sm_eq)
def spear_rank(a, c):
    return spearman(a, c)
def perturb(ndraw, seed=42, with_boot=False):
    r = np.random.default_rng(seed); res = []; t3 = np.zeros(B); al = np.zeros(B)
    for _ in range(ndraw):
        w = Wv * r.uniform(0.7, 1.3, 7)
        e = eval_w(w, with_boot)
        res.append((e['min'], e['all_gt1'], e['all6_gt1'], e['top3'], spear_rank(e['rank'], e0['rank'])))
        if with_boot:
            t3 += e['top3_b']; al += e['all_b']
    res = np.array(res, float)
    out = dict(draws=ndraw, min_sri_min=float(res[:, 0].min()), share_all_gt1=float(res[:, 1].mean()), share_all6_gt1=float(res[:, 2].mean()),
               share_top3=float(res[:, 3].mean()), rho_mean=float(res[:, 4].mean()), rho_min=float(res[:, 4].min()),
               rho_ci=ci(res[:, 4]))
    if with_boot:
        out['top3_boot_ci'] = ci(t3 / ndraw); out['all_gt1_boot_ci'] = ci(al / ndraw)
    return out
R['perturb200'] = perturb(200, 42, True)
R['perturb2000'] = perturb(2000, 43, False)
print('perturb200', R['perturb200']); print('perturb2000', R['perturb2000'])

# ---------------------------------------------------------------- 5. split-half reference selection
nspl = 1000
H = np.zeros((nspl, N))
strat = images['stratum'].values
for st in np.unique(strat):
    ii = np.where(strat == st)[0]
    for s in range(nspl):
        H[s, rng.permutation(ii)[:len(ii) // 2]] = 1
cnt_all, cnt6, mins = 0, 0, []
sums = {}
for m in MODELS:
    for md in MODS:
        wv, cv = b.vec(m, 'w')[mask[md]], b.vec(m, 'claims')[mask[md]]
        Hm = H[:, mask[md]]
        sums[(m, md)] = (Hm @ wv, Hm @ cv, wv.sum(), cv.sum())
for s in range(nspl):
    ok, ok6, mn = True, True, 9
    for md in MODS:
        A = {m: sums[(m, md)][0][s] / sums[(m, md)][1][s] for m in GEN}
        ref = min(A, key=A.get)
        Bs = lambda m: (sums[(m, md)][2] - sums[(m, md)][0][s]) / (sums[(m, md)][3] - sums[(m, md)][1][s])
        for sp in SPEC:
            v = Bs(sp) / Bs(ref); mn = min(mn, v)
            if v <= 1:
                ok = False
                if sp != 'chexagent':
                    ok6 = False
    cnt_all += ok; cnt6 += ok6; mins.append(mn)
R['split_half'] = dict(splits=nspl, share_all9_gt1=cnt_all / nspl, share_six_gt1=cnt6 / nspl, min_sri=float(min(mins)))

# ---------------------------------------------------------------- 6. symmetric random label flips (claim level)
def flips(p, ndraw=1000, seed=5):
    r = np.random.default_rng(seed); out = []
    top2_ref = set(order[:2])
    base_cls = {md: sum(PT[(m, md)][[0, 2, 3, 4, 5, 6]] for m in MODELS) for md in MODS}
    for _ in range(ndraw):
        sm = {}
        for md in MODS:
            pc = base_cls[md] / base_cls[md].sum()
            for m in MODELS:
                v = PT[(m, md)]
                n_om = None
                om = b.vec(m, 'omn')[mask[md]].sum()
                judged = v[7] - om
                hall = v[[0, 2, 3, 4, 5, 6]]
                removed = r.binomial(hall.astype(int), p)
                n_h = hall.sum()
                added_n = r.binomial(int(judged - n_h), p)
                added = r.multinomial(added_n, pc)
                new = hall - removed + added
                num = new @ Wv[[0, 2, 3, 4, 5, 6]] + om * W[2]
                sm[(m, md)] = num / v[7]
        ok = True; ok6 = True
        for md in MODS:
            ref = min(GEN, key=lambda g: sm[(g, md)])
            for sp in SPEC:
                if sm[(sp, md)] / sm[(ref, md)] <= 1:
                    ok = False
                    if sp != 'chexagent':
                        ok6 = False
        ovx = {m: sum(sm[(m, md)] * PT[(m, md)][7] for md in MODS) / sum(PT[(m, md)][7] for md in MODS) for m in MODELS}
        o2 = sorted(MODELS, key=lambda m: ovx[m])
        out.append((ok, ok6, set(o2[:2]) == top2_ref, o2[0] == order[0], set(o2[:5]) == set(order[:5])))
    a = np.array(out, float)
    return dict(p=p, draws=ndraw, share_all9_gt1=float(a[:, 0].mean()), share_six_gt1=float(a[:, 1].mean()),
                share_top2_same=float(a[:, 2].mean()), share_first_same=float(a[:, 3].mean()), share_top5_same=float(a[:, 4].mean()))
R['flips'] = [flips(p) for p in (0.03, 0.05, 0.10, 0.13, 0.20)]
print('flips', R['flips'])

# ---------------------------------------------------------------- 7. cell table, modality, variance decomposition
cell = {}
for m in MODELS:
    for md in MODS:
        p, bs = rat(m, 'w', 'claims', mask[md])
        pc, bc = rat(m, 'chr', 'valid', mask[md])
        cell[(m, md)] = (p, ci(bs), bs, pc)
R['cell'] = {f'{m}|{md}': [cell[(m, md)][0]] + cell[(m, md)][1] + [cell[(m, md)][3]] for m in MODELS for md in MODS}
C = np.array([[cell[(m, md)][0] for md in MODS] for m in MODELS])
gm = C.mean(); ssm = 3 * ((C.mean(1) - gm) ** 2).sum(); ssd = 12 * ((C.mean(0) - gm) ** 2).sum(); sst = ((C - gm) ** 2).sum()
R['variance'] = dict(model=ssm / sst, modality=ssd / sst, interaction=(sst - ssm - ssd) / sst, cells=36)
lowest = C.argmin(1); highest = C.argmax(1)
CB = np.array([[cell[(m, md)][2] for md in MODS] for m in MODELS])       # 12 x 3 x B
low_b = CB.argmin(1)                                                        # 12 x B
R['modality_extremes'] = dict(
    lowest_counts={md: int((lowest == i).sum()) for i, md in enumerate(MODS)},
    highest_counts={md: int((highest == i).sum()) for i, md in enumerate(MODS)},
    lowest_boot_range={md: [float(np.percentile((low_b == i).sum(0), 2.5)), float(np.percentile((low_b == i).sum(0), 97.5))] for i, md in enumerate(MODS)},
    mean_by_modality={md: float(C[:, i].mean()) for i, md in enumerate(MODS)})
# class composition
comp = {}
CL = ['fabrication', 'omission', 'misclassification', 'severity', 'anatomical', 'evasion', 'reasoning']
for md in MODS:
    tot = sum(PT[(m, md)][:7] for m in MODELS)
    macro = np.mean([PT[(m, md)][:7] / PT[(m, md)][:7].sum() for m in MODELS], axis=0)
    comp[md] = dict(pooled=dict(zip(CL, (tot / tot.sum()).tolist())), macro=dict(zip(CL, macro.tolist())), flagged=float(tot.sum()))
R['composition'] = comp
R['flagged_total'] = float(sum(v['flagged'] for v in comp.values()))
tot_all = sum(PT[(m, md)][:7] for m in MODELS for md in MODS)
R['fab_om_pooled_overall'] = float((tot_all[0] + tot_all[1]) / tot_all.sum())
R['fab_om_pooled_by_mod'] = {md: comp[md]['pooled']['fabrication'] + comp[md]['pooled']['omission'] for md in MODS}
R['fab_om_macro_by_mod'] = {md: comp[md]['macro']['fabrication'] + comp[md]['macro']['omission'] for md in MODS}

# ---------------------------------------------------------------- 8. correlations across modalities
xm = {md: [cell[(m, md)][0] for m in MODELS] for md in MODS}
cors = []
for a_, c_ in itertools.combinations(MODS, 2):
    p, r_ = spearman_perm(xm[a_], xm[c_], 100000, seed=len(cors) + 3)
    g = spearman(xm[a_][:9], xm[c_][:9])
    cors.append(dict(a=a_, b=c_, rho=r_, p=p, fisher=fisher(r_, 12), rho_general_only=g))
ph = holm([c['p'] for c in cors])
for c, a in zip(cors, ph):
    c['p_holm'] = float(a)
R['cross_modality'] = cors
R['sri_corr_n3_min_p'] = 0.333

# ---------------------------------------------------------------- 9. per-query table, normal/abnormal, Q4
pq = {}
for m in MODELS:
    pq[m] = [rat(m, 'w', 'claims', allm, f'Q{i}')[0] for i in (1, 2, 3, 4)]
R['per_query'] = pq
R['per_query_best'] = {f'Q{i + 1}': min(MODELS, key=lambda m: pq[m][i]) for i in range(4)}
R['q1_lowest_count'] = int(sum(np.argmin(pq[m]) == 0 for m in MODELS))
nm = images['stratum'].isin(NORMAL).values
R['n_normal'] = int(nm.sum()); R['n_abnormal'] = int((~nm).sum())
na_ = {}
for md in MODS:
    d = []
    for m in MODELS:
        pn, bn = rat(m, 'w', 'claims', mask[md] & nm, 'Q123')
        pa, ba = rat(m, 'w', 'claims', mask[md] & ~nm, 'Q123')
        d.append((m, pn - pa, ci(bn - ba)))
    na_[md] = dict(mean_diff=float(np.mean([x[1] for x in d])), n_lower=int(sum(x[1] < 0 for x in d)), n_higher=int(sum(x[1] > 0 for x in d)),
                   n_lower_sig=int(sum(x[2][1] < 0 for x in d)), n_higher_sig=int(sum(x[2][0] > 0 for x in d)), per_model={x[0]: x[1] for x in d})
R['normal_vs_abnormal'] = na_
q4 = []
for m in MODELS:
    p4, b4 = rat(m, 'w', 'claims', nm, 'Q4'); p3, b3 = rat(m, 'w', 'claims', nm, 'Q123')
    q4.append((m, p4 - p3, ci(b4 - b3)))
R['q4_vs_q123_normal'] = dict(per_model={x[0]: [x[1]] + x[2] for x in q4}, higher=sum(x[2][0] > 0 for x in q4), lower=sum(x[2][1] < 0 for x in q4),
                              unchanged=sum(x[2][0] <= 0 <= x[2][1] for x in q4), mean_diff=float(np.mean([x[1] for x in q4])))

# ---------------------------------------------------------------- save
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o
json.dump(clean(R), open('stats3_results.json', 'w'), indent=1)
print('saved')
