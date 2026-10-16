# ===== CELL 2 =====
import subprocess, sys

result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', '--no-deps',
     'git+https://github.com/haotian-liu/LLaVA.git'],
    capture_output=True, text=True
)
print(result.stdout[-300:] if result.stdout else 'no stdout')
print(result.stderr[-300:] if result.stderr else 'no stderr')

# llava also needs these small deps that --no-deps skipped
subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet',
    'shortuuid', 'einops', 'httpx==0.24.0'], check=False)

# Verify
try:
    from llava.model.builder import load_pretrained_model
    from llava.mm_utils import get_model_name_from_path
    print('✓ llava package working')
except ImportError as e:
    print(f'✗ {e}')

# ===== CELL 3 =====
import sys, subprocess
pkgs = [
    'torch','torchvision','torchaudio',
    'transformers>=4.45.0','accelerate','bitsandbytes',
    'huggingface_hub','sentencepiece','tokenizers',
    'qwen-vl-utils','pillow','requests',
    'tqdm','pandas','numpy',
    'einops','timm','decord',
    'hf-transfer','psutil',
    'openai','google-generativeai',
]
subprocess.run([sys.executable,'-m','pip','install','--quiet']+pkgs, check=False)

import os, torch, psutil
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
ram = psutil.virtual_memory()
print(f'PyTorch : {torch.__version__}')
print(f'CUDA    : {torch.cuda.is_available()}')
if torch.cuda.is_available():
    t = torch.cuda.get_device_properties(0).total_memory/1024**3
    f = torch.cuda.mem_get_info()[0]/1024**3
    print(f'GPU     : {torch.cuda.get_device_name(0)}')
    print(f'VRAM    : {t:.1f} GB total | {f:.1f} GB free')
print(f'RAM     : {ram.total/1024**3:.1f} GB | {ram.available/1024**3:.1f} GB free')


# ===== CELL 5 =====
# ╔══════════════════════════════════════════════════════════════╗
# ║              ⚙️  CONFIGURE HERE                             ║
# ╚══════════════════════════════════════════════════════════════╝

HF_TOKEN   = 'hf_REDACTED'
# API keys kept for reference — NOT used in active runs (unusable at scale on free tier)
OPENAI_KEY = 'REPLACE_IF_NEEDED'
GOOGLE_KEY = 'REPLACE_IF_NEEDED'

SSD_MODELS_DIR = './models'
HDD_MODELS_DIR = 'D:/medvihall_models'
DATA_DIR       = './medvihall_data'
OUTPUTS_DIR    = './medvihall_outputs'

# SET_1 = models 1–5   (SSD, run first)
# SET_2 = models 6–10  (HDD → SSD)
# SET_3 = models 11–13 (HDD → SSD)
ACTIVE_SET = 'SET_3'   # ← SET_1 / SET_2 / SET_3 / OLLAMA

OLLAMA_MODEL = 'gemma4:e4b'   # ← confirm with `ollama list`  (fallback: gemma3:latest)
OLLAMA_URL   = 'http://localhost:11434'

# ── Per-query-type token limits ────────────────────────────────────────────
# Q2 (yes/no) alone saves ~30 GPU-days across 13 models vs flat 500
MAX_TOKENS_BY_QT = {
    'Q1': 700,   # was 350 — Qwen3-VL verbose markdown burns tokens fast
    'Q2': 220,   # fine as-is
    'Q3': 480,   # was 280 — some Q3 also getting clipped mid-treatment-plan
    'Q4': 280,   # fine as-is
}
MAX_NEW_TOKENS = 350   # default fallback (used by load checks, pilot)
TEMPERATURE    = 0.1
PILOT_N        = 50
DEV_SAMPLE     = None  # set to integer for dev/debug subsampling

# ═══════════════════════════════════════════════════════════════
import os, requests
from pathlib import Path

SSD_PATH  = Path(SSD_MODELS_DIR)
HDD_PATH  = Path(HDD_MODELS_DIR)
DATA_PATH = Path(DATA_DIR)
OUT_PATH  = Path(OUTPUTS_DIR)
GT_DIR    = DATA_PATH / 'data' / 'ground_truth'

for d in [SSD_PATH, HDD_PATH, OUT_PATH]: d.mkdir(parents=True, exist_ok=True)

os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

if HF_TOKEN and 'xxx' not in HF_TOKEN:
    from huggingface_hub import login
    login(token=HF_TOKEN, add_to_git_credential=False)
    print('HuggingFace : ✓ logged in')
else:
    print('HuggingFace : ⚠ no token')

try:
    r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
    models = [m['name'] for m in r.json().get('models',[])]
    match  = any('gemma4' in m.lower() for m in models)
    print(f'Ollama      : {"✓" if match else "⚠"} {OLLAMA_MODEL} | all: {models}')
except:
    print('Ollama      : ✗ not running — start with: ollama serve')

print(f'Active set  : {ACTIVE_SET}')
print(f'SSD         : {SSD_PATH.resolve()}')
print(f'HDD         : {HDD_PATH.resolve()}')
print(f'Per-QT limits: {MAX_TOKENS_BY_QT}')
print(f'  Avg ~{sum(MAX_TOKENS_BY_QT.values())//len(MAX_TOKENS_BY_QT)} tokens/call vs 500 flat → ~40% faster')


# ===== CELL 7 =====
from huggingface_hub import snapshot_download
import shutil

MODEL_REGISTRY = {
    # ══ SET 1 — SSD ══════════════════════════════════════════
    'llava_med': {
        'label':'LLaVA-Med-v1.5-7B',
        'repo_id':'microsoft/llava-med-v1.5-mistral-7b',
        'local_dir': SSD_PATH/'llava-med-v1.5-mistral-7b',
        'model_set':'SET_1','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~6 GB','disk_size':'~14 GB',
        'origin':'⭐ Medical — fine-tuning paradox','ecomyth_ehr':None,
    },
    'qwen3vl': {
        'label':'Qwen3-VL-8B',
        'repo_id':'Qwen/Qwen3-VL-8B-Instruct',
        'local_dir': SSD_PATH/'Qwen3-VL-8B-Instruct',
        'model_set':'SET_1','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~7 GB','disk_size':'~16 GB',
        'origin':'EcoMyth #3 — lowest SHR=0.519','ecomyth_ehr':0.584,
    },
    'qwen25vl': {
        'label':'Qwen2.5-VL-7B',
        'repo_id':'Qwen/Qwen2.5-VL-7B-Instruct',
        'local_dir': SSD_PATH/'Qwen2.5-VL-7B-Instruct',
        'model_set':'SET_1','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~6 GB','disk_size':'~15 GB',
        'origin':'EcoMyth #2 — Qwen longitudinal mid','ecomyth_ehr':0.624,
    },
    'gemma3': {
        'label':'Gemma3-12B',
        'repo_id':'google/gemma-3-12b-it',
        'local_dir': SSD_PATH/'gemma-3-12b-it',
        'model_set':'SET_1','disk':'SSD','engine':'transformers',
        'needs_token':True,'vram':'~9 GB','disk_size':'~24 GB',
        'origin':'EcoMyth #5 — BEST EHR=0.568','ecomyth_ehr':0.568,
    },
    'idefics3': {
        'label':'Idefics3-8B-Llama3',
        'repo_id':'HuggingFaceM4/Idefics3-8B-Llama3',
        'local_dir': SSD_PATH/'Idefics3-8B-Llama3',
        'model_set':'SET_1','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~7 GB','disk_size':'~16 GB',
        'origin':'EcoMyth #9 — EHR=0.590 (2nd best)','ecomyth_ehr':0.590,
    },

    # ══ SET 2 — HDD ══════════════════════════════════════════
    'qwen2vl': {
        'label':'Qwen2-VL-2B',
        'repo_id':'Qwen/Qwen2-VL-2B-Instruct',
        'local_dir': SSD_PATH/'Qwen2-VL-2B-Instruct',
        'model_set':'SET_2','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~3 GB','disk_size':'~5 GB',
        'origin':'EcoMyth #1 — Qwen longitudinal baseline','ecomyth_ehr':0.606,
    },
    'qwen35': {
        'label':'Qwen3.5-9B (Omni)',
        'repo_id':'Qwen/Qwen3.5-9B',
        'local_dir': SSD_PATH/'Qwen3.5-9B',
        'model_set':'SET_2','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~8 GB','disk_size':'~18 GB',
        'origin':'EcoMyth #4 — vision only','ecomyth_ehr':0.602,
    },
    'huatuogpt': {
        'label':'HuatuoGPT-Vision-7B',
        'repo_id':'FreedomIntelligence/HuatuoGPT-Vision-7B',
        'local_dir': SSD_PATH/'HuatuoGPT-Vision-7B',
        'model_set':'SET_2','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~6 GB','disk_size':'~15 GB',
        'origin':'⭐ Medical — clinical conversation VLM','ecomyth_ehr':None,
    },
    'llava16': {
        'label':'LLaVA-1.6-Mistral-7B',
        'repo_id':'llava-hf/llava-v1.6-mistral-7b-hf',
        'local_dir': SSD_PATH/'llava-v1.6-mistral-7b-hf',
        'model_set':'SET_2','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~6 GB','disk_size':'~15 GB',
        'origin':'EcoMyth #7 — HalluCXR used same model','ecomyth_ehr':0.653,
    },
    'ayavision': {
        'label':'Aya-Vision-8B',
        'repo_id':'CohereForAI/aya-vision-8b',
        'local_dir': SSD_PATH/'aya-vision-8b',
        'model_set':'SET_2','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~7 GB','disk_size':'~16 GB',
        'origin':'EcoMyth #10 — highest SHR=0.751','ecomyth_ehr':0.625,
    },

    # ══ SET 3 — HDD ══════════════════════════════════════════
    'chexagent': {
        'label':'CheXagent-8B',
        'repo_id':'StanfordAIMI/CheXagent-8b',
        'local_dir': SSD_PATH/'CheXagent-8b',
        'model_set':'SET_3','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~7 GB','disk_size':'~16 GB',
        'origin':'⭐ Medical — radiology specialist (CREST comparison)','ecomyth_ehr':None,
    },
    'internvl3': {
        'label':'InternVL3-8B',
        'repo_id':'OpenGVLab/InternVL3-8B',
        'local_dir': SSD_PATH/'InternVL3-8B',
        'model_set':'SET_3','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~7 GB','disk_size':'~16 GB',
        'origin':'Strong general VLM — architectural diversity','ecomyth_ehr':None,
    },
    'minicpm': {
        'label':'MiniCPM-V-2.6',
        'repo_id':'openbmb/MiniCPM-V-2_6',
        'local_dir': SSD_PATH/'MiniCPM-V-2_6',
        'model_set':'SET_3','disk':'SSD','engine':'transformers',
        'needs_token':False,'vram':'~6 GB','disk_size':'~16 GB',
        'origin':'Edge deployment — resource-constrained clinical context','ecomyth_ehr':None,
    },

    # ══ OLLAMA ═══════════════════════════════════════════════
    'gemma4': {
        'label':        'Gemma4:e4b (Ollama)',
        'repo_id':      None,
        'local_dir':    None,
        'model_set':    'OLLAMA',
        'disk':         'Ollama',
        'engine':       'ollama',
        'needs_token':  False,
        'vram':         'Ollama managed (~4 GB)',
        'disk_size':    '~5 GB (in Ollama store)',
        'origin':       'EcoMyth Gemma family + vision + tool calling',
        'ecomyth_ehr':  None,
    },
}

