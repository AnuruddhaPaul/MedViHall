"""Round 2: broad title/abstract sweeps with pagination (no category restriction) to raise recall.
Adds to lit_cache/candidates.json (key = arXiv id) and records the queries in the log."""
import json

import lit_tool as L

START = "2026-06-01"
VL_TI = '(ti:VLM OR ti:VLMs OR ti:"vision-language" OR ti:"vision language" OR ti:MLLM OR ti:MLLMs OR ti:LVLM OR ti:LVLMs OR ti:multimodal OR ti:"large language model")'
BROAD = {
    "r2-medical-title-vlm": f'(ti:medical OR ti:clinical OR ti:radiology OR ti:radiologic) AND {VL_TI}',
    "r2-cxr-title-vlm": f'(ti:chest OR ti:radiograph OR ti:"X-ray" OR ti:CXR) AND {VL_TI}',
    "r2-derm-title": f'(ti:dermatology OR ti:dermoscopy OR ti:skin OR ti:dermatologic) AND {VL_TI}',
    "r2-path-title": f'(ti:pathology OR ti:histopathology OR ti:"whole-slide" OR ti:"whole slide") AND {VL_TI}',
    "r2-ophth-title": f'(ti:ophthalmology OR ti:fundus OR ti:retinal OR ti:ophthalmic) AND {VL_TI}',
    "r2-halluc-title-all": 'ti:hallucination OR ti:hallucinations OR ti:hallucinate',
    "r2-halluc-abs-medvqa": 'abs:hallucination AND (abs:"medical visual question answering" OR abs:"medical VQA" OR abs:"Med-VQA" OR abs:"medical image")',
    "r2-sycophancy-title": 'ti:sycophancy OR ti:sycophantic',
    "r2-calibration-title-med": '(ti:calibration OR ti:confidence OR ti:uncertainty OR ti:overconfident OR ti:overconfidence) AND (ti:medical OR ti:clinical OR ti:radiology OR ti:pathology)',
    "r2-shortcut-med": '(ti:shortcut OR ti:shortcuts OR ti:"blind" OR ti:"without an image" OR ti:"language prior" OR ti:context) AND (ti:medical OR ti:radiology OR ti:clinical OR ti:chest) AND abs:vision',
    "r2-benchmark-med-mllm": '(ti:benchmark OR ti:bench) AND (ti:medical OR ti:clinical) AND (ti:multimodal OR ti:vision OR ti:VLM OR ti:MLLM OR ti:LVLM)',
    "r2-causal-failure-med": '(ti:causal OR ti:failure OR ti:"error analysis" OR ti:diagnosing OR ti:tracing) AND (ti:medical OR ti:clinical) AND (ti:vision OR ti:multimodal OR ti:VLM OR ti:MLLM)',
}
PAGES = 4  # x100 results


def main():
    obj = json.load(open("lit_cache/candidates.json", encoding="utf-8"))
    pool, log = obj["pool"], obj["log"]
    new = 0
    for group, q in BROAD.items():
        total = 0
        for pg in range(PAGES):
            for cats in [None]:
                res = L.arxiv_search(q, START, 100, cats=cats, start=pg * 100)
            total += len(res)
            for p in res:
                if p["id"] not in pool:
                    new += 1
                e = pool.setdefault(p["id"], {**p, "src": "arxiv", "hits": []})
                e["hits"].append(group)
            if len(res) < 100:
                break
        log.append({"src": "arxiv", "group": group, "q": q, "n": total, "paged": True})
        print(f"[{group}] {total:4d}  {q[:90]}")
    obj["log"] = log
    json.dump(obj, open("lit_cache/candidates.json", "w", encoding="utf-8"), indent=1)
    print("new arXiv candidates:", new, "pool:", len(pool))


if __name__ == "__main__":
    main()
