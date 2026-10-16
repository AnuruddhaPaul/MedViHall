r"""
test_llava_med.py  —  verified working on anaconda3 Python 3.12 / transformers 5.3 / torch 2.12+cu128
Run with: C:/Users/PC/anaconda3/python.exe test_llava_med.py

Prerequisites (one-time fixes applied to the installed llava package):
  1. pip install --no-deps git+https://github.com/haotian-liu/LLaVA.git
  2. llava_mistral.py forward() patched to accept cache_position=None (transformers 5.x compat)
     File: C:/Users/PC/anaconda3/Lib/site-packages/llava/model/language_model/llava_mistral.py
"""

import subprocess
import sys

print("=" * 60)
print("STEP 1: Ensuring llava package dependencies")
print(f"Python: {sys.executable}  ({sys.version.split()[0]})")
print("=" * 60)

def _pip(*args):
    subprocess.run([sys.executable, "-m", "pip", "install"] + list(args), check=True)

try:
    from llava.model import LlavaMistralForCausalLM  # noqa: F401
    print("llava package already installed.")
except ImportError:
    print("Installing llava (--no-deps) ...")
    _pip("--no-deps", "git+https://github.com/haotian-liu/LLaVA.git")

try:
    import shortuuid  # noqa: F401
    import einops     # noqa: F401
    print("shortuuid + einops already present.")
except ImportError:
    _pip("shortuuid", "einops")

print("\n" + "=" * 60)
print("STEP 2: Importing libraries")
print("=" * 60)

import glob
import traceback
import torch
from PIL import Image
from transformers import AutoTokenizer, BitsAndBytesConfig, CLIPImageProcessor
from llava.constants import DEFAULT_IMAGE_TOKEN, IMAGE_TOKEN_INDEX
from llava.mm_utils import process_images, tokenizer_image_token
from llava.model import LlavaMistralForCausalLM
import transformers

print(f"  torch        : {torch.__version__}")
print(f"  transformers : {transformers.__version__}")
print(f"  GPU          : {torch.cuda.get_device_name(0)}")
print(f"  VRAM total   : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

print("\n" + "=" * 60)
print("STEP 3: Finding test image")
print("=" * 60)

images = (
    glob.glob("./medvihall_data/**/*.jpg", recursive=True)
    + glob.glob("./medvihall_data/**/*.png", recursive=True)
)
if not images:
    raise FileNotFoundError("No .jpg or .png found under ./medvihall_data/")
img_path = images[0]
print(f"Using: {img_path}")

print("\n" + "=" * 60)
print("STEP 4: Loading model (BNB 4-bit / NF4)")
print("=" * 60)

MODEL_PATH = "./models/llava-med-v1.5-mistral-7b"

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = LlavaMistralForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_cfg,
    device_map={"": 0},
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)

# Manual vision tower load (required when llava was installed --no-deps)
model.get_vision_tower().load_model(device_map={"": 0})
model.get_vision_tower().to(device="cuda", dtype=torch.float16)
model.eval()
print(f"Model ready. VRAM allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

print("\n" + "=" * 60)
print("STEP 5: Loading tokenizer + CLIPImageProcessor")
print("=" * 60)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
tokenizer.pad_token = tokenizer.unk_token
print(f"Tokenizer OK | vocab_size={tokenizer.vocab_size} | pad={tokenizer.pad_token!r}")

image_processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
context_len = 2048
print("CLIPImageProcessor OK (openai/clip-vit-large-patch14-336)")

print("\n" + "=" * 60)
print("STEP 6: Inference")
print("=" * 60)

try:
    PROMPT = "[INST] You are a radiologist. " + DEFAULT_IMAGE_TOKEN + "\nDescribe this image in one sentence. [/INST]"

    input_ids = tokenizer_image_token(
        PROMPT, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt"
    ).unsqueeze(0).to("cuda")
    attention_mask = torch.ones_like(input_ids)

    image = Image.open(img_path).convert("RGB")
    image_tensor = process_images([image], image_processor, model.config)
    image_tensor = image_tensor.to("cuda", dtype=torch.float16)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            attention_mask=attention_mask,
            images=image_tensor,
            image_sizes=[image.size],
            max_new_tokens=100,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )

    # When inputs_embeds is used internally, generate() returns only new tokens.
    # output_ids.shape[1] < input_ids.shape[1] in that case → decode all of output_ids[0].
    if output_ids.shape[1] <= input_ids.shape[1]:
        response = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    else:
        response = tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True).strip()

    print("\n" + "=" * 60)
    print("RESPONSE:", response)
    print("=" * 60)

    if not response:
        print("WARNING: empty response")
        print("Raw token ids:", output_ids[0].tolist())

except Exception:
    traceback.print_exc()
    sys.exit(1)