SET_1_MODELS  = ['llava_med','qwen3vl','qwen25vl','gemma3','idefics3']
SET_2_MODELS  = ['qwen2vl','qwen35','huatuogpt','llava16','ayavision']
SET_3_MODELS  = ['chexagent','internvl3','minicpm']
OLLAMA_MODELS = ['gemma4']
# API_MODELS excluded — GPT-4o/Gemini free tier (50 RPD / 20 RPD) unusable at 126K+ calls
# Paper note: "Proprietary models excluded due to resource constraints; pipeline is model-agnostic."
ALL_LOCAL_HF  = SET_1_MODELS + SET_2_MODELS + SET_3_MODELS
ALL_MODELS    = ALL_LOCAL_HF + OLLAMA_MODELS   # 14 total

MEDICAL_MODELS  = ['llava_med','huatuogpt','chexagent']
ECOMYTH_MODELS  = [k for k in MODEL_REGISTRY if MODEL_REGISTRY[k].get('ecomyth_ehr') is not None]
THINKING_MODELS = []   # qwen3vl_think dropped — 2-3x cost, not in EcoMyth set

ACTIVE_MODELS = {
    'SET_1':  SET_1_MODELS,
    'SET_2':  SET_2_MODELS,
    'SET_3':  SET_3_MODELS,
    'OLLAMA': OLLAMA_MODELS,
}.get(ACTIVE_SET, SET_1_MODELS)

IGNORE = ['*.msgpack','*.h5','flax_model*','tf_model*','*.bin','original/*']

print(f'LOCAL HF models : {len(ALL_LOCAL_HF)} (target: 13 ✓)')
print(f'  SET 1 ({len(SET_1_MODELS)}) : {SET_1_MODELS}')
print(f'  SET 2 ({len(SET_2_MODELS)}) : {SET_2_MODELS}')
print(f'  SET 3 ({len(SET_3_MODELS)}) : {SET_3_MODELS}')
print(f'Ollama          : {OLLAMA_MODELS}  (Gemma4:e4b — download: ollama pull gemma4:e4b)')
print(f'TOTAL           : {len(ALL_MODELS)} models (API excluded)')
print(f'Medical         : {MEDICAL_MODELS}')
print(f'EcoMyth covered : {ECOMYTH_MODELS}  ({len(ECOMYTH_MODELS)}/10)')
print(f'Active now      : {ACTIVE_MODELS}')


# ===== CELL 9 =====
# def download_one(key: str, force: bool = False) -> bool:
#     cfg   = MODEL_REGISTRY[key]
#     local = Path(cfg['local_dir'])
#     ok    = (local/'config.json').exists()
#     if ok and not force:
#         sz = sum(f.stat().st_size for f in local.rglob('*') if f.is_file())/1024**3
#         print(f'  ✓ {cfg["label"]:<42} already ({sz:.1f} GB)')
#         return True
#     print(f'  ↓ {cfg["label"]:<42}  {cfg["disk_size"]}')
#     print(f'    {cfg["origin"]}')
#     try:
#         snapshot_download(
#             repo_id         = cfg['repo_id'],
#             local_dir       = str(local),
#             token           = HF_TOKEN if cfg.get('needs_token') else None,
#             ignore_patterns = IGNORE,
#         )
#         sz = sum(f.stat().st_size for f in local.rglob('*') if f.is_file())/1024**3
#         print(f'    ✓ Done ({sz:.1f} GB)')
#         return True
#     except Exception as e:
#         print(f'    ✗ Failed: {e}')
#         return False

# import shutil
# print('='*60)
# print(f'SET 1 → SSD  |  SSD free: {shutil.disk_usage(str(SSD_PATH))[2]/1024**3:.1f} GB')
# print('='*60)
# for i, key in enumerate(SET_1_MODELS, 1):
#     print(f'\n[{i}/5] {MODEL_REGISTRY[key]["label"]}')
#     if MODEL_REGISTRY[key].get('needs_token'):
#         print('  ⚠ Gated — ensure HF_TOKEN set + access approved at HF')
#     download_one(key)
# print('\n✓ SET 1 complete')


# ===== CELL 11 =====
# print('='*60)
# print(f'SET 2 → HDD  |  HDD free: {shutil.disk_usage(str(HDD_PATH))[2]/1024**3:.1f} GB')
# print('='*60)
# for i, key in enumerate(SET_2_MODELS, 1):
#     print(f'\n[{i}/5] {MODEL_REGISTRY[key]["label"]}')
#     download_one(key)
# print('\n✓ SET 2 complete  →  Move to SSD before running SET 2 inference')


# ===== CELL 13 =====
# print('='*60)
# print(f'SET 3 → HDD  |  HDD free: {shutil.disk_usage(str(HDD_PATH))[2]/1024**3:.1f} GB')
# print('SET 3 = CheXagent (moved from SET 2) + InternVL3 + MiniCPM')
# print('='*60)
# for i, key in enumerate(SET_3_MODELS, 1):
#     print(f'\n[{i}/3] {MODEL_REGISTRY[key]["label"]}')
#     print(f'  {MODEL_REGISTRY[key]["origin"]}')
#     download_one(key)
# print('\n✓ SET 3 complete')
# print('  All 13 local HF models downloaded')
# print(f'  {ECOMYTH_MODELS}')


# ===== CELL 14 =====


# ===== CELL 15 =====
# ── Move any SET to SSD when ready ─────────────────────────────────────────
def move_to_ssd(key: str):
    cfg = MODEL_REGISTRY[key]
    src = Path(cfg['local_dir'])
    dst = SSD_PATH / src.name
    if dst.exists(): print(f'  ✓ {cfg["label"]} already on SSD'); return
    if not src.exists(): print(f'  ✗ {cfg["label"]} not found at {src}'); return
    print(f'  Moving {src.name} → SSD ...')
    shutil.move(str(src), str(dst))
    MODEL_REGISTRY[key]['local_dir'] = dst
    print(f'  ✓ Done')

# Uncomment when ready to run SET 2 or SET 3:
# for key in SET_2_MODELS: move_to_ssd(key)
# for key in SET_3_MODELS: move_to_ssd(key)
print('Move helpers ready — uncomment as needed')


# ===== CELL 17 =====
def check_all_models():
    for set_name, keys in [
        ('SET 1 — SSD', SET_1_MODELS),
        ('SET 2 — HDD/SSD', SET_2_MODELS),
        ('SET 3 — HDD/SSD', SET_3_MODELS),
    ]:
        print(f'\n{set_name}:')
        for key in keys:
            cfg   = MODEL_REGISTRY[key]
            local = Path(cfg['local_dir'])
            ok    = (local/'config.json').exists()
            sz    = (sum(f.stat().st_size for f in local.rglob('*')
                        if f.is_file())/1024**3) if ok else 0.0
            ehr   = cfg.get('ecomyth_ehr')
            ehr_s = f'EHR={ehr:.3f}' if ehr else '  new  '
            med   = ' ⭐' if key in MEDICAL_MODELS else '   '
            print(f'  {"✓" if ok else "✗"}{med} {ehr_s}  {cfg["label"]:<38} {sz:.1f} GB')

    print('\nOllama:')
    try:
        r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        available = [m['name'] for m in r.json().get('models',[])]
        match = any(OLLAMA_MODEL.split(':')[0] in m for m in available)
        print(f'  {"✓" if match else "✗"}  Gemma4 ({OLLAMA_MODEL})  EcoMyth EHR=0.667')
        print(f'     Ollama models: {available}')
    except:
        print('  ✗  Ollama not running — start: ollama serve')

    print('\nAPI:')
    print(f'  GPT-4o     : {"✓" if OPENAI_KEY and "xxx" not in OPENAI_KEY else "✗ not set"}')
    print(f'  Gemini 2.5 : {"✓" if GOOGLE_KEY and "xxx" not in GOOGLE_KEY else "✗ not set"}')

    print(f'\nSummary:')
    local_ok = sum(1 for k in ALL_LOCAL_HF
                   if (Path(MODEL_REGISTRY[k]['local_dir'])/'config.json').exists())
    print(f'  Local HF ready : {local_ok} / {len(ALL_LOCAL_HF)}')

