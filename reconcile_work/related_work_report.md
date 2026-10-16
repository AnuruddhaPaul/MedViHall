# MedViHall: related-work landscape and novelty check

Prepared 2026-10-14 for the paper's author. Evidence base: the verified Prompt A cache (`lit_update.md`, `claims_at_risk.md`) plus a second round for this report (arXiv API title searches back to 2024-01-01, DOI registrars, the medRxiv API, publisher pages, four web searches). Where I read a paper's HTML full text I say "full text"; otherwise "abstract". Anything I could not verify from a primary source is marked **unverified** and is not used as evidence.

Your project notes say the `human_annotations/` files are renamed Claude-generated persona outputs, not clinician labels. This report treats that as a fact about the paper's validation section (Section 5), not as a footnote.

---

## 0. Corrections to my earlier Prompt A verdicts

Reading MedHEval (2503.02157) and HalluCXR (2605.20469) in full changed three of my earlier statements:

1. **Contribution 6 (mitigation comparison).** I said "no overlapping paper found." That was too strong. MedHEval, which is on your known list, evaluates **7 mitigation methods on 11 Med-LVLMs**. All seven are inference-time decoding or attention methods (VCD, OPERA, DoLa, AVISC, M3ID, DAMRO, PAI); there is no RAG and no fine-tuning arm, and it covers X-ray, CT, MRI and chest X-ray only. So the *head-to-head across RAG and contrastive decoding on non-radiology modalities* (the planned fine-tuning arm was dropped) is still open, but "comparing mitigation strategies in medical VLMs" is not new.
2. **Contribution 7 (stage localization).** MedHEval also splits hallucinations by cause (visual misinterpretation, knowledge deficiency, context misalignment). It does this by dataset construction, not by interventions, so ClinHallu remains the closest, but there are now three prior works with stage/cause decompositions.
3. **Contribution 1 (normalization).** MediHall Score (2406.10185) already averages severity-level scores over *all* sentences including correct ones, so "normalized by total units rather than by errors" has a direct precedent (details in Section 2).

---

## 1. Executive summary (10 lines)

1. **Crowded:** medical VLM hallucination benchmarks (a dozen or more since 2024), radiology-only detectors, calibration of medical VLMs (8+ papers in 2026), and single-method mitigation (contrastive decoding alone has 5+ papers).
2. **Crowded and hostile to your headline:** "medical-specialist models are worse than general ones" has been reported since MedVH (2024) and is now contested by paired base-vs-tuned studies that find *no consistent* effect.
3. **Open:** a shared claim-level, severity-graded protocol applied to dermatology, histopathology and ophthalmology for both specialist and general VLMs; a two-family mitigation comparison (RAG, decoding; the planned fine-tuning arm was dropped) outside radiology; rank-transfer analysis across modalities; calibration stability across decoding settings.
4. **Weak as worded:** "first multi-modality hallucination benchmark" (CARES already spans derm and fundus; a medRxiv study already grades hallucinations in histopathology), and "causal stage localization" (ClinHallu).
5. **Your taxonomy is not new:** five of your seven classes (fabrication, omission, severity distortion, anatomical/spatial confusion, reasoning error) map to HalluCXR's categories; only misclassification and evasion are distinctive.
6. **Most threatening paper 1: MedHEval** (2503.02157): benchmark + cause taxonomy + mitigation evaluation, 11 models.
7. **Most threatening paper 2: ClinHallu** (2606.14697): stage-wise decomposition with replacement interventions.
8. **Most threatening paper 3: MediHall Score** (2406.10185), with **CREST** (medRxiv 2025) as its radiology-only sibling: both already weight hallucination/error by clinical severity, one normalizing over all sentences.
9. **Biggest reviewer risk is not novelty but validation:** the annotation set is AI-generated, severity weights are not clinician-elicited, and the field's own LLM-judge validation is weak but reviewers now know it (Section 5).
10. **Second biggest:** "specialization" is confounded with model age and size and with CheXagent being a chest-X-ray-only model tested on three non-radiology modalities.

---

## 2. Themes

### a. Medical VLM hallucination benchmarks and taxonomies

