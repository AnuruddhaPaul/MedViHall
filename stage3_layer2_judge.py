"""
Stage 3 -- Layer 2 LLM-as-judge classification using the same local
Qwen2.5-7B-Instruct (4-bit, temp=0.0, text-only) used for Stage 1 claim
extraction. Classifies every claim from extracted_claims.jsonl into the
7-class hallucination taxonomy, using the GROUND_TRUTH payload (gt_payload.py)
and the Layer 1 automated verdict (layer1_verdicts.jsonl) as judging context.

Design note on class 2 (OMISSION): omission is inherently about a finding
that's *absent* from the response, not a property of any extracted claim --
so it cannot be assigned to a claim_id by this per-claim judge. Layer 1
already computes omissions structurally (GT positive finding with no
matching claim/mention). Stage 4's SMHR computation folds Layer 1's
per-record omissions back in as synthetic weight-1.0 hallucination entries
alongside this stage's per-claim judgments, so the LLM here is asked to
classify with classes {0,1,3,4,5,6,7} only and never emit 2.

Batching matches Stage 1: one LLM call judges *all* claims of one
(model, image_id, query_type) record at once (141,000 calls total, not one
per individual claim -- avoids a ~3x call-volume blowup versus per-claim
calls, since records average ~4.5 claims each).

Resume-safe: same pattern as Stage 1/Stage 2 -- the output file is the
source of truth for "already done", re-scanned on every start.

Usage:
  python stage3_layer2_judge.py                 # full run, all models
  python stage3_layer2_judge.py --model llava_med   # just one model (for the
                                                      # required sanity-check
                                                      # pass before running
                                                      # the rest)
  python stage3_layer2_judge.py --limit 500      # stop after N new records
"""
import os
import re
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

from gt_payload import load_gt_index, build_gt_payload

CLAIMS_FILE     = Path('medvihall_outputs/extracted_claims.jsonl')
LAYER1_FILE     = Path('medvihall_outputs/layer1_verdicts.jsonl')
OUT_FILE        = Path('medvihall_outputs/layer2_judge.jsonl')
PARSE_FAIL_FILE = Path('medvihall_outputs/layer2_judge_parse_failures.jsonl')
PROGRESS_FILE   = Path('medvihall_outputs/layer2_judge_progress.json')
MODEL_DIR       = 'D:/medvihall_models/Qwen2.5-7B-Instruct'

BATCH_SIZE            = 24   # 32 overflows VRAM once the (sorted) tail batches cluster high-claim records together -- confirmed via a real thrashing repro (100% util, 64W draw vs ~220W healthy)
CHECKPOINT_EVERY_N_BATCHES = 5
MAX_INPUT_TOKENS      = 3072

# Dynamic per-batch max_new_tokens instead of one flat worst-case value.
# A flat 2048 (needed for the rare 28-claim record) made every batch pay the
# worst case even though 89% of records have <=7 claims -- ~5-8x slower than
# necessary. Since HF's batched generate() runs every sequence in a batch to
# the same step count, todo is sorted by claim count before chunking so each
# batch is claim-count-homogeneous, then each batch gets its own budget sized
# to its own max claim count (confirmed ~30 tokens/claim after the rationale
# was shortened to <=8 words; 45/claim + 100 buffer leaves comfortable margin).
TOKENS_PER_CLAIM      = 45
TOKEN_BUDGET_BUFFER   = 100
MIN_NEW_TOKENS        = 150
MAX_NEW_TOKENS_CAP    = 1536

