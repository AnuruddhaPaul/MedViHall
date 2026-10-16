"""
Stage 1 -- Claim extraction using a local Qwen2.5-7B-Instruct (4-bit, temp=0.0,
text-only, no API). Extracts atomic medical claims from every model response in
medvihall_results_deduped.jsonl.

Batched generation: sequential single-call throughput measured at 7.62s/call
(298.5h projected for 141,000 records) -- unusable. Batch=32 (left-padded,
greedy decode) measured at 1.44s/record (~56h projected), with comfortable
VRAM headroom (9.5GB peak of 16GB card). Batch=64 overflows VRAM and thrashes
(100% GPU-util but ~70W draw vs 300W TDP -- the exact PCIe-thrashing symptom
documented in the original notebook's safety-helpers cell) -- do not raise
batch size past 32 on this card without re-validating VRAM headroom.

Resume-safe: the source of truth for "already done" is the actual output file
(extracted_claims.jsonl), re-scanned on every start. A separate progress file
is kept only for human-readable stats and is rewritten every checkpoint.

Usage:
  python stage1_extract_claims.py            # full run
  python stage1_extract_claims.py --limit 500  # stop after N newly processed records
"""
import os
import re
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

RESULTS_FILE      = Path('medvihall_outputs/medvihall_results_deduped.jsonl')
CLAIMS_FILE       = Path('medvihall_outputs/extracted_claims.jsonl')
PARSE_FAIL_FILE   = Path('medvihall_outputs/extracted_claims_parse_failures.jsonl')
PROGRESS_FILE     = Path('medvihall_outputs/extracted_claims_progress.json')
MODEL_DIR         = 'D:/medvihall_models/Qwen2.5-7B-Instruct'

BATCH_SIZE          = 32   # verified safe VRAM ceiling on this 16GB card -- see module docstring
CHECKPOINT_EVERY_N_BATCHES = 5   # ~160 records
# 512 was too small: verbose models (qwen3vl, qwen35, gemma3 -- mean response
# 1470-1780 chars, richly multi-finding) produced JSON arrays that got cut off
# before the closing ']', silently collapsing to claims=[] on parse failure.
# Measured against a real failing case (5 findings x location/severity/
# significance -- should be ~15-20 atomic claims): 1024 resolves it.
MAX_NEW_TOKENS      = 1024
MAX_INPUT_TOKENS     = 2048
DEGENERATE_LEN       = 3   # responses shorter than this (or literal [EMPTY]) skip the LLM call

SYSTEM_PROMPT = (
    'Extract all atomic medical claims from the VLM output.\n'
    'Return ONLY valid JSON array. No preamble:\n'
    '[{"claim_id":1,"claim_text":"...","finding":"...","assertion_type":"presence|absence|severity|location|type|significance","verifiable":true/false}]\n'
    'Return [] if no claims.'
)


def build_user_message(modality, response):
    return f'MODALITY: {modality}\nVLM OUTPUT:\n{response}'


def extract_json_array(text):
    """Find the outermost [...] block and json.loads it. Returns None on failure."""
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def load_source_records():
    records = []
    with open(RESULTS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_done_keys():
    """(model, image_id, query_type) tuples already present in CLAIMS_FILE."""
    done = set()
    if not CLAIMS_FILE.exists():
        return done
    with open(CLAIMS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a truncated last line from a prior crash
            done.add((rec['model'], rec['image_id'], rec['query_type']))
    return done


def save_progress(n_done, n_total, n_errors, started_at):
    data = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'started_at': started_at,
        'records_done': n_done,
        'records_total': n_total,
        'parse_errors': n_errors,
        'batch_size': BATCH_SIZE,
    }
    PROGRESS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')


def load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
    )
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    tok.padding_side = 'left'
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    mdl = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR, quantization_config=bnb, device_map='auto',
        torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    mdl.eval()
    return mdl, tok