| Work | Date | What it is |
|---|---|---|
| Hallucination Benchmark in Medical VQA (arXiv:2401.05827, ICLR 2024 Tiny Papers) | 2024-01-11 | Early Med-VQA hallucination benchmark with prompting-strategy analysis (abstract). |
| Med-HallMark / MediHall Score (2406.10185) | 2024-06-14 | 5 hallucination levels; question types incl. conventional, confidence-weakening, counterfactual; 3 doctors annotated; radiology sources (SLAKE, VQA-RAD, MIMIC, OpenI) (full text). |
| CARES (2406.06007, NeurIPS 2024 D&B) | 2024-06-10 | ~41K QA, "16 medical image modalities", five trust dimensions (trustfulness, fairness, safety, privacy, robustness); includes dermoscopy (HAM10000) and fundus; models: LLaVA-Med, Med-Flamingo, MedVInT, RadFM vs Qwen-VL-Chat, LLaVA-v1.6 (full text, first 100k chars). |
| MedVH (2407.02730; journal version Advanced Intelligent Systems, doi 10.1002/aisy.202500255, 2025-07-21) | 2024-07-03 | Five hallucination tasks; reports medical LVLMs often *more* hallucination-prone than general ones (abstract; the Wiley record confirms the venue). |
| MedHEval (2503.02157) | 2025-03-04 | Hallucination causes: visual misinterpretation, knowledge deficiency, context misalignment; 11 models (4 general, 7 medical); 7 mitigation methods; radiology only; 0-5 judge score validated on 2 human annotators, Pearson 0.834 (full text, first 100k chars). |
| HEAL-MedVQA (2505.00744, IJCAI 2025) | 2025-04-30 | 67K VQA pairs with doctor-annotated segmentation masks; protocols for visual and textual shortcut learning (abstract). |
| MedHallTune (2502.20780, now v2 2026-07-30) | 2025-02-28 | Instruction-tuning hallucination benchmark (known). |
| HalluCXR (2605.20469) | 2026-05-19 | CXR; 8-category taxonomy with severity 1-3; only one domain-specific model (BiomedCLIP, non-generative) among six (full text). |
| ClinHallu (2606.14697) | 2026-06-12 | Stage-wise (full text; see f). |
| Med-StepBench (2605.10002; IJCAI-ECAI 2026) | 2026-05-11 | Step-wise PET/CT hallucination benchmark (full text). |
| MedBench v5 (2606.24155) | 2026-06-23 | Hallucination propagation in clinical multimodal dialogue (full text, first 100k chars). |
| GI endoscopy hallucination-detection benchmark (2606.24115) | 2026-06-23 | 9 detectors, 5 VLMs (full text). |
| CREST (medRxiv 10.1101/2025.07.13.25331222) | 2025-07-14 | 12 radiology-specific error types, each with physician-assigned risk (low/medium/high); 3 VLMs (DeepSeek-VL2, CXR-LLaVA, CheXagent) on 685 expert-annotated MIMIC-CXR cases; CREST risk-weighted score (medRxiv API abstract). |
| EchoBench (2509.20146) | 2025-09-24 | Sycophancy, 20 modalities (incl. DERM, FUNDUS, HISTO, OCT), 24 LVLMs (full text, first 100k chars). |

Surveys: *A Survey of Multimodal Hallucination Evaluation and Detection* (2507.19024, 2025-07-25; general MLLMs, abstract) and 2410.15359 / 2404.18930 (general multimodal; abstracts). I did not find a verified survey specific to medical VLM hallucination; 2606.13211 is a narrative review (Section c).

**Taxonomy overlap (blunt).** HalluCXR's categories are fabrication, omission, spatial error, severity distortion, reasoning error, template overfitting, self-contradiction, detail fabrication. Your seven classes (fabrication, omission, misclassification, severity distortion, anatomical confusion, evasion, clinical reasoning error) share five concepts with it. CREST has 12 error types, MedHEval has three causes, Med-HallMark has five severity-ordered levels. A reviewer who knows HalluCXR will see the taxonomy as an adaptation, not a contribution.