SYSTEM_PROMPT = (
    'You are a clinical hallucination auditor for medical VLM outputs. For each '
    'numbered CLAIM extracted from a VLM response, classify it using this exact '
    'taxonomy:\n'
    '0 = NOT_HALLUCINATION -- claim is accurate and supported by, or not contradicted by, the ground truth\n'
    '1 = FABRICATION -- claim asserts a finding/diagnosis with no support in, or contradicted by, the ground truth\n'
    '3 = MISCLASSIFICATION -- claim confuses one distinct category (finding, diagnosis, tissue type) for another that the ground truth actually shows\n'
    '4 = SEVERITY_DISTORTION -- claim significantly overstates or understates severity/grade/ratio relative to a severity field the ground truth actually provides (e.g. cup_disc_ratio, malignant)\n'
    '5 = ANATOMICAL_CONFUSION -- claim states a location/site/laterality that DIRECTLY CONTRADICTS a location field the ground truth explicitly provides (e.g. anatomical_site)\n'
    '6 = EVASION -- claim is vague, non-committal, or refuses to give a concrete answer when the ground truth supports one\n'
    '7 = CLINICAL_REASONING_ERROR -- claim draws an incorrect or unsupported clinical inference/recommendation from an otherwise correct finding\n'
    'Class 2 (OMISSION) is handled separately elsewhere in the pipeline -- never output 2.\n'
    '\n'
    'How to read GROUND_TRUTH (do not assume anything beyond this):\n'
    '- "positive_labels" (radiology) = findings CONFIRMED PRESENT.\n'
    '- "negative_labels" (radiology) = findings CONFIRMED ABSENT. A name appearing here means the finding is NOT present -- never treat it as a positive finding.\n'
    '- Any finding name that appears in NEITHER positive_labels nor negative_labels is UNSTATED/UNKNOWN -- the ground truth is simply silent on it, which is NOT evidence the claim is wrong.\n'
    '- Other modalities give a single confirmed value per field (e.g. "diagnosis", "glaucoma", "tumor_present") -- treat that value as the confirmed truth for that field only.\n'
    '\n'
    'Important calibration rules:\n'
    '- IMPORTANT: classes 4 and 5 require a MATCHING field to actually be present in GROUND_TRUTH (a severity/ratio field for 4, a location/site field for 5). '
    'If GROUND_TRUTH has no such field, you MUST NOT use that class -- fall back to class 1 if the underlying finding itself lacks support, or class 0 if it does not.\n'
    '- Mentioning a location or severity word is not automatically class 5 or 4 -- only use them when GROUND_TRUTH actually contradicts that specific location or severity value.\n'
    '- Prefer class 1 (FABRICATION) as the default for any claimed finding/diagnosis that has no support in GROUND_TRUTH, unless a more specific class clearly applies per the rules above.\n'
    '\n'
    'Judge only against the given MODALITY, GROUND_TRUTH, and LAYER1_SIGNAL context; do not assume facts beyond them. '
    'LAYER1_SIGNAL is an independent automated check (may be noisy) -- use it as a hint, not as ground truth itself.\n'
    'Keep "rationale" to at most 8 words -- it is a short tag, not an explanation.\n'
    'Return ONLY valid JSON array. No preamble:\n'
    '[{"claim_id":1,"is_hallucination":true/false,"hallucination_class":0,"rationale":"..."}]\n'
    'One entry per input claim_id. Return [] if no claims given.'
)


def sanitize_claims(claims):
    """
    A small fraction (~0.4%) of Stage 1's extracted claims are malformed --
    Stage 1 only validated the 'verifiable' field, so some claims slipped
    through with claim_text and claim_id swapped/missing (confirmed: the
    LLM occasionally put the claim's descriptive text into claim_id and
    dropped claim_text entirely). Reconstruct a usable claim_text/claim_id
    here rather than crashing or silently dropping the claim.
    """
    fixed = []
    for i, c in enumerate(claims):
        claim_id = c.get('claim_id')
        if not isinstance(claim_id, int):
            claim_id = i + 1
        claim_text = c.get('claim_text')
        if not claim_text:
            # The original 'claim_id' field sometimes holds the actual text.
            fallback = c.get('claim_id')
            claim_text = fallback if isinstance(fallback, str) and fallback else (c.get('finding') or '[unknown claim]')
        fixed.append({'claim_id': claim_id, 'claim_text': claim_text,
                       'finding': c.get('finding'), 'assertion_type': c.get('assertion_type')})
    return fixed


def build_user_message(modality, gt_payload, layer1_signal, claims):
    claims_input = [
        {'claim_id': c['claim_id'], 'claim_text': c['claim_text'],
         'finding': c.get('finding'), 'assertion_type': c.get('assertion_type')}
        for c in sanitize_claims(claims)
    ]
    return (
        f'MODALITY: {modality}\n'
        f'GROUND_TRUTH: {json.dumps(gt_payload, ensure_ascii=False)}\n'
        f'LAYER1_SIGNAL: {json.dumps(layer1_signal, ensure_ascii=False)}\n'
        f'CLAIMS:\n{json.dumps(claims_input, ensure_ascii=False)}'
    )


