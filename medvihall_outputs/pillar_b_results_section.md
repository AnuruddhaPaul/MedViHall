# Pillar B (RQ8): comparative mitigation efficacy -- results draft (auto-filled; edit prose before use)

SMHR per model and strategy (class-weighted hallucinated claims / claims incl. Layer-1 omissions; lower is safer).
Greedy decoding throughout; baseline = unmitigated prompt; RAG = top-3 modality reference snippets; contrastive = visual contrastive decoding (alpha=1.0, beta=0.1, diffusion-noise t=500).

| Model | baseline SMHR | rag SMHR | contrastive SMHR | Δ rag [95% CI] | Δ contrastive [95% CI] |
|---|---|---|---|---|---|
| qwen25vl | 0.537 | 0.508 | 0.533 | -0.028 [-0.046, -0.009]* | -0.003 [-0.021, +0.016] |
| llava16 | 0.669 | 0.627 | 0.583 | -0.042 [-0.063, -0.020]* | -0.085 [-0.106, -0.066]* |
| chexagent | 0.751 | 0.778 | 0.709 | +0.026 [+0.003, +0.048]* | -0.041 [-0.069, -0.013]* |
| huatuogpt | 0.699 | 0.704 | 0.676 | +0.004 [-0.012, +0.020] | -0.025 [-0.041, -0.009]* |
| llava_med | 0.728 | 0.731 | 0.724 | +0.003 [-0.014, +0.018] | -0.005 [-0.019, +0.008] |

\* = bootstrap 95% CI (resampling images, paired on the same image/query keys) excludes 0.

**(a) Best strategy per model:** qwen25vl: rag (-0.028); llava16: contrastive (-0.085); chexagent: contrastive (-0.041); huatuogpt: contrastive (-0.025); llava_med: contrastive (-0.005).
**(b) Differs by model:** yes (specialists: {'chexagent': 'contrastive', 'huatuogpt': 'contrastive', 'llava_med': 'contrastive'}; generals: {'qwen25vl': 'rag', 'llava16': 'contrastive'}).
**(c) Specialist-vs-general gap (mean SRI, baseline 1.40):** rag: 1.47 (widens); contrastive: 1.41 (widens).
**(d) Strategies that increased SMHR:** chexagent+rag (+0.026, significant); huatuogpt+rag (+0.004, n.s.); llava_med+rag (+0.003, n.s.).

Data-quality notes: see `data_quality` in pillar_b_mitigation_results.json (missing-confidence, chopped-start and unlabeled rates per cell).