**Gap relative to MedViHall.** All hallucination benchmarks above are radiology-centred or single-domain; CARES touches derm/fundus but is a trust suite with accuracy and overconfidence metrics, not a claim-level hallucination protocol. The open space is a shared claim-level protocol across four modalities with specialist vs general models.

### b. Hallucination metrics, especially severity-weighted ones

- **MediHall Score** (2406.10185, full text): level scores Catastrophic 0.0, Critical 0.2, Attribute 0.4, Prompt-induced 0.6, Minor 0.8, Correct 1.0; for generated reports the score is the mean of sentence scores, and the overall score the mean over items. This is already severity-weighted and normalized over *all* sentences (correct ones included). SMHR's "normalized by total claims" is conceptually the claim-level version of this.
- **CREST** (medRxiv, abstract): risk-weighted error score over 12 error types with physician-assigned risk levels; a normalized variant rescales to 0-1 and a companion "High-Risk Error Rate" is the share of errors that are high-risk (from a web-search summary of the paper; the exact formula is in the full text, which I did not read). Normalizing by errors is exactly the contrast you draw, so CREST is the paper to compare against in an ablation.
- **HalluCXR** (full text): three severity levels with no numeric weights; headline rates are per response ("at least one hallucination"), not per claim; per-claim normalization is absent.
- **CTest-Metric** (2601.11488, abstract): severity-graded synthetic error injection to test metric validity for CT reports. Useful as a precedent for validating a severity-weighted metric.
- **Risk-sensitive hallucination for text** (2602.07319, abstract): scores risk-bearing language (treatment directives, contraindications, urgency cues, high-risk drugs) and combines it with relevance; text-only LLMs, no clinical correctness assessment.
- **Clinical Safety Index** (2603.22623, full text): geometric mean of grounding, autonomy and calibration; not severity-weighted.
- **Report metrics** with clinical-significance handling: GREEN (2405.03595, EMNLP Findings 2024), RaTEScore (2406.16845, EMNLP 2024), RadEval (2509.18030, EMNLP 2025 demo), all abstract-level reads.

**Gap relative to MedViHall.** The unique property would be a *frequency-sensitive* severity-weighted rate over atomic claims and across non-radiology modalities. What is not unique: severity weighting itself, and normalization over all units. You need an empirical case where SMHR re-ranks models relative to (i) an unweighted claim rate, (ii) MediHall's sentence-level mean and (iii) an error-normalized CREST-style score. Without it, the metric looks like a re-parameterization.

### c. Evidence on specialized medical VLMs vs general ones

For "specialists are worse/less safe":
- MedVH (2407.02730): medical LVLMs "often more [susceptible] than the general models" (abstract).
- EchoBench (2509.20146): medical-specific models average ~83.0% sycophancy vs ~74.7% for 12 general open models; LLaVA-Med V1.5 98.75% vs 55.39% for its own base LLaVA-V1.5-7B (full text).
- 2606.13211 (review, 2026-06-11): claims general-purpose models outperform medical-specialised ones on hallucination benchmarks, with re-aggregated text-benchmark numbers and internal inconsistencies (full text). I would not cite its numbers.
- 2607.21065 (PathBind): Patho-R1-7B has a 5.8-point lower multimodal gain than Qwen2.5-VL-7B; the pattern is mixed across the other pathology models (full text, first 100k chars).

For "no consistent difference, or specialists are better":
- **2604.09841** (*Is There Knowledge Left to Extract?*, 2026-04-10, full text): four paired comparisons (LLaVA vs LLaVA-Med, Gemma vs MedGemma) on **four modalities** (brain-tumour MRI, pneumonia CXR, melanoma dermoscopy, IDC histopathology): "no consistent advantage"; LLaVA-Med worse on brain MRI but better on the other three; MedGemma better on three of four. Measures accuracy/refusal, not hallucination.
- 2603.22623 (full text): medical fine-tuning "does not consistently improve safety"; the most pressure-resistant general model hallucinates more than all three medical ones.
- 2608.02790 (full text): MedGemma-4B has the *lowest* open-ended hallucination rate (0.061) in its panel on brain MRI, but the worst abstention drop vs its base.
- CARES (full text, first 100k chars): LLaVA-Med best on factuality overall; general models better on uncertainty estimation.
- MVC-Bench (2608.27004): medical pretraining generally lowers ECE for CLIP-type classifiers (full text, first 100k chars).
- npj Digital Medicine (doi 10.1038/s41746-026-03191-3; arXiv 2512.22275): "no consistent advantage" of medical-specific models on an orthopaedics benchmark (abstract).

