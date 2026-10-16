"""
Shared context for make_figures.py: loads the result files once, runs the
verification assertions, saves figures (PDF + 300 dpi PNG + source CSV) and
collects everything that goes into figure_manifest.md / figure_checks.md.
"""
import ast
import re
import traceback
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.text as mtext
import numpy as np
import pandas as pd

import fig_data as fd
import fig_style as st
from fig_data import MissingData, ROOT, OUT, load_json, need, pct_ci

FIG_DIR = ROOT / 'paper_figures'
TAB_DIR = ROOT / 'paper_tables'

# Sanity values supplied with the figure request (3-decimal core SMHR per model).
# They are used ONLY as a stop condition, never plotted.
EXPECTED_CORE_SMHR = {
    'qwen25vl': 0.529, 'gemma3': 0.532, 'internvl3': 0.539, 'qwen35': 0.549, 'qwen3vl': 0.562,
    'minicpm': 0.580, 'idefics3': 0.636, 'qwen2vl': 0.643, 'llava16': 0.675, 'huatuogpt': 0.691,
    'chexagent': 0.748, 'llava_med': 0.794,
}


class StopFigures(Exception):
    """Computed core values differ from the expected ones: stop and report instead of plotting."""


def fmt_ci(p, lo, hi, nd=3):
    return f'{p:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]'


