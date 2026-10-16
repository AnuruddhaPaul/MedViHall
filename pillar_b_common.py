"""
Pillar B shared generation loop. Reuses Pillar D's loaders, patched inference
functions, prompt templates, MAX_TOKENS_BY_QT (unchanged) and call list
(Q1-Q3 for all 500 images, Q4 only for NORMAL_STRATA = 1,679 calls/model).
Decoding is greedy (do_sample=False, temperature=0.0) and logged on every record.
Resume-safe: the output file is rescanned on start, keyed (model, image_id, query_type).
llava16 is NOT token-capped here (Pillar D's 220-token cap does not apply).
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import stage2_pillar_d_calibration as S
from pillar_d_load_fns import LOAD_FNS, unload
from pillar_d_infer_fns import PATCHED_INFER_FNS

MODELS = ['qwen25vl', 'llava16', 'chexagent', 'huatuogpt', 'llava_med']
CHECKPOINT_EVERY_N = 20
DECODING = {'do_sample': False, 'temperature': 0.0, 'top_p': None}


def load_done(out_file):
    done = set()
    if Path(out_file).exists():
        with open(out_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done.add((r['model'], r['image_id'], r['query_type']))
    return done


def run_condition(out_file, progress_file, condition, models, make_prompt, limit=0, infer_for=None):
    """make_prompt(img, qt, base_prompt) -> (prompt_text, extra_fields_dict).
    infer_for(model_key) -> inference fn (defaults to Pillar D's patched greedy-capable fn)."""
    manifest = json.loads(S.MANIFEST_FILE.read_text(encoding='utf-8'))
    calls = S.build_call_list(manifest)
    print(f'[{datetime.now().isoformat()}] {condition}: {len(manifest)} images, {len(calls)} calls/model, models={models}')
    done = load_done(out_file)
    print(f'  {len(done)} calls already done (any model)')
    out_f = open(out_file, 'a', encoding='utf-8')
    started = datetime.now(timezone.utc).isoformat()
    try:
        for model_key in models:
            todo = [(img, qt) for img, qt in calls if (model_key, img['image_id'], qt) not in done]
            print(f'\n[{datetime.now().isoformat()}] {model_key}: {len(todo)} calls remaining')
            if not todo:
                continue
            if limit:
                todo = todo[:limit]
                print(f'  --limit: only {len(todo)} calls this run')
            mdl, proc = LOAD_FNS[model_key]()
            infer_fn = infer_for(model_key) if infer_for else PATCHED_INFER_FNS[model_key]
            t0, n, n_err = time.time(), 0, 0
            for img, qt in todo:
                base = S.get_prompt(img['modality'], qt, img['stratum'])
                prompt, extra = make_prompt(img, qt, base)
                max_new = S.MAX_TOKENS_BY_QT[qt]
                try:
                    t_call = time.time()
                    response = infer_fn(mdl, proc, img['image_path'], prompt, S.SYSTEM_PROMPTS[img['modality']],
                                        temperature=0.0, top_p=0.9, do_sample=False, max_new_tokens=max_new)
                    latency_ms = (time.time() - t_call) * 1000
                except Exception as e:
                    response, latency_ms = f'[ERROR] {type(e).__name__}: {e}', None
                    n_err += 1
                rec = {
                    'model': model_key, 'condition': condition, 'image_id': img['image_id'],
                    'modality': img['modality'], 'stratum': img['stratum'], 'query_type': qt,
                    'prompt': prompt, 'response': response, 'confidence': S.parse_confidence(response),
                    'decoding': {**DECODING, 'max_new_tokens': max_new},
                    'latency_ms': round(latency_ms, 1) if latency_ms is not None else None,
                    'timestamp': datetime.now(timezone.utc).isoformat(), **extra,
                }
                out_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                n += 1
                if n % CHECKPOINT_EVERY_N == 0:
                    out_f.flush()
                    os.fsync(out_f.fileno())
                    elapsed = time.time() - t0
                    rate = n / elapsed
                    eta_h = (len(todo) - n) / rate / 3600
                    Path(progress_file).write_text(json.dumps({
                        'condition': condition, 'model': model_key, 'done_this_model': n, 'todo_this_model': len(todo),
                        'started_at': started, 'last_updated': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf-8')
                    print(f'  [{model_key}] [{n}/{len(todo)}] {elapsed/60:.1f}min rate={rate:.2f}call/s errors={n_err} ETA={eta_h:.2f}h')
            out_f.flush()
            os.fsync(out_f.fileno())
            print(f'[{datetime.now().isoformat()}] {model_key} done this run: {n} calls, {n_err} errors')
            unload(mdl, proc)
    finally:
        out_f.close()
    print(f'\n[{datetime.now().isoformat()}] {condition} run finished.')
