"""Mitigation experiment, three-modality release: strategy effects against the benchmark baseline and against the
greedy baseline, on the same (image, query) items. 2,000 stratified image resamples (seed 42), 20,000 label-swap
permutations, Holm over 10 tests per baseline. Run from ~/work3."""
import json, hashlib, itertools, collections, math
from pathlib import Path
import numpy as np
import pandas as pd
import fig_data as fd
import stage3_pd_label as L

OUT = Path('medvihall_outputs')
W2 = 1.0
CW = {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.5, 5: 0.4, 6: 0.1, 7: 0.6}
MODELS = ['qwen25vl', 'llava16', 'chexagent', 'huatuogpt', 'llava_med']
SPEC = ['chexagent', 'huatuogpt', 'llava_med']
MODS = ['dermatology', 'histopathology', 'ophthalmology']
FILES = {'baseline': OUT / 'pillar_b_baseline.jsonl', 'rag': OUT / 'pillar_b_rag.jsonl', 'cd': OUT / 'pillar_b_contrastive.jsonl'}
FIXED = OUT / 'pillar_b_baseline_llava_med_fixed.jsonl'

def jl(p):
    return L._iter_jsonl(p)

def pseudo(m, resp):
    return f'{m}__{hashlib.sha1(resp.encode("utf-8")).hexdigest()[:12]}'

def load_labels(l2, l1):
    om = {}
    for r in jl(l1):
        om[(r['model'], r['image_id'], r['query_type'])] = len(r.get('omissions', []))
    out = {}
    for r in jl(l2):
        if r.get('_parse_error'):
            continue
        k = (r['model'], r['image_id'], r['query_type'])
        n_om = om.get(k, 0)
        w, c, c12, fab = n_om * CW[2], len(r['claim_judgments']) + n_om, n_om > 0, 0
        for j in r['claim_judgments']:
            if j.get('is_hallucination'):
                w += CW.get(j.get('hallucination_class'), 0)
                if j.get('hallucination_class') in (1, 2):
                    c12 = True
        out[k] = (w, c, int(c12))
    return out

core_lab = load_labels(OUT / 'layer2_judge.jsonl', OUT / 'layer1_verdicts.jsonl')
pb_lab = load_labels(OUT / 'pillar_b_stage3' / 'layer2_judge.jsonl', OUT / 'pillar_b_stage3' / 'layer1_verdicts.jsonl')
pd_lab = load_labels(OUT / 'pillar_d_stage3' / 'layer2_judge.jsonl', OUT / 'pillar_d_stage3' / 'layer1_verdicts.jsonl')
core_resp = {(r['model'], r['image_id'], r['query_type']): r['response'] for r in jl(OUT / 'medvihall_results_deduped.jsonl')}

def label_for(m, img, qt, resp, pool):
    if m != 'llava_med' or pool != 'baseline_fixed':
        pass
    lab = pool.get((pseudo(m, resp), img, qt)) if isinstance(pool, dict) else None
    return lab

# ---- strategy and baseline label tables: dict[m][(img, qt)] = (w, claims, chr)
T = {c: {m: {} for m in MODELS} for c in ('bench', 'greedy', 'rag', 'cd')}
unl = collections.Counter()
rows = {}
for c in ('baseline', 'rag', 'cd'):
    rows[c] = {}
    for r in jl(FILES[c]):
        rows[c][(r['model'], r['image_id'], r['query_type'])] = r
for r in jl(FIXED):
    rows['baseline'][(r['model'], r['image_id'], r['query_type'])] = r
for (m, img, qt), r in rows['baseline'].items():
    if m not in MODELS:
        continue
    if m == 'llava_med':
        lab = pb_lab.get((pseudo(m, r['response']), img, qt)) or (core_lab.get((m, img, qt)) if core_resp.get((m, img, qt)) == r['response'] else None)
    else:
        lab = core_lab.get((m, img, qt))
    if lab is None:
        unl[('bench', m)] += 1; continue
    T['bench'][m][(img, qt)] = lab
for c, name in (('rag', 'rag'), ('cd', 'cd')):
    for (m, img, qt), r in rows[c].items():
        lab = pb_lab.get((pseudo(m, r['response']), img, qt))
        if lab is None and core_resp.get((m, img, qt)) == r['response']:
            lab = core_lab.get((m, img, qt))
        if lab is None:
            unl[(name, m)] += 1; continue
        T[name][m][(img, qt)] = lab
