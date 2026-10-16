"""Cell-level SMHR intervals and class composition (pooled and macro-averaged over models)."""
import json, collections, os
import numpy as np
OUT=os.path.expanduser('~/mnt/MediViHall/medvihall_outputs')
W={0:0.0,1:1.0,2:1.0,3:0.7,4:0.5,5:0.4,6:0.1,7:0.6}
MODELS=['qwen25vl','gemma3','internvl3','qwen35','qwen3vl','minicpm','idefics3','qwen2vl','llava16','huatuogpt','chexagent','llava_med']
MODS=['dermatology','histopathology','ophthalmology']
om={}
for l in open(f'{OUT}/layer1_verdicts.jsonl'):
    r=json.loads(l); om[(r['model'],r['image_id'],r['query_type'])]=len(r.get('omissions') or [])
per=collections.defaultdict(lambda: collections.defaultdict(lambda: np.zeros(10)))  # (model,mod)-> image -> [num, den, c1..c7 counts at idx 2..8, om idx9?]
# idx: 0 num,1 den,2..8 = classes 1..7 counts (class 2 = omission)
for l in open(f'{OUT}/layer2_judge.jsonl'):
    r=json.loads(l)
    if '_parse_error' in r: continue
    a=per[(r['model'],r['modality'])][r['image_id']]
    m=om.get((r['model'],r['image_id'],r['query_type']),0)
    cj=r.get('claim_judgments') or []
    a[0]+=W[2]*m; a[1]+=len(cj)+m; a[2+1]+=m  # class 2 at idx 3
    for j in cj:
        if j.get('is_hallucination'):
            cl=j.get('hallucination_class',0)
            if cl in W and cl>0:
                a[0]+=W[cl]; a[2+cl-1]+=1
imgs={md:sorted({im for (mo,m2),d in per.items() if m2==md for im in d}) for md in MODS}
rng=np.random.default_rng(42)
B=2000
res={'cells':{},'class_pooled':{},'class_macro':{}}
boots={md:[rng.integers(0,len(imgs[md]),len(imgs[md])) for _ in range(B)] for md in MODS}
M={}
for mo in MODELS:
    for md in MODS:
        M[(mo,md)]=np.array([per[(mo,md)].get(im,np.zeros(10)) for im in imgs[md]])
for md in MODS:
    for mo in MODELS:
        X=M[(mo,md)]
        pt=X[:,0].sum()/X[:,1].sum()
        bs=[X[b,0].sum()/X[b,1].sum() for b in boots[md]]
        res['cells'][f'{mo}|{md}']=[pt,float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))]
for md in MODS:
    tot=sum(M[(mo,md)].sum(0) for mo in MODELS)
    cls=tot[2:9]; res['class_pooled'][md]=(cls/cls.sum()).tolist()
    shares=[]
    for mo in MODELS:
        c=M[(mo,md)].sum(0)[2:9]; shares.append(c/c.sum())
    res['class_macro'][md]=np.mean(shares,axis=0).tolist()
    res['class_pooled'][md+'_n']=float(cls.sum())
json.dump(res,open('controls2_results.json','w'),indent=1)
names=['fab','omi','mis','sev','ana','eva','rea']
for md in MODS:
    print(md,'pooled',{n:round(x*100) for n,x in zip(names,res['class_pooled'][md])},'macro',{n:round(x*100) for n,x in zip(names,res['class_macro'][md])})
print(sum(res['class_pooled'][m+'_n'] for m in MODS))