**Gap relative to MedViHall.** The effect direction is already in print (MedVH, EchoBench) and already contradicted (2604.09841, 2603.22623, 2608.02790). Your contribution can only be the *measured, severity-weighted, four-modality* evidence, stated as conditional on metric, model family and modality. See Section 4 for the confounds a reviewer will raise.

### d. Calibration and overconfidence

- Byun et al. (2604.02543; v2 2026-09-30, COLM 2026): general VLMs only, three medical VQA sets, overconfidence persists with scale and prompting, Platt scaling beats prompt-based confidence, hallucination-aware calibration helps (full text, first 100k chars).
- CARES defines an "overconfidence ratio" for Med-LVLMs (full text, first 100k chars).
- MVC-Bench (2608.27004): classification, three modalities, prompt-template and seed stability.
- 2606.16583 (EMNLP 2026 Findings): 8 uncertainty methods on 12 VLMs over 8 modalities with fixed T=0.6 sampling; the two MedGemma models are the worst calibrated; uncertainty barely moves when the right option is removed.
- 2606.15910: nine estimators, greedy decoding; 2608.02790: greedy decoding; AIES 2026 extended abstract on demographic calibration for derm and CXR (doi 10.1609/aies.v9i4.43348, Crossref abstract).
- RadFlag (2411.00299, abstract): samples reports at varying temperatures and flags claims not consistently supported, i.e. it *uses* sampling temperature as a hallucination signal. This is the closest conceptual neighbour to "calibration across decoding settings" and should be cited.

**Gap relative to MedViHall.** Calibration of medical VLMs is the most crowded sub-area; a decoding-setting sweep is not done in any paper I read. Position the contribution as "stability of calibration rankings under decoding changes" and cite RadFlag's temperature-sampling idea.

### e. Mitigation

- **Decoding/attention (all radiology):** MedHEval's seven methods; CCD (2509.23379, ACL 2026), Med-VCD (2512.01922), ARCD (2512.17189), CAST (2608.17427, MICCAI 2026); SAE steering (2605.24977); semantic-entropy filtering (arXiv 2510.09256, listed in search, abstract not read; the European Radiology version is **unverified**).
- **Retrieval:** RULE (2407.05131, EMNLP 2024): calibrated retrieval-context selection and a countermeasure for over-reliance on retrieved context (abstract); Visual RAG (2502.15040, AAAI-25 GenAI4Health workshop): improves entity probing, RadGraph-F1 (abstract); *When Retrieval Hurts* (2609.31733): retrieval-induced hallucination up to 0.98 under mismatched retrieval, 100-study pilot (full text).
- **Training:** MedHallTune, ClinHallu trace-supervised fine-tuning, CORAL (2607.03647), Pair-DPO (2609.32185).
- **Prompting/ensemble:** EchoBench prompt-level interventions; HalluCXR six-model ensemble cutting fabrication by up to 84.8% at the cost of more omission (abstract).
- Mixed outcomes are the norm: MedHEval finds "no method works reliably across all three types" and, in its context task, all methods hurt LLaVA-Med.

**Gap relative to MedViHall.** A *two-family* comparison (retrieval, decoding; the planned fine-tuning arm was dropped) under one metric, outside radiology, is open. Your results will be read against MedHEval (decoding-only) and 2609.31733 (RAG can hurt); say explicitly which of their findings you confirm.

### f. Causal or stage-wise analysis

