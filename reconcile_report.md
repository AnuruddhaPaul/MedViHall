# Reconcile report

## Summary

- **The files the brief targets are not on this machine.** `MedViHall_Research_Proposal_v3.pdf`, the proposal build script, a root `README` and any paper `.tex` (other than `annotation_paper_paragraphs.tex`) do not exist in the project folder, Desktop, Documents, Downloads, OneDrive or D:. No PDF was touched or rebuilt (page count before/after: not applicable).
- **None of the Pillar F / RQ11 / multilingual material exists in this tree.** Searched all scripts, notebooks (cell by cell), markdown, TeX, text and small JSON/CSV files: zero occurrences of "RQ11", "RQ12", "Pillar F", "Pillar G", "multilingual", "Beaton", "Hindi", "8,750", "seven pillars", "nine pillars", "eleven" (as a count), "13 RQs". The only remaining hits for those strings are digits inside numbers (false positives).
- **What did need reconciling, and was reconciled,** is in the files that do exist: the v4 notebook (14 models, "126K+ calls", proprietary-model note), a planning script (15-model estimate), the results documents (no limitations), and three literature-memo files (fine-tuning arm described as part of the comparison).
- **Work is on copies, in a git repo.** The project folder is not a git repository, so I made `reconcile_work/` (its own repo): `main` holds unmodified copies of the 7 files I touch, branch **`reconcile`** holds 4 commits, one per category. The originals are untouched. `reconcile.patch` applies cleanly to the originals (checked on a fresh copy, result identical to the branch). Nothing was pushed.

| Commit (branch `reconcile`) | Files | Lines +/- |
|---|---|---|
| `f8fb5a6` Model counts: 12 evaluated models | v4 notebook, `subsample_manifest.py` | 6 / 5 |
| `7755784` Calls, strata and token limits for the final run | v4 notebook | 5 / 4 |
| `b98c5ed` Limitations: English-only; proprietary models not evaluated | v4 notebook, `RESULTS_AND_ANALYSIS.md`, `results/07_...txt` | 11 / 3 |
| `7120229` Mitigation arms: fine-tuning arm was dropped | `claims_at_risk.md`, `lit_update.md`, `related_work_report.md` | 7 / 7 |
| **Total** | **7 files** | **28 / 18** (baseline `300d7a3`) |

