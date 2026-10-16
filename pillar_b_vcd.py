"""
Pillar B (RQ8), Stage 2 -- visual contrastive decoding (VCD) for the 5 models.

Formulation (Leng et al., VCD): at every decoding step the model sees the
original image and a heavily distorted copy; the next-token logits are
    logits_vcd = (1 + alpha) * logits(original) - alpha * logits(distorted)
restricted to the adaptive plausibility set {v : p_orig(v) >= beta * max p_orig}
(beta = 0.1, the paper's default), then argmax (greedy, matching the Stage 1 /
Pillar D matched-baseline decoding).

Implementation: the original and distorted images are run as a BATCH OF 2 through
each model's own generate() (so every model-specific detail -- mrope, KV caches,
projector paths -- is handled natively) with a LogitsProcessor that combines the
two rows and writes the SAME distribution into both rows, so both sequences take
the identical token each step and stay aligned. Cost is about one batched decode,
not two sequential ones.

Distortion: Gaussian forward-diffusion noise, t=500/1000 of the DDPM linear beta
schedule (1e-4 -> 2e-2), i.e. x_d = sqrt(abar) * x + sqrt(1 - abar) * eps with
abar = 0.0793 on pixels scaled to [-1, 1] (signal amplitude 0.28, noise 0.96), the
VCD paper's setting. The noise seed is derived from the image path, so the
distorted image is identical across models and reruns.
"""
import zlib
import numpy as np
import torch
from transformers import LogitsProcessor, LogitsProcessorList

from pillar_d_infer_fns import safe_load_image, process_vision_info

ALPHA_DEFAULT = 1.0
BETA = 0.1
DIFFUSION_T = 500


def diffusion_abar(t=DIFFUSION_T, T=1000, b0=1e-4, b1=2e-2):
    betas = b0 + (b1 - b0) * np.arange(T) / (T - 1)
    return float(np.prod(1.0 - betas[:t]))


ABAR = diffusion_abar()
VCD_PARAMS = {'method': 'VCD', 'beta_plausibility': BETA, 'distortion': 'gaussian_forward_diffusion',
              'diffusion_t': DIFFUSION_T, 'abar': round(ABAR, 4), 'batch_of_2_logits_processor': True}


def distort_image(img, key):
    """Heavily noised copy of a PIL image; deterministic given `key` (the image path)."""
    from PIL import Image
    x = np.asarray(img.convert('RGB'), dtype=np.float32) / 127.5 - 1.0
    rng = np.random.default_rng(zlib.crc32(str(key).encode('utf-8')))
    xd = np.sqrt(ABAR) * x + np.sqrt(1.0 - ABAR) * rng.standard_normal(x.shape).astype(np.float32)
    xd = np.clip((xd + 1.0) * 127.5, 0, 255).astype(np.uint8)
    return Image.fromarray(xd)


class VCDProcessor(LogitsProcessor):
    """Row 0 = original image, row 1 = distorted image. Returns the contrastive
    distribution in BOTH rows so greedy decoding keeps the two sequences identical."""

    def __init__(self, alpha=ALPHA_DEFAULT, beta=BETA):
        self.alpha, self.beta = alpha, beta

    def __call__(self, input_ids, scores):
        lo = scores[0].float()
        ld = scores[1].float()
        finite = torch.isfinite(lo)
        ld = torch.where(torch.isfinite(ld), ld, lo)            # distorted -inf (e.g. min_new_tokens) -> no contrast
        cd = torch.where(finite, (1.0 + self.alpha) * lo - self.alpha * ld, torch.full_like(lo, float('-inf')))
        p = torch.softmax(torch.where(finite, lo, torch.full_like(lo, -1e30)), dim=-1)
        cd = torch.where(p >= self.beta * p.max(), cd, torch.full_like(cd, float('-inf')))
        return cd.unsqueeze(0).expand(scores.shape[0], -1).to(scores.dtype).clone()


def _proc_list(alpha):
    return LogitsProcessorList([VCDProcessor(alpha=alpha)])


def _decode_check(text):
    return text if text else '[EMPTY]'


# ---------------------------------------------------------------- per-model backends
def vcd_qwen25vl(mdl, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                 max_new_tokens=512, alpha=ALPHA_DEFAULT):
    img = safe_load_image(img_path)
    imgs = [img, distort_image(img, img_path)]
    msgs = lambda im: [{'role': 'system', 'content': sys_p},
                       {'role': 'user', 'content': [{'type': 'image', 'image': im}, {'type': 'text', 'text': prompt}]}]
    text = proc.apply_chat_template(msgs(imgs[0]), tokenize=False, add_generation_prompt=True)
    ii = []
    for im in imgs:
        i_, _ = process_vision_info(msgs(im))
        ii += i_
    inp = proc(text=[text, text], images=ii, videos=None, padding=True, return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=max_new_tokens, do_sample=False, logits_processor=_proc_list(alpha))
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out
    torch.cuda.empty_cache()
    return _decode_check(res)


def vcd_llava16(mdl, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                max_new_tokens=512, alpha=ALPHA_DEFAULT):
    img = safe_load_image(img_path)
    imgs = [img, distort_image(img, img_path)]
    conv = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': f'{sys_p}\n\n{prompt}'}]}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True)
    inp = proc(images=imgs, text=[text, text], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=max_new_tokens, do_sample=False, logits_processor=_proc_list(alpha))
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out
    torch.cuda.empty_cache()
    return _decode_check(res)


