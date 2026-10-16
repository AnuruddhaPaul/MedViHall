"""SRI under random reassignment of the class weights (permutation of the seven weight values; Dirichlet draws)."""
import json, collections, os
import numpy as np
OUT=os.path.expanduser('~/mnt/MediViHall/medvihall_outputs')
MODELS=['qwen25vl','gemma3','internvl3','qwen35','qwen3vl','minicpm','idefics3','qwen2vl','llava16','huatuogpt','chexagent','llava_med']
GEN=MODELS[:9]; SPEC=MODELS[9:]
MODS=['dermatology','histopathology','ophthalmology']
om={}
for l in open(f'{OUT}/layer1_verdicts.jsonl'):
    r=json.loads(l); om[(r['model'],r['image_id'],r['query_type'])]=len(r.get('omissions') or [])
C={ (m,md):np.zeros(8) for m in MODELS for md in MODS}   # idx0 den, idx1..7 class counts
for l in open(f'{OUT}/layer2_judge.jsonl'):
    r=json.loads(l)
    if r['modality'] not in MODS: continue
    if '_parse_error' in r: continue
    a=C[(r['model'],r['modality'])]
    m=om.get((r['model'],r['image_id'],r['query_type']),0)
    cj=r.get('claim_judgments') or []
    a[0]+=len(cj)+m; a[2]+=m
    for j in cj:
        if j.get('is_hallucination'):
            cl=j.get('hallucination_class',0)
            if 1<=cl<=7: a[cl]+=1
w0=np.array([1.0,1.0,0.7,0.5,0.4,0.1,0.6])
def evaluate(w):
    sm={k:(v[1:]@w)/v[0] for k,v in C.items()}
    ov={m:sum(C[(m,md)][1:]@w for md in MODS)/sum(C[(m,md)][0] for md in MODS) for m in MODELS}
    cells=[];
    for md in MODS:
        ref=min(GEN,key=lambda g:sm[(g,md)])
        for s in SPEC: cells.append(sm[(s,md)]/sm[(ref,md)])
    rank=np.argsort(np.argsort([ov[m] for m in MODELS]))
    top3=set(sorted(MODELS,key=lambda m:ov[m])[-3:])==set(SPEC)
    top2=set(sorted(MODELS,key=lambda m:ov[m])[-2:])=={'llava_med','chexagent'}
    return min(cells), all(c>1 for c in cells), rank, top3, cells, top2
base=evaluate(w0)
rng=np.random.default_rng(42)
def spear(a,b):
    a=a-a.mean(); b=b-b.mean(); return float((a@b)/np.sqrt((a@a)*(b@b)))
res={}
for name in ['permutation','dirichlet']:
    mins=[];alls=[];rhos=[];top3=[];top2=[]
    for _ in range(2000):
        if name=='permutation': w=rng.permutation(w0)
        else:
            w=rng.dirichlet(np.ones(7))
        mn,al,rk,t3,_,t2=evaluate(w)
        top2.append(t2)
        mins.append(mn);alls.append(al);rhos.append(spear(rk.astype(float),base[2].astype(float)));top3.append(t3)
    res[name]={'draws':2000,'share_all_cells_above_1':float(np.mean(alls)),'min_sri_min':float(np.min(mins)),'min_sri_median':float(np.median(mins)),'min_sri_p5':float(np.percentile(mins,5)),
      'rho_mean':float(np.mean(rhos)),'rho_min':float(np.min(rhos)),'rho_p5':float(np.percentile(rhos,5)),'share_spec_top3':float(np.mean(top3)),'share_top2':float(np.mean(top2))}
res['base_check']={'min_sri':base[0],'cells':base[4]}
json.dump(res,open('controls3_results.json','w'),indent=1)
print(json.dumps(res,indent=1))