class Ctx:
    def __init__(self, force_rebuild=False):
        st.apply_style()
        FIG_DIR.mkdir(exist_ok=True)
        TAB_DIR.mkdir(exist_ok=True)
        self.checks = []         # (id, status, description, detail)
        self.notes = []          # (figure, text)  places where a number looked odd
        self.overlaps = []       # (figure, text)  ranking caveats
        self.not_generated = []  # (figure, reason)
        self.manifest = []       # dicts
        self.tables = []         # dicts
        self.current = 'setup'

        self.W = self._read_weights()
        self.df, self.rec_info = fd.build_record_table(self.W, force=force_rebuild)
        self.images = fd.load_manifest()
        self.boot = fd.Boot(self.df, self.images)
        self.boot_u = fd.Boot(self.df, self.images, stratified=False)   # conservative cross-check
        self.ms = load_json(OUT / 'metrics_summary.json')
        self.models = list(st.MODEL_ORDER)
        self.is_medical = {m: v['is_medical'] for m, v in self.ms['models'].items()}
        self._cell_cache = {}

    # ------------------------------------------------------------ bookkeeping
    def check(self, cid, ok, description, detail=''):
        self.checks.append((cid, 'PASS' if ok else 'FAIL', description, detail))
        return ok

    def note(self, text, fig=None):
        self.notes.append((fig or self.current, text))

    def overlap_note(self, text, fig=None):
        self.overlaps.append((fig or self.current, text))

    # ------------------------------------------------------------ weights
    def _read_weights(self):
        src = (ROOT / 'compute_model_metrics.py').read_text(encoding='utf-8')
        m = re.search(r'CLASS_WEIGHTS\s*=\s*(\{[^}]*\})', src)
        return {int(k): float(v) for k, v in ast.literal_eval(m.group(1)).items()}

    # ------------------------------------------------------------ core cells
    def cell(self, model, modality=None, field='smhr'):
        """Point estimate + 95% image-bootstrap CI for SMHR or CHR, overall or per modality."""
        key = (model, modality, field)
        if key not in self._cell_cache:
            mask = self.boot.mask(modality) if modality else None
            if field == 'smhr':
                p, b = self.boot.ratio(model, mask=mask)
            else:
                p, b = self.boot.ratio(model, 'has12', 'records', mask=mask)
            lo, hi = pct_ci(b)
            self._cell_cache[key] = {'point': p, 'lo': lo, 'hi': hi, 'boots': b}
        return self._cell_cache[key]

    # ------------------------------------------------------------ verification
    def run_core_checks(self):
        self.current = 'core'
        ms = self.ms['models']
        per_model = load_json(OUT / 'stage3_metrics_by_model.json')
        c1 = pd.read_csv(need(ROOT / 'annotation_results' / 'C1_smhr_by_model_assumed_vs_equal.csv')).set_index('model')

        self.check('C00', self.rec_info['duplicate_keys'] == 0,
                   'No duplicate (model, image, query) keys in layer2_judge.jsonl',
                   f"{self.rec_info['duplicate_keys']} duplicates in {self.rec_info['n_rows']} rows")
        self.check('C01', set(self.df['image_id']) <= set(self.images['image_id']),
                   'Every judged image id is in manifest_3500.json', f"{self.images.shape[0]} manifest images")
        mm = self.df.drop_duplicates('image_id').merge(self.images[['image_id', 'modality']], on='image_id',
                                                        suffixes=('', '_man'))
        self.check('C02', bool((mm['modality'] == mm['modality_man']).all()),
                   'Modality in layer2_judge.jsonl equals manifest modality for every image')
        self.check('C03', bool(set(self.W) == set(range(1, 8)) and self.W == {1: 1.0, 2: 1.0, 3: 0.7, 4: 0.5, 5: 0.4, 6: 0.1, 7: 0.6}),
                   'Class weights read from compute_model_metrics.py', str(self.W))
        mit = OUT / 'pillar_b_mitigation_results.json'
        if mit.exists():
            wj = {int(k): v for k, v in load_json(mit)['parameters']['class_weights'].items()}
            self.check('C04', wj == self.W, 'Class weights identical in compute_model_metrics.py and Pillar B results')

        mismatches = []
        for m in self.models:
            pt = self.cell(m)['point']
            recs = int((self.df['model'] == m).sum())
            self.check(f'C10_{m}', recs == ms[m]['n_records'],
                       f'{m}: record count {recs} == metrics_summary n_records {ms[m]["n_records"]}')
            self.check(f'C11_{m}', abs(pt - ms[m]['smhr_overall']) < 1e-9,
                       f'{m}: recomputed overall SMHR {pt:.6f} == metrics_summary.json {ms[m]["smhr_overall"]:.6f}')
            self.check(f'C12_{m}', abs(pt - per_model[m]['smhr_overall']) < 1e-9,
                       f'{m}: recomputed SMHR == stage3_metrics_by_model.json')
            self.check(f'C13_{m}', abs(pt - c1.loc[m, 'SMHR_assumed_weights']) < 1e-9,
                       f'{m}: recomputed SMHR == annotation_results/C1 SMHR_assumed_weights')
            chr_pt = self.cell(m, field='chr')['point']
            self.check(f'C14_{m}', abs(chr_pt - ms[m]['chr_overall']) < 1e-9,
                       f'{m}: recomputed CHR {chr_pt:.6f} == metrics_summary.json')
            for mod in st.MODALITY_ORDER:
                pt_m = self.cell(m, mod)['point']
                self.check(f'C15_{m}_{mod}', abs(pt_m - ms[m]['by_modality'][mod]['smhr']) < 1e-9,
                           f'{m}/{mod}: recomputed SMHR == metrics_summary.json')
            if round(pt, 3) != EXPECTED_CORE_SMHR[m]:
                mismatches.append((m, round(pt, 3), EXPECTED_CORE_SMHR[m]))
        self.check('C20', not mismatches, 'Core SMHR (3 dp) equals the expected sanity values from the request',
                   'differences: ' + str(mismatches) if mismatches else 'all 12 match')
        if mismatches:
            raise StopFigures('Core SMHR differs from the expected sanity values: ' +
                              '; '.join(f'{m}: computed {a} vs expected {b}' for m, a, b in mismatches))

        by_smhr = sorted(self.models, key=lambda m: self.cell(m)['point'])
        self.check('C21', by_smhr == st.MODEL_ORDER,
                   'fig_style.MODEL_ORDER equals the SMHR-ascending order computed from the data',
                   ' > '.join(by_smhr))
        spec = sorted(m for m in self.models if self.is_medical[m])
        self.check('C22', spec == sorted(st.SPECIALISTS), 'fig_style.SPECIALISTS equals the is_medical flag in the results',
                   str(spec))

    # ------------------------------------------------------------ saving
    def save(self, fig, name, source_df, note=None):
        """Write paper_figures/<name>.{pdf,png,csv}; also verify minimum font size."""
        pdf, png, csv = (FIG_DIR / f'{name}.{e}' for e in ('pdf', 'png', 'csv'))
        fig.savefig(pdf)
        fig.savefig(png, dpi=st.DPI_PNG)
        source_df.to_csv(csv, index=False)
        small = sorted({round(t.get_fontsize(), 1) for t in fig.findobj(mtext.Text)
                        if t.get_visible() and t.get_text().strip() and t.get_fontsize() < st.FS_BASE - 1e-6})
        self.check(f'F_{name}_font', not small, f'{name}: every text element >= {st.FS_BASE:g} pt',
                   f'sizes below minimum: {small}' if small else '')
        w, h = fig.get_size_inches()
        plt.close(fig)
        return {'file': name, 'width_in': w, 'height_in': h}

    def add_manifest(self, **kw):
        self.manifest.append(kw)

    # ------------------------------------------------------------ labels
    def name(self, m):
        return st.MODEL_SHORT[m]


def ci_overlap(a_lo, a_hi, b_lo, b_hi):
    return not (a_hi < b_lo or b_hi < a_lo)


def spread_labels(y, min_gap, lo=0.0, hi=1.0):
    """Push label positions apart (1-D) so that consecutive labels are >= min_gap apart."""
    order = np.argsort(y)
    ys = np.array(y, dtype=float)[order]
    for _ in range(200):
        moved = False
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < min_gap:
                d = (min_gap - (ys[i] - ys[i - 1])) / 2
                ys[i - 1] -= d
                ys[i] += d
                moved = True
        ys = np.clip(ys, lo, hi)
        if not moved:
            break
    out = np.empty_like(ys)
    out[order] = ys
    return out


def safe_run(ctx, label, fn):
    ctx.current = label
    try:
        fn(ctx)
    except MissingData as e:
        ctx.not_generated.append((label, str(e)))
    except StopFigures:
        raise
    except Exception as e:  # a bug is reported, never silently swallowed
        tb = traceback.format_exc(limit=4)
        ctx.not_generated.append((label, f'ERROR while building the figure: {type(e).__name__}: {e}'))
        ctx.checks.append((f'ERR_{label}', 'FAIL', f'{label} raised an exception', tb))
