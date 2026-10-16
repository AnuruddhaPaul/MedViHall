"""
Pillar B (RQ8), Stage 2 -- visual contrastive decoding (VCD) generation run.

Same call list, prompts (unchanged base prompt, no retrieval), MAX_TOKENS_BY_QT and greedy
decoding as Stage 0/1; only the decoding rule changes (see pillar_b_vcd.py). Resume-safe via
pillar_b_common.run_condition (output file rescanned on start).

Usage:
  python pillar_b_contrastive.py --models qwen25vl --limit 6 --out medvihall_outputs/pillar_b_contrastive_smoke.jsonl
  python pillar_b_contrastive.py                      # full run, all 5 models, one at a time
"""
import argparse
from functools import partial
from pathlib import Path

import pillar_b_common as C
import pillar_b_vcd as V

OUT_FILE = Path('medvihall_outputs/pillar_b_contrastive.jsonl')
PROGRESS_FILE = Path('medvihall_outputs/pillar_b_contrastive_progress.json')


def make_prompt_factory(alpha):
    extra = {'vcd': {**V.VCD_PARAMS, 'alpha': alpha}}

    def make_prompt(img, qt, base):
        return base, extra
    return make_prompt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', nargs='*', default=C.MODELS)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--out', default=str(OUT_FILE))
    ap.add_argument('--alpha', type=float, default=V.ALPHA_DEFAULT)
    args = ap.parse_args()
    infer_for = lambda m: partial(V.VCD_INFER_FNS[m], alpha=args.alpha)
    C.run_condition(args.out, PROGRESS_FILE, 'contrastive', args.models, make_prompt_factory(args.alpha),
                    limit=args.limit, infer_for=infer_for)


if __name__ == '__main__':
    main()
