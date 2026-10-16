"""
Pillar B (RQ8), Stage 1 -- RAG mitigation.

Embeds each modality's reference snippets (pillar_b_kb.py) with all-MiniLM-L6-v2,
retrieves the top-3 for each query, and prepends them to the existing prompt
under a "Reference context:" header. The retrieval query is the prompt text
itself (image content is not available to a text embedder), so retrieval is a
function of (modality, query type, stratum) only; the full retrieval table is
saved to pillar_b_rag_retrieval.json for inspection.

A retrieval failure = an exception, fewer than TOP_K hits, or a top-1 cosine
similarity below MIN_SIM; failed retrievals fall back to the plain prompt and
are flagged on the record.

Usage:
  python pillar_b_rag.py --retrieval-only          # build + print retrieval table, no GPU
  python pillar_b_rag.py --models qwen25vl --limit 6 --out medvihall_outputs/pillar_b_rag_smoke.jsonl
  python pillar_b_rag.py                           # full run, all 5 models, one at a time
"""
import json
import argparse
from pathlib import Path

import numpy as np

import stage2_pillar_d_calibration as S
import pillar_b_common as C
from pillar_b_kb import KB

OUT_FILE = Path('medvihall_outputs/pillar_b_rag.jsonl')
PROGRESS_FILE = Path('medvihall_outputs/pillar_b_rag_progress.json')
RETRIEVAL_FILE = Path('medvihall_outputs/pillar_b_rag_retrieval.json')
TOP_K, MIN_SIM = 3, 0.20
CONF_TAIL = 'Confidence (0-100%)?'


def build_retrieval():
    from sentence_transformers import SentenceTransformer
    emb = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
    kb_vecs = {m: emb.encode([t for _, t in docs], normalize_embeddings=True) for m, docs in KB.items()}
    manifest = json.loads(S.MANIFEST_FILE.read_text(encoding='utf-8'))
    table = {}
    for img, qt in S.build_call_list(manifest):
        prompt = S.get_prompt(img['modality'], qt, img['stratum'])
        key = (img['modality'], prompt)
        if key in table:
            continue
        try:
            q = emb.encode([f"{img['modality']}: {prompt.replace(CONF_TAIL, '').strip()}"], normalize_embeddings=True)[0]
            sims = kb_vecs[img['modality']] @ q
            top = np.argsort(-sims)[:TOP_K]
            hits = [{'id': KB[img['modality']][i][0], 'text': KB[img['modality']][i][1], 'score': float(sims[i])} for i in top]
            failed = len(hits) < TOP_K or hits[0]['score'] < MIN_SIM
            err = None
        except Exception as e:
            hits, failed, err = [], True, f'{type(e).__name__}: {e}'
        table[key] = {'modality': img['modality'], 'query_type': qt, 'stratum': img['stratum'], 'prompt': prompt,
                      'hits': hits, 'failed': failed, 'error': err}
    return table


def make_prompt_factory(table):
    def make_prompt(img, qt, base):
        r = table[(img['modality'], base)]
        if r['failed'] or not r['hits']:
            return base, {'rag_retrieval_failed': True, 'rag_snippet_ids': [], 'rag_scores': []}
        ctx = '\n'.join(f"- {h['text']}" for h in r['hits'])
        return f'Reference context:\n{ctx}\n\n{base}', {
            'rag_retrieval_failed': False, 'rag_snippet_ids': [h['id'] for h in r['hits']],
            'rag_scores': [round(h['score'], 4) for h in r['hits']]}
    return make_prompt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', nargs='*', default=C.MODELS)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--out', default=str(OUT_FILE))
    ap.add_argument('--retrieval-only', action='store_true')
    args = ap.parse_args()

    table = build_retrieval()
    RETRIEVAL_FILE.write_text(json.dumps(
        [{'key': f'{m}|{p}', **v} for (m, p), v in table.items()], indent=1), encoding='utf-8')
    n_fail = sum(v['failed'] for v in table.values())
    print(f'retrieval table: {len(table)} unique prompts, failures: {n_fail} -> {RETRIEVAL_FILE}')
    if args.retrieval_only:
        for (m, p), v in table.items():
            print(f"\n[{m} {v['query_type']} {v['stratum']}] {p[:90]}")
            for h in v['hits']:
                print(f"    {h['score']:.3f} {h['id']}")
        return
    C.run_condition(args.out, PROGRESS_FILE, 'rag', args.models, make_prompt_factory(table), limit=args.limit)


if __name__ == '__main__':
    main()
