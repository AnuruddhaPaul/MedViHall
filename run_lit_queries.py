"""Run all MedViHall literature-check query groups; save candidate pool to lit_cache/candidates.json."""
import datetime
import json
import os

import lit_tool as L

START = "2026-06-01"
MED = '(abs:medical OR abs:clinical OR abs:radiology OR abs:radiograph OR ti:medical)'
HAL = '(abs:hallucination OR abs:hallucinations OR abs:hallucinate OR abs:hallucinated)'
VLM = ('(abs:"vision-language" OR abs:"vision language" OR abs:multimodal OR abs:VLM OR abs:VLMs '
       'OR abs:MLLM OR abs:MLLMs OR abs:LVLM OR abs:LVLMs)')

ARXIV_Q = {
    "benchmark-general": [
        f'{HAL} AND {MED} AND {VLM} AND (abs:benchmark OR abs:evaluation)',
        f'ti:hallucination AND {MED}',
        'ti:hallucination AND (ti:vision OR ti:multimodal OR ti:VLM OR ti:LVLM OR ti:MLLM)',
        'abs:"medical" AND abs:"hallucination benchmark"',
        'abs:"medical multimodal" AND abs:hallucination',
        'abs:"medical VQA" AND abs:hallucination',
        'abs:"radiology report generation" AND abs:hallucination',
    ],
    "cxr": [
        f'{HAL} AND (abs:"chest X-ray" OR abs:"chest radiograph" OR abs:CXR)',
        f'{HAL} AND (abs:radiology OR abs:radiologist) AND {VLM}',
        'abs:"report generation" AND (abs:"chest X-ray" OR abs:CXR) AND (abs:factual OR abs:hallucination)',
    ],
    "derm": [
        f'{HAL} AND (abs:dermatology OR abs:dermoscopy OR abs:dermatoscopic OR abs:skin)',
        f'(abs:dermatology OR abs:dermoscopy OR abs:"skin lesion") AND {VLM} AND (abs:benchmark OR abs:reliability OR abs:safety)',
    ],
    "path": [
        f'{HAL} AND (abs:histopathology OR abs:pathology OR abs:"whole slide")',
        f'(abs:pathology OR abs:histopathology) AND {VLM} AND (abs:benchmark OR abs:reliability OR abs:safety OR abs:trustworthy)',
    ],
    "ophth": [
        f'{HAL} AND (abs:ophthalmology OR abs:fundus OR abs:retinal OR abs:OCT)',
        f'(abs:ophthalmology OR abs:fundus OR abs:retina) AND {VLM} AND (abs:benchmark OR abs:reliability OR abs:safety)',
    ],
    "severity-metric": [
        f'{HAL} AND (abs:severity OR abs:"clinical risk" OR abs:"clinically weighted" OR abs:"risk-weighted" OR abs:harm) AND {MED}',
        'abs:"severity-weighted" OR abs:"severity weighted"',
        f'abs:"clinical significance" AND {HAL} AND {VLM}',
        f'abs:"clinical harm" AND {HAL}',
    ],
    "specialization": [
        f'abs:medical AND {VLM} AND (abs:"general-purpose" OR abs:"general purpose" OR abs:"general-domain" OR abs:generalist) AND (abs:hallucination OR abs:safety OR abs:reliability)',
        'abs:"specialization paradox" OR abs:"specialisation paradox"',
        f'(abs:"domain-specific" OR abs:"medical-specific" OR abs:"medical-tuned" OR abs:"medical fine-tuned") AND {HAL} AND {VLM}',
        f'abs:"medical fine-tuning" AND (abs:degrade OR abs:worse OR abs:underperform) AND {VLM}',
    ],
    "named-models": [
        f'(abs:LLaVA-Med OR abs:CheXagent OR abs:HuatuoGPT-Vision OR abs:Med-Flamingo OR abs:RadFM OR abs:MedGemma OR abs:Lingshu) AND {HAL}',
        '(abs:LLaVA-Med OR abs:CheXagent OR abs:HuatuoGPT-Vision OR abs:MedGemma OR abs:Lingshu) AND (abs:benchmark OR abs:safety OR abs:reliability)',
    ],
    "calibration": [
        f'{MED} AND {VLM} AND (abs:calibration OR abs:overconfidence OR abs:overconfident OR abs:"expected calibration error" OR abs:ECE)',
        f'{MED} AND {VLM} AND (abs:"confidence elicitation" OR abs:"verbalized confidence" OR abs:uncertainty)',
        f'{HAL} AND {MED} AND (abs:"uncertainty estimation" OR abs:"uncertainty quantification" OR abs:abstention OR abs:abstain)',
        f'{MED} AND {VLM} AND (abs:decoding OR abs:temperature) AND (abs:robustness OR abs:calibration)',
    ],
    "mitigation": [
        f'{HAL} AND {MED} AND {VLM} AND (abs:mitigation OR abs:mitigate OR abs:reduce OR abs:alleviate)',
        f'{HAL} AND {MED} AND (abs:"retrieval-augmented" OR abs:RAG OR abs:"retrieval augmented")',
        f'{HAL} AND {MED} AND (abs:"contrastive decoding" OR abs:"visual contrastive decoding" OR abs:VCD OR abs:"decoding strategy")',
        f'{HAL} AND {MED} AND {VLM} AND (abs:"fine-tuning" OR abs:"preference optimization" OR abs:DPO OR abs:RLHF)',
        f'{HAL} AND {MED} AND (abs:"training-free" OR abs:"inference-time")',
    ],
    "stage-causal": [
        f'{HAL} AND {MED} AND (abs:"root cause" OR abs:causal OR abs:"error attribution" OR abs:"failure mode" OR abs:taxonomy)',
        f'{MED} AND {VLM} AND abs:perception AND abs:knowledge AND abs:reasoning AND (abs:error OR abs:failure OR abs:hallucination)',
        f'{MED} AND {VLM} AND (abs:"stage-wise" OR abs:"stage-level" OR abs:disentangle OR abs:"error localization")',
        f'{HAL} AND {MED} AND (abs:"visual grounding" OR abs:"visual perception") AND (abs:"knowledge gap" OR abs:"medical knowledge")',
    ],
    "context-occlusion": [
        f'{MED} AND {VLM} AND (abs:occlusion OR abs:"masked region" OR abs:"region masking")',
        f'{MED} AND {VLM} AND (abs:shortcut OR abs:"context bias" OR abs:"background bias" OR abs:"spurious correlation" OR abs:"language prior")',
        f'{MED} AND {VLM} AND (abs:blind OR abs:"without the image" OR abs:"image-free" OR abs:"text-only") AND (abs:VQA OR abs:benchmark)',
        f'{HAL} AND {MED} AND (abs:"visual reliance" OR abs:"image dependence" OR abs:"visual dependency")',
    ],
    "3d": [
        f'{HAL} AND (abs:CT OR abs:3D OR abs:volumetric OR abs:"PET/CT" OR abs:MRI) AND {MED} AND {VLM}',
        f'{MED} AND (abs:"3D medical" OR abs:volumetric) AND {VLM} AND abs:benchmark AND (abs:reliability OR abs:safety OR abs:hallucination)',
    ],
    "sycophancy": [
        f'{MED} AND {VLM} AND (abs:sycophancy OR abs:sycophantic)',
        f'{MED} AND (abs:"false premise" OR abs:counterfactual OR abs:"misleading prompt" OR abs:"adversarial prompt" OR abs:"leading question") AND {VLM}',
        f'{HAL} AND {MED} AND (abs:"false-premise" OR abs:"false premise" OR abs:misleading)',
    ],
    "judge": [
        f'{HAL} AND {MED} AND (abs:"LLM-as-a-judge" OR abs:"LLM-as-judge" OR abs:"LLM judge" OR abs:"automatic evaluation" OR abs:"claim-level" OR abs:"fact-checking")',
        f'{HAL} AND {MED} AND (abs:clinician OR abs:radiologist OR abs:"expert annotation" OR abs:"inter-annotator" OR abs:"human evaluation")',
        f'{HAL} AND {MED} AND abs:detection AND {VLM}',
    ],
    "safety-transfer": [
        f'{MED} AND {VLM} AND (abs:"cross-modal" OR abs:"cross-modality" OR abs:"across modalities") AND (abs:safety OR abs:hallucination OR abs:reliability)',
        f'{MED} AND {VLM} AND abs:benchmark AND (abs:"multi-modality" OR abs:"multiple modalities" OR abs:"four modalities") AND (abs:hallucination OR abs:trustworthiness OR abs:safety)',
        f'abs:trustworthiness AND {MED} AND {VLM} AND abs:benchmark',
    ],
    "known-followups": [
        'abs:HalluCXR', 'abs:ClinHallu', 'abs:Med-HallMark OR abs:"MediHall Score"', 'abs:MedHallTune',
        'abs:MedHEval OR abs:MedHallBench OR abs:MedVH', 'abs:CARES AND abs:medical AND abs:trustworthiness',
        'abs:GMAI-MMBench', 'abs:CREST AND abs:medical AND abs:hallucination',
        'ti:specialization AND abs:medical AND abs:sycophancy',
    ],
}

