"""
Stage 0 (Pillar D prep) -- patched infer_* functions for the 5 models in
representative_subset.json, extracted from MedViHall_Phase3_Phase4_v4.ipynb.

Bug found: _infer_qwen_vl (backs qwen25vl), infer_llava16, and infer_chexagent
all called model.generate(..., do_sample=True) unconditionally -- greedy
decoding (temperature=0.0) requires do_sample=False, so at TEMPERATURE=0.0
these three were silently still sampling instead of decoding greedily.
infer_llava_med and infer_huatuogpt already had the correct
do_sample=(TEMPERATURE > 0) logic.

Fix applied to all 5 (not just the 3 buggy ones): temperature and top_p are
now function parameters instead of reads of a fixed global TEMPERATURE, with
do_sample defaulting to (temperature > 0.0) -- matching Stage 0's bug-fix
rule -- but overridable via an explicit do_sample parameter. The override
exists because Pillar D's calibration sweep (Stage 2) needs greedy/nucleus
as an axis INDEPENDENT of temperature (e.g. greedy at temp=0.3, nucleus at
temp=0.0), which a temperature-derived default alone cannot express. This
also lets Stage 2 sweep 6 configs per model without reloading -- the
previous global-TEMPERATURE design meant temperature could only change
between full kernel/notebook reruns.

Diffs, one per function:

  _infer_qwen_vl (backed qwen25vl):
    - out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    + do_sample = temperature > 0.0
    + gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample)
    + if do_sample: gen_kwargs.update(temperature=temperature, top_p=top_p)
    + out = mdl.generate(**inp, **gen_kwargs)

  infer_llava16:
    (identical shape of fix as _infer_qwen_vl above)

  infer_chexagent:
    (identical shape of fix, plus min_new_tokens=100 preserved unchanged --
     that's an unrelated, already-correct fix for CheXagent's premature-EOS
     behavior, not part of this bug)

  infer_llava_med:
    - do_sample=(TEMPERATURE > 0), top_p=0.9,
    + do_sample=(temperature > 0.0), top_p=top_p,
    (logic was already right; only the global->parameter change applies)

  infer_huatuogpt:
    - temperature=TEMPERATURE, do_sample=(TEMPERATURE > 0),
    + temperature=temperature, do_sample=(temperature > 0.0),
    (same -- logic was already right, only parameterized)
"""
import torch
from qwen_vl_utils import process_vision_info


def safe_load_image(img_path):
    from PIL import Image
    return Image.open(img_path).convert('RGB')


def _sampling_kwargs(temperature, top_p, do_sample):
    """Only pass sampling kwargs when actually sampling -- HF warns (harmlessly)
    if temperature/top_p are given alongside do_sample=False, so keep it clean.
    HF's generate() rejects/misbehaves on temperature<=0 while do_sample=True
    (nucleus-at-temp=0 is a deliberate Pillar D edge case, not a mistake) --
    clamp to a tiny epsilon for numerical safety while keeping the *requested*
    temperature=0.0 in the saved record for calibration analysis."""
    if do_sample:
        return {'temperature': max(temperature, 1e-4), 'top_p': top_p}
    return {}


def resolve_do_sample(temperature, do_sample=None):
    """Stage 0's bug-fix default is do_sample=(temperature>0.0) -- correct for
    the core pipeline, which only ever has one implicit decoding mode per
    temperature. Pillar D's calibration sweep needs greedy/nucleus as an
    INDEPENDENT axis (e.g. greedy at temp=0.3, nucleus at temp=0.0), so an
    explicit override is accepted here; when omitted, the Stage 0 default
    still applies unchanged."""
    return (temperature > 0.0) if do_sample is None else do_sample


def infer_qwen25vl(mdl, proc, img_path, prompt, sys_p, temperature, top_p=0.9, do_sample=None, max_new_tokens=512):
    """Patched _infer_qwen_vl (shared by qwen3vl/qwen25vl/qwen2vl/qwen35 in the
    original notebook) -- was do_sample=True hardcoded."""
    do_sample = resolve_do_sample(temperature, do_sample)
    img = safe_load_image(img_path)
    msgs = [{'role': 'system', 'content': sys_p},
            {'role': 'user', 'content': [{'type': 'image', 'image': img}, {'type': 'text', 'text': prompt}]}]
    text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ii, vi = process_vision_info(msgs)
    inp = proc(text=[text], images=ii, videos=vi, return_tensors='pt').to('cuda')
    gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample)
    gen_kwargs.update(_sampling_kwargs(temperature, top_p, do_sample))
    with torch.no_grad():
        out = mdl.generate(**inp, **gen_kwargs)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


