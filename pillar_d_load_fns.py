"""
LOAD_FNS for the 5 representative_subset.json models, extracted unchanged
from MedViHall_Phase3_Phase4_v4.ipynb (cells 21-23), with local_dir resolved
to where these checkpoints actually live on disk in this project:
  - qwen25vl, chexagent  -> ./models/<name>          (confirmed on disk)
  - llava_med, huatuogpt, llava16 -> D:/medvihall_models/<name>  (confirmed on disk)
"""
import sys
import subprocess
import inspect
from pathlib import Path

import torch
from transformers import (
    AutoProcessor, AutoTokenizer, AutoModelForCausalLM,
    LlavaNextProcessor, LlavaNextForConditionalGeneration,
    BitsAndBytesConfig,
)

SSD_PATH = Path('./models')
HDD_PATH = Path('D:/medvihall_models')

BNB_4BIT = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type='nf4',
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)

MODEL_PATHS = {
    'llava_med': HDD_PATH / 'llava-med-v1.5-mistral-7b',
    'qwen25vl':  SSD_PATH / 'Qwen2.5-VL-7B-Instruct',
    'chexagent': SSD_PATH / 'CheXagent-8b',
    'huatuogpt': HDD_PATH / 'HuatuoGPT-Vision-7B',
    'llava16':   HDD_PATH / 'llava-v1.6-mistral-7b-hf',
}


def vram_used():
    return torch.cuda.memory_allocated() / 1024 ** 3 if torch.cuda.is_available() else 0


def vram_free():
    return torch.cuda.mem_get_info()[0] / 1024 ** 3 if torch.cuda.is_available() else 0


def unload(model, proc):
    import gc
    try:
        del model, proc
    except Exception:
        pass
    gc.collect()
    if torch.cuda.is_available():
        try:
            torch.cuda.synchronize()
        except Exception:
            pass
        try:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        except Exception:
            pass
    print(f'  VRAM after unload: {vram_free():.1f} GB free')


def qwen_processor_kwargs():
    return dict(min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)


def _patch_forward_kwargs(cls):
    """LlavaMistralForCausalLM (llava_med) and LlavaQwen2ForCausalLM (huatuogpt)
    both ship forward() signatures written against transformers ~4.40 with no
    **kwargs. Newer transformers' generate() always feeds
    prepare_inputs_for_generation()'s dict (now including keys like
    cache_position) straight into forward(**model_inputs), which raises
    TypeError: forward() got an unexpected keyword argument 'cache_position'
    on the old signature. This was already fixed for huatuogpt in the
    original notebook; confirmed here (via Stage 0/Pillar D pilot testing)
    that llava_med hits the identical issue -- the transformers version was
    evidently upgraded (for the Stage 3 judge model) after the original
    Stage 1 run already completed llava_med's calls under an older version
    that didn't pass cache_position. Filter to only the kwargs the old
    forward() actually declares, same fix as huatuogpt's.

    functools.wraps matters here, not just style: generate()'s own
    _validate_model_kwargs() calls inspect.signature(model.forward) BEFORE
    ever invoking it, to reject kwargs it thinks forward() doesn't accept.
    A bare def patched_forward(self, *args, **kwargs) hides the real
    parameters from that check (raising "attention_mask not used by the
    model" even though the wrapped call accepts it) -- wraps() makes
    inspect.signature follow __wrapped__ back to the original signature."""
    import inspect
    import functools
    if getattr(cls, '_kwargs_patched', False):
        return
    orig_forward = cls.forward
    allowed = set(inspect.signature(orig_forward).parameters.keys())

    @functools.wraps(orig_forward)
    def patched_forward(self, *args, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if k in allowed}
        return orig_forward(self, *args, **kwargs)
    cls.forward = patched_forward
    cls._kwargs_patched = True


