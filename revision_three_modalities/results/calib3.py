import json, itertools, numpy as np
from pathlib import Path
import stage3_pd_label as L, stage3_pd_ece as E, fig_data as fd
runs, excl, regen = L.load_effective_runs()
core = L.load_core_responses()
cl = E.load_labels(E.CORE_L2, E.CORE_L1); fl = E.load_labels(L.L2, L.L1_ALL)
cells = {}
for (m, cfg, img, qt), r in runs.items():
    if r.get('confidence') is None: continue
    resp = r['response']
    lab = cl.get((m, img, qt)) if core.get((m, img, qt)) == resp else fl.get((L.pseudo_model(m, resp), img, qt))
    if lab is None: continue
    cells.setdefault((m, cfg), []).append((img, min(max(float(r['confidence']), 0), 100) / 100, int(lab['claims_ok'] and lab['n_omissions'] == 0)))
imgs = sorted({x[0] for v in cells.values() for x in v})
man = fd.load_manifest().set_index('image_id'); sub = man.loc[imgs].reset_index(); idx = {i: n for n, i in enumerate(sub['image_id'])}
N = len(sub); B = 2000; rng = np.random.default_rng(42)
counts = np.zeros((B, N))
for st, g in sub.groupby('stratum').groups.items():
    ii = np.asarray(list(g)); counts[:, ii] = rng.multinomial(len(ii), np.full(len(ii), 1 / len(ii)), size=B)
MODELS = E.MODELS; EFF = ['temp0.0_greedy', 'temp0.0_nucleus', 'temp0.3_nucleus', 'temp0.7_nucleus']
def ece_w(conf, corr, w):          # w: B x n weights
    bins = np.minimum((conf * 10).astype(int), 9); out = np.zeros(w.shape[0]); tot = w.sum(1)
    for b in range(10):
        s = bins == b
        if not s.any(): continue
        wb = w[:, s]; sw = wb.sum(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            acc = (wb * corr[s]).sum(1) / sw; cf = (wb * conf[s]).sum(1) / sw
        out += np.nan_to_num(sw / tot * np.abs(acc - cf))
    return out
ece_b = {}; over = {}; acc = {}; conf_m = {}
for (m, cfg), rows in cells.items():
    ii = np.array([idx[r[0]] for r in rows]); conf = np.array([r[1] for r in rows]); corr = np.array([r[2] for r in rows], float)
    ece_b[(m, cfg)] = ece_w(conf, corr, counts[:, ii])
    bins = np.minimum((conf * 10).astype(int), 9); n = len(conf); e = o = 0
    for b in range(10):
        s = bins == b
        if s.any():
            d = conf[s].mean() - corr[s].mean(); e += s.sum() / n * abs(d); o += s.sum() / n * max(d, 0)
    over[(m, cfg)] = o / e; acc[(m, cfg)] = corr.mean(); conf_m[(m, cfg)] = conf.mean()
def mean_rho(Ece):                 # Ece: dict cfg -> B x 5
    rhos = []
    for a, c in itertools.combinations(EFF, 2):
        ra = np.argsort(np.argsort(Ece[a], 1), 1).astype(float); rc = np.argsort(np.argsort(Ece[c], 1), 1).astype(float)
        ra -= ra.mean(1, keepdims=True); rc -= rc.mean(1, keepdims=True)
        rhos.append((ra * rc).sum(1) / np.sqrt((ra ** 2).sum(1) * (rc ** 2).sum(1)))
    return np.mean(rhos, 0)
Ece = {c: np.stack([ece_b[(m, c)] for m in MODELS], 1) for c in EFF}
mr = mean_rho(Ece)
top_hua = {c: float(np.mean(Ece[c].argmax(1) == MODELS.index('huatuogpt'))) for c in EFF}
res = dict(n_images=N, mean_pairwise_rho_boot_mean=float(mr.mean()), rho_ci=[float(np.percentile(mr, 2.5)), float(np.percentile(mr, 97.5))],
           p_huatuo_highest=top_hua, min_overconfident_share=float(min(over.values())), max_overconfident_share=float(max(over.values())),
           acc_range=[float(min(acc.values())), float(max(acc.values()))], conf_range=[float(min(conf_m.values())), float(max(conf_m.values()))],
           n_range=[min(len(v) for v in cells.values()), max(len(v) for v in cells.values())])
# pairwise: huatuogpt vs llava_med ECE difference under greedy
d = Ece['temp0.0_greedy'][:, MODELS.index('huatuogpt')] - Ece['temp0.0_greedy'][:, MODELS.index('llava_med')]
res['huatuo_minus_llavamed_greedy_ci'] = [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
json.dump(res, open('calib3_results.json', 'w'), indent=1); print(json.dumps(res, indent=1))
