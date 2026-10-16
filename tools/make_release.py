#!/usr/bin/env python3
"""Build a clean, GitHub-ready copy of the MedViHall project folder.

Usage (run on the machine that holds the project):
    python make_release.py --src "C:/Users/PC/Desktop/Programs/MediViHall" --out ./release_staging
    python make_release.py --src ... --out ... --dry-run     # report only

What it does (the source folder is never modified):
  1. Skips model weights, dataset images, backup duplicates and caches.
  2. Drops radiology records from .jsonl / .csv files (rows whose `modality`
     is radiology, or whose image_id/key starts with a radiology prefix) and
     skips files that are radiology-only by name.
  3. Replaces API keys/tokens (hf_..., sk-..., ghp_...) in text files with REDACTED_SECRET.
  4. Splits any file larger than --max-mb (default 95; GitHub rejects >100 MB)
     into <file>.parts/part_000, part_001, ... plus a SHA-256 manifest.
     Rejoin with:  python tools/rejoin_chunks.py <file>.parts
"""
import argparse, hashlib, json, os, re, shutil, sys, csv, io

SKIP_DIRS = {"models", "__pycache__", ".claude", ".git", ".ipynb_checkpoints",
             "stage1_corrupted_backup_20260920", "images", "tmp", "raw", "lit_cache"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
WEIGHT_EXT = {".safetensors", ".bin", ".pt", ".pth", ".ckpt", ".gguf", ".onnx", ".h5"}
BACKUP_PAT = re.compile(r"(\.bak[\w.\-]*$|_before_|\bcopy\b|\.orig$|~$|_backup)", re.I)
RADIO_NAME = re.compile(r"(radiolog|chexbert|chexpert|chexagent|layer1_radiology)", re.I)
RADIO_ID = re.compile(r"^(chexpert|mimic|nih|vindr|padchest|radiology)", re.I)
TEXT_EXT = {".py", ".ipynb", ".md", ".txt", ".json", ".sh", ".tex", ".bib",
            ".yaml", ".yml", ".cfg", ".toml", ".log"}
TOKEN = re.compile(r"(hf_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{30,})")


def is_radiology_row(d):
    if not isinstance(d, dict):
        return False
    if str(d.get("modality", "")).lower() == "radiology":
        return True
    for k in ("image_id", "key", "id"):
        v = d.get(k)
        if isinstance(v, str) and RADIO_ID.match(v):
            return True
    return False


def copy_filtered_jsonl(src, dst, stats):
    kept = dropped = 0
    with open(src, "r", encoding="utf-8", errors="replace") as fi, \
         open(dst, "w", encoding="utf-8", newline="\n") as fo:
        for line in fi:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                fo.write(line if line.endswith("\n") else line + "\n"); kept += 1
                continue
            if is_radiology_row(d):
                dropped += 1
            else:
                fo.write(line if line.endswith("\n") else line + "\n"); kept += 1
    stats["rows_dropped"] += dropped
    return kept, dropped


def copy_filtered_csv(src, dst, stats):
    with open(src, "r", encoding="utf-8", errors="replace", newline="") as fi:
        rd = csv.DictReader(fi)
        cols = rd.fieldnames or []
        key = [c for c in cols if c in ("modality", "image_id", "key", "id")]
        if not key:
            shutil.copy2(src, dst); return None
        kept = dropped = 0
        with open(dst, "w", encoding="utf-8", newline="") as fo:
            wr = csv.DictWriter(fo, fieldnames=cols); wr.writeheader()
            for r in rd:
                if is_radiology_row(r):
                    dropped += 1
                else:
                    wr.writerow(r); kept += 1
    stats["rows_dropped"] += dropped
    return kept, dropped


def scrub(path, stats):
    try:
        with open(path, "r", encoding="utf-8") as f:
            s = f.read()
    except Exception:
        return
    n = len(TOKEN.findall(s))
    if n:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(TOKEN.sub("REDACTED_SECRET", s))
        stats["tokens_scrubbed"] += n
        stats["scrubbed_files"].append(path)


def split_file(path, max_bytes, stats):
    size = os.path.getsize(path)
    pdir = path + ".parts"
    os.makedirs(pdir, exist_ok=True)
    h = hashlib.sha256(); parts = []
    with open(path, "rb") as f:
        i = 0
        while True:
            buf = f.read(max_bytes)
            if not buf:
                break
            name = "part_%03d" % i
            with open(os.path.join(pdir, name), "wb") as o:
                o.write(buf)
            h.update(buf)
            parts.append({"name": name, "bytes": len(buf),
                          "sha256": hashlib.sha256(buf).hexdigest()})
            i += 1
    meta = {"original": os.path.basename(path), "bytes": size,
            "sha256": h.hexdigest(), "parts": parts}
    with open(os.path.join(pdir, "MANIFEST.json"), "w") as f:
        json.dump(meta, f, indent=2)
    os.remove(path)
    stats["split"].append((os.path.relpath(path), size, len(parts)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-mb", type=float, default=95)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    src, out = os.path.abspath(a.src), os.path.abspath(a.out)
    if out == src:
        sys.exit("--out must differ from --src")
    stats = {"copied": 0, "skipped": [], "rows_dropped": 0, "tokens_scrubbed": 0,
             "scrubbed_files": [], "split": [], "filtered": []}
    if not a.dry_run:
        os.makedirs(out, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS
                   and os.path.abspath(os.path.join(root, d)) != out]
        for fn in files:
            rel = os.path.normpath(os.path.join(rel_root, fn))
            ext = os.path.splitext(fn)[1].lower()
            reason = None
            if ext in IMG_EXT: reason = "image"
            elif ext in WEIGHT_EXT: reason = "weights"
            elif BACKUP_PAT.search(fn): reason = "backup"
            elif RADIO_NAME.search(fn): reason = "radiology-only"
            if reason:
                stats["skipped"].append((rel, reason)); continue
            if a.dry_run:
                stats["copied"] += 1; continue
            dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            if ext == ".jsonl":
                k, d = copy_filtered_jsonl(os.path.join(root, fn), dst, stats)
                stats["filtered"].append((rel, k, d))
            elif ext == ".csv":
                r = copy_filtered_csv(os.path.join(root, fn), dst, stats)
                if r: stats["filtered"].append((rel, *r))
            else:
                shutil.copy2(os.path.join(root, fn), dst)
            if ext in TEXT_EXT:
                scrub(dst, stats)
            stats["copied"] += 1
    if not a.dry_run:
        mb = int(a.max_mb * 1024 * 1024)
        for root, _, files in os.walk(out):
            for fn in files:
                p = os.path.join(root, fn)
                if os.path.getsize(p) > mb:
                    split_file(p, mb, stats)
        shutil.copy2(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejoin_chunks.py"),
                     os.path.join(out, "rejoin_chunks.py"))
    print("files copied      :", stats["copied"])
    print("rows dropped (radiology):", stats["rows_dropped"])
    print("tokens scrubbed   :", stats["tokens_scrubbed"], "in", len(stats["scrubbed_files"]), "files")
    print("skipped           :", len(stats["skipped"]))
    for r, why in stats["skipped"][:60]: print("   -", why, r)
    for r, k, d in stats["filtered"]:
        if d: print("   filtered %s: kept %d, dropped %d" % (r, k, d))
    for r, s, n in stats["split"]:
        print("   split %s: %.1f MB -> %d parts" % (r, s / 1048576, n))


if __name__ == "__main__":
    main()