def load_llava_med():
    from llava.model import LlavaMistralForCausalLM
    from transformers import CLIPImageProcessor
    _patch_forward_kwargs(LlavaMistralForCausalLM)
    model_path = str(MODEL_PATHS['llava_med'])
    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
    )
    model = LlavaMistralForCausalLM.from_pretrained(
        model_path, quantization_config=bnb,
        device_map={'': 0}, torch_dtype=torch.float16, low_cpu_mem_usage=True,
    )
    model.get_vision_tower().load_model(device_map={'': 0})
    model.get_vision_tower().to(device='cuda', dtype=torch.float16)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
    tokenizer.pad_token = tokenizer.unk_token
    image_processor = CLIPImageProcessor.from_pretrained('openai/clip-vit-large-patch14-336')
    context_len = 2048
    print(f'  OK LLaVA-Med loaded | {vram_used():.1f} GB')
    return model, (tokenizer, image_processor, context_len)


def load_qwen25vl():
    from transformers import Qwen2_5_VLForConditionalGeneration
    p = str(MODEL_PATHS['qwen25vl'])
    try:
        proc = AutoProcessor.from_pretrained(p, **qwen_processor_kwargs())
    except TypeError:
        proc = AutoProcessor.from_pretrained(p)
    mdl = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval()
    print(f'  OK Qwen2.5-VL-7B loaded | {vram_used():.1f} GB')
    return mdl, proc


def load_chexagent():
    p = str(MODEL_PATHS['chexagent'])
    proc = AutoProcessor.from_pretrained(p, trust_remote_code=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto',
        torch_dtype=torch.bfloat16, trust_remote_code=True)
    mdl.eval()
    print(f'  OK CheXagent loaded | {vram_used():.1f} GB')
    return mdl, proc


def load_llava16():
    p = str(MODEL_PATHS['llava16'])
    proc = LlavaNextProcessor.from_pretrained(p)
    mdl = LlavaNextForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval()
    print(f'  OK LLaVA-1.6 loaded | {vram_used():.1f} GB')
    return mdl, proc


def _setup_huatuogpt_repo():
    import re
    repo_root = Path.cwd() / 'external' / 'HuatuoGPT-Vision'
    pkg_dir = repo_root / 'huatuo_llava'
    marker = repo_root / '.isolated'

    if not repo_root.exists():
        subprocess.run(
            ['git', 'clone', '--depth', '1',
             'https://github.com/FreedomIntelligence/HuatuoGPT-Vision.git', str(repo_root)],
            check=True,
        )
    if not marker.exists():
        src_dir = repo_root / 'llava'
        if src_dir.exists():
            src_dir.rename(pkg_dir)
        for py in repo_root.rglob('*.py'):
            text = py.read_text(encoding='utf-8')
            patched = re.sub(r'\bfrom llava\b', 'from huatuo_llava', text)
            patched = re.sub(r'\bimport llava\b', 'import huatuo_llava', patched)
            if patched != text:
                py.write_text(patched, encoding='utf-8')
        marker.write_text('ok', encoding='utf-8')
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def load_huatuogpt():
    _setup_huatuogpt_repo()
    from huatuo_llava.model.language_model.llava_qwen2 import LlavaQwen2ForCausalLM
    _patch_forward_kwargs(LlavaQwen2ForCausalLM)
    p = str(MODEL_PATHS['huatuogpt'])
    tokenizer = AutoTokenizer.from_pretrained(p)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    mdl, loading_info = LlavaQwen2ForCausalLM.from_pretrained(
        p, init_vision_encoder_from_ckpt=False, output_loading_info=True,
        quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    unexpected = loading_info.get('unexpected_keys', [])
    assert all('vision_tower' in k for k in unexpected), \
        f'Unexpected non-vision keys while loading HuatuoGPT-Vision: {unexpected}'
    vision_tower = mdl.get_vision_tower()
    if not vision_tower.is_loaded:
        vision_tower.vision_tower_name = 'openai/clip-vit-large-patch14-336'
        vision_tower.load_model()
    vision_tower.to(dtype=torch.bfloat16, device=mdl.device)
    mdl.eval()
    print(f'  OK HuatuoGPT-Vision-7B loaded | {vram_used():.1f} GB')
    return mdl, (tokenizer, vision_tower.image_processor)


LOAD_FNS = {
    'llava_med': load_llava_med,
    'qwen25vl': load_qwen25vl,
    'chexagent': load_chexagent,
    'huatuogpt': load_huatuogpt,
    'llava16': load_llava16,
}