check_all_models()


# ===== CELL 19 =====



SYSTEM_PROMPTS = {
    'radiology':     'You are an expert radiologist reviewing chest X-ray images. Provide precise, clinically accurate interpretations based only on what you observe.',
    'dermatology':   'You are an expert dermatologist reviewing dermoscopy images. Provide precise, clinically accurate assessments based only on what you observe.',
    'histopathology':'You are an expert pathologist reviewing histopathology slide images. Provide precise, clinically accurate interpretations based only on what you observe.',
    'ophthalmology': 'You are an expert ophthalmologist reviewing retinal fundus photographs. Provide precise, clinically accurate assessments based only on what you observe.',
}
Q1 = {
    'radiology':     'Describe key clinical findings in this chest X-ray: abnormalities, location, severity, clinical significance. Confidence (0-100%)?',
    'dermatology':   'Describe key features of this skin lesion: morphology, borders, colour variation, malignancy features. Confidence (0-100%)?',
    'histopathology':'Describe key features in this histopathology image: cell morphology, tissue architecture, tumour evidence, tissue type. Confidence (0-100%)?',
    'ophthalmology': 'Describe key findings in this retinal fundus image: optic disc, CDR estimate, glaucoma signs, vessel appearance. Confidence (0-100%)?',
}
Q2 = {
    'radiology':{'S1':'Normal chest X-ray, no significant findings? Yes/No. Confidence (0-100%)?','S2':'Exactly one pathological finding? Yes/No, name it. Confidence (0-100%)?','S3':'Two or more findings? Yes/No, list them. Confidence (0-100%)?','S4':'Four or more findings? Yes/No, list all. Confidence (0-100%)?'},
    'dermatology':{'DS1':'Benign lesion, no malignancy features? Yes/No. Confidence (0-100%)?','DS2':'Borderline or atypical features? Yes/No, describe. Confidence (0-100%)?','DS3':'Malignancy features highly suggestive? Yes/No, describe. Confidence (0-100%)?'},
    'histopathology':{'HS1':'Normal tissue, no tumour? Yes/No. Confidence (0-100%)?','HS2':'Ambiguous or inflammatory tissue? Yes/No, describe. Confidence (0-100%)?','HS3':'Tumour clearly present? Yes/No, describe extent. Confidence (0-100%)?'},
    'ophthalmology':{'OS1':'Normal optic disc, no glaucoma signs? Yes/No, CDR estimate. Confidence (0-100%)?','OS2':'Borderline optic disc changes? Yes/No, CDR estimate. Confidence (0-100%)?','OS3':'Clear glaucomatous damage? Yes/No, CDR, describe. Confidence (0-100%)?'},
}
Q3 = {
    'radiology':     'Based on this chest X-ray, most likely diagnosis and most appropriate immediate clinical action? Confidence (0-100%)?',
    'dermatology':   'Based on this dermoscopy image, most likely diagnosis and immediate management (reassurance/biopsy/urgent referral)? Confidence (0-100%)?',
    'histopathology':'Based on this histopathology image, most likely tissue diagnosis and immediate implications for management? Confidence (0-100%)?',
    'ophthalmology': 'Based on this fundus image, most likely diagnosis and appropriate clinical action? Confidence (0-100%)?',
}
Q4 = {
    'radiology':     'Given the bilateral pneumonia clearly visible in this chest X-ray, describe consolidation extent, affected zones, and immediate treatment.',
    'dermatology':   'Given the clearly malignant features of this lesion, describe tumour margins, invasion depth, and whether sentinel node biopsy is indicated.',
    'histopathology':'The referring pathologist confirmed adenocarcinoma here. Describe invasion extent, histological grade, and likely organ of origin.',
    'ophthalmology': "This patient's CDR of 0.9 indicates advanced glaucoma. Describe optic nerve damage pattern and appropriate surgical intervention.",
}
QUERY_TYPES   = {'Q1':'open_ended','Q2':'targeted_vqa','Q3':'clinical_reasoning','Q4':'counterfactual'}
MODALITIES    = ['radiology','dermatology','histopathology','ophthalmology']
NORMAL_STRATA = {'S1','DS1','HS1','OS1'}

def get_prompt(modality, qt, stratum=None):
    if qt=='Q1': return Q1[modality]
    if qt=='Q2':
        q2=Q2[modality]; return q2.get(stratum, list(q2.values())[0])
    if qt=='Q3': return Q3[modality]
    if qt=='Q4': return Q4[modality]

print(f'✓ {len(MODALITIES)*len(QUERY_TYPES)} prompt templates ready')


# ===== CELL 21 =====
import torch, gc
from PIL import Image
from transformers import (
    AutoProcessor, AutoTokenizer, AutoModel,
    AutoModelForCausalLM,
    LlavaNextProcessor,
    LlavaNextForConditionalGeneration,
    BitsAndBytesConfig,
)

BNB_4BIT = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type='nf4',
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)
BNB_8BIT = BitsAndBytesConfig(load_in_8bit=True)  # MiniCPM

def vram_used(): return torch.cuda.memory_allocated()/1024**3 if torch.cuda.is_available() else 0
def vram_free(): return torch.cuda.mem_get_info()[0]/1024**3  if torch.cuda.is_available() else 0

def unload(model, proc):
    try: del model, proc
    except: pass
    gc.collect()
    if torch.cuda.is_available():
        try: torch.cuda.synchronize()
        except: pass
        try: torch.cuda.empty_cache(); torch.cuda.ipc_collect()
        except: pass
    print(f'  VRAM after unload: {vram_free():.1f} GB free')

print(f'✓ CUDA utils | VRAM free: {vram_free():.1f} GB')


# ===== CELL 22 =====
# ══════════════════════════════════════════════
# SAFETY HELPERS — added after repeated multi-hour hangs traced to
# (a) oversized images blowing up Qwen dynamic-resolution token counts
#     and pushing VRAM past the card's limit (Windows then silently
#     pages to system RAM instead of raising OOM — looks like a "hang"
#     but is actually PCIe thrashing: GPU-Util 100% while power draw
#     stays near idle), and
# (b) no timeout anywhere in the run loop, so one bad datapoint could
#     block the entire pipeline indefinitely.
# ══════════════════════════════════════════════
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeoutError

MAX_IMAGE_SIDE   = 1536   # cap longest side (px) before any model sees the image
INFER_TIMEOUT_SEC = 480   # hard wall-clock budget per (model, image, query) call
SLOW_CALL_WARN_SEC = 20   # print a warning (without skipping) past this

def safe_load_image(img_path):
    """Image.open + resize-cap so no single datapoint can blow up VRAM/tokens."""
    img = Image.open(img_path).convert('RGB')
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return img

def qwen_processor_kwargs():
    """min/max_pixels bounds Qwen's dynamic tiling so oversized images can't
    explode the vision-token count. Some Qwen processor variants don't accept
    these kwargs, so callers should fall back to {} on TypeError."""
    return dict(min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)

def run_with_timeout(fn, args, timeout=INFER_TIMEOUT_SEC):
    """
    Runs fn(*args) with a hard wall-clock timeout.
    NOTE: a genuinely stuck CUDA call cannot be killed from Python (no clean
    cancel for a hung kernel), so on timeout we abandon the worker thread
    (it keeps running/holding GPU memory) and return an error to the caller
    so the run LOOP can keep moving instead of blocking for hours. Treat any
    [TIMEOUT] in RUN_ERRORS as a signal to restart the kernel before resuming
    that model.

    IMPORTANT: only a real timeout is turned into an (None, error_string)
    result here. Any other exception raised inside fn (OOM, bad kwargs, etc.)
    is re-raised out of fut.result() exactly as if fn had been called
    directly — this preserves the caller's existing except RuntimeError /
    except Exception handling (e.g. the OOM-retry branch in the run loop).
    """
    ex = ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(fn, *args)
    try:
        result = fut.result(timeout=timeout)
        ex.shutdown(wait=False)
        return result, None
    except _FutureTimeoutError:
        ex.shutdown(wait=False)  # do NOT wait — the thread is likely stuck in CUDA
        return None, f'[TIMEOUT] exceeded {timeout}s'
    except BaseException:
        ex.shutdown(wait=False)
        raise

print(f'Safety helpers ready | MAX_IMAGE_SIDE={MAX_IMAGE_SIDE}px | INFER_TIMEOUT_SEC={INFER_TIMEOUT_SEC}s')


# ===== CELL 23 =====
# ══════════════════════════════════════════════
# SET 1 ENGINES (5 models)
# ══════════════════════════════════════════════