def sanitize_hallucination_class(modality, gt_payload, judgment):
    """
    Deterministic guardrail: classes 4 (SEVERITY_DISTORTION) and 5
    (ANATOMICAL_CONFUSION) are only valid when the GT payload actually
    contains a matching severity/location field for that modality (see
    gt_coverage_notes.json's per-modality class-coverage table). The 7B
    judge does not reliably self-enforce this despite being told to in the
    prompt (confirmed empirically: it invents class 4/5 for radiology, which
    has neither field) -- so it's enforced here in code instead. A
    misapplied 4/5 is downgraded to 1 (FABRICATION) if still flagged as a
    hallucination, since the judge only reaches for 4/5 when it already
    believes the underlying claim is unsupported.
    """
    cls = judgment.get('hallucination_class')
    has_severity_field = (
        (modality == 'dermatology' and gt_payload.get('malignant') is not None) or
        (modality == 'ophthalmology' and gt_payload.get('cup_disc_ratio') is not None)
    )
    has_location_field = (
        (modality == 'dermatology' and gt_payload.get('anatomical_site') is not None) or
        (modality == 'histopathology' and gt_payload.get('tissue_full') is not None)
    )
    if cls == 4 and not has_severity_field:
        judgment['hallucination_class'] = 1
    elif cls == 5 and not has_location_field:
        judgment['hallucination_class'] = 1
    return judgment


