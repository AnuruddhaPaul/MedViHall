# Reconcile: questions and open items

Everything below was left as the default or left unchanged. Nothing here needed a guess about an experimental number.

## A. The four decisions from the brief (default applied)

| # | Decision | Default applied | What actually changed |
|---|---|---|---|
| 1 | RQ numbering after removing RQ11 | Renumber contiguously and fix cross-references | Nothing to renumber. No file in this tree mentions RQ11 or RQ12. The labels that exist are RQ5 (Pillar E), RQ8 (Pillar B), RQ9 (Pillar C), RQ10 (Pillar D) and all resolve. If Pillar G keeps an RQ, it becomes **RQ11** (was RQ12). RQ1-4, 6, 7 are defined only in the missing proposal, so contiguity cannot be checked here. |
| 2 | How to state the pillar count | State what was run | Written for the paper in `reconcile_report.md` Appendix A: the core benchmark plus four analysis pillars with results (B, C, D, E). I did not state a number for Pillar A or for the stage-localization and context-occlusion work (see B3). |
| 3 | Pillar G | Keep as "optional / future work" | No file mentions Pillar G or 3D volumetric evaluation, so nothing was changed. A ready sentence is in Appendix A. |
| 4 | The three dropped models | One sentence in the methods | A sentence is drafted in Appendix A with a **[reason]** placeholder, because the files do not confirm the reason (see B1). |

## B. Questions I cannot answer from the files

**B1. Which three models were "dropped as EcoMyth overlaps", and why?** The notebooks record this:
- v2 planned 15 models; v3 planned 18; the v4 registry has 14 (13 local plus `gemma4` on Ollama); the final results contain 12.
- `qwen3vl_think`: dropped for cost ("chain-of-thought tokens = 2-3x cost"), per the v4 header.
- `llava_il`: in the v3 registry, absent from v4; no reason recorded.
- `ayavision` and `gemma4`: registered in v4, no results; no reason recorded.
- "EcoMyth overlap" appears nowhere as a reason. In the results, `in_ecomyth` is True for 7 of the 12 final models (gemma3, idefics3, llava16, qwen25vl, qwen2vl, qwen35, qwen3vl).
Which models are the three, and what is the correct reason?

**B2. Were any final results generated with the earlier token limits (350/120/280/220)?** I cannot confirm that none were.
- The values 350/120/280/220 appear in no saved notebook. v2 used a flat 800, v3 a flat 500, and every saved v4 copy (from 2026-08-13) uses 700/220/480/280. The v4 comments say "was 350" for Q1 and "was 280" for Q3.
- Result records do not store `max_new_tokens`.
- Responses longer than the old limits (counted in words, which is a lower bound on tokens) exist for 38 of the 48 model x query-type cells, so the old caps were not in force for those responses. For the other 10 cells (all of llava_med, huatuogpt Q3/Q4, a few others) answers are too short to test.
- The earliest runs (llava_med 12-13 June, qwen3vl 13-20 June, qwen25vl 20-24 June) predate the oldest saved v4 backup (13 August); their longest answers (Q1 467-485 words, Q3 353-354) exceed what the old caps allow, which argues against them but does not prove the final limits.
- gemma3 changes behaviour between its first week (24-28 June) and its second (1-6 July): Q1 median 173 -> 262 words; share of Q3 answers above 280 words 4.5% -> 45%. I cannot attribute that to token limits.
Could you check the run logs or the notebook version used for each model? Until then the source-of-truth line "token limits Q1 700, Q2 220, Q3 480, Q4 280" is true of the notebook configuration, not proven for every result.

**B3. What is the status of the stage-localization and context-occlusion work?** `claims_at_risk.md` and `lit_update.md` list "causal stage localization" (contribution 7) and "context-occlusion robustness" (contribution 8), and the earlier audit brief mentions "Pillar A stage replacement". No result file, script or text for either exists in this tree. Are they run, planned, or dropped? Nothing was changed about them.

**B4. Does the novelty argument for contribution 6 survive with two families?** I only reworded descriptors: three-family (RAG, decoding, fine-tuning) became two-family (RAG, decoding) in `claims_at_risk.md` (2 places), `lit_update.md` (1) and `related_work_report.md` (4 lines). The verdicts that depend on the third family were not re-assessed. `related_work_report.md` rated the comparison "Open as a three-family, four-modality comparison"; I marked that cell "re-assess". With fine-tuning dropped, the gap statement ("a two-family comparison outside radiology is open") needs your judgement, especially against MedHEval and 2609.31733.

## C. Places where a text number disagrees with a result or data file (not changed)

| Where | Text says | Data show | Source |
|---|---|---|---|
| Brief and v4 notebook | 3,500 images | 3,500 image identifiers, but only **2,405 distinct image files**: radiology 115 of 1,200 (1,073 identifiers are one file), dermatology 899 of 900, histopathology 800, ophthalmology 591 of 600. Only 113 radiology images have unique content. | `manifest_3500.json` + image md5; see `claim_audit_report.md` X1 |
| `annotation_paper_paragraphs.tex` | "48 images" | 48 files, 37 distinct images (the 12 radiology files are one X-ray) | `annotation_key.csv`, image md5 |
| Brief | "Pillar B ... with a matched greedy baseline" | `RESULTS_AND_ANALYSIS.md` reports the baseline as the core-run response (temperature 0.1 sampling, not greedy) and says "Greedy decoding in every condition". The matched greedy baseline exists as the Pillar D greedy run (and the llava_med rerun) and was added in `claim_audit_report.md`, not in the results documents. | `pillar_b_baseline.jsonl`, `pillar_d_calibration_runs.jsonl` |
| `annotation_paper_paragraphs.tex` | provenance placeholder; `[0.877, 0.912]$ ($n=717$` | The placeholder is correct (the annotations are AI-persona outputs; `human_annotations/` is a rename of `ai_annotations/`). The stray `$` after `0.912]` is a LaTeX syntax slip that would break compilation. | file text |
| `subsample_manifest.py` docstring | "full manifest (9,346 images)" | Correct: it is the pool (2,000 + 3,000 + 2,400 + 1,946 ground-truth records), not the benchmark. Kept. | `*_gt_merged.json` |

## D. Left unchanged on purpose (please confirm)

1. `MedViHall_Phase3_Phase4_v2.ipynb` (15 models) and `_v3.ipynb` (18 models), `notebook_source_dump.py` (a dump of an older notebook), the `.bak` notebooks: superseded versions. Editing them would falsify history. Should I add a one-line "superseded" banner instead?
2. `claim_audit_report.md` and `claim_ledger.csv` quote the old "14 models" statement on purpose.
3. The v4 notebook code still registers `ayavision` and `gemma4`; only comments, headers and table labels were changed, no code.
4. `subsample_manifest.py` now prints the GPU-time estimate for 12 models instead of 15. This is a planning estimate, not an experimental number; it assumes 17 s per call, as before. Revert if you want the original estimate kept.

## E. Files named in the brief that are not on this machine

`MedViHall_Research_Proposal_v3.pdf`, the proposal build script, a root `README`, and any `.tex` paper draft (apart from `annotation_paper_paragraphs.tex`). I searched the project folder, Desktop, Documents, Downloads, OneDrive and D:. The reconciliation therefore covers the text that exists. If those files are elsewhere, give me the path and I will run the same procedure on them; the replacement sentences in Appendix A of `reconcile_report.md` are written to be pasted in.
