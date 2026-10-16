# MedViHall: claims at risk (as of 2026-10-13)

Basis: the searches described in `lit_update.md` (arXiv API, OpenAlex, DOI registrars, two web searches), 2025-09-01 to 2026-10-13. Everything below is "as far as these queries could see". I did not read the MedViHall implementation, so where a claim's exact wording matters I say so. Paper identifiers are arXiv ids unless marked doi.

## Verdict at a glance

| # | Contribution | Still novel? | Most threatening paper | Level |
|---|---|---|---|---|
| 1 | SMHR / CHR / SRI (severity-weighted, frequency-sensitive) | **Yes, conditionally** | HalluCXR 2605.20469 and MediHall Score 2406.10185 (both already known) | MEDIUM (known) |
| 2 | Hallucination fingerprints, 4 modalities, 3 "with no prior benchmark" | **No, as worded**; the "no prior benchmark" sentence is false for histopathology | medRxiv 10.64898/2026.09.18.26363369 (clinician-graded hallucinations in histopathology) | HIGH |
| 3 | Specialization paradox | **No as a direction; partly as a measurement** | MedVH 2407.02730 (2024) and the review 2606.13211 | HIGH |
| 4 | Cross-modal safety transfer | **Yes** (no overlapping paper found) | 2606.15910 (natural-to-medical transfer of a confidence signal), adjacent only | LOW |
| 5 | Calibration robustness across decoding settings | **Yes on the decoding axis; the calibration topic itself is crowded** | Byun et al. 2604.02543 (v2, COLM 2026) | MEDIUM |
| 6 | Comparative mitigation (RAG vs contrastive decoding; the planned fine-tuning arm was dropped) | **Yes as a head-to-head comparison**; each method alone has prior art | 2609.31733 (RAG increases hallucination in CXR) | MEDIUM |
| 7 | Causal stage localization (visual / knowledge / reasoning) | **No as stated** | ClinHallu 2606.14697 (known), then Med-StepBench 2605.10002 (missed before) | HIGH |
| 8 | Context-occlusion robustness | **Partly**: taken for chest X-ray, open for the other modalities and for a hallucination framing | SHOVIR 2606.30201 | HIGH (CXR) |

Short version: contributions 4, 5 (decoding axis) and 6 (head-to-head) hold up; 1 holds if it is contrasted explicitly with MediHall and HalluCXR; 2, 3, 7 and 8 each need rewording because a published paper already makes the core claim.

---

## 1. SMHR, CHR, SRI

**Status: still novel, conditional on the "severity-weighted AND frequency-sensitive" combination.** No overlapping paper found with these queries (queries: severity/clinical-risk/harm/clinically-weighted hallucination groups, "severity-weighted", back-sweep `bs-severity`).

What exists:
- MediHall Score (2406.10185, v2 2026-04-27) and HalluCXR (2605.20469, chest X-ray only, clinical severity ratings, 6 VLMs) are both known and both severity-aware. HalluCXR is the closer one; the explicit comparison in the paper must stay.
- 2603.22623 (March 2026, missed before) defines a Clinical Safety Index but it is a geometric mean of grounding, autonomy and calibration; it does not weight by clinical severity.
- 2606.24155 (MedBench v5) tracks hallucination propagation, no severity weighting. 2606.24115 notes qualitatively that "not all hallucinations carry equal clinical weight" and then scores binary.
- The histopathology study (doi 10.64898/2026.09.18.26363369) grades clinical impact 0-4 per output; from the abstract it does not aggregate it into a rate. Full text not read (blocked).

Risk: a reviewer who knows MediHall and HalluCXR will ask what SMHR adds. Be ready to show a case where SMHR ranks models differently from an unweighted rate and from MediHall.

## 2. Hallucination fingerprints across four modalities; three modalities "with no prior hallucination benchmark"

**Status: not defensible as worded. HIGH threat to the sentence, MEDIUM to the idea of modality fingerprints.**