def vcd_chexagent(mdl, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                  max_new_tokens=512, alpha=ALPHA_DEFAULT):
    img = safe_load_image(img_path)
    text = f'{sys_p}\n{prompt}'
    a = proc(images=img, text=text, return_tensors='pt')
    b = proc(images=distort_image(img, img_path), text=text, return_tensors='pt')
    pv = torch.cat([a['pixel_values'], b['pixel_values']], dim=0).to('cuda')
    ids = torch.cat([a['input_ids'], b['input_ids']], dim=0).to('cuda')
    am = torch.cat([a['attention_mask'], b['attention_mask']], dim=0).to('cuda')
    with torch.no_grad():
        out = mdl.generate(pixel_values=pv, input_ids=ids, attention_mask=am, max_new_tokens=max_new_tokens,
                           min_new_tokens=100, do_sample=False, logits_processor=_proc_list(alpha))
    res = proc.decode(out[0], skip_special_tokens=True).strip()
    del pv, ids, am, out
    torch.cuda.empty_cache()
    return _decode_check(res)


def vcd_huatuogpt(mdl, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                  max_new_tokens=512, alpha=ALPHA_DEFAULT):
    from huatuo_llava.constants import IMAGE_TOKEN_INDEX
    from PIL import Image
    tokenizer, image_processor = proc

    def tokenizer_image_token(text):
        chunks = [tokenizer(c, add_special_tokens=False).input_ids for c in text.split('<image>')]
        ids, offset = [], 0
        if chunks and chunks[0] and chunks[0][0] == tokenizer.bos_token_id:
            offset = 1
            ids.append(chunks[0][0])
        sep = [IMAGE_TOKEN_INDEX] * (offset + 1)
        interleaved = [x for pair in zip(chunks, [sep] * len(chunks)) for x in pair][:-1]
        for x in interleaved:
            ids.extend(x[offset:])
        return torch.tensor(ids, dtype=torch.long)

    def expand2square(pil_img, bg):
        w, h = pil_img.size
        if w == h:
            return pil_img
        side = max(w, h)
        result = Image.new(pil_img.mode, (side, side), bg)
        result.paste(pil_img, ((side - w) // 2, (side - h) // 2))
        return result

    img = safe_load_image(img_path)
    bg = tuple(int(x * 255) for x in image_processor.image_mean)
    tensors = [image_processor.preprocess(expand2square(im, bg), return_tensors='pt')['pixel_values'][0]
               for im in (img, distort_image(img, img_path))]
    image_tensor = torch.stack(tensors).to('cuda', dtype=torch.bfloat16)
    text = f'<|user|>\n<image>\n{sys_p}\n\n{prompt}\n<|assistant|>\n'
    input_ids = tokenizer_image_token(text).unsqueeze(0).repeat(2, 1).to('cuda')
    with torch.no_grad():
        out = mdl.generate(input_ids, images=image_tensor, pad_token_id=tokenizer.pad_token_id, use_cache=True,
                           max_new_tokens=max_new_tokens, do_sample=False, logits_processor=_proc_list(alpha))
    res = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    del input_ids, image_tensor, out
    torch.cuda.empty_cache()
    return _decode_check(res)


def vcd_llava_med(model, proc, img_path, prompt, sys_p, temperature=0.0, top_p=0.9, do_sample=False,
                  max_new_tokens=512, alpha=ALPHA_DEFAULT):
    from llava.mm_utils import process_images, tokenizer_image_token
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    tokenizer, image_processor, context_len = proc
    full_prompt = f'[INST] {sys_p}\n\n{DEFAULT_IMAGE_TOKEN}\n{prompt} [/INST]'
    ids1 = tokenizer_image_token(full_prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0)
    input_ids = ids1.repeat(2, 1).to(model.device)
    attention_mask = torch.ones_like(input_ids)
    img = safe_load_image(img_path)
    imgs = [img, distort_image(img, img_path)]
    image_tensor = process_images(imgs, image_processor, model.config).to(model.device, dtype=torch.float16)
    with torch.no_grad():
        output_ids = model.generate(input_ids, attention_mask=attention_mask, images=image_tensor,
                                    image_sizes=[im.size for im in imgs], pad_token_id=tokenizer.eos_token_id,
                                    use_cache=True, max_new_tokens=max_new_tokens, do_sample=False,
                                    logits_processor=_proc_list(alpha))
    # LLaVA's generate() (inputs_embeds path) returns ONLY the new tokens; slicing off input_ids.shape[1]
    # chopped the start of any answer longer than the prompt (Pillar D / core baseline bug, ~33% of
    # llava_med responses). Decode everything and drop a prompt echo only if one is present.
    res = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if '[/INST]' in res:
        res = res.rsplit('[/INST]', 1)[1]
    res = res.strip()
    del input_ids, attention_mask, image_tensor, output_ids
    torch.cuda.empty_cache()
    return _decode_check(res)


VCD_INFER_FNS = {
    'qwen25vl': vcd_qwen25vl, 'llava16': vcd_llava16, 'chexagent': vcd_chexagent,
    'huatuogpt': vcd_huatuogpt, 'llava_med': vcd_llava_med,
}


def degenerate_flags(text, max_run=8):
    """Instability diagnostics on a decoded response: empty/[EMPTY], a token repeated
    >= max_run times in a row, or very low distinct-token ratio on long outputs."""
    toks = text.split()
    run = best = 1
    for a, b in zip(toks, toks[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    distinct = len(set(toks)) / max(len(toks), 1)
    return {'empty': text.strip() in ('', '[EMPTY]'), 'max_repeat_run': best,
            'distinct_ratio': round(distinct, 3),
            'degenerate': text.strip() in ('', '[EMPTY]') or best >= max_run or (len(toks) >= 40 and distinct < 0.25)}