# greedy baseline: temperature-0 greedy configuration of the calibration experiment, responses with a stated confidence
runs, excl, regen = L.load_effective_runs()
for (m, cfg, img, qt), r in runs.items():
    if cfg != 'temp0.0_greedy' or m not in MODELS or m == 'llava_med':
        continue
    if r.get('confidence') is None:
        continue
    resp = r['response']
    lab = core_lab.get((m, img, qt)) if core_resp.get((m, img, qt)) == resp else pd_lab.get((pseudo(m, resp), img, qt))
    if lab is None:
        unl[('greedy', m)] += 1; continue
    T['greedy'][m][(img, qt)] = lab
T['greedy']['llava_med'] = dict(T['bench']['llava_med'])        # corrected greedy rerun is the benchmark baseline for this model
print('labelled items', {c: {m: len(v) for m, v in d.items()} for c, d in T.items()})
print('unlabelled', dict(unl))

# ---- subset images
imgs = sorted({k[0] for m in MODELS for k in T['bench'][m]} | {k[0] for m in MODELS for k in T['rag'][m]})
man = fd.load_manifest().set_index('image_id')
sub = man.loc[imgs].reset_index()
N = len(sub); idx = {i: n for n, i in enumerate(sub['image_id'])}
print('subset images', N, sub['stratum'].value_counts().to_dict(), sub['modality'].value_counts().to_dict())
B = 2000
rng = np.random.default_rng(42)
counts = np.zeros((B, N))
for st, g in sub.groupby('stratum').groups.items():
    ii = np.asarray(list(g)); n = len(ii)
    counts[:, ii] = rng.multinomial(n, np.full(n, 1 / n), size=B)
modv = sub['modality'].values

def arr(m, c, keys=None):
    num, den, chrv, cnt = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
    for (img, qt), (w, cl, ch) in T[c][m].items():
        if keys is not None and (img, qt) not in keys:
            continue
        i = idx[img]; num[i] += w; den[i] += cl; chrv[i] += ch; cnt[i] += 1
    return num, den, chrv, cnt

def perm_p(na, da, nb, db, nperm=20000, seed=0):
    r = np.random.default_rng(seed); n = len(na)
    tn, td = na.sum() + nb.sum(), da.sum() + db.sum()
    obs = na.sum() / da.sum() - nb.sum() / db.sum()
    cnt = done = 0
    dn, dd = na - nb, da - db
    while done < nperm:
        k = min(4000, nperm - done)
        S = (r.random((k, n)) < 0.5).astype(float)
        N1 = nb.sum() + S @ dn; D1 = db.sum() + S @ dd
        st = N1 / D1 - (tn - N1) / (td - D1)
        cnt += int(np.sum(np.abs(st) >= abs(obs) - 1e-12)); done += k
    return (1 + cnt) / (nperm + 1)

def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1, run)
    return adj

def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]

def paired(m, a, base, seed=0):
    ka, kb = set(T[a][m]), set(T[base][m]); keys = ka & kb
    na, da, ca, cta = arr(m, a, keys); nb, db, cb, ctb = arr(m, base, keys)
    pa, pb = na.sum() / da.sum(), nb.sum() / db.sum()
    with np.errstate(invalid='ignore', divide='ignore'):
        bd = (counts @ na) / (counts @ da) - (counts @ nb) / (counts @ db)
        bc = (counts @ ca) / (counts @ cta) - (counts @ cb) / (counts @ ctb)
    return dict(n=len(keys), base=float(pb), strat=float(pa), delta=float(pa - pb), ci=ci(bd), p=perm_p(na, da, nb, db, 20000, seed),
                chr_delta=float(ca.sum() / cta.sum() - cb.sum() / ctb.sum()), chr_ci=ci(bc))

R = {'subset': dict(images=N, strata=sub['stratum'].value_counts().to_dict(), modality=sub['modality'].value_counts().to_dict(),
                    items_bench={m: len(T['bench'][m]) for m in MODELS}, items_greedy={m: len(T['greedy'][m]) for m in MODELS},
                    items_rag={m: len(T['rag'][m]) for m in MODELS}, items_cd={m: len(T['cd'][m]) for m in MODELS},
                    unlabelled={f'{k[0]}|{k[1]}': v for k, v in unl.items()})}
res = {}
sd = 0
for base in ('bench', 'greedy'):
    res[base] = {}
    for m in MODELS:
        for s in ('rag', 'cd'):
            sd += 1
            res[base][(m, s)] = paired(m, s, base, seed=sd)
    keys = list(res[base])
    adj = holm([res[base][k]['p'] for k in keys])
    for k, a in zip(keys, adj):
        res[base][k]['p_holm'] = float(a)