def run_batch_extraction(mdl, tok, batch_items):
    """batch_items: list of (modality, response). Returns list of raw decoded strings, same order."""
    import torch
    texts = []
    for modality, response in batch_items:
        msgs = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': build_user_message(modality, response)},
        ]
        texts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    inp = tok(texts, return_tensors='pt', padding=True, truncation=True,
              max_length=MAX_INPUT_TOKENS).to(mdl.device)
    with torch.no_grad():
        out = mdl.generate(
            **inp, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
            pad_token_id=tok.pad_token_id,
        )
    results = []
    in_len = inp['input_ids'].shape[1]
    for i in range(len(batch_items)):
        raw = tok.decode(out[i][in_len:], skip_special_tokens=True).strip()
        results.append(raw)
    del inp, out
    torch.cuda.empty_cache()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='Stop after N newly processed records (0 = no limit)')
    args = ap.parse_args()

    print(f'[{datetime.now().isoformat()}] Loading source records from {RESULTS_FILE} ...')
    records = load_source_records()
    print(f'  {len(records)} total records')

    print(f'[{datetime.now().isoformat()}] Scanning {CLAIMS_FILE} for already-completed keys ...')
    done_keys = load_done_keys()
    print(f'  {len(done_keys)} already done')

    todo = [r for r in records if (r['model'], r['image_id'], r['query_type']) not in done_keys]
    print(f'  {len(todo)} remaining to process')

    if not todo:
        print('Stage 1 already complete. Nothing to do.')
        return

    if args.limit:
        todo = todo[:args.limit]
        print(f'  --limit set: processing only {len(todo)} records this run')

    print(f'[{datetime.now().isoformat()}] Loading Qwen2.5-7B-Instruct (4-bit) from {MODEL_DIR} ...')
    mdl, tok = load_model()
    print(f'  Model loaded. Batch size={BATCH_SIZE}')

    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    n_done = 0
    n_errors = 0
    n_skipped_degenerate = 0
    n_batches = 0

    out_f = open(CLAIMS_FILE, 'a', encoding='utf-8')
    fail_f = open(PARSE_FAIL_FILE, 'a', encoding='utf-8')
    try:
        i = 0
        while i < len(todo):
            chunk = todo[i:i + BATCH_SIZE]
            i += len(chunk)

            # Split degenerate (empty/near-empty response) records out -- no LLM call needed.
            llm_items = []       # (idx_in_chunk, modality, response)
            chunk_claims = [None] * len(chunk)
            for j, r in enumerate(chunk):
                resp = r['response']
                if len(resp.strip()) < DEGENERATE_LEN or resp.strip() == '[EMPTY]':
                    chunk_claims[j] = []
                    n_skipped_degenerate += 1
                else:
                    llm_items.append((j, r['modality'], resp))

            if llm_items:
                batch_input = [(m, resp) for (_, m, resp) in llm_items]
                try:
                    raw_outputs = run_batch_extraction(mdl, tok, batch_input)
                except Exception as e:
                    print(f'  !! BATCH ERROR ({len(llm_items)} items): {e}')
                    raw_outputs = [None] * len(llm_items)
                    n_errors += len(llm_items)

                for (j, modality, resp), raw in zip(llm_items, raw_outputs):
                    r = chunk[j]
                    if raw is None:
                        chunk_claims[j] = []
                        fail_f.write(json.dumps({
                            'model': r['model'], 'image_id': r['image_id'], 'query_type': r['query_type'],
                            'reason': 'exception', 'raw_output': None,
                        }, ensure_ascii=False) + '\n')
                        continue
                    parsed = extract_json_array(raw)
                    if parsed is None:
                        n_errors += 1
                        chunk_claims[j] = []
                        fail_f.write(json.dumps({
                            'model': r['model'], 'image_id': r['image_id'], 'query_type': r['query_type'],
                            'reason': 'unparseable_json', 'raw_output': raw,
                        }, ensure_ascii=False) + '\n')
                    else:
                        chunk_claims[j] = [c for c in parsed if isinstance(c, dict) and c.get('verifiable') is True]

            for r, claims in zip(chunk, chunk_claims):
                rec_out = {
                    'model': r['model'], 'image_id': r['image_id'], 'modality': r['modality'],
                    'query_type': r['query_type'], 'claims': claims,
                }
                out_f.write(json.dumps(rec_out, ensure_ascii=False) + '\n')
                n_done += 1

            n_batches += 1
            if n_batches % CHECKPOINT_EVERY_N_BATCHES == 0:
                out_f.flush()
                os.fsync(out_f.fileno())
                fail_f.flush()
                os.fsync(fail_f.fileno())
                save_progress(len(done_keys) + n_done, len(records), n_errors, started_at)
                elapsed = time.time() - t0
                rate = n_done / elapsed
                remaining = len(todo) - n_done
                eta_h = remaining / rate / 3600 if rate > 0 else float('inf')
                print(f'  [{n_done}/{len(todo)}] elapsed={elapsed/60:.1f}min '
                      f'rate={rate:.2f}rec/s errors={n_errors} degenerate_skipped={n_skipped_degenerate} '
                      f'ETA={eta_h:.1f}h')
    finally:
        out_f.close()
        fail_f.close()
        save_progress(len(done_keys) + n_done, len(records), n_errors, started_at)

    print(f'\n[{datetime.now().isoformat()}] Stage 1 run finished.')
    print(f'  Processed this run: {n_done}  |  Errors (parse/exception): {n_errors}  |  Degenerate skipped: {n_skipped_degenerate}')
    print(f'  Total done overall: {len(done_keys) + n_done} / {len(records)}')


if __name__ == '__main__':
    main()
