"""Re-analysis controls for the MedViHall revision (reads existing result files only).
Outputs revision_controls/controls_results.json.  Weights as in Table 3 of the paper."""
import json, collections, sys, os
import numpy as np
OUT=os.path.expanduser('~/mnt/MediViHall/medvihall_outputs')
W={0:0.0,1:1.0,2:1.0,3:0.7,4:0.5,5:0.4,6:0.1,7:0.6}
GEN=['qwen25vl','gemma3','internvl3','qwen35','qwen3vl','minicpm','idefics3','qwen2vl','llava16']
SPEC=['huatuogpt','chexagent','llava_med']
QWEN={'qwen25vl','qwen35','qwen3vl','qwen2vl'}
MODS=['dermatology','histopathology','ophthalmology']
om={}
for l in open(f'{OUT}/layer1_verdicts.jsonl'):
    r=json.loads(l); om[(r['model'],r['image_id'],r['query_type'])]=len(r.get('omissions') or [])
# record fields: numc (judged-claim weight sum), nc, m, fab, perr, chr, resp_smhr
rec=collections.defaultdict(list)  # (model,modality,image) -> list of tuples (q, numc, nc, m, fab, perr, chrflag)
for l in open(f'{OUT}/layer2_judge.jsonl'):
    r=json.loads(l)
    if r['modality'] not in MODS: continue
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
        if den>0: a[6]+=num/den; a[7]+=1
        a[8]+=fab; a[9]+=m; a[10]+=numc; a[11]+=nc
        qi=int(q[1])-1
        a[12+qi]+=num; a[16+qi]+=den
VAR={
 'smhr':      lambda s: s[0]/s[1],
 'smhr_noQ4': lambda s: s[2]/s[3],
 'chr':       lambda s: s[4]/s[5],
 'macro':     lambda s: s[6]/s[7],
 'fab_rate':  lambda s: s[8]/s[1],
 'om_rate':   lambda s: s[9]/s[1],
 'claims_only': lambda s: s[10]/s[11],
}
def stat(mo,md,rows,fn):
    return fn(A[(mo,md)][rows].sum(0))
rng=np.random.default_rng(42)
B=2000
res={'meta':{'bootstrap':B,'seed':42,'resampling':'images within modality'}}
boots={md:[rng.integers(0,len(imgs[md]),len(imgs[md])) for _ in range(B)] for md in MODS}
allrows={md:np.arange(len(imgs[md])) for md in MODS}
def sri_table(vn,fn,refset):
    out={}
    for md in MODS:
        pts={g:stat(g,md,allrows[md],fn) for g in refset}
        ref=min(pts,key=pts.get)
        full={m:stat(m,md,allrows[md],fn) for m in GEN+SPEC}
        out[md]={'ref':ref,'ref_value':pts[ref],'values':full,'sri':{}}
        for s in SPEC:
            ps=full[s]/pts[ref]
            bs=np.array([stat(s,md,r,fn)/stat(ref,md,r,fn) for r in boots[md]])
            out[md]['sri'][s]=[ps,float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))]
    return out
for vn,fn in VAR.items():
    res[vn]={'all_general':sri_table(vn,fn,GEN)}
res['smhr']['non_qwen_ref']=sri_table('smhr',VAR['smhr'],[g for g in GEN if g not in QWEN])
res['chr']['non_qwen_ref']=sri_table('chr',VAR['chr'],[g for g in GEN if g not in QWEN])
# per-query SMHR pooled over modalities and by modality
pq={}
for mo in GEN+SPEC:
    tot=sum(A[(mo,md)].sum(0) for md in MODS)
    pq[mo]=[float(tot[12+i]/tot[16+i]) for i in range(4)]
res['per_query_pooled']=pq
res['n_den_by_query']={mo:[float(sum(A[(mo,md)].sum(0) for md in MODS)[16+i]) for i in range(4)] for mo in GEN+SPEC}
# overall check
res['check_overall_smhr']={mo:float(sum(A[(mo,md)].sum(0) for md in MODS)[0]/sum(A[(mo,md)].sum(0) for md in MODS)[1]) for mo in GEN+SPEC}
res['check_overall_chr']={mo:float(sum(A[(mo,md)].sum(0) for md in MODS)[4]/sum(A[(mo,md)].sum(0) for md in MODS)[5]) for mo in GEN+SPEC}
# rank correlation SMHR vs CHR etc
from math import isnan
json.dump(res,open(os.path.expanduser('~/mnt/MediViHall/revision_three_modalities/controls_results.json'),'w'),indent=1)
print('done')