R['table'] = {base: {f'{m}|{s}': v for (m, s), v in d.items()} for base, d in res.items()}
# decoding alone: greedy minus benchmark baseline on the same items
R['decoding_alone'] = {m: paired(m, 'greedy', 'bench', seed=900 + i) for i, m in enumerate(MODELS)}
# RAG effect vs benchmark baseline restricted to items that have a greedy label
R['rag_vs_bench_on_greedy_items'] = {}
for m in MODELS:
    keys = set(T['rag'][m]) & set(T['bench'][m]) & set(T['greedy'][m])
    na, da, _, _ = arr(m, 'rag', keys); nb, db, _, _ = arr(m, 'bench', keys)
    bd = (counts @ na) / (counts @ da) - (counts @ nb) / (counts @ db)
    R['rag_vs_bench_on_greedy_items'][m] = dict(n=len(keys), delta=float(na.sum() / da.sum() - nb.sum() / db.sum()), ci=ci(bd))
# CD versus RAG, direct
dd = {}
for i, m in enumerate(MODELS):
    keys = set(T['rag'][m]) & set(T['cd'][m])
    na, da, _, _ = arr(m, 'cd', keys); nb, db, _, _ = arr(m, 'rag', keys)
    dd[m] = dict(n=len(keys), delta=float(na.sum() / da.sum() - nb.sum() / db.sum()),
                 ci=ci((counts @ na) / (counts @ da) - (counts @ nb) / (counts @ db)), p=perm_p(na, da, nb, db, 20000, 500 + i))
adj = holm([v['p'] for v in dd.values()])
for (m, v), a in zip(dd.items(), adj):
    v['p_holm5'] = float(a)
R['cd_vs_rag'] = dd
# by-modality effect (for the "without X" style statements): strategy vs benchmark baseline within each modality
bym = {}
for m in MODELS:
    for s in ('rag', 'cd'):
        for md in MODS:
            keys = {k for k in set(T[s][m]) & set(T['bench'][m]) if modv[idx[k[0]]] == md}
            na, da, _, _ = arr(m, s, keys); nb, db, _, _ = arr(m, 'bench', keys)
            bd = (counts @ na) / (counts @ da) - (counts @ nb) / (counts @ db)
            bym[f'{m}|{s}|{md}'] = dict(n=len(keys), delta=float(na.sum() / da.sum() - nb.sum() / db.sum()), ci=ci(bd))
R['by_modality_vs_bench'] = bym
# mean SRI over the nine cells (reference = better of the two general models in each modality and condition)
def sri_mean(c, keys_fn=None):
    sums = {}
    for m in MODELS:
        n_, d_, _, _ = arr(m, c)
        for md in MODS:
            sel = modv == md
            sums[(m, md)] = (counts[:, sel] @ n_[sel], counts[:, sel] @ d_[sel], n_[sel].sum(), d_[sel].sum())
    out_b, out_p = [], []
    for md in MODS:
        refb = np.minimum(sums[('qwen25vl', md)][0] / sums[('qwen25vl', md)][1], sums[('llava16', md)][0] / sums[('llava16', md)][1])
        refp = min(sums[('qwen25vl', md)][2] / sums[('qwen25vl', md)][3], sums[('llava16', md)][2] / sums[('llava16', md)][3])
        for s in SPEC:
            out_b.append((sums[(s, md)][0] / sums[(s, md)][1]) / refb)
            out_p.append((sums[(s, md)][2] / sums[(s, md)][3]) / refp)
    return np.mean(out_b, 0), float(np.mean(out_p))
sm = {c: sri_mean(c) for c in ('bench', 'greedy', 'rag', 'cd')}
R['mean_sri'] = {c: float(v[1]) for c, v in sm.items()}
R['mean_sri_diff'] = {}
for s in ('rag', 'cd'):
    for base in ('bench', 'greedy'):
        d = sm[s][0] - sm[base][0]
        R['mean_sri_diff'][f'{s}_vs_{base}'] = dict(delta=float(sm[s][1] - sm[base][1]), ci=ci(d))
json.dump(R, open('mitig3_results.json', 'w'), indent=1, default=float)

print(json.dumps(R['subset'], indent=0)[:900])
for base in ('bench', 'greedy'):
    print('==', base)
    for (m, s), v in res[base].items():
        print(f'{m:10s} {s:4s} n={v["n"]} delta {v["delta"]:+.3f} [{v["ci"][0]:+.3f},{v["ci"][1]:+.3f}] p={v["p"]:.4f} holm={v["p_holm"]:.3f} | chr {v["chr_delta"]:+.3f} [{v["chr_ci"][0]:+.3f},{v["chr_ci"][1]:+.3f}]')
print('decoding alone', {m: (round(v['delta'], 3), [round(x, 3) for x in v['ci']], v['n']) for m, v in R['decoding_alone'].items()})
print('rag on greedy items', R['rag_vs_bench_on_greedy_items'])
print('cd vs rag', {m: (round(v['delta'], 3), round(v['p_holm5'], 4)) for m, v in dd.items()})
print('mean sri', R['mean_sri'], R['mean_sri_diff'])
