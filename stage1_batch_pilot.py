"""Quick prototype: batched claim extraction to measure real throughput gain
over the sequential per-call approach (7.62s/call, 298h projected)."""
import json, random, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_DIR = 'D:/medvihall_models/Qwen2.5-7B-Instruct'
SYSTEM_PROMPT = (
    'Extract all atomic medical claims from the VLM output.\n'
    'Return ONLY valid JSON array. No preamble:\n'
    '[{"claim_id":1,"claim_text":"...","finding":"...","assertion_type":"presence|absence|severity|location|type|significance","verifiable":true/false}]\n'
    'Return [] if no claims.'
)

def build_user_message(modality, response):
    return f'MODALITY: {modality}\nVLM OUTPUT:\n{response}'

def extract_json_array(text):
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end+1])
    except json.JSONDecodeError:
        return None

def main():
    random.seed(1)
    records = []
    with open('medvihall_outputs/medvihall_results_deduped.jsonl', encoding='utf-8') as f:
        for line in f:
            records.append(json.loads(line))
    sample = [r for r in random.sample(records, 200) if len(r['response'].strip()) >= 3][:64]

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                              bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    tok.padding_side = 'left'
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    mdl = AutoModelForCausalLM.from_pretrained(MODEL_DIR, quantization_config=bnb,
                                                device_map='auto', torch_dtype=torch.bfloat16,
                                                attn_implementation='sdpa')
    mdl.eval()
    print(f'Model loaded. VRAM used: {torch.cuda.memory_allocated()/1024**3:.1f} GB')

    for batch_size in [8, 16, 32]:
        batch = sample[:batch_size]
        texts = []
        for r in batch:
            msgs = [{'role':'system','content':SYSTEM_PROMPT},
                    {'role':'user','content':build_user_message(r['modality'], r['response'])}]
            texts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        inp = tok(texts, return_tensors='pt', padding=True, truncation=True, max_length=2048).to(mdl.device)
        t0 = time.time()
        with torch.no_grad():
            out = mdl.generate(**inp, max_new_tokens=512, do_sample=False,
                                pad_token_id=tok.pad_token_id)
        dt = time.time() - t0
        n_ok = 0
        for i in range(len(batch)):
            gen = tok.decode(out[i][inp['input_ids'].shape[1]:], skip_special_tokens=True)
            if extract_json_array(gen) is not None:
                n_ok += 1
        print(f'batch={batch_size:3d}  total={dt:6.1f}s  per-record={dt/batch_size:5.2f}s  parse_ok={n_ok}/{batch_size}  peak_vram={torch.cuda.max_memory_allocated()/1024**3:.1f}GB')
        torch.cuda.reset_peak_memory_stats()
        del inp, out
        torch.cuda.empty_cache()

if __name__ == '__main__':
    main()