- **ClinHallu** (full text): Visual Recognition / Knowledge Recall / Reasoning Integration; stage-replacement interventions (Rep-V, Rep-K, Rep-VK); four VQA sets; no severity, no RAG/decoding.
- **MedHEval**: three causes by dataset design; no interventions.
- **Med-StepBench** (full text): four diagnostic steps, per-step P/R/F1; "no formal causal attribution."
- **CRAFT** (2609.38810, NeurIPS 2026 Spotlight): head-level causal localization of context-override and over-commitment failures.
- MedBench v5: hallucination propagation across turns.
- 2604.27720 (*Why Does Grounding Hurt Medical VQA?*, v2 2026-07-28, abstract): separates VQA reasoning from visual grounding for frontier and medical VLMs; finds localization poor for all.

**Gap relative to MedViHall.** Causal stage interventions linked to severity weights and to mitigation choice, across four modalities, is the remaining space. The claim "first causal stage localization" is not available.

### g. Context shortcuts, background reliance, occlusion

- SHOVIR (2606.30201; full text): region and context occlusion on CXR report generation, no hallucination metric.
- MC-CXR (2608.24118; full text, first 100k chars): misleading text/prior/overlay context; domain specialization "does not insulate".
- HEAL-MedVQA: visual and textual shortcut protocols (abstract).
- *On the Risk of Misleading Reports* (2508.00171, MICCAI 2025 workshop, abstract): Selective Modality Shifting swaps images or text across samples on MIMIC-CXR and FairVLMed (ophthalmology SLO); six VLMs (four generalist, two medical-tuned).
- Image-removal controls: 2607.03647, 2603.03437, 2607.21065, 2609.32185, 2608.04885, Hearsay (2607.26886), the Gemini histopathology blank-image study (medRxiv 10.64898/2026.07.04.26357257).

**Gap relative to MedViHall.** Occlusion tied to hallucination rate and severity, across four modalities, with a context/target distinction. Cite SHOVIR for the CXR precedent.

### h. LLM-as-judge for clinical text and clinician agreement

Covered in Section 5. Headline: judge validation in this literature is thin (two co-author annotators, no kappa, no CIs is common), and recent work shows LLM judges perform poorly on exactly the error types in your taxonomy (omission, completeness).

### i. Sycophancy and false-premise robustness

- EchoBench (above); 2509.21979 (known, v7, last updated 2026-05-28; sycophancy in medical VLMs); 2603.22623 (grounding-sycophancy trade-off); CoT-Mediate (2607.27304); *Talked Out of the Truth* (2608.28623); contextual sycophancy (2609.00067); CRAFT's arbitration failures.
- **Precedent for your counterfactual query type:** Med-HallMark's question types already include *confidence-weakening* and *counterfactual* questions (full text), and MedHEval has a context-misalignment task built from clinical notes (full text). The query type is not new; the severity-graded scoring of responses to it is the differentiator.

**Gap relative to MedViHall.** Sycophancy work measures answer flips; yours measures hallucination severity under false premises. State that distinction.

### j. Non-radiology medical VLM evaluation

- **Dermatology:** DermBench/DermEval (2511.09195, v2 2026-01-12): 4,000 images with expert-certified narratives, nine MLLMs (incl. HuatuoGPT-Vision, LLaVA-Med-7B), six scored dimensions, *no* hallucination dimension; judge validated against two dermatologist co-authors with MAE only, no kappa, no CIs (full text). Real-world dermatology evaluation of LLaVA-Med, SkinGPT4, MedGemma, InternVL, GPT-4.1 (2605.04098, abstract). Benchmarking against dermatologists (2609.24190, abstract). Hearsay (2607.26886).
- **Histopathology:** PathMMU (2401.16355), HistoVL (2503.12990), PathBind (2607.21065), CleanSlide (2609.32185), the medRxiv hallucination study of four general LLMs with 21 pathologists (10.64898/2026.09.18.26363369; API abstract only), the Gemini blank-image study.
- **Ophthalmology:** LMOD (2410.01620, NAACL 2025) and LMOD+ (2509.25620, ACM TCH), EyeVQA (2609.32352), FunBench (arXiv 2503.00901, listed by the arXiv search; abstract not read) and the fundus cognitive-audit paper (doi 10.3390/app16126064), OCT-Bench (2607.16609, abstract).
- Cross-modality of these is mostly *capability* benchmarking; hallucination is rarely scored as a first-class outcome outside radiology.