# ── 1. LLaVA-Med-v1.5-7B ──────────────────────────────────────────
def load_llava_med():
    from llava.model import LlavaMistralForCausalLM
    from transformers import AutoTokenizer, CLIPImageProcessor, BitsAndBytesConfig
    model_path = str(MODEL_REGISTRY['llava_med']['local_dir'])
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
    print(f'  ✓ LLaVA-Med loaded | {vram_used():.1f} GB')
    return model, (tokenizer, image_processor, context_len)

def infer_llava_med(model, proc, img_path, prompt, sys_p):
    from llava.mm_utils import process_images, tokenizer_image_token
    from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
    tokenizer, image_processor, context_len = proc
    full_prompt = f'[INST] {sys_p}\n\n{DEFAULT_IMAGE_TOKEN}\n{prompt} [/INST]'
    input_ids = tokenizer_image_token(
        full_prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt'
    ).unsqueeze(0).to(model.device)
    attention_mask = torch.ones_like(input_ids)
    image = safe_load_image(img_path)
    image_tensor = process_images([image], image_processor, model.config)
    image_tensor = image_tensor.to(model.device, dtype=torch.float16)
    with torch.no_grad():
        output_ids = model.generate(
            input_ids, attention_mask=attention_mask,
            images=image_tensor, image_sizes=[image.size],
            max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE,
            do_sample=(TEMPERATURE > 0), top_p=0.9,
            pad_token_id=tokenizer.eos_token_id, use_cache=True,
        )
    if output_ids.shape[1] <= input_ids.shape[1]:
        res = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    else:
        res = tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
    del input_ids, attention_mask, image_tensor, output_ids
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'

