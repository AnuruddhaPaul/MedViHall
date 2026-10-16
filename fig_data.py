"""
Data layer for the paper figures.

Everything here reads saved result files; nothing is typed in from memory.
  * build_record_table(): re-derives per-(model, image, query) SMHR ingredients from
    layer2_judge.jsonl + layer1_verdicts.jsonl, using exactly the rule in
    compute_model_metrics.py (omissions folded in, parse errors contribute nothing).
  * Boot: image-level (cluster) bootstrap.  Images are resampled with replacement
    inside each of the 13 design strata (stratified=True; stratified=False resamples all images at once), the same resampled images are used for every
    model/metric (paired), fixed seed, B resamples.  Claims are never resampled.
"""
import json
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'medvihall_outputs'
CACHE = ROOT / 'paper_figures' / '.cache'

L2_FILE = OUT / 'layer2_judge.jsonl'
L1_FILE = OUT / 'layer1_verdicts.jsonl'
MANIFEST_FILE = ROOT / 'medvihall_data' / 'data' / 'ground_truth' / 'manifest_3500.json'
NOTEBOOK_FILE = ROOT / 'MedViHall_Phase3_Phase4_v4.ipynb'

BOOT_B = 2000
BOOT_SEED = 42


class MissingData(Exception):
    """Raised when a needed result file is absent or empty; the figure is then skipped."""


def need(path, what=None):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        raise MissingData(f'{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} is missing or empty'
                          + (f' ({what})' if what else ''))
    return path


def load_json(path):
    return json.loads(need(path).read_text(encoding='utf-8'))


# ------------------------------------------------------------------ record table
def _sig(paths):
    return [(str(p), p.stat().st_size, int(p.stat().st_mtime)) for p in paths]