def extract_json_array(text):
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def load_claims_records(model_filter=None):
    records = []
    with open(CLAIMS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if model_filter and r['model'] != model_filter:
                continue
            records.append(r)
    return records


def load_layer1_index():
    """(model, image_id, query_type) -> {fabrications, omissions, matches}"""
    idx = {}
    with open(LAYER1_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r['model'], r['image_id'], r['query_type'])
            idx[key] = {
                'fabrications': r.get('fabrications', []),
                'omissions': r.get('omissions', []),
                'matches': r.get('matches', []),
            }
    return idx


def load_done_keys():
    done = set()
    if not OUT_FILE.exists():
        return done
    with open(OUT_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            done.add((rec['model'], rec['image_id'], rec['query_type']))
    return done


def save_progress(n_done, n_total, n_errors, started_at):
    PROGRESS_FILE.write_text(json.dumps({
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'started_at': started_at,
        'records_done': n_done,
        'records_total': n_total,
        'parse_errors': n_errors,
        'batch_size': BATCH_SIZE,
    }, indent=2), encoding='utf-8')


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


def compute_batch_max_new_tokens(batch_claims):
    max_claims = max((len(c) for c in batch_claims), default=0)
    budget = TOKENS_PER_CLAIM * max_claims + TOKEN_BUDGET_BUFFER
    return max(MIN_NEW_TOKENS, min(budget, MAX_NEW_TOKENS_CAP))


def run_batch_judge(mdl, tok, batch_items):
    """batch_items: list of (modality, gt_payload, layer1_signal, claims). Returns list of raw decoded strings."""
    import torch
    texts = []
    for modality, gt_payload, layer1_signal, claims in batch_items:
        msgs = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': build_user_message(modality, gt_payload, layer1_signal, claims)},
        ]
        texts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    inp = tok(texts, return_tensors='pt', padding=True, truncation=True,
              max_length=MAX_INPUT_TOKENS).to(mdl.device)
    batch_max_new_tokens = compute_batch_max_new_tokens([claims for (_, _, _, claims) in batch_items])
    with torch.no_grad():
        out = mdl.generate(
            **inp, max_new_tokens=batch_max_new_tokens, do_sample=False,
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
    ap.add_argument('--model', type=str, default=None, help='Restrict to a single model (e.g. for sanity-check pass)')
    ap.add_argument('--limit', type=int, default=0, help='Stop after N newly processed records (0 = no limit)')
    args = ap.parse_args()

    print(f'[{datetime.now().isoformat()}] Loading GT index ...')
    gt_index = load_gt_index()

    print(f'[{datetime.now().isoformat()}] Loading Layer 1 verdicts ...')
    layer1_index = load_layer1_index()
    print(f'  {len(layer1_index)} Layer 1 records')

    print(f'[{datetime.now().isoformat()}] Loading claims records ...')
    records = load_claims_records(model_filter=args.model)
    print(f'  {len(records)} records' + (f' for model={args.model}' if args.model else ' (all models)'))

    print(f'[{datetime.now().isoformat()}] Scanning {OUT_FILE} for done keys ...')
    done_keys = load_done_keys()
    print(f'  {len(done_keys)} already done (any model)')

    todo = [r for r in records if (r['model'], r['image_id'], r['query_type']) not in done_keys]
    todo.sort(key=lambda r: len(r['claims']))  # groups batches by claim count -- see compute_batch_max_new_tokens
    print(f'  {len(todo)} remaining')

    if not todo:
        print('Stage 3 already complete for this selection.')
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
    n_skipped_empty = 0
    n_batches = 0

    out_f = open(OUT_FILE, 'a', encoding='utf-8')
    fail_f = open(PARSE_FAIL_FILE, 'a', encoding='utf-8')
    try:
        i = 0
        while i < len(todo):
            chunk = todo[i:i + BATCH_SIZE]
            i += len(chunk)

            llm_items = []       # (idx_in_chunk, modality, gt_payload, layer1_signal, claims)
            chunk_judgments = [None] * len(chunk)
            for j, r in enumerate(chunk):
                claims = r['claims']
                if not claims:
                    chunk_judgments[j] = []
                    n_skipped_empty += 1
                    continue
                key = (r['model'], r['image_id'], r['query_type'])
                gt_rec = gt_index.get(r['modality'], {}).get(r['image_id'])
                gt_payload = build_gt_payload(r['modality'], gt_rec)
                layer1_signal = layer1_index.get(key, {'fabrications': [], 'omissions': [], 'matches': []})
                llm_items.append((j, r['modality'], gt_payload, layer1_signal, claims))

            if llm_items:
                batch_input = [(m, g, l1, c) for (_, m, g, l1, c) in llm_items]
                try:
                    raw_outputs = run_batch_judge(mdl, tok, batch_input)
                except Exception as e:
                    print(f'  !! BATCH ERROR ({len(llm_items)} items): {e}')
                    raw_outputs = [None] * len(llm_items)
                    n_errors += len(llm_items)

                for (j, modality, gt_payload, layer1_signal, claims), raw in zip(llm_items, raw_outputs):
                    r = chunk[j]
                    if raw is None:
                        chunk_judgments[j] = {'_parse_error': True, 'raw_output': None}
                        fail_f.write(json.dumps({
                            'model': r['model'], 'image_id': r['image_id'], 'query_type': r['query_type'],
                            'reason': 'exception', 'raw_output': None,
                        }, ensure_ascii=False) + '\n')
                        continue
                    parsed = extract_json_array(raw)
                    if parsed is None:
                        n_errors += 1
                        chunk_judgments[j] = {'_parse_error': True, 'raw_output': raw}
                        fail_f.write(json.dumps({
                            'model': r['model'], 'image_id': r['image_id'], 'query_type': r['query_type'],
                            'reason': 'unparseable_json', 'raw_output': raw,
                        }, ensure_ascii=False) + '\n')
                    else:
                        valid = [
                            sanitize_hallucination_class(modality, gt_payload, c)
                            for c in parsed
                            if isinstance(c, dict) and 'claim_id' in c
                            and c.get('hallucination_class') in (0, 1, 3, 4, 5, 6, 7)
                        ]
                        chunk_judgments[j] = valid

            for r, judgments in zip(chunk, chunk_judgments):
                rec_out = {
                    'model': r['model'], 'image_id': r['image_id'], 'modality': r['modality'],
                    'query_type': r['query_type'],
                }
                if isinstance(judgments, dict) and judgments.get('_parse_error'):
                    rec_out['_parse_error'] = True
                    rec_out['claim_judgments'] = []
                else:
                    rec_out['claim_judgments'] = judgments
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
                      f'rate={rate:.2f}rec/s errors={n_errors} empty_skipped={n_skipped_empty} '
                      f'ETA={eta_h:.2f}h')
    finally:
        out_f.close()
        fail_f.close()
        save_progress(len(done_keys) + n_done, len(records), n_errors, started_at)

    print(f'\n[{datetime.now().isoformat()}] Stage 3 run finished.')
    print(f'  Processed this run: {n_done}  |  Errors: {n_errors}  |  Empty-claims skipped: {n_skipped_empty}')


if __name__ == '__main__':
    main()
