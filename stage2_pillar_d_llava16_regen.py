"""
Regenerate llava16's Pillar D Q1/Q3 responses that were truncated by the 220-token
cap (added 2026-09-26 17:35:45 UTC). Runs the unchanged calibration loop with the
original MAX_TOKENS_BY_QT budgets (Q1=700, Q3=480) and writes to a SEPARATE file,
medvihall_outputs/pillar_d_llava16_uncapped.jsonl, which stage3_pd_label's
load_effective_runs() lets supersede the capped rows. The main results file is
never modified.

Q4 is skipped (no model emits a confidence on Q4, so it never enters ECE/ACE).
Resume-safe; relaunch freely:  python stage2_pillar_d_llava16_regen.py
"""
import sys
from pathlib import Path

import stage2_pillar_d_calibration as S
import stage3_pd_label as L

REGEN_FILE = L.LLAVA16_REGEN_FILE

S.OUT_FILE = REGEN_FILE
S.PROGRESS_FILE = Path('medvihall_outputs/pillar_d_llava16_regen_progress.json')
S.LLAVA16_PARALLEL_MAX_NEW_TOKENS_CAP = 10 ** 9   # lift the cap; MAX_TOKENS_BY_QT applies

_orig_build = S.build_call_list
S.build_call_list = lambda manifest: [(img, qt) for img, qt in _orig_build(manifest) if qt != 'Q4']


def load_done_keys():
    runs, _, _ = L.load_effective_runs()
    return set(runs.keys())


S.load_done_keys = load_done_keys

if __name__ == '__main__':
    sys.argv = [sys.argv[0], '--model', 'llava16'] + sys.argv[1:]
    S.main()