- **Histopathology.** doi 10.64898/2026.09.18.26363369 (medRxiv, 2026-09-24): 153 cases over 20 organs, four frontier LLMs with images, 21 pathologists grading error and hallucination type and burden and clinical impact; hallucinations in 76.6% of outputs, fabricated histologic features dominant (74.5%). It is a study rather than a released benchmark, and it covers general-purpose models only, but it is a clinician-graded hallucination evaluation in histopathology and it predates our submission. Also doi 10.64898/2026.07.04.26357257: confident confabulation on blank histology images, with a temperature sweep.
- **Dermatology / CXR / brain MRI.** 2607.26886 (Hearsay) shows frontier VLMs confabulate diagnoses with no image at all in these three.
- **Ophthalmology.** doi 10.3390/app16126064 audits six fundus LVLMs for textual dependency, logical inconsistency and CoT fidelity; 2607.16609 (OCT-Bench, abstract only) is a perception-to-reasoning benchmark.
- **Other modalities already have hallucination benchmarks:** GI endoscopy (2606.24115), PET/CT (Med-StepBench 2605.10002), chest X-ray (HalluCXR and others), plus EchoBench (2509.20146) for sycophancy over 20 modalities including DERM, FUNDUS, HISTO and OCT.
- The word "fingerprint" appears in MedBench v5 ("model-specific failure fingerprints", process audit of clinical dialogues), not for imaging modalities. No paper found that builds per-modality hallucination fingerprints.

Suggested rewording: replace "no prior hallucination benchmark" with something like "no prior benchmark that evaluates medical-tuned and general VLMs with a shared, claim-level, severity-graded protocol across these modalities", and cite the histopathology study and Hearsay as the closest prior evaluations. Verify the sentence per modality: I found something for histopathology, dermatology (partial), ophthalmology (partial); I did not find a dermatology hallucination benchmark with a standard protocol, so that claim is the safest of the three.

## 3. Specialization paradox

**Status: the direction is already published; the measurement is the contribution. HIGH threat to the novelty framing.**

Already says medical-tuned VLMs hallucinate or fail more than general ones:
- MedVH 2407.02730 (2024): medical LVLMs "often more [susceptible to hallucination] than the general models".
- 2606.13211 (review, 2026-06-11): "general-purpose foundation models outperform medical-specialized models on hallucination-specific benchmarks ... narrow domain fine-tuning can introduce overfitting-induced confabulation". Evidence is re-aggregated text-benchmark numbers (Med-HALT) with internal inconsistencies; do not borrow its numbers.
- EchoBench 2509.20146: medical-specific models average ~83.0% sycophancy vs ~74.7% for general open models, and LLaVA-Med 98.75% vs 55.39% for its own base model.
- 2509.21979 (known, v7): sycophancy in medical VLMs.

Evidence AGAINST a blanket paradox (your paper must address these or reviewers will):
- 2603.22623: medical fine-tuning "does not consistently improve safety", but the most pressure-resistant model (general) hallucinates more than all three medical models.
- 2608.02790: MedGemma-4B has the LOWEST open-ended hallucination rate in its panel (0.061) on brain MRI, though worse ECE.
- 2606.24115: the general LLaVA-v1.6-7B sits between medical models on hallucination rate.
- 2608.27004: medical pretraining generally gives lower ECE for CLIP-type classifiers.
- doi 10.1038/s41746-026-03191-3 (npj Digit Med): medical-specific models "no consistent advantage".

Suggested framing: state the paradox as conditional (which metric, which modalities, which model sizes) and present the 12-VLM, 4-modality, severity-weighted measurement as the new evidence. Avoid "we discover that".

## 4. Cross-modal safety transfer

**Status: still novel. No overlapping paper found with these queries** (queries: `safety-transfer` group, cross-modal/cross-modality/across-modalities safety or reliability, back-sweep `bs-multimod`).

Adjacent only: 2606.15910 transfers confidence probes trained on natural images to medical VQA; 2606.16583, 2606.15910 and EchoBench report per-modality breakdowns without testing whether safety behaviour on one modality predicts another; MVC-Bench compares calibration across three modalities for classifiers. I cannot judge how closely these match your operational definition of "transfer" without reading it.

## 5. Calibration robustness across decoding settings

**Status: novel on the decoding axis; the calibration topic is crowded.** At least eight 2026 papers study medical VLM calibration (2604.02543, 2608.27004, 2606.16583, 2606.15910, 2608.02790, 2606.19950, 2606.27023, 2608.10964), none of which sweeps decoding settings for calibration:
- Byun et al. 2604.02543 (known; **v2 2026-09-30, COLM 2026 accepted**): general VLMs only, VQA, prompting strategies and post-hoc calibration; sampling parameters not varied in what I read. Closest prior art.
- 2606.16583 fixes T=0.6, p=0.9; 2606.15910 and 2608.02790 use greedy; MVC-Bench varies prompt templates and seeds, not decoding.
- doi 10.64898/2026.07.04.26357257 is the only item varying temperature (0.0 / 0.5 / 1.0), but for confabulation rate on blank histology images, not calibration.