**Gap relative to MedViHall.** The distinctive element is a *common hallucination protocol* over these domains, not the existence of benchmarks in them.

---

## 3. Novelty-check table

| Claim | Status | Closest paper(s) | Suggested wording |
|---|---|---|---|
| First multi-modality hallucination benchmark covering dermatology, histopathology and ophthalmology | **Partly covered; do not say "first"** | CARES (2406.06007; derm + fundus trust metrics, 2024); medRxiv histopathology hallucination study (2026-09-24); EchoBench (20 modalities, sycophancy); DermBench/DermEval (derm narratives, no hallucination dimension) | "To our knowledge, the first benchmark applying one claim-level, severity-graded hallucination protocol to dermatology, histopathology and ophthalmology (plus chest X-ray) for both medical-specialist and general VLMs." Verify per modality before submission. |
| Severity-weighted hallucination rate normalized by total claims (not errors) | **Partly covered** | MediHall Score (2406.10185: severity-level scores averaged over all sentences, correct included); CREST (risk-weighted error score; high-risk error rate normalized by errors) | "SMHR extends sentence-level severity scoring (MediHall) to atomic claims with explicit clinical weights and frequency sensitivity, and normalizes by all claims rather than by errors (cf. CREST)", backed by a re-ranking ablation. |
| Quantified specialization paradox across several modalities | **Partly covered and contested** | MedVH (2407.02730); EchoBench; 2604.09841 (4 modalities, no consistent advantage); 2603.22623; 2608.02790 | "Across four modalities, the three specialist models show higher severity-weighted hallucination than the best general models; the paired-base comparison (X) shows how much is due to tuning." Avoid "paradox" as a discovery. |
| Cross-modality transfer of safety rankings | **Open** (no paper found with these queries) | Adjacent: EchoBench and 2606.16583 per-modality breakdowns; 2606.15910 natural-to-medical probe transfer | "Rank agreement of model safety across modalities (Kendall tau with bootstrap CIs, n = 12 models)", plus a statement about power. |
| Causal stage localization across four modalities | **Partly covered** | ClinHallu (stage-replacement, 4 VQA sets); MedHEval (causes, radiology); Med-StepBench (4 steps, PET/CT) | "Extending stage-replacement analysis (Yang et al. 2026) to four modalities and linking stage failures to severity and to mitigation effectiveness." |
| Comparison of two mitigation strategies (RAG, contrastive decoding) across four modalities | **Open as a two-family, four-modality comparison (re-assess: the fine-tuning arm was dropped); not open as "mitigation comparison"** | MedHEval (7 decoding methods, radiology, 11 models); RULE; 2609.31733 | "We compare retrieval and contrastive decoding under one severity-weighted metric on four modalities, complementing MedHEval's decoding-only radiology study." |

---

## 4. Where the field disagrees: the strongest reviewer arguments against you