def infer_llava16(mdl, proc, img_path, prompt, sys_p, temperature, top_p=0.9, do_sample=None, max_new_tokens=512):
    """Patched -- was do_sample=True hardcoded."""
    do_sample = resolve_do_sample(temperature, do_sample)
    img = safe_load_image(img_path)
    conv = [{'role': 'user', 'content': [
        {'type': 'image'},
        {'type': 'text', 'text': f'{sys_p}\n\n{prompt}'}]}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True)
    inp = proc(images=img, text=text, return_tensors='pt').to('cuda')
    gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample)
    gen_kwargs.update(_sampling_kwargs(temperature, top_p, do_sample))
    with torch.no_grad():
        out = mdl.generate(**inp, **gen_kwargs)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


def infer_chexagent(mdl, proc, img_path, prompt, sys_p, temperature, top_p=0.9, do_sample=None, max_new_tokens=512):
    """Patched -- was do_sample=True hardcoded. min_new_tokens=100 kept as-is:
    unrelated pre-existing fix for CheXagent's premature-EOS-after-confidence-
    number behavior, not part of this decoding bug."""
    do_sample = resolve_do_sample(temperature, do_sample)
    img = safe_load_image(img_path)
    inp = proc(images=img, text=f'{sys_p}\n{prompt}', return_tensors='pt').to('cuda')
    gen_kwargs = dict(max_new_tokens=max_new_tokens, min_new_tokens=100, do_sample=do_sample)
    gen_kwargs.update(_sampling_kwargs(temperature, top_p, do_sample))
    with torch.no_grad():
        out = mdl.generate(**inp, **gen_kwargs)
    res = proc.decode(out[0], skip_special_tokens=True).strip()
    del inp, out
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


def infer_huatuogpt(mdl, proc, img_path, prompt, sys_p, temperature, top_p=0.9, do_sample=None, max_new_tokens=512):
    """Parameterized only -- do_sample=(TEMPERATURE>0) logic was already correct
    in the original notebook, just needed temperature/top_p off the global."""
    from huatuo_llava.constants import IMAGE_TOKEN_INDEX
    from PIL import Image
    tokenizer, image_processor = proc
    do_sample = resolve_do_sample(temperature, do_sample)

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
    img_sq = expand2square(img, bg)
    image_tensor = image_processor.preprocess(img_sq, return_tensors='pt')['pixel_values'][0]
    image_tensor = image_tensor.unsqueeze(0).to('cuda', dtype=torch.bfloat16)

    text = f'<image>\n{sys_p}\n\n{prompt}'
    text = f'<|user|>\n{text}\n<|assistant|>\n'
    input_ids = tokenizer_image_token(text).unsqueeze(0).to('cuda')

    gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample)
    gen_kwargs.update(_sampling_kwargs(temperature, top_p, do_sample))
    with torch.no_grad():
        out = mdl.generate(
            input_ids, images=image_tensor,
            pad_token_id=tokenizer.pad_token_id, use_cache=True, **gen_kwargs)
    res = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    del input_ids, image_tensor, out
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


def infer_llava_med(model, proc, img_path, prompt, sys_p, temperature, top_p=0.9, do_sample=None, max_new_tokens=512):
    """Parameterized only -- do_sample=(TEMPERATURE>0) logic was already correct."""
    from llava.mm_utils import process_images, tokenizer_image_token
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    do_sample = resolve_do_sample(temperature, do_sample)
    tokenizer, image_processor, context_len = proc
    full_prompt = f'[INST] {sys_p}\n\n{DEFAULT_IMAGE_TOKEN}\n{prompt} [/INST]'
    input_ids = tokenizer_image_token(
        full_prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt'
    ).unsqueeze(0).to(model.device)
    attention_mask = torch.ones_like(input_ids)
    image = safe_load_image(img_path)
    image_tensor = process_images([image], image_processor, model.config)
    image_tensor = image_tensor.to(model.device, dtype=torch.float16)
    gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample)
    gen_kwargs.update(_sampling_kwargs(temperature, top_p, do_sample))
    with torch.no_grad():
        output_ids = model.generate(
            input_ids, attention_mask=attention_mask,
            images=image_tensor, image_sizes=[image.size],
            pad_token_id=tokenizer.eos_token_id, use_cache=True, **gen_kwargs,
        )
    if output_ids.shape[1] <= input_ids.shape[1]:
        res = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    else:
        res = tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
    del input_ids, attention_mask, image_tensor, output_ids
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'


PATCHED_INFER_FNS = {
    'qwen25vl': infer_qwen25vl,
    'llava16': infer_llava16,
    'chexagent': infer_chexagent,
    'huatuogpt': infer_huatuogpt,
    'llava_med': infer_llava_med,
}
