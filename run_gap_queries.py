"""Prompt-B gap queries (2024-01-01..today, no category restriction). Prints top hits per query; results cached."""
import json
import lit_tool as L

Q = {
 "benchmarks-trust": 'ti:CARES OR ti:"GMAI-MMBench" OR ti:MedHEval OR ti:MedHallBench OR ti:"MedVH" OR ti:"Med-HallMark" OR (ti:trustworthiness AND ti:medical AND ti:vision)',
 "med-halluc-benchmark-title": 'ti:hallucination AND (ti:medical OR ti:radiology OR ti:clinical) AND (ti:benchmark OR ti:evaluating OR ti:detecting OR ti:assessing)',
 "survey": '(ti:survey OR ti:review) AND ti:hallucination AND (ti:medical OR ti:clinical OR ti:healthcare OR ti:multimodal)',
 "judge-rad": '(abs:"LLM-as-a-judge" OR abs:"LLM judge" OR abs:GREEN OR abs:RaTEScore OR abs:"radiologist agreement" OR abs:"expert agreement") AND (ti:radiology OR ti:"report generation" OR ti:"clinical" OR ti:medical) AND (ti:evaluation OR ti:metric OR ti:judge)',
 "judge-validation-med": '(abs:"inter-annotator" OR abs:"Cohen" OR abs:"Fleiss" OR abs:"Krippendorff" OR abs:"kappa") AND abs:"hallucination" AND (abs:medical OR abs:radiology) AND (abs:LLM OR abs:VLM)',
 "derm-vlm": '(ti:dermatology OR ti:dermatologic OR ti:skin) AND (ti:"vision-language" OR ti:multimodal OR ti:VLM OR ti:LLM OR ti:GPT) AND (ti:benchmark OR ti:evaluation OR ti:evaluating)',
 "path-vlm": '(ti:pathology OR ti:histopathology) AND (ti:"vision-language" OR ti:multimodal OR ti:VLM) AND (ti:benchmark OR ti:evaluating OR ti:evaluation)',
 "ophth-vlm": '(ti:ophthalmology OR ti:ophthalmic OR ti:fundus OR ti:retinal) AND (ti:"vision-language" OR ti:multimodal OR ti:VLM OR ti:MLLM OR ti:LVLM) AND (ti:benchmark OR ti:evaluating OR ti:evaluation)',
 "false-premise": '(ti:"false premise" OR ti:"false-premise" OR ti:counterfactual OR ti:misleading) AND (ti:medical OR ti:radiology OR ti:clinical) AND (ti:vision OR ti:multimodal OR ti:VQA)',
 "med-vlm-safety-benchmark": '(ti:safety OR ti:trustworthy OR ti:reliability OR ti:robustness) AND (ti:medical OR ti:clinical) AND (ti:"vision-language" OR ti:multimodal OR ti:MLLM OR ti:LVLM OR ti:VLM) AND ti:benchmark',
 "mitigation-med-rag": '(ti:retrieval OR ti:RAG) AND (ti:medical OR ti:radiology) AND (ti:hallucination OR ti:factual) AND (ti:vision OR ti:multimodal OR ti:VLM)',
 "med-vlm-finetune-degrade": '(ti:"medical" AND (ti:"fine-tuning" OR ti:"domain adaptation" OR ti:"specialization" OR ti:"specialised" OR ti:"specialized") AND (ti:"vision-language" OR ti:VLM OR ti:multimodal))',
}
seen = {}
for g, q in Q.items():
    res = L.arxiv_search(q, "2024-01-01", 60, cats=None)
    print(f"\n=== {g}: {len(res)}")
    for p in res[:60]:
        seen[p["id"]] = p
        print(p["published"][:10], p["id"], p["title"][:105])
json.dump(seen, open("lit_cache/gap_pool.json", "w", encoding="utf-8"), indent=1)