1. **"Specialization" is confounded.** Your three specialists (LLaVA-Med, CheXagent, HuatuoGPT-Vision) are older, mostly LLaVA-1.5-era or domain-narrow models, while the nine general models are probably newer and larger (check this). Paired designs (2604.09841; EchoBench's LLaVA-Med vs LLaVA-1.5) isolate tuning; yours does not unless you add base-model pairs. n = 3 specialists cannot support "in every modality."
2. **CheXagent is a chest-X-ray model.** Its performance on dermatology, histology and fundus images is out-of-distribution by design. A reviewer will say you measure domain mismatch, not specialization, outside radiology. MedHEval makes the same observation about CheXagent ("performs well on chest X-rays but struggles on other modalities", full text).
3. **A known measurement confound.** Your project notes (written 2026-10; verify the current status) record that ~33% of LLaVA-Med baseline/Pillar D responses started mid-sentence and that a baseline rerun was pending. If still unresolved, LLaVA-Med's hallucination and omission rates may be partly an output-truncation artefact. Since LLaVA-Med carries much of the paradox, this must be closed before submission. Med-HallMark itself warns that short outputs can look better on report scores.
4. **Severity weights are hand-set.** MediHall's level scores are fixed by the authors; CREST's risk levels come from physicians. Without clinician-elicited weights and a sensitivity analysis, SMHR rankings can be dismissed as weight artefacts.
5. **Judges are bad at omissions.** Omission and evasion are in your taxonomy. Recent evidence: LLM judges discriminate omissions only at 0.50-0.63 paired accuracy on clinical notes (2608.31016, abstract) and discriminate incomplete from complete patient-facing answers at AUC 0.49-0.66 (2604.16383, full text). Though those are text domains, a reviewer will transfer them.
6. **Same-family judge bias.** 2607.18828 reports a positive same-provider effect among LLM judges (abstract; text-only clinical conversations). If a judge model is also among your 12 VLMs, say how you handle it.
7. **Rank transfer with n = 12.** A Spearman or Kendall correlation over 12 models has wide CIs; "transfers across skin, tissue and retina but not radiology" can be noise unless you report intervals and a permutation test.
8. **Taxonomy novelty and prevalence.** Overlap with HalluCXR (Section 2a) and the low-prevalence problem of agreement statistics (Section 5).
9. **Normalization can reward silence.** MediHall's authors note that short outputs can score better because they say less; claim-normalized rates can behave the same way. Report claims per response and omission rate alongside SMHR. HalluCXR found response length alone predicts hallucination (AUC up to 0.908 in its abstract), so a length control is expected.

---

## 5. Method precedents: judge validation, agreement, confidence intervals

| Work | Judge | Human validation | Agreement statistic | CIs |
|---|---|---|---|---|
| HalluCXR (2605.20469) | Gemini; GPT-5.1 cross-check | 250 annotations by **two co-authors** with clinical-informatics training; disagreements by discussion | Auto-detector F1 0.959, kappa 0.870; LLM judge F1 0.907 but **kappa 0.150** (base-rate effect, 97.6% vs 81.9% positive); inter-judge kappa 0.515; severity within ±1 on 97.1% of 175 | 95% CIs on headline rates, bootstrap on some differences; none for judge metrics |
| Med-HallMark (2406.10185) | MediHallDetector | Three doctors plus lead; 300-sample test | Per-category accuracy/recall; **no kappa**; 93.88% round-to-round self-consistency | None |
| MedHEval (2503.02157) | Claude 3.5 Sonnet 0-5 score (appendix names an Azure ChatGPT API, an inconsistency) | Two human annotators; GT answers checked on 50 samples | Pearson 0.834, Spearman 0.716, Kendall 0.658 | Not reported |
| ClinHallu (2606.14697) | Qwen3.5-27B | 10% subset | 89.7-94.0% agreement (Sec. 5.3, Table 6) | Not reported |
| DermBench/DermEval (2511.09195) | DeepSeek-R1 judge + trained evaluator | **Two dermatologist co-authors**; the paper says inter-rater reliability "was not formally quantified" | MAE vs expert scores only | None |
| VERT (2604.03376) | LLM judges (RadFact, GREEN, FineRadScore, VERT) | Expert labels from RadEval (148 CXR reports) and RaTE-Eval (1,856 pairs) | Kendall tau only | p-values, no bootstrap CIs |
| CTest-Metric (2601.11488, abstract) | Metric validation | 175 "disagreement" cases rated by clinicians | Metric-vs-expert correlation + graded error injection | not read |
| 2604.16383 | Three LLM-judge designs | Clinician-annotated sets (108 questions); no inter-clinician agreement reported | AUC 0.49-0.66, F1 | None |

**What these tell you to do** (these are my inferences from the table, not claims from the papers):
- Report **Cohen's or Fleiss' kappa plus a prevalence-robust statistic** (e.g. Gwet's AC1 or PABAK) because HalluCXR shows how kappa collapses at skewed base rates; use **weighted kappa or Krippendorff's alpha** for ordinal severity.
- Report **human-human agreement** as the ceiling and judge-human agreement against it, **per taxonomy class**, with omission and evasion shown separately.
- Use **cluster (image- or case-level) bootstrap CIs** for SMHR and for rank correlations, not response-level resampling.
- Use at least two independent judge families, and state if a judged model shares a family with a judge.
- **State annotator provenance exactly.** Per your project notes, the current annotation files are Claude-generated persona outputs renamed `human_annotations/`. That is a legitimate *AI-annotator reliability* study, but it must not be described as clinician annotation. The field's bar is low (two co-author annotators in HalluCXR and DermBench), yet even those are human. The cheapest fix with the largest payoff is a small independent clinician subset (a few hundred claims) for both the taxonomy labels and the severity weights, with agreement reported against the AI labels.

---

## 6. Reading list, ranked by importance to this paper

1. **MedHEval** (2503.02157, 2025-03-04): closest benchmark + mitigation + cause taxonomy; your main benchmarking foil.
2. **ClinHallu** (2606.14697, 2026-06-12): stage-replacement interventions; defines the prior art for contribution 7.
3. **MediHall Score / Med-HallMark** (2406.10185): severity-level scores averaged over all sentences; the precedent for SMHR's normalization.
4. **CREST** (medRxiv 10.1101/2025.07.13.25331222, 2025-07-14): risk-weighted, error-normalized comparator; read the full text for the formula.
5. **HalluCXR** (2605.20469): taxonomy overlap, judge-validation numbers (kappa 0.150), length confound.
6. **2604.09841** (2026-04-10): paired base-vs-tuned on four modalities; the strongest counter to the paradox.
7. **MedVH** (2407.02730; Wiley doi 10.1002/aisy.202500255): origin of the "specialists hallucinate more" claim.
8. **EchoBench** (2509.20146) and **2603.22623**: specialization vs sycophancy/hallucination with mixed evidence.
9. **CARES** (2406.06007): multi-modality trust benchmark incl. derm and fundus; blocks "first multi-modality."
10. **Med-StepBench** (2605.10002 / IJCAI-ECAI 2026) and **CRAFT** (2609.38810): other stage/causal work.
11. **SHOVIR** (2606.30201) and **MC-CXR** (2608.24118): occlusion and context for chest X-ray.
12. **2609.31733** (RAG hurts) and **RULE** (2407.05131): RAG failure modes for your retrieval arm.
13. **Byun et al.** (2604.02543 v2, COLM 2026) and **2606.16583**: calibration prior art and fixed-decoding practice; **RadFlag** (2411.00299) for temperature as a signal.
14. **VERT** (2604.03376), **2604.16383**, **2608.31016**: how and why LLM judges fail in clinical settings.
15. The medRxiv histopathology hallucination study (10.64898/2026.09.18.26363369; **full text not read**).

---

## 7. Verification status

Verified from a primary source and abstract/full text read: every arXiv id above (arXiv API; full text for those labelled), CREST and the two medRxiv histopathology papers (medRxiv API abstracts), MedVH Wiley record (Crossref metadata and abstract fragment), npj and Applied Sciences and AIES records (registrar/Crossref).

**Unverified (do not cite without checking):**
- The MDPI *Life* study "Visual Large Language Models in Radiology: A Systematic Multimodel Evaluation of Diagnostic Accuracy and Hallucinations" (RWTH Aachen, PMC12842777): found only through a web-search summary (7 models, 180 images, 74.4% hallucination rate); the PMC page was blocked by a browser check.
- The European Radiology (2026) semantic-entropy paper: web-search summary only; arXiv 2510.09256 is its likely preprint, abstract not read.
- A "GI hallucination benchmark (MICCAI 2025)" and the list of datasets inside MedVH (PathVQA, PMC-VQA, VQA-Med-2021, MIMIC-Diff-VQA): from web-search snippets only.
- The CREST normalization details ("High-Risk Error Rate", normalized score): from a web-search summary of the full paper; the medRxiv API abstract confirms only the taxonomy, risk levels, models and the CREST score.
- Anything about papers published after about 2026-10-12: the search window ends there, and the field is producing roughly one relevant paper a week (about 45 verified in the 4.5 months to 2026-10-13), so re-run the Prompt A search shortly before submission.