To use the changes: from `MediViHall\`, `git -C reconcile_work diff main reconcile` shows them; `git apply reconcile.patch` (run in a copy of the folder with `core.autocrlf=false`) applies them, or copy the 7 files from `reconcile_work\`. `related_work_report.md` was created during this session by another process; re-check the patch (`git apply --check`) if it changes again.

## Source of truth, verified against the data

| Item | Brief | Verified | Evidence |
|---|---|---|---|
| Models evaluated | 12 | **Yes**, same 12 names | `medvihall_results_deduped.jsonl` |
| Specialists | chexagent, huatuogpt, llava_med | **Yes** | `is_medical` flag |
| Images | 3,500; S1-S4 300 each; DS1 400/DS2 200/DS3 300; HS1 300/HS2 200/HS3 300; OS1 250/OS2 200/OS3 150 | **Yes** as identifiers (see caveat) | `manifest_3500.json` |
| Calls per model | 11,750 (3,500 x 3 + 1,250 normal-stratum Q4) | **Yes** | Q4 present for 1,250 images per model |
| Records | 141,000 | **Yes** | 12 x 11,750 |
| Token limits | Q1 700, Q2 220, Q3 480, Q4 280 | **Yes in the notebook; not provable for every result** | v4 config; see Questions B2 |
| Pillar D | 5 models x 6 configs | **Yes**, 50,370 unique calls | `pillar_d_calibration_runs.jsonl` |
| Pillar B | 5 models x 500 images | **Yes**, 8,395 calls per condition (1,679 per model) | `pillar_b_*.jsonl` |
| Pillar B "matched greedy baseline" | present | **Partly**: the reported baseline is the core-run response (temperature 0.1); a greedy baseline exists as the Pillar D greedy run | Questions section C |
| Pillar F removed, G on hold, English-only and proprietary limitations | stated | No file contained F or G; limitation lines added | commits `b98c5ed` |

**Caveat on "3,500 images":** these are 3,500 identifiers; 1,087 radiology identifiers point to duplicate files, leaving **2,405 distinct image files** (details: `claim_audit_report.md`, X1). I wrote "3,500 images" in the notebook because that is the manifest, and flagged the issue in `reconcile_questions.md` section C.

## Step 1: inventory of hits (before any change)

Scanned 193 files (scripts, markdown, TeX, text, small JSON/CSV, and 6 notebooks read cell by cell; `.bak`, `.jsonl`, logs, images, models and the literature cache excluded). Hits by file, with what was done:

| File | Hits | What they are | Action |
|---|---|---|---|
| `MedViHall_Phase3_Phase4_v4.ipynb` | 34 + 26 | "14 models total", `ayavision`/`gemma4`/`qwen3vl_think` registry and code, "126K+ calls", proprietary-model note, old `350` comments | header, table labels, call counts, notes **changed**; registry code and `was 350` history comments **kept** |
| `MedViHall_Phase3_Phase4_v2.ipynb` | 32 + 33 | "15 models", `qwen3vl_think`, `ayavision`, `gemma4` | superseded planning notebook, **unchanged** (Questions D1) |
| `MedViHall_Phase3_Phase4_v3.ipynb` | 45 + 31 | "18 models", `ayavision`, `llava_il` | superseded, **unchanged** |
| `notebook_source_dump.py` | 28 + 23 | source dump of an older notebook | generated snapshot, **unchanged** |
| `subsample_manifest.py` | 2 + 1 | "15 models total" estimate; "9,346 images" | estimate **changed to 12**; 9,346 verified correct (pool size), **kept** |
| `claims_at_risk.md`, `lit_update.md`, `related_work_report.md` | 0 + 0 on the scan patterns | "three-family ... fine-tuning" mitigation comparison (found by reading, not by the scan) | **changed** (7 places) |
| `medvihall_outputs/progress.json` | 2 | model names `ayavision`, `gemma4` in run-progress state | record of the run, **unchanged** |
| `claim_audit_report.md`, `claim_ledger.csv` | 1 + 2 | quote the old "14 models" statement | quoted history, **unchanged** |
| `lit_update.md`, `triage_data.py`, `build_lit_outputs.py`, `lit_update.bib`, `related_work_report.md`, `annotation_report.md` (secondary pattern) | 40 | citations of other papers (GPT-4o, Gemini, OpenAI baselines), `350` as a number | not about this project, **unchanged** |
| `pillar_d_load_fns.py`, `test_llava_med.py`, `MedViHall_Dataset_Download.ipynb` | 5 | `openai/clip-vit-...` model id; "OS3 +350" shortfall comment | not stale, **unchanged** |
| CSV/JSON/log files (`annotation_results`, `paper_figures`, `pillar_c_...json`, `watchdog_log.txt`) | 12 | digits inside numbers ("9346", "8750" in floats and timestamps) | false positives |

## Step 3: what changed, file by file

**`MedViHall_Phase3_Phase4_v4.ipynb`** (cells 0, 7, 27; no code behaviour changed)
- Header: "13 Local HF + 1 Ollama = 14 models total" -> "13 Local HF + 1 Ollama registered (14 in this notebook); 12 evaluated in the final results | API models not evaluated".
- Model table: `ayavision` and `gemma4` rows marked "(registered, no results)".
- New blockquote "Final evaluated set: 12 models" (names, the three specialists, which registered models have no results, which were dropped earlier, v2/v3 plans of 15/18).
- New blockquote "Final run": 3,500 images with strata, 11,750 calls per model, 141,000 in total, token limits Q1 700, Q2 220, Q3 480, Q4 280 ("defined in this notebook").
- "126K+ calls" -> "141,000 calls" in the markdown note and two code comments.
- Proprietary-model note: "excluded due to resource constraints" -> "were not evaluated (no funding)" in the markdown note and two code comments.

**`subsample_manifest.py`**: GPU estimate now multiplies by 12 models and is labelled "12 models total".

**`medvihall-annotation-sample/RESULTS_AND_ANALYSIS.md` and `results/07_data_quality_and_known_issues.txt`**: new item "8. Scope limits": "Evaluation is English-only; cross-lingual extension is left to future work." and the proprietary-models line (CRLF line endings preserved).

**`claims_at_risk.md`** (2 lines), **`lit_update.md`** (1 line), **`related_work_report.md`** (4 lines): comparison described as RAG vs contrastive decoding, "the planned fine-tuning arm was dropped"; the mitigation verdict cell now says "re-assess".

Counts: 7 files, 28 lines added, 18 removed; 4 commits.

## Not changed, with reasons

- Any statement about Pillar F, RQ11, Pillar G, multilingual evaluation, or "N pillars": none exists. Ready sentences are in Appendix A.
- No experimental number was edited. Disagreements between text and data are in `reconcile_questions.md` section C, with both values and the file.
- Historical files (v2, v3, source dump, audit files): kept as records, listed above.
- Prior-art entries that mention fine-tuning (for example `lit_update.md` line 161, which says a cited pilot "compares only retrieval conditions - not RAG vs contrastive decoding vs fine-tuning", and the entries cited as fine-tuning datapoints for contribution 6): they describe other papers, so they stay.

## Step 4: verification

- **Re-scan** of the reconciled state (originals with the 7 copies substituted): the strings "15 models", "17 models", "18 models" (as a plan for this study), "126K+", "fine-tuning" (as a planned arm), "14 models total" no longer appear in any current document. Remaining hits are the 12 classes in the table above: historical notebooks and dump, run-state JSON, quoted audit history, citations of other work, registry code in v4, and digits in numbers. In the reconciled v4 notebook the 35 remaining hits are all `ayavision`/`gemma4`/`qwen3vl_think` registry code, comments and the new statements that name them.
- **Cross-references:** every RQ and Pillar label that exists resolves (RQ5 -> Pillar E, RQ8 -> B, RQ9 -> C, RQ10 -> D, in `RESULTS_AND_ANALYSIS.md`, `results/00_overview.txt`, the pillar scripts and the Pillars C/D/E notebook). No "Table n" or "Figure n" label of this project exists in any text file (one table reference in `related_work_report.md` points to another paper). RQ1-4, 6, 7 cannot be checked (definitions are in the missing proposal).
- **PDF/LaTeX build:** no build script and no LaTeX document exist; page count before/after is not applicable. For `annotation_paper_paragraphs.tex` I made no change (note the stray `$` in Questions section C).
- **Patch check:** `reconcile.patch` applies cleanly to unmodified copies of the 7 files and reproduces the branch byte for byte.

## Remaining questions

See `reconcile_questions.md`: which three models were dropped and why (B1), whether any result used the earlier token limits (B2), status of the stage-localization and occlusion work (B3), whether the mitigation novelty claim survives two families (B4), and the text/data disagreements (section C).

## Appendix A: ready-to-paste text for the proposal or paper

The brief says to give LaTeX for LaTeX files. These are standalone; line and page-count effect cannot be measured without the document. Each adds roughly the number of lines shown if it is a new paragraph; replacing an older sentence is net zero or negative.

**Models (replaces any "15/17/18 models" sentence; about 3 lines)**
```latex
We evaluate 12 vision-language models: nine general-purpose models (Gemma3-12B, Idefics3-8B,
InternVL3-8B, LLaVA-1.6-Mistral-7B, MiniCPM-V-2.6, Qwen2-VL-2B, Qwen2.5-VL-7B, Qwen3-VL-8B and
Qwen3.5-9B) and three medical specialists (CheXagent-8B, HuatuoGPT-Vision-7B and LLaVA-Med-v1.5-7B).
```

**Dropped models (about 2 lines; fill in the reason, see Questions B1)**
```latex
Earlier plans listed up to 18 models; \texttt{qwen3vl\_think} was dropped for cost, and
\texttt{ayavision}, \texttt{gemma4} and \texttt{llava\_il} were not part of the final evaluation [reason to be confirmed].
```

**Data and calls (about 4 lines)**
```latex
The benchmark contains 3,500 images in four modalities (radiology 1,200; dermatology 900;
histopathology 800; ophthalmology 600), sampled from 9,346 candidates and stratified by image type
(S1--S4: 300 each; DS1/DS2/DS3: 400/200/300; HS1/HS2/HS3: 300/200/300; OS1/OS2/OS3: 250/200/150).
Each model answers three questions per image and a fourth on the 1,250 normal-stratum images,
giving 11,750 responses per model and 141,000 in total. Maximum new tokens were 700, 220, 480 and 280
for Q1--Q4.
```
(Open item: 1,087 radiology identifiers point to duplicate files, so only about 2,405 files are distinct; see Questions section C before this paragraph is used.)

**Pillars (about 4 lines; replaces any "seven/nine pillars" or "eleven RQs" text)**
```latex
Beyond the core benchmark we report four analysis pillars: mitigation (RAG and contrastive decoding,
five models, 500 images), metric concordance, calibration under decoding changes (five models,
six decoding configurations, 50{,}370 calls) and cross-modal transfer. Multilingual evaluation was
removed from the study; 3D volumetric evaluation is left to future work.
```

**Limitations (2 lines each)**
```latex
Evaluation is English-only; cross-lingual extension is left to future work.
Proprietary API models were not evaluated (no funding); the pipeline is model-agnostic.
```

**RQ numbering:** keep RQ5, RQ8, RQ9, RQ10 as they are; if Pillar G keeps a research question it becomes RQ11 (was RQ12). Remove RQ11 (multilingual) from the list, the contributions list and the cost table.