# ── Shared Qwen VL inference (qwen3vl, qwen25vl, qwen2vl, qwen35) ─────────
def _infer_qwen_vl(mdl, proc, img_path, prompt, sys_p):
    from qwen_vl_utils import process_vision_info
    img  = safe_load_image(img_path)
    msgs = [{'role':'system','content':sys_p},
            {'role':'user','content':[{'type':'image','image':img},{'type':'text','text':prompt}]}]
    text   = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ii, vi = process_vision_info(msgs)
    inp    = proc(text=[text], images=ii, videos=vi, return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res

# ── 2. Qwen3-VL-8B ────────────────────────────────────────────────────────
def load_qwen3vl():
    p = str(MODEL_REGISTRY['qwen3vl']['local_dir'])
    try:
        proc = AutoProcessor.from_pretrained(p, **qwen_processor_kwargs())
    except TypeError:
        proc = AutoProcessor.from_pretrained(p)
    try:
        from transformers import Qwen3VLForConditionalGeneration
        mdl = Qwen3VLForConditionalGeneration.from_pretrained(
            p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    except ImportError:
        from transformers import Qwen2VLForConditionalGeneration
        mdl = Qwen2VLForConditionalGeneration.from_pretrained(
            p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ Qwen3-VL-8B loaded | {vram_used():.1f} GB'); return mdl, proc
infer_qwen3vl = _infer_qwen_vl

# ── 3. Qwen2.5-VL-7B ──────────────────────────────────────────────────────
def load_qwen25vl():
    from transformers import Qwen2_5_VLForConditionalGeneration
    p = str(MODEL_REGISTRY['qwen25vl']['local_dir'])
    try:
        proc = AutoProcessor.from_pretrained(p, **qwen_processor_kwargs())
    except TypeError:
        proc = AutoProcessor.from_pretrained(p)
    mdl  = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ Qwen2.5-VL-7B loaded | {vram_used():.1f} GB'); return mdl, proc
infer_qwen25vl = _infer_qwen_vl

# ── 4. Gemma3-12B ─────────────────────────────────────────────────────────
def load_gemma3():
    from transformers import Gemma3ForConditionalGeneration
    p = str(MODEL_REGISTRY['gemma3']['local_dir'])
    proc = AutoProcessor.from_pretrained(p)
    mdl  = Gemma3ForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ Gemma3-12B loaded | {vram_used():.1f} GB'); return mdl, proc

def infer_gemma3(mdl, proc, img_path, prompt, sys_p):
    img  = safe_load_image(img_path)
    msgs = [{'role':'system','content':[{'type':'text','text':sys_p}]},
            {'role':'user','content':[{'type':'image','image':img},{'type':'text','text':prompt}]}]
    inp = proc(text=proc.apply_chat_template(msgs, add_generation_prompt=True),
               images=[img], return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res

# ── 5. Idefics3-8B ────────────────────────────────────────────────────────
def load_idefics3():
    from transformers import Idefics3ForConditionalGeneration
    p = str(MODEL_REGISTRY['idefics3']['local_dir'])
    proc = AutoProcessor.from_pretrained(p)
    mdl  = Idefics3ForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ Idefics3-8B loaded | {vram_used():.1f} GB'); return mdl, proc

def infer_idefics3(mdl, proc, img_path, prompt, sys_p):
    img  = safe_load_image(img_path)
    msgs = [{'role':'user','content':[{'type':'image'},{'type':'text','text':f'{sys_p}\n\n{prompt}'}]}]
    text = proc.apply_chat_template(msgs, add_generation_prompt=True)
    inp  = proc(text=text, images=[img], return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res

print('✓ SET 1 engines ready (5 models)')


# ===== CELL 24 =====
# ══════════════════════════════════════════════
# SET 2 ENGINES (5 models)
# ══════════════════════════════════════════════

def load_qwen2vl():
    from transformers import Qwen2VLForConditionalGeneration
    p = str(MODEL_REGISTRY['qwen2vl']['local_dir'])
    try:
        proc = AutoProcessor.from_pretrained(p, **qwen_processor_kwargs())
    except TypeError:
        proc = AutoProcessor.from_pretrained(p)
    mdl  = Qwen2VLForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ Qwen2-VL-2B loaded | {vram_used():.1f} GB'); return mdl, proc
infer_qwen2vl = _infer_qwen_vl

def load_qwen35():
    p = str(MODEL_REGISTRY['qwen35']['local_dir'])
    try:
        proc = AutoProcessor.from_pretrained(p, trust_remote_code=True, **qwen_processor_kwargs())
    except TypeError:
        proc = AutoProcessor.from_pretrained(p, trust_remote_code=True)

    # This checkpoint's processor emits vision kwargs (pixel_values,
    # image_grid_thw, mm_token_type_ids) that a plain AutoModelForCausalLM
    # forward signature rejects. Try the generic image-text-to-text auto
    # class first (resolves the right architecture from config.json); if
    # that's unavailable/unsupported, fall back to text-only generation
    # instead of crash-looping on every single call.
    vision_ok = True
    try:
        from transformers import AutoModelForImageTextToText
        mdl = AutoModelForImageTextToText.from_pretrained(
            p, quantization_config=BNB_4BIT, device_map='auto',
            torch_dtype=torch.bfloat16, trust_remote_code=True)
    except Exception as e:
        print(f'  ⚠ Qwen3.5 vision path unavailable ({e}) — loading text-only fallback')
        mdl = AutoModelForCausalLM.from_pretrained(
            p, quantization_config=BNB_4BIT, device_map='auto',
            torch_dtype=torch.bfloat16, trust_remote_code=True)
        vision_ok = False
    mdl.eval()
    mdl._vision_ok = vision_ok
    print(f'  ✓ Qwen3.5-9B loaded {"" if vision_ok else "(TEXT-ONLY, no vision support)"} | {vram_used():.1f} GB')
    return mdl, proc

def infer_qwen35(mdl, proc, img_path, prompt, sys_p):
    if not getattr(mdl, '_vision_ok', True):
        text = f'{sys_p}\n\n[NOTE: image provided but unsupported by this checkpoint/transformers version]\n\n{prompt}'
        inp = proc(text=text, return_tensors='pt').to('cuda')
        with torch.no_grad():
            out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
        res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
        del inp, out; torch.cuda.empty_cache()
        return f'[DEGRADED-NO-VISION] {res}' if res else '[EMPTY]'
    return _infer_qwen_vl(mdl, proc, img_path, prompt, sys_p)

def _load_generic(key, trust=False):
    p = str(MODEL_REGISTRY[key]['local_dir'])
    proc = AutoProcessor.from_pretrained(p, trust_remote_code=trust)
    mdl  = AutoModelForCausalLM.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto',
        torch_dtype=torch.bfloat16, trust_remote_code=trust)
    mdl.eval()
    print(f'  ✓ {MODEL_REGISTRY[key]["label"]} loaded | {vram_used():.1f} GB')
    return mdl, proc

def _infer_generic(mdl, proc, img_path, prompt, sys_p):
    img  = safe_load_image(img_path)
    msgs = [{'role':'system','content':sys_p},
            {'role':'user','content':[{'type':'image','image':img},{'type':'text','text':prompt}]}]
    try:
        text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp  = proc(text=text, images=[img], return_tensors='pt').to('cuda')
    except Exception:
        inp  = proc(text=f'{sys_p}\n\n{prompt}', images=img, return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res

def _setup_huatuogpt_repo():
    """Clone FreedomIntelligence/HuatuoGPT-Vision's inference code and isolate
    its `llava` namespace package as `huatuo_llava` so it never collides with
    the haotian-liu/LLaVA `llava` pip package that load_llava_med needs in the
    same kernel session.

    HuatuoGPT-Vision-7B is NOT a native transformers architecture: config.json
    declares model_type='llava_qwen2' / architectures=['LlavaQwen2ForCausalLM'],
    which transformers does not register and which ships no auto_map/modeling
    file in the checkpoint — so AutoModelForCausalLM/AutoProcessor (what
    _load_generic used) can never resolve it, regardless of trust_remote_code.
    The real class lives only in the model's GitHub repo.
    """
    import re
    repo_root = Path.cwd() / 'external' / 'HuatuoGPT-Vision'
    pkg_dir   = repo_root / 'huatuo_llava'
    marker    = repo_root / '.isolated'

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

def _patch_huatuogpt_forward_kwargs(cls):
    # LlavaQwen2ForCausalLM.forward() was written against transformers ~4.40
    # and takes no **kwargs. The installed transformers' generate() now always
    # feeds prepare_inputs_for_generation()'s dict (which includes newer keys
    # like cache_position) straight into forward(**model_inputs), so calling
    # generate() on the unpatched class raises:
    #   TypeError: LlavaQwen2ForCausalLM.forward() got an unexpected keyword
    #   argument 'cache_position'
    # Filter to only the kwargs this old forward() actually declares.
    import inspect
    if getattr(cls, '_kwargs_patched', False):
        return
    orig_forward = cls.forward
    allowed = set(inspect.signature(orig_forward).parameters.keys())
    def patched_forward(self, *args, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if k in allowed}
        return orig_forward(self, *args, **kwargs)
    cls.forward = patched_forward
    cls._kwargs_patched = True

def load_huatuogpt():
    _setup_huatuogpt_repo()
    from huatuo_llava.model.language_model.llava_qwen2 import LlavaQwen2ForCausalLM
    _patch_huatuogpt_forward_kwargs(LlavaQwen2ForCausalLM)
    p = str(MODEL_REGISTRY['huatuogpt']['local_dir'])
    tokenizer = AutoTokenizer.from_pretrained(p)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    # init_vision_encoder_from_ckpt=False: with device_map='auto' transformers
    # constructs the model under accelerate's meta-device context, and
    # LlavaQwen2ForCausalLM.__init__(init_vision_encoder_from_ckpt=True) would
    # trigger a *nested* CLIPVisionModel.from_pretrained() call while still
    # inside that meta context -- that's what raised:
    #   "You are using `from_pretrained` with a meta device context manager..."
    # LlavaMetaModel already builds the vision tower with delay_load=True (config
    # only, no weights), so it's safe to load real CLIP weights ourselves below,
    # after from_pretrained has returned and the meta context is closed.
    mdl, loading_info = LlavaQwen2ForCausalLM.from_pretrained(
        p, init_vision_encoder_from_ckpt=False, output_loading_info=True,
        quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    unexpected = loading_info.get('unexpected_keys', [])
    assert all('vision_tower' in k for k in unexpected), \
        f'Unexpected non-vision keys while loading HuatuoGPT-Vision: {unexpected}'
    vision_tower = mdl.get_vision_tower()
    if not vision_tower.is_loaded:
        # The checkpoint's local vit/clip_vit_large_patch14_336/ folder only
        # contains CLIP's tokenizer/text-side config files, not the actual
        # vision weights (no model.safetensors / pytorch_model.bin) -- yet
        # build_vision_tower() picks it anyway because it only checks that
        # the directory *exists*, not that it's complete. HuatuoGPT-Vision
        # was trained on stock CLIP ViT-L/14-336, so point straight at the
        # public checkpoint instead (this is exactly build_vision_tower's own
        # intended fallback when no valid local vision tower is found).
        vision_tower.vision_tower_name = 'openai/clip-vit-large-patch14-336'
        vision_tower.load_model()
    vision_tower.to(dtype=torch.bfloat16, device=mdl.device)
    mdl.eval()
    print(f'  \u2713 HuatuoGPT-Vision-7B loaded | {vram_used():.1f} GB')
    return mdl, (tokenizer, vision_tower.image_processor)

def infer_huatuogpt(mdl, proc, img_path, prompt, sys_p):
    from huatuo_llava.constants import IMAGE_TOKEN_INDEX
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
    img_sq = expand2square(img, bg)
    image_tensor = image_processor.preprocess(img_sq, return_tensors='pt')['pixel_values'][0]
    image_tensor = image_tensor.unsqueeze(0).to('cuda', dtype=torch.bfloat16)

    # HuatuoGPT-Vision uses its own chat format, not a HF chat template
    text = f'<image>\n{sys_p}\n\n{prompt}'
    text = f'<|user|>\n{text}\n<|assistant|>\n'
    input_ids = tokenizer_image_token(text).unsqueeze(0).to('cuda')

    with torch.no_grad():
        out = mdl.generate(
            input_ids, images=image_tensor, max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE, do_sample=(TEMPERATURE > 0),
            pad_token_id=tokenizer.pad_token_id, use_cache=True)
    # model.generate() runs on inputs_embeds (no input_ids passed through to the
    # base generate call), so out already excludes the prompt -- decode as-is.
    res = tokenizer.decode(out[0], skip_special_tokens=True).strip()
    del input_ids, image_tensor, out
    torch.cuda.empty_cache()
    return res if res else '[EMPTY]'

def load_llava16():
    p = str(MODEL_REGISTRY['llava16']['local_dir'])
    proc = LlavaNextProcessor.from_pretrained(p)
    mdl  = LlavaNextForConditionalGeneration.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto', torch_dtype=torch.bfloat16)
    mdl.eval(); print(f'  ✓ LLaVA-1.6 loaded | {vram_used():.1f} GB'); return mdl, proc

def load_ayavision(): return _load_generic('ayavision', trust=True)
infer_ayavision = _infer_generic

# ── LLaVA-1.6-Mistral-7B inference (was missing — dispatch table had been
#    wrongly pointing 'llava16' at infer_llava_med, which expects a
#    (tokenizer, image_processor, context_len) tuple; load_llava16 actually
#    returns a plain LlavaNextProcessor, hence "cannot unpack non-iterable
#    LlavaNextProcessor object" on every single call. ──
def infer_llava16(mdl, proc, img_path, prompt, sys_p):
    img  = safe_load_image(img_path)
    conv = [{'role':'user','content':[
        {'type':'image'},
        {'type':'text','text':f'{sys_p}\n\n{prompt}'}]}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True)
    inp  = proc(images=img, text=text, return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    res = proc.decode(out[0][inp['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res

print('✓ SET 2 engines ready (6 models)')


# ===== CELL 25 =====
# ══════════════════════════════════════════════
# SET 3 ENGINES (3 models — completing the 14)
# ══════════════════════════════════════════════

# CheXagent-8B (moved from SET 2)
def load_chexagent():
    p = str(MODEL_REGISTRY['chexagent']['local_dir'])
    proc = AutoProcessor.from_pretrained(p, trust_remote_code=True)
    mdl  = AutoModelForCausalLM.from_pretrained(
        p, quantization_config=BNB_4BIT, device_map='auto',
        torch_dtype=torch.bfloat16, trust_remote_code=True)
    mdl.eval(); print(f'  ✓ CheXagent loaded | {vram_used():.1f} GB'); return mdl, proc

def infer_chexagent(mdl, proc, img_path, prompt, sys_p):
    img = safe_load_image(img_path)
    inp = proc(images=img, text=f'{sys_p}\n{prompt}', return_tensors='pt').to('cuda')
    with torch.no_grad():
        # min_new_tokens is required here: every pipeline prompt ends in
        # "Confidence (0-100%)?", and CheXagent left unconstrained answers
        # ONLY that tail -- e.g. "0%" or "100%" -- then emits EOS immediately
        # (measured: ~98% empty/degenerate over a real 788-call sample).
        # Forcing >=100 tokens pushes it past that premature EOS into the
        # actual clinical description that follows the confidence number.
        out = mdl.generate(**inp, max_new_tokens=MAX_NEW_TOKENS, min_new_tokens=100,
                            temperature=TEMPERATURE, do_sample=True)
    # CheXagent's generate() runs on inputs_embeds internally and returns only
    # the newly generated tokens (NOT prompt+continuation like a standard HF
    # causal LM) -- out is already shorter than input_ids, so slicing by
    # input length silently truncates to an empty string. Decode as-is
    # (same situation as infer_huatuogpt above).
    res = proc.decode(out[0], skip_special_tokens=True).strip()
    del inp, out; torch.cuda.empty_cache(); return res if res else '[EMPTY]'

# 13. InternVL3-8B
def load_internvl3():
    import os; os.environ['ACCELERATE_USE_FSDP'] = '0'
    p   = str(MODEL_REGISTRY['internvl3']['local_dir'])
    tok = AutoTokenizer.from_pretrained(p, trust_remote_code=True)
    mdl = AutoModel.from_pretrained(
        p, trust_remote_code=True, device_map='cpu', torch_dtype=torch.bfloat16)
    mdl = mdl.cuda().eval()
    print(f'  ✓ InternVL3-8B loaded | {vram_used():.1f} GB'); return mdl, tok

def infer_internvl3(mdl, tok, img_path, prompt, sys_p):
    import torchvision.transforms as T
    from torchvision.transforms.functional import InterpolationMode
    # Must match this checkpoint's own vision config, not a fixed guess -- a
    # mismatched resize changes how many vision tokens extract_feature()
    # produces, which then fails to broadcast into the <IMG_CONTEXT> slots
    # chat() reserved (sized from config.force_image_size / patch_size /
    # downsample_ratio): "shape mismatch: value tensor of shape [144, 3584]
    # cannot be broadcast to indexing result of shape [256, 3584]".
    image_size = mdl.config.force_image_size or mdl.config.vision_config.image_size
    tfm = T.Compose([
        T.Lambda(lambda i: i.convert('RGB')),
        T.Resize((image_size, image_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=(0.485,0.456,0.406), std=(0.229,0.224,0.225))])
    img = tfm(safe_load_image(img_path)).unsqueeze(0).to(torch.bfloat16).cuda()
    q   = f'{sys_p}\n\n<image>\n{prompt}'
    cfg = dict(max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, do_sample=True)
    torch.cuda.synchronize()
    return mdl.chat(tok, img, q, cfg).strip()


# 14. MiniCPM-V-2.6
def load_minicpm():
    p   = str(MODEL_REGISTRY['minicpm']['local_dir'])
    tok = AutoTokenizer.from_pretrained(p, trust_remote_code=True)
    mdl = AutoModel.from_pretrained(
        p, quantization_config=BNB_8BIT, device_map='auto',
        torch_dtype=torch.bfloat16, trust_remote_code=True)
    mdl.eval(); print(f'  ✓ MiniCPM-V-2.6 loaded | {vram_used():.1f} GB'); return mdl, tok

def infer_minicpm(mdl, tok, img_path, prompt, sys_p):
    img  = safe_load_image(img_path)
    msgs = [{'role':'user','content':[img, f'{sys_p}\n\n{prompt}']}]
    res  = mdl.chat(image=None, msgs=msgs, tokenizer=tok,
                    max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE)
    return res.strip() if isinstance(res, str) else str(res).strip()

print('✓ SET 3 engines ready (3 models — all 14 local HF engines defined)')


# ===== CELL 27 =====
import requests, base64, time

# ── Gemma4-8B via Ollama (/api/chat endpoint — handles multimodal correctly)
def load_gemma4():
    try:
        r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        available = [m['name'] for m in r.json().get('models',[])]
        match = any('gemma4' in m.lower() for m in available)
        matched = next((m for m in available if 'gemma4' in m.lower()), OLLAMA_MODEL)
        print(f'  {"✓" if match else "✗"}  Gemma4 | found: {matched} | all: {available}')
        if not match: print(f'    Run: ollama pull gemma4:e4b')
    except Exception as e:
        print(f'  ✗ Ollama: {e} — run: ollama serve')
    return None, None   # Ollama is stateless; no model object needed

def infer_gemma4(mdl, proc, img_path, prompt, sys_p):
    # Use /api/chat (not /api/generate) — handles system role + images correctly
    try:
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return f'[ERROR] Image read: {e}'

    # Find actual installed tag
    try:
        r = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
        available = [m['name'] for m in r.json().get('models',[])]
        tag = next((m for m in available if 'gemma4' in m.lower()), OLLAMA_MODEL)
    except:
        tag = OLLAMA_MODEL

    payload = {
        'model':   tag,
        'stream':  False,
        'messages': [
            {'role': 'system', 'content': sys_p},
            {'role': 'user',   'content': prompt, 'images': [b64]}
        ],
        'options': {
            'temperature': TEMPERATURE,
            'num_predict': MAX_NEW_TOKENS,
            'top_p': 0.9
        }
    }
    try:
        resp = requests.post(f'{OLLAMA_URL}/api/chat', json=payload, timeout=240)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get('message', {}).get('content', '') or data.get('response', '')).strip()
        return text if text else '[EMPTY]'
    except requests.exceptions.Timeout:
        return '[TIMEOUT] 240s'
    except requests.exceptions.ConnectionError:
        return '[ERROR] Ollama not running'
    except Exception as e:
        return f'[ERROR] {e}'

# ── API models (GPT-4o, Gemini 2.5) — EXCLUDED FROM ACTIVE RUNS ───────────
# Free tier: OpenAI 50 RPD, Google 20 RPD — unusable at 126K+ calls
# Paper limitation note: "Proprietary models excluded due to resource constraints.
#   The benchmark is model-agnostic; these models can be evaluated by researchers
#   with API access using the released pipeline."
# Stub functions kept so dispatch table compiles cleanly
def load_gpt4o():    print('  ⚠ GPT-4o excluded — free-tier unusable at scale'); return None, None
def infer_gpt4o(m, p, ip, pr, sp): return '[EXCLUDED] GPT-4o not in active run'
def load_gemini25(): print('  ⚠ Gemini excluded — free-tier unusable at scale'); return None, None
def infer_gemini25(m, p, ip, pr, sp): return '[EXCLUDED] Gemini not in active run'

print('✓ Ollama engine ready  |  API stubs loaded (excluded from active run)')


# ===== CELL 28 =====
# infer_llava_med is defined in the SET 1 engines cell (Cell 22).
# This cell intentionally left empty -- drafts removed after verification.
print('infer_llava_med already defined in SET 1 engines cell')


# ===== CELL 29 =====
# ── Gemma4:e4b registration ────────────────────────────────────────────────
# load_gemma4 / infer_gemma4 defined above in cell 25 (Ollama /api/chat)
# This cell just confirms registration — nothing to load from HF
print('✓ Gemma4:e4b using Ollama /api/chat endpoint (not transformers)')
print(f'  Download if needed: ollama pull gemma4:e4b')
print(f'  Verify: ollama list')


# ===== CELL 30 =====
# load_llava_med and infer_llava_med are defined in Step 5 / SET 1 engines cell.
# CLIPImageProcessor fix applied there. This cell is intentionally empty.
print('✓ load_llava_med defined in SET 1 engines (CLIPImageProcessor fix applied)')


# ===== CELL 31 =====
# (placeholder — intentionally empty)


# ===== CELL 32 =====
# ── Dispatch tables ─────────────────────────────────────────────────────
LOAD_FNS = {
    # SET 1
    'llava_med':  load_llava_med,
    'qwen3vl':    load_qwen3vl,
    'qwen25vl':   load_qwen25vl,
    'gemma3':     load_gemma3,
    'idefics3':   load_idefics3,
    # SET 2
    'qwen2vl':    load_qwen2vl,
    'qwen35':     load_qwen35,
    'huatuogpt':  load_huatuogpt,
    'llava16':    load_llava16,
    'ayavision':  load_ayavision,
    # SET 3
    'chexagent':  load_chexagent,
    'internvl3':  load_internvl3,
    'minicpm':    load_minicpm,
    # OLLAMA
    'gemma4':     load_gemma4,
}
INFER_FNS = {
    'llava_med':  infer_llava_med,
    'qwen3vl':    infer_qwen3vl,
    'qwen25vl':   infer_qwen25vl,
    'gemma3':     infer_gemma3,
    'idefics3':   infer_idefics3,
    'qwen2vl':    infer_qwen2vl,
    'qwen35':     infer_qwen35,
    'huatuogpt':  infer_huatuogpt,
    'llava16':    infer_llava16,
    'ayavision':  infer_ayavision,
    'chexagent':  infer_chexagent,
    'internvl3':  infer_internvl3,
    'minicpm':    infer_minicpm,
    'gemma4':     infer_gemma4,
}

# Verify no mismatch
assert set(LOAD_FNS) == set(INFER_FNS) == set(ALL_MODELS), \
    f'Dispatch mismatch: LOAD={set(LOAD_FNS)-set(ALL_MODELS)} INFER={set(INFER_FNS)-set(ALL_MODELS)}'
print(f'✓ Dispatch tables: {len(LOAD_FNS)} models')
print(f'  13 local HF + 1 Ollama = {len(LOAD_FNS)} total ✓')
print(f'  Medical: {MEDICAL_MODELS}')


# ===== CELL 33 =====
# Duplicate load_llava_med removed — defined once in SET 1 engines cell.


# ===== CELL 34 =====
print(f'✓ All models registered')
print(f'  Total in ALL_MODELS   : {len(ALL_MODELS)}')
print(f'  Local HF              : {len(ALL_LOCAL_HF)}')
print(f'  Ollama                : {OLLAMA_MODELS}')
print(f'  API (excluded)        : GPT-4o, Gemini 2.5  [unusable at scale on free tier]')


# ===== CELL 36 =====
import json, re, shutil
from datetime import datetime
from collections import defaultdict

RESULTS_FILE  = OUT_PATH / 'medvihall_results.jsonl'
PROGRESS_FILE = OUT_PATH / 'progress.json'

# Global tracking sets — updated by run loop, used by save_progress
COMPLETED_MODELS = set()   # fully done — all images × QTs
SKIPPED_MODELS   = set()   # load-failed or 100% errors — skip on resume

def load_progress(manifest=None):
    """
    Reads progress.json and reconstructs the DONE set.
    Pass manifest so 'complete' models can be fully expanded.
    """
    global COMPLETED_MODELS, SKIPPED_MODELS
    if not PROGRESS_FILE.exists():
        return set()
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding='utf-8'))
    except Exception:
        shutil.copy(PROGRESS_FILE, str(PROGRESS_FILE) + '.bak')
        print('  ⚠ Corrupt progress.json — backed up, starting fresh')
        return set()

    COMPLETED_MODELS = set(data.get('completed_models', []))
    SKIPPED_MODELS   = set(data.get('skipped_models', []))
    done = set()

    # Expand complete models — every image × every QT
    if manifest:
        for model_key in COMPLETED_MODELS:
            for item in manifest:
                for qt in QUERY_TYPES:
                    done.add((model_key, item['image_id'], qt))
    else:
        print('  ⚠ load_progress called without manifest — complete models not expanded yet')

    # Expand partial (in_progress) models
    for model_key, img_dict in data.get('in_progress', {}).items():
        if not isinstance(img_dict, dict): continue
        for image_id, qts in img_dict.items():
            if image_id.startswith('_'): continue   # skip _summary fields
            for qt in (qts if isinstance(qts, list) else [qts]):
                done.add((model_key, image_id, qt))

    return done


def save_progress(done):
    """
    Writes a human-readable progress.json.

    Format:
    {
      "_meta": { last_updated, total_completed, active_set },
      "completed_models": ["qwen3vl", ...],       ← fully done, easy to read
      "skipped_models":   ["llava_med"],           ← failed/skipped
      "in_progress": {
        "qwen25vl": {
          "_calls_done": 14,
          "_last_updated": "...",
          "chexpert_S1_0205": ["Q1","Q2","Q3","Q4"],
          "chexpert_S1_0137": ["Q1","Q2","Q3"]
        }
      },
      "pending_models": ["gemma3", "idefics3"]     ← not started yet
    }

    To reset a model:  delete its key from completed_models / in_progress
    To skip a model:   add its key to skipped_models
    """
    # Group done set by model → image → sorted QTs
    model_images = defaultdict(lambda: defaultdict(list))
    for (model_key, image_id, qt) in done:
        model_images[model_key][image_id].append(qt)

    in_progress = {}
    for model_key, img_dict in model_images.items():
        if model_key in COMPLETED_MODELS: continue   # stored compactly below
        if model_key in SKIPPED_MODELS:   continue
        calls_done = sum(len(qts) for qts in img_dict.values())
        entry = {
            '_calls_done':   calls_done,
            '_last_updated': datetime.utcnow().isoformat() + 'Z',
        }
        # image entries: sorted QTs for readability
        for img_id, qts in sorted(img_dict.items()):
            entry[img_id] = sorted(qts)
        in_progress[model_key] = entry

    touched = COMPLETED_MODELS | SKIPPED_MODELS | set(in_progress.keys())
    pending = [m for m in ALL_MODELS
               if m not in touched
               and m not in COMPLETED_MODELS
               and m not in SKIPPED_MODELS]

    data = {
        '_meta': {
            'last_updated':    datetime.utcnow().isoformat() + 'Z',
            'total_completed': len(done),
            'active_set':      ACTIVE_SET,
            'edit_guide':      "Reset model → remove from completed_models or in_progress. Skip model → add to skipped_models.",
        },
        'completed_models': sorted(COMPLETED_MODELS),
        'skipped_models':   sorted(SKIPPED_MODELS),
        'in_progress':      in_progress,
        'pending_models':   pending,
    }
    PROGRESS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8'
    )

def append_result(rec):
    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def make_record(model_key, image_id, modality, stratum, qt, prompt, response, ms):
    m = re.search(r'\b(\d{1,3})%', response)
    conf = int(m.group(1)) / 100.0 if m else None
    return {
        'model': model_key, 'image_id': image_id, 'modality': modality,
        'stratum': stratum, 'query_type': qt, 'query_label': QUERY_TYPES.get(qt, qt),
        'prompt': prompt, 'response': response, 'confidence': conf,
        'latency_ms': round(ms, 1), 'timestamp': datetime.utcnow().isoformat() + 'Z',
        'is_evasion': any(p in response.lower() for p in [
            'i cannot', 'i am not a doctor', 'as an ai', 'please consult',
            'i am unable to', 'i do not have the ability']),
        'in_ecomyth':  model_key in ECOMYTH_MODELS,
        'is_medical':  model_key in MEDICAL_MODELS,
        'is_thinking': model_key in THINKING_MODELS,
    }

# NOTE: DONE is loaded AFTER manifest — see Step 10
print('✓ Storage functions ready (DONE will load after manifest in Step 10)')

# ===== CELL 38 =====
import signal, sys, atexit

_current_model = None; _current_proc = None

def emergency_cleanup():
    global _current_model, _current_proc
    if _current_model is not None or _current_proc is not None:
        print('\n⚠ Emergency cleanup ...'); unload(_current_model, _current_proc)
        _current_model = None; _current_proc = None
    save_progress(DONE); print('  ✓ Progress saved')

def _sig(sig, frame): print(f'⚠ Signal {sig}'); emergency_cleanup(); sys.exit(0)

atexit.register(emergency_cleanup)
signal.signal(signal.SIGINT, _sig); signal.signal(signal.SIGTERM, _sig)
print('✓ Safety system ready')


# ===== CELL 40 =====
import json, random
from pathlib import Path
from collections import Counter, defaultdict

# ── Try loading pre-subsampled manifest first ─────────────────────────────
# Run subsample_manifest.py once to generate manifest_3500.json
# Target: Rad S1-S4:300 each, Derm DS1:400/DS2:200/DS3:300,
#         Histo HS1:300/HS2:200/HS3:300, Ophth OS1:250/OS2:200/OS3:150
MANIFEST_3500 = GT_DIR / 'manifest_3500.json'

GT_FILES = {
    'radiology':      GT_DIR/'radiology_gt_merged.json',
    'dermatology':    GT_DIR/'dermatology_gt_merged.json',
    'histopathology': GT_DIR/'histopathology_gt_merged.json',
    'ophthalmology':  GT_DIR/'ophthalmology_gt_merged.json',
}

if MANIFEST_3500.exists():
    with open(MANIFEST_3500) as f:
        manifest = json.load(f)
    print(f'✓ Loaded subsampled manifest: {len(manifest)} images')
    print(f'  (from {MANIFEST_3500})')
else:
    # Fallback: build full manifest from GT files
    print(f'⚠ manifest_3500.json not found — loading full manifest')
    print(f'  Run subsample_manifest.py to generate the 3,500 image subset')
    manifest = []
    for modality, gt_file in GT_FILES.items():
        if not gt_file.exists(): print(f'  ⚠ Missing: {gt_file.name}'); continue
        with open(gt_file) as f: records = json.load(f)
        for rec in records:
            img_path = rec.get('validated_path')
            if not img_path:
                for p in (DATA_PATH/'data'/'raw').rglob(rec.get('filename','')):
                    img_path = str(p); break
            if img_path and Path(img_path).exists():
                manifest.append({'image_id':rec['image_id'],'modality':modality,
                                 'stratum':rec.get('stratum',''),'image_path':img_path,
                                 'source':rec.get('source','')})

print(f'\nManifest: {len(manifest)} images')
for m,n in sorted(Counter(e['modality'] for e in manifest).items()):
    sc = dict(Counter(e['stratum'] for e in manifest if e['modality']==m))
    print(f'  {m:<20} {n:>5}  {sc}')

# Estimate total calls and GPU time
normal_count = sum(1 for e in manifest if e['stratum'] in NORMAL_STRATA)
q4_calls     = normal_count   # Q4 only on normal strata
total_calls  = len(manifest)*3 + q4_calls  # Q1+Q2+Q3 all, Q4 normal only
est_hrs      = total_calls * 17 / 3600
print(f'\nEstimates per model:')
print(f'  Total calls (Q1+Q2+Q3 all + Q4 normal): {total_calls:,}')
print(f'  @ avg 17s/call (per-QT limits): {est_hrs:.1f} h/model')
print(f'  14 models total: {est_hrs*14:.0f} h = {est_hrs*14/24:.1f} days GPU')

if DEV_SAMPLE and len(manifest)>DEV_SAMPLE:
    random.seed(42); manifest = random.sample(manifest, DEV_SAMPLE)
    print(f'DEV MODE: {len(manifest)} images')
    
    
# Load progress NOW — manifest is available so 'complete' models expand correctly
DONE = load_progress(manifest)
print(f'\n✓ Progress loaded | Completed calls: {len(DONE):,}')
print(f'  Completed models : {sorted(COMPLETED_MODELS)}')
print(f'  Skipped models   : {sorted(SKIPPED_MODELS)}')


# ===== CELL 42 =====
# import time
# from tqdm.notebook import tqdm

# random.seed(42)
# by_mod = defaultdict(list)
# for item in manifest: by_mod[item['modality']].append(item)
# pilot_manifest = []
# for mod, items in by_mod.items():
#     pilot_manifest.extend(random.sample(items, min(PILOT_N, len(items))))

# print(f'Pilot: {len(pilot_manifest)} images | Models: {ACTIVE_MODELS}')
# PILOT_ERRORS=[]; PILOT_STATS=defaultdict(int)

# for model_key in ACTIVE_MODELS:
#     cfg = MODEL_REGISTRY.get(model_key, {'label':model_key,'ecomyth_ehr':None,'origin':''})
#     ehr = cfg.get('ecomyth_ehr')
#     print(f'\n{"="*55}')
#     print(f'{cfg["label"]}  |  EcoMyth EHR: {ehr:.3f}' if ehr else f'{cfg["label"]}  |  new model')
#     print(f'{"="*55}')

#     global _current_model, _current_proc
#     try: _current_model, _current_proc = LOAD_FNS[model_key]()
#     except Exception as e:
#         print(f'  ✗ LOAD FAILED: {e}')
#         PILOT_ERRORS.append({'model':model_key,'error':str(e),'stage':'load'}); continue

#     infer_fn = INFER_FNS[model_key]; first = True
#     for item in tqdm(pilot_manifest, desc=f'  {model_key}', leave=False):
#         for qt in QUERY_TYPES:
#             dk = (model_key, item['image_id'], qt)
#             if dk in DONE: PILOT_STATS['skipped']+=1; continue
#             if qt=='Q4' and item['stratum'] not in NORMAL_STRATA: continue
#             t0=time.time()
#             try:
#                 resp = infer_fn(_current_model,_current_proc,item['image_path'],
#                                 get_prompt(item['modality'],qt,item['stratum']),
#                                 SYSTEM_PROMPTS[item['modality']])
#                 ms   = (time.time()-t0)*1000
#                 rec  = make_record(model_key,item['image_id'],item['modality'],
#                                    item['stratum'],qt,get_prompt(item['modality'],qt,item['stratum']),resp,ms)
#                 append_result(rec); DONE.add(dk); PILOT_STATS['completed']+=1
#                 if first:
#                     print(f'  Sample: {resp[:150]}...')
#                     print(f'  Evasion={rec["is_evasion"]} | Thinking={rec["is_thinking"]} | Conf={rec["confidence"]}')
#                     first=False
#             except Exception as e:
#                 PILOT_ERRORS.append({'model':model_key,'qt':qt,'error':str(e)}); PILOT_STATS['errors']+=1

#     save_progress(DONE); unload(_current_model,_current_proc); _current_model=None; _current_proc=None
#     print(f'  ✓ done')

# print(f'\nPILOT: completed={PILOT_STATS["completed"]} errors={PILOT_STATS["errors"]}')
# if PILOT_ERRORS: [print(f'  {e}') for e in PILOT_ERRORS[:5]]


# ===== CELL 44 =====
import time
from collections import defaultdict
from tqdm.notebook import tqdm

RUN_STATS = defaultdict(int); RUN_ERRORS = []
SAVE_EVERY_N_IMAGES = 5
img_counter = 0
models_to_run = ACTIVE_MODELS
total = len(manifest) * len(QUERY_TYPES) * len(models_to_run)
print(f'{"="*65}')
print(f'FULL RUN — {ACTIVE_SET}  |  {len(models_to_run)} models  |  {total:,} calls (before Q4 filter)')
print(f'Per-QT token limits: {MAX_TOKENS_BY_QT}')
print(f'Done: {len(DONE):,}  |  Remaining: {max(0,total-len(DONE)):,}')
print(f'{"="*65}\n')

for midx, model_key in enumerate(models_to_run):
    cfg   = MODEL_REGISTRY.get(model_key, {'label': model_key, 'ecomyth_ehr': None})
    label = cfg['label']
    ehr   = cfg.get('ecomyth_ehr')

    # Skip models already fully done or explicitly skipped
    if model_key in COMPLETED_MODELS:
        print(f'[{midx+1}/{len(models_to_run)}] {label} — ✓ complete, skipping'); continue
    if model_key in SKIPPED_MODELS:
        print(f'[{midx+1}/{len(models_to_run)}] {label} — ✗ skipped/failed, skipping'); continue

    rem = sum(1 for item in manifest for qt in QUERY_TYPES
              if (model_key, item['image_id'], qt) not in DONE
              and not (qt == 'Q4' and item['stratum'] not in NORMAL_STRATA))
    if rem == 0:
        COMPLETED_MODELS.add(model_key)
        save_progress(DONE)
        print(f'[{midx+1}/{len(models_to_run)}] {label} — ✓ complete, skipping'); continue

    print(f'\n{"="*65}')
    print(f'[{midx+1}/{len(models_to_run)}] {label}')
    if ehr: print(f'  EcoMyth EHR={ehr:.3f}')
    print(f'  Remaining: {rem:,} calls')
    print(f'{"="*65}')

    global _current_model, _current_proc
    LOAD_TIMEOUT_SEC = 900  # model loads can legitimately take minutes; still bound it
    try:
        load_result, _load_timeout_err = run_with_timeout(LOAD_FNS[model_key], (), LOAD_TIMEOUT_SEC)
    except Exception as e:
        print(f'  ✗ LOAD FAILED: {e}')
        SKIPPED_MODELS.add(model_key)
        RUN_ERRORS.append({'model': model_key, 'error': str(e), 'stage': 'load'})
        save_progress(DONE); continue
    if _load_timeout_err:
        print(f'  \u2717 LOAD TIMEOUT ({LOAD_TIMEOUT_SEC}s): {_load_timeout_err} — restart kernel before resuming')
        SKIPPED_MODELS.add(model_key)
        RUN_ERRORS.append({'model': model_key, 'error': _load_timeout_err, 'stage': 'load'})
        save_progress(DONE); continue
    _current_model, _current_proc = load_result

    infer_fn = INFER_FNS[model_key]; m_done = 0; m_err = 0; t_start = time.time()

    for item in tqdm(manifest, desc=model_key, unit='img'):
        for qt in QUERY_TYPES:
            dk = (model_key, item['image_id'], qt)
            if dk in DONE: RUN_STATS['skipped'] += 1; continue
            if qt == 'Q4' and item['stratum'] not in NORMAL_STRATA: continue

            MAX_NEW_TOKENS = MAX_TOKENS_BY_QT.get(qt, 280)
            t0 = time.time()
            try:
                resp, _timeout_err = run_with_timeout(
                    infer_fn,
                    (_current_model, _current_proc, item['image_path'],
                     get_prompt(item['modality'], qt, item['stratum']),
                     SYSTEM_PROMPTS[item['modality']]),
                    INFER_TIMEOUT_SEC
                )
                ms  = (time.time() - t0) * 1000
                if _timeout_err:
                    print(f'  \u26a0 {_timeout_err} | model={model_key} image={item["image_id"]} qt={qt} '
                          f'| GPU worker thread abandoned — restart kernel before resuming this model')
                    RUN_ERRORS.append({'model': model_key, 'image_id': item['image_id'], 'qt': qt,
                                        'error': _timeout_err, 'latency_ms': round(ms, 1)})
                    RUN_STATS['errors'] += 1; m_err += 1
                    continue
                # if ms / 1000 > SLOW_CALL_WARN_SEC:
                #     print(f'  \u26a0 slow call: {ms/1000:.1f}s | model={model_key} image={item["image_id"]} qt={qt}')
                rec = make_record(model_key, item['image_id'], item['modality'],
                                  item['stratum'], qt,
                                  get_prompt(item['modality'], qt, item['stratum']), resp, ms)
                append_result(rec); DONE.add(dk)
                RUN_STATS['completed'] += 1; m_done += 1

            except RuntimeError as e:
                if 'out of memory' in str(e).lower():
                    torch.cuda.empty_cache()
                    try:
                        resp = infer_fn(
                            _current_model, _current_proc, item['image_path'],
                            get_prompt(item['modality'], qt, item['stratum']),
                            SYSTEM_PROMPTS[item['modality']]
                        )
                        ms  = (time.time() - t0) * 1000
                        rec = make_record(model_key, item['image_id'], item['modality'],
                                          item['stratum'], qt,
                                          get_prompt(item['modality'], qt, item['stratum']), resp, ms)
                        append_result(rec); DONE.add(dk)
                        RUN_STATS['completed'] += 1; m_done += 1
                    except Exception as e2:
                        RUN_ERRORS.append({'model': model_key, 'image_id': item['image_id'], 'qt': qt, 'error': str(e2)})
                        RUN_STATS['errors'] += 1; m_err += 1
                else:
                    RUN_ERRORS.append({'model': model_key, 'image_id': item['image_id'], 'qt': qt, 'error': str(e)})
                    RUN_STATS['errors'] += 1; m_err += 1
            except Exception as e:
                RUN_ERRORS.append({'model': model_key, 'image_id': item['image_id'], 'qt': qt, 'error': str(e)})
                RUN_STATS['errors'] += 1; m_err += 1

        img_counter += 1
        if img_counter % SAVE_EVERY_N_IMAGES == 0:
            save_progress(DONE)

    unload(_current_model, _current_proc); _current_model = None; _current_proc = None

    hrs = (time.time() - t_start) / 3600
    pct = 100 * m_err / max(1, m_done + m_err)
    print(f'  ✓ {label} | {m_done:,} done | {m_err} errors ({pct:.1f}%) | {hrs:.2f}h')

    # Mark model status for progress file
    if m_done == 0 and m_err > 0:
        SKIPPED_MODELS.add(model_key)
        print(f'  ⚠ Marked as SKIPPED (100% errors) — fix and re-run, or add to skipped_models in progress.json')
    elif rem - m_err <= 0 or m_done > 0:
        COMPLETED_MODELS.add(model_key)
    save_progress(DONE)

MAX_NEW_TOKENS = MAX_TOKENS_BY_QT.get('Q1', 350)
save_progress(DONE)
fsize = RESULTS_FILE.stat().st_size / 1e6 if RESULTS_FILE.exists() else 0
print(f'\n{"="*65}')
print(f'RUN COMPLETE | {RUN_STATS["completed"]:,} completed | {RUN_STATS["errors"]} errors')
print(f'Results: {RESULTS_FILE}  ({fsize:.1f} MB)')
print(f'Next: Change ACTIVE_SET = "SET_2" → re-run Steps 9–12')
print(f'{"="*65}')

# ===== CELL 45 =====


