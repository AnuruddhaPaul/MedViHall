"""Back-sweep 2025-09-01..2026-05-31 on the core claims (papers possibly missed in the June 2026 search)."""
import json, re
import lit_tool as L

S, E = "2025-09-01", "2026-05-31"
MED = '(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical)'
HAL = '(abs:hallucination OR abs:hallucinations OR abs:hallucinate)'
VLM = '(abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:MLLM OR abs:LVLM OR abs:LVLMs OR abs:VLMs OR abs:MLLMs)'
Q = {
 "bs-halluc-med-vlm": f'{HAL} AND {MED} AND {VLM}',
 "bs-halluc-title-med": f'ti:hallucination AND (ti:medical OR ti:clinical OR ti:radiology OR ti:CXR OR ti:chest OR ti:pathology OR ti:dermatology OR ti:ophthalmic)',
 "bs-severity": f'{HAL} AND {MED} AND (abs:severity OR abs:"clinical risk" OR abs:harm OR abs:"clinically weighted")',
 "bs-special": f'{MED} AND {VLM} AND (abs:"general-purpose" OR abs:generalist OR abs:"general-domain" OR abs:"general purpose") AND (abs:hallucination OR abs:sycophancy OR abs:safety OR abs:reliability OR abs:robustness)',
 "bs-stage": f'{HAL} AND {MED} AND (abs:causal OR abs:"root cause" OR abs:"step-wise" OR abs:"stage-wise" OR abs:perception OR abs:"error attribution")',
 "bs-mitig": f'{HAL} AND {MED} AND (abs:"contrastive decoding" OR abs:"retrieval-augmented" OR abs:RAG OR abs:mitigation)',
 "bs-calib": f'{MED} AND {VLM} AND (abs:calibration OR abs:overconfidence OR abs:"confidence")',
 "bs-syc": f'{MED} AND {VLM} AND (abs:sycophancy OR abs:sycophantic OR abs:"false premise" OR abs:misleading)',
 "bs-occl": f'{MED} AND {VLM} AND (abs:occlusion OR abs:shortcut OR abs:"context bias" OR abs:"language prior" OR abs:"without the image")',
 "bs-multimod": f'{HAL} AND {MED} AND (abs:dermatology OR abs:pathology OR abs:histopathology OR abs:ophthalmology OR abs:fundus OR abs:dermoscopy)',
}
pool = {}
for g, q in Q.items():
    tot = 0
    for pg in range(3):
        res = L.arxiv_search(q, S, 100, cats=None, end_date=E, start=pg * 100)
        tot += len(res)
        for p in res:
            pool.setdefault(p["id"], {**p, "hits": []})["hits"].append(g)
        if len(res) < 100: break
    print(f"[{g}] {tot}")
json.dump(pool, open("lit_cache/backsweep.json", "w", encoding="utf-8"), indent=1)
hal = re.compile(r"hallucinat|sycophan|confabul|calibrat|overconfiden|shortcut|occlusion|severity", re.I)
med = re.compile(r"medic|clinic|radiolog|chest|x-ray|patholog|dermat|ophthal|fundus|retina|CXR", re.I)
vl = re.compile(r"vision|visual|multimodal|VLM|MLLM|LVLM|image", re.I)
rows = sorted([(p["published"][:10], k, p["title"][:110]) for k, p in pool.items()
               if hal.search(p["title"] + p["abstract"]) and med.search(p["title"]) and vl.search(p["title"] + p["abstract"][:300])], reverse=True)
print(len(rows), "back-sweep title-screened")
for r in rows: print(*r)
