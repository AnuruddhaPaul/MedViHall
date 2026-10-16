"""
Pillar B Stage 0b -- llava_med "no mitigation" baseline rerun with the decoding fix.

The core run and Pillar D greedy decoded llava_med with
    output_ids[0][input_ids.shape[1]:]
but LLaVA's generate() returns only the NEW tokens, so the first len(prompt) tokens of any answer longer
than the prompt were cut (~33% of llava_med baseline responses start mid-sentence). This reruns the
baseline for llava_med only: same prompts, same greedy decoding, same MAX_TOKENS_BY_QT, whole output decoded.
Output: medvihall_outputs/pillar_b_baseline_llava_med_fixed.jsonl (1,679 calls), used in place of the
llava_med rows of pillar_b_baseline.jsonl by the labeling / Stage 4 / annotation scripts.
Resume-safe via pillar_b_common.run_condition.

Usage:
  python pillar_b_baseline_llava_med.py [--limit N] [--out FILE]
"""
import argparse
from pathlib import Path

import torch

import pillar_b_common as C
from pillar_d_infer_fns import safe_load_image

OUT_FILE = Path('medvihall_outputs/pillar_b_baseline_llava_med_fixed.jsonl')
PROGRESS_FILE = Path('medvihall_outputs/pillar_b_baseline_llava_med_fixed_progress.json')


def infer_llava_med_fixed(model, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                          max_new_tokens=512):
    from llava.mm_utils import process_images, tokenizer_image_token
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    tokenizer, image_processor, context_len = proc
    full_prompt = f'[INST] {sys_p}\n\n{DEFAULT_IMAGE_TOKEN}\n{prompt} [/INST]'
    input_ids = tokenizer_image_token(
        full_prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).to(model.device)
    attention_mask = torch.ones_like(input_ids)
    image = safe_load_image(img_path)
    image_tensor = process_images([image], image_processor, model.config).to(model.device, dtype=torch.float16)
    with torch.no_grad():
        output_ids = model.generate(
            input_ids, attention_mask=attention_mask, images=image_tensor, image_sizes=[image.size],
            pad_token_id=tokenizer.eos_token_id, use_cache=True, max_new_tokens=max_new_tokens, do_sample=False)
    res = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if '[/INST]' in res:                      # only if a prompt echo is ever present
        res = res.rsplit('[/INST]', 1)[1]
    res = res.strip()
    del input_ids, attention_mask, image_tensor, output_ids
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--out', default=str(OUT_FILE))
    args = ap.parse_args()
    C.run_condition(args.out, PROGRESS_FILE, 'baseline_fixed', ['llava_med'],
                    lambda img, qt, base: (base, {}), limit=args.limit,
                    infer_for=lambda m: infer_llava_med_fixed)


if __name__ == '__main__':
    main()