Action: update the Byun citation to v2, re-read it for any new decoding experiments (the changelog is not visible), and make the decoding sweep the stated differentiator.

## 6. Comparative mitigation (RAG vs contrastive decoding; the planned fine-tuning arm was dropped)

**Status: still novel as a single-benchmark head-to-head. No overlapping paper found with these queries** (mitigation group, back-sweep `bs-mitig`). Each ingredient has prior art:
- Contrastive decoding in medical VLMs: CCD 2509.23379 (ACL 2026), Med-VCD 2512.01922, ARCD 2512.17189, CAST 2608.17427 (MICCAI 2026). These were not on the known list; CCD, Med-VCD and ARCD predate the June search.
- RAG: 2609.31733 shows retrieval can multiply hallucination (retrieval-induced rate 0.00 to 0.76) in CXR report generation with a general generator; Med-StepBench's knowledge injection gave marginal, inconsistent gains. Whatever our RAG arm shows, discuss it against these two.
- Fine-tuning: MedHallTune 2502.20780 (**v2 2026-07-30**), ClinHallu trace-supervised fine-tuning, CORAL 2607.03647, Pair-DPO 2609.32185.
- HalluCXR already reports a six-model ensemble mitigation.

## 7. Causal stage localization (visual / knowledge / reasoning)

**Status: not novel as stated. HIGH threat; the paper that does it is already on the known list.**

- **ClinHallu 2606.14697** splits traces into Visual Recognition, Knowledge Recall and Reasoning Integration and runs stage-replacement interventions (reference stage supplied, effect on final answer measured), concluding e.g. that VQA-RAD is visually bottlenecked and MedXpertQA knowledge-bottlenecked. This is the same decomposition as your contribution 7.
- **Med-StepBench 2605.10002** (IJCAI-ECAI 2026, submitted 2026-05-11, missed before) localises hallucinations over four diagnostic stages in PET/CT, without causal interventions.
- CRAFT 2609.38810 does causal localization at attention-head level for context-override and over-commitment, not for reasoning stages.

What remains: causal stage interventions across four named modalities, linked to severity-weighted rates and to which mitigation fixes which stage. Cite ClinHallu in the first paragraph where stage localization is introduced, and check that your intervention definitions are not a re-derivation of its Eqs. 9-12.

## 8. Context-occlusion robustness

**Status: partly taken. HIGH threat for chest X-ray; open elsewhere.** (I interpret this as masking/removing image regions or context and measuring the change; confirm against the implementation.)

- **SHOVIR 2606.30201** (v2, 2026-07-22): image-level and disease-level occlusion on MIMIC-CXR and PadChest-GR, with a random-box control and a co-pathology occlusion (DOCO) that targets exactly the "context" notion; eight models; it reports no hallucination rate or severity.
- MC-CXR 2608.24118 (Findings of EMNLP 2026): context perturbation (text, prior CXR, overlays) rather than occlusion; finds text override dominates and domain specialisation "does not insulate" against it.
- Evidence-removal controls in other modalities: 2608.04885 (brain MRI, lesion slices removed, forced diagnosis up to 76.1%), 2609.32185 (pathology, no image / lesion / WSI), 2607.21065 (pathology no-image accuracy), doi 10.3390/app16126064 (fundus modality ablation), 2607.03647 and 2603.03437 (blank/shuffled/corrupted images), 2609.38810 (masked diagnostic regions).

Suggested framing: occlusion robustness measured on hallucination rate and severity, across four modalities, with the context/target distinction made explicit. Cite SHOVIR as the CXR precedent.

---

## Things to do before submission (ordered)

1. Reword contribution 7 around ClinHallu; reword contribution 2's "no prior benchmark" sentence; reframe contribution 3 as a conditional measurement.
2. Add a SMHR vs MediHall vs HalluCXR comparison table if it is not already there.
3. Update citations: Byun et al. (COLM 2026), MedHallTune v2, Med-StepBench (IJCAI-ECAI 2026 / arXiv:2605.10002).
4. Read in full before quoting numbers: the histopathology medRxiv study, Hearsay, 2603.03437, CleanSlide 2609.32185, and the v2 diffs of 2604.02543 and 2502.20780.
5. Re-run the search shortly before submission: this field produced about four relevant papers per month in the window.