OA_Q = [
    "medical vision-language model hallucination benchmark",
    "hallucination chest X-ray vision-language model",
    "hallucination dermatology vision-language model",
    "histopathology vision-language model hallucination",
    "ophthalmology fundus vision-language model hallucination",
    "severity-weighted hallucination medical",
    "medical multimodal large language model hallucination mitigation",
    "calibration confidence medical vision-language models",
    "medical vision-language model sycophancy",
    "radiology report generation hallucination evaluation",
    "medical-specific versus general-purpose vision language models hallucination",
    "clinical safety evaluation multimodal large language models medical imaging",
]


def main():
    pool, log = {}, []
    for group, qs in ARXIV_Q.items():
        for q in qs:
            try:
                res = L.arxiv_search(q, START, 100)
            except Exception as ex:
                log.append({"src": "arxiv", "group": group, "q": q, "error": str(ex)})
                print("ERR", group, ex)
                continue
            log.append({"src": "arxiv", "group": group, "q": q, "n": len(res)})
            print(f"[{group}] {len(res):3d}  {q[:100]}")
            for p in res:
                e = pool.setdefault(p["id"], {**p, "src": "arxiv", "hits": []})
                e["hits"].append(group)
    for q in OA_Q:
        try:
            res = L.openalex_search(q, START, 25)
        except Exception as ex:
            log.append({"src": "openalex", "q": q, "error": str(ex)})
            print("ERR oa", ex)
            continue
        log.append({"src": "openalex", "q": q, "n": len(res)})
        print(f"[openalex] {len(res):3d}  {q}")
        for p in res:
            key = "oa:" + (p["doi"] or p["openalex_id"])
            e = pool.setdefault(key, {**p, "src": "openalex", "hits": []})
            e["hits"].append("openalex")
    os.makedirs("lit_cache", exist_ok=True)
    json.dump({"run_date": str(datetime.date.today()), "log": log, "pool": pool},
              open("lit_cache/candidates.json", "w", encoding="utf-8"), indent=1)
    print("pool size", len(pool), "arxiv:", sum(1 for k in pool if not k.startswith("oa:")))


if __name__ == "__main__":
    main()