def build_record_table(class_weights, force=False):
    """One row per (model, image_id, query_type) Layer-2 record."""
    need(L2_FILE), need(L1_FILE)
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / 'records.pkl'
    sig = _sig([L2_FILE, L1_FILE]) + [('weights', json.dumps(class_weights, sort_keys=True), 0)]
    if cache.exists() and not force:
        try:
            with open(cache, 'rb') as f:
                saved = pickle.load(f)
            if saved['sig'] == sig:
                return saved['df'], saved['info']
        except Exception:
            pass

    omissions = {}
    with open(L1_FILE, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            omissions[(r['model'], r['image_id'], r['query_type'])] = len(r.get('omissions', []))

    cols = ['model', 'image_id', 'query_type', 'modality', 'parse_error', 'w', 'claims', 'n_om', 'has12'] + \
        [f'c{k}' for k in range(1, 8)]
    rows, seen, dupes = [], set(), 0
    with open(L2_FILE, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            key = (r['model'], r['image_id'], r['query_type'])
            if key in seen:
                dupes += 1
            seen.add(key)
            if r.get('_parse_error'):
                rows.append((r['model'], r['image_id'], r['query_type'], r['modality'], True, 0.0, 0, 0, False,
                             *([0] * 7)))
                continue
            n_om = omissions.get(key, 0)
            w = n_om * class_weights[2]
            claims = len(r['claim_judgments']) + n_om
            has12 = n_om > 0
            cc = [0] * 7
            cc[1] = n_om
            for j in r['claim_judgments']:
                if j.get('is_hallucination'):
                    k = j.get('hallucination_class')
                    w += class_weights.get(k, 0)
                    if k in (1, 2):
                        has12 = True
                    if k in range(1, 8):
                        cc[k - 1] += 1
            rows.append((r['model'], r['image_id'], r['query_type'], r['modality'], False, w, claims, n_om, has12, *cc))
    df = pd.DataFrame(rows, columns=cols)
    info = {'n_rows': len(df), 'duplicate_keys': dupes}
    with open(cache, 'wb') as f:
        pickle.dump({'sig': sig, 'df': df, 'info': info}, f)
    return df, info


def load_manifest():
    m = load_json(MANIFEST_FILE)
    df = pd.DataFrame(m)[['image_id', 'modality', 'stratum', 'source']]
    mod_rank = {k: i for i, k in enumerate(['radiology', 'dermatology', 'histopathology', 'ophthalmology'])}
    df['_m'] = df['modality'].map(mod_rank)
    df = df.sort_values(['_m', 'stratum', 'image_id']).drop(columns='_m').reset_index(drop=True)
    return df


# ------------------------------------------------------------------ bootstrap
class Boot:
    def __init__(self, df, images, B=BOOT_B, seed=BOOT_SEED, stratified=True):
        self.stratified = stratified
        self.images = images
        self.N = len(images)
        self.B = B
        self.seed = seed
        self.idx = {iid: i for i, iid in enumerate(images['image_id'])}
        rng = np.random.default_rng(seed)
        counts = np.zeros((B, self.N), dtype=np.float64)
        if stratified:
            for _, grp in images.groupby('stratum').groups.items():
                ii = np.asarray(list(grp))
                n = len(ii)
                counts[:, ii] = rng.multinomial(n, np.full(n, 1.0 / n), size=B)
        else:
            counts[:, :] = rng.multinomial(self.N, np.full(self.N, 1.0 / self.N), size=B)
        self.counts = counts
        d = df.copy()
        d['img'] = d['image_id'].map(self.idx)
        d['records'] = 1
        d['has12'] = d['has12'].astype(int)
        self.df = d
        self.models = sorted(d['model'].unique())
        self._cache = {}

    def vec(self, model, field, qgroup='all'):
        key = (model, field, qgroup)
        if key not in self._cache:
            d = self.df[self.df['model'] == model]
            if qgroup == 'Q123':
                d = d[d['query_type'].isin(['Q1', 'Q2', 'Q3'])]
            elif qgroup in ('Q1', 'Q2', 'Q3', 'Q4'):
                d = d[d['query_type'] == qgroup]
            s = d.groupby('img')[field].sum()
            v = np.zeros(self.N)
            v[s.index.values] = s.values
            self._cache[key] = v
        return self._cache[key]

    def ratio(self, model, num='w', den='claims', mask=None, qgroup='all'):
        """Point estimate and bootstrap distribution of sum(num)/sum(den) over `mask` images."""
        n, d = self.vec(model, num, qgroup), self.vec(model, den, qgroup)
        if mask is not None:
            n, d, c = n[mask], d[mask], self.counts[:, mask]
        else:
            c = self.counts
        point = n.sum() / d.sum() if d.sum() else np.nan
        with np.errstate(invalid='ignore', divide='ignore'):
            boots = (c @ n) / (c @ d)
        return point, boots

    def mask(self, modality=None, strata=None, exclude_strata=None):
        m = np.ones(self.N, dtype=bool)
        if modality is not None:
            m &= (self.images['modality'] == modality).values
        if strata is not None:
            m &= self.images['stratum'].isin(strata).values
        if exclude_strata is not None:
            m &= ~self.images['stratum'].isin(exclude_strata).values
        return m


def pct_ci(boots, level=0.95):
    a = (1 - level) / 2
    b = boots[np.isfinite(boots)]
    return float(np.quantile(b, a)), float(np.quantile(b, 1 - a))


# ------------------------------------------------------------------ model registry (T2)
def load_registry():
    """label / repo id per model from the inference notebook's MODEL_REGISTRY cell (no secrets are read)."""
    nb = json.loads(need(NOTEBOOK_FILE).read_text(encoding='utf-8'))
    pat = re.compile(r"'(\w+)':\s*\{\s*'label':\s*'([^']+)',\s*'repo_id':\s*(?:'([^']+)'|None)")
    reg = {}
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        src = ''.join(c['source'])
        if 'MODEL_REGISTRY' in src and "'label'" in src:
            for m in pat.finditer(src):
                reg[m.group(1)] = {'label': m.group(2), 'repo_id': m.group(3)}
    if not reg:
        raise MissingData('MODEL_REGISTRY not found in inference notebook')
    return reg


def param_billions(label, local_dir_name=None):
    """(value in billions, source) -- from the registry label, else from local safetensors metadata."""
    m = re.search(r'(\d+(?:\.\d+)?)B\b', label)
    if m:
        return float(m.group(1)), 'registry label'
    if local_dir_name:
        idx = ROOT / 'models' / local_dir_name / 'model.safetensors.index.json'
        if idx.exists():
            meta = json.loads(idx.read_text(encoding='utf-8')).get('metadata', {})
            if 'total_size' in meta:
                return round(meta['total_size'] / 2 / 1e9, 1), 'safetensors total_size / 2 bytes (bf16)'
    return None, 'not recorded in repo'
