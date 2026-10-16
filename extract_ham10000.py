"""
Extract HAM10000 images into medvihall_data/data/raw/dermatology/ham10000/
Targets: DS1=300, DS2=300, DS3=400  (total 1000)
Source:  C:/Users/PC/.cache/kagglehub/datasets/kmader/skin-cancer-mnist-ham10000/versions/2
"""

import json
from pathlib import Path
import pandas as pd
from PIL import Image
from tqdm import tqdm

RANDOM_SEED  = 42
DATASET_PATH = Path(r"C:\Users\PC\.cache\kagglehub\datasets\kmader\skin-cancer-mnist-ham10000\versions\2")

BASE_DIR  = Path("medvihall_data")
HAM_DIR   = BASE_DIR / "data" / "raw" / "dermatology" / "ham10000"
GT_DIR    = BASE_DIR / "data" / "ground_truth"
HAM_DIR.mkdir(parents=True, exist_ok=True)
GT_DIR.mkdir(parents=True, exist_ok=True)

HAM_STRATUM = {
    "nv":    "DS1",
    "df":    "DS1",
    "bkl":   "DS1",
    "vasc":  "DS1",
    "akiec": "DS2",
    "mel":   "DS3",
    "bcc":   "DS3",
    "scc":   "DS3",
}
HAM_FULL = {
    "nv":    "Melanocytic nevi",
    "df":    "Dermatofibroma",
    "bkl":   "Benign keratosis",
    "vasc":  "Vascular lesion",
    "akiec": "Actinic keratosis / Bowen's disease",
    "mel":   "Melanoma",
    "bcc":   "Basal cell carcinoma",
    "scc":   "Squamous cell carcinoma",
}
TARGETS = {"DS1": 300, "DS2": 300, "DS3": 400}

# ── Step 1: Load metadata ─────────────────────────────────────────────────
csv_path = DATASET_PATH / "HAM10000_metadata.csv"
assert csv_path.exists(), f"CSV not found at {csv_path}"

df = pd.read_csv(csv_path)
print(f"Loaded {len(df):,} records from metadata")

df["stratum"]        = df["dx"].map(HAM_STRATUM)
df["diagnosis_full"] = df["dx"].map(HAM_FULL)
df = df.dropna(subset=["stratum"])
print(f"After stratum mapping: {len(df):,} usable records")
print(f"\nDiagnosis distribution:\n{df['dx'].value_counts()}")
print(f"\nStratum distribution:\n{df['stratum'].value_counts()}")

# ── Step 2: Build image lookup (part_1 + part_2) ──────────────────────────
print("\nBuilding image lookup from both image parts ...")
img_lookup: dict[str, Path] = {}
for part in ["HAM10000_images_part_1", "HAM10000_images_part_2"]:
    part_dir = DATASET_PATH / part
    if not part_dir.exists():
        print(f"  Warning: {part} not found, skipping")
        continue
    for p in part_dir.iterdir():
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            img_lookup[p.stem] = p
print(f"Found {len(img_lookup):,} images total")

# ── Step 3: Stratified sample ─────────────────────────────────────────────
print(f"\nTargets: {TARGETS}")
print("\nAvailable per stratum:")
for s, t in TARGETS.items():
    available = len(df[df["stratum"] == s])
    print(f"  {s}: {available:>6,} available  ->  {t} requested")

selected = pd.concat([
    df[df["stratum"] == s].sample(
        n=min(t, len(df[df["stratum"] == s])),
        random_state=RANDOM_SEED
    )
    for s, t in TARGETS.items()
]).reset_index(drop=True)

print(f"\nSelected {len(selected)} images: {dict(selected['stratum'].value_counts())}")

# ── Step 4: Copy images + build GT ────────────────────────────────────────
print(f"\nCopying to {HAM_DIR} ...")

gt_ham    = []
saved_ham = 0
not_found = []

for _, row in tqdm(selected.iterrows(), total=len(selected), desc="HAM10000"):
    orig_id  = row["image_id"]
    src_path = img_lookup.get(orig_id)

    if src_path is None or not src_path.exists():
        not_found.append(orig_id)
        continue

    stratum = row["stratum"]
    img_id  = f"ham10000_{stratum}_{saved_ham:04d}"
    fname   = f"{img_id}.jpg"
    fpath   = HAM_DIR / fname

    if fpath.exists():
        saved_ham += 1
        continue

    try:
        Image.open(src_path).convert("RGB").save(str(fpath), "JPEG", quality=95)
    except Exception as e:
        not_found.append(f"{orig_id} ({e})")
        continue

    gt_ham.append({
        "image_id":        img_id,
        "filename":        fname,
        "source":          "HAM10000",
        "modality":        "dermatology",
        "stratum":         stratum,
        "original_id":     orig_id,
        "diagnosis":       row["dx"],
        "diagnosis_full":  row["diagnosis_full"],
        "malignant":       stratum == "DS3",
        "localization":    row.get("localization", ""),
        "age":             row["age"] if pd.notna(row.get("age")) else None,
        "sex":             str(row.get("sex", "")),
        "dx_type":         str(row.get("dx_type", "")),
        "expert_verified": row.get("dx_type") in ("histo", "follow_up", "consensus"),
    })
    saved_ham += 1

# ── Step 5: Save ground truth ─────────────────────────────────────────────
gt_path = GT_DIR / "dermatology_ham10000_gt.json"
with open(gt_path, "w") as f:
    json.dump(gt_ham, f, indent=2)

strata_counts = {}
for r in gt_ham:
    strata_counts[r["stratum"]] = strata_counts.get(r["stratum"], 0) + 1

print(f"\n{'='*55}")
print(f"HAM10000 extraction complete")
print(f"  Saved     : {saved_ham} / {len(selected)}")
print(f"  Strata    : {strata_counts}")
print(f"  Dest      : {HAM_DIR.resolve()}")
print(f"  GT file   : {gt_path.resolve()}")
if not_found:
    print(f"  Not found : {len(not_found)}")
    for x in not_found[:5]:
        print(f"    {x}")
print(f"{'='*55}")
