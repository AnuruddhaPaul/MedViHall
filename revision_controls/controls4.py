"""Re-analysis controls for the MedViHall revision (reads existing result files only).
Outputs revision_controls/controls_results.json.  Weights as in Table 3 of the paper."""
import json, collections, sys, os
import numpy as np
OUT=os.path.expanduser('~/mnt/MediViHall/medvihall_outputs')
W={0:0.0,1:1.0,2:1.0,3:0.7,4:0.5,5:0.4,6:0.1,7:0.6}
GEN=['qwen25vl','gemma3','internvl3','qwen35','qwen3vl','minicpm','idefics3','qwen2vl','llava16']
SPEC=['huatuogpt','chexagent','llava_med']
QWEN={'qwen25vl','qwen35','qwen3vl','qwen2vl'}
MODS=['radiology','dermatology','histopathology','ophthalmology']
om={}
for l in open(f'{OUT}/layer1_verdicts.jsonl'):
    r=json.loads(l); om[(r['model'],r['image_id'],r['query_type'])]=len(r.get('omissions') or [])
# record fields: numc (judged-claim weight sum), nc, m, fab, perr, chr, resp_smhr
rec=collections.defaultdict(list)  # (model,modality,image) -> list of tuples (q, numc, nc, m, fab, perr, chrflag)
for l in open(f'{OUT}/layer2_judge.jsonl'):
    r=json.loads(l)
    perr='_parse_error' in r
    cj=r.get('claim_judgments') or []
    m=om.get((r['model'],r['image_id'],r['query_type']),0)
    numc=0.0;fab=0
    for j in cj:
        cl=j.get('hallucination_class',0)
        if not j.get('is_hallucination',False): cl=0
        numc+=W.get(cl,0.0)
        if cl==1: fab+=1
    chrf=1 if (fab>0 or m>0) else 0
    rec[(r['model'],r['modality'],r['image_id'])].append((r['query_type'],numc,len(cj),m,fab,perr,chrf))
# stats vector per image: 
# 0 num_all 1 den_all 2 num_noQ4 3 den_noQ4 4 chr_cnt 5 resp_cnt 6 macro_sum 7 macro_n 8 fab 9 om 10 numc 11 nc
# 12..15: per-query num (Q1..Q4) ; 16..19 per-query den
K=20
imgs={md:sorted({k[2] for k in rec if k[1]==md}) for md in MODS}
idx={md:{im:i for i,im in enumerate(imgs[md])} for md in MODS}
A={}
for mo in GEN+SPEC:
    for md in MODS:
        A[(mo,md)]=np.zeros((len(imgs[md]),K))
for (mo,md,im),lst in rec.items():
    a=A[(mo,md)][idx[md][im]]
    for (q,numc,nc,m,fab,perr,chrf) in lst:
        a[5]+=1
        if perr: continue
        a[4]+=chrf
        num=numc+W[2]*m; den=nc+m
        a[0]+=num; a[1]+=den
        if q!='Q4': a[2]+=num; a[3]+=den
# ---- paired permutation test of SRI = 1 (swap the two model labels within each image) ----
NPERM=20000
rng=np.random.default_rng(42)
def holm(p):
    p=np.asarray(p); o=np.argsort(p); m=len(p); adj=np.empty(m); run=0
    for k,i in enumerate(o):
        run=max(run,(m-k)*p[i]); adj[i]=min(1,run)
    return adj
cells=[];raw=[]
for md in MODS:
    n=len(imgs[md])
    pts={g:A[(g,md)][:,0].sum()/A[(g,md)][:,1].sum() for g in GEN}
    ref=min(pts,key=pts.get)
    R=A[(ref,md)]
    S=rng.integers(0,2,size=(NPERM,n)).astype(np.float64)
    for sp in SPEC:
        Sp=A[(sp,md)]
        obs=np.log((Sp[:,0].sum()/Sp[:,1].sum())/(R[:,0].sum()/R[:,1].sum()))
        na=S@Sp[:,0]+(1-S)@R[:,0]; da=S@Sp[:,1]+(1-S)@R[:,1]
        nb=S@R[:,0]+(1-S)@Sp[:,0]; db=S@R[:,1]+(1-S)@Sp[:,1]
        perm=np.log((na/da)/(nb/db))
        p=(1+np.sum(np.abs(perm)>=abs(obs)-1e-12))/(NPERM+1)
        cells.append((sp,md,ref,float(np.exp(obs)),float(p))); raw.append(p)
adj=holm(raw)
out=[dict(model=c[0],modality=c[1],ref=c[2],sri=c[3],p_raw=c[4],p_holm=float(a)) for c,a in zip(cells,adj)]
json.dump(dict(n_perm=NPERM,seed=42,cells=out),open('controls4_results.json','w'),indent=1)
for o in out: print(o)
print('max holm',max(adj),'floor',12/(NPERM+1))
