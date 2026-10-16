#!/usr/bin/env python3
"""
Keep a persona annotation run going until all items are done, waiting out usage limits.

A Claude session cannot act once its usage limit is hit, so the "wait and restart"
has to live outside the session. This script launches `claude -p` with a persona
file, and when the session ends before all items are written (limit hit, crash),
it waits and launches a fresh session. The persona prompt resumes from its own
output file, so nothing is redone.

Usage:
  python run_persona_loop.py persona_1_generalist.md [persona_2_radiology_specialist.md ...]
Personas run one after another, because all of them share the same usage limit.

Options:
  --total 720            items expected per persona
  --poll-minutes 30      wait between retries when a session made no progress
  --max-stalls 24        stop after this many retries in a row with no progress
  --allowed-tools "Read Write Bash"   tools claude may use without asking
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time


def count_done(out_path: pathlib.Path) -> int:
    """Number of distinct item_ids present as valid JSON lines."""
    if not out_path.exists():
        return 0
    ids = set()
    for line in out_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue  # cut-off last line from an interrupted write
        if isinstance(rec, dict) and rec.get("item_id"):
            ids.add(rec["item_id"])
    return len(ids)


def stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_persona(persona_file: pathlib.Path, args, claude_bin: str) -> bool:
    text = persona_file.read_text(encoding="utf-8")
    m = re.search(r"annotator id:\s*([a-z_]+)", text)
    if not m:
        print(f"[{stamp()}] cannot find 'annotator id:' in {persona_file}", flush=True)
        return False
    annotator = m.group(1)
    out_path = pathlib.Path(f"annotations_ai_{annotator}.jsonl")
    log_path = pathlib.Path(f"runner_log_{annotator}.txt")
    stalls = 0

    while True:
        done = count_done(out_path)
        print(f"[{stamp()}] {annotator}: {done}/{args.total} done", flush=True)
        if done >= args.total:
            print(f"[{stamp()}] {annotator}: complete", flush=True)
            return True

        cmd = [claude_bin, "-p"]
        if args.allowed_tools:
            cmd += ["--allowedTools", args.allowed_tools]
        print(f"[{stamp()}] {annotator}: starting session", flush=True)
        proc = subprocess.run(cmd, input=text, text=True, capture_output=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n===== {stamp()} exit={proc.returncode} =====\n")
            log.write((proc.stdout or "")[-4000:])
            log.write((proc.stderr or "")[-2000:])

        new_done = count_done(out_path)
        if new_done > done:
            stalls = 0
            time.sleep(30)  # progress was made; relaunch soon (limit may be near)
            continue

        stalls += 1
        if stalls >= args.max_stalls:
            print(
                f"[{stamp()}] {annotator}: no progress in {stalls} tries in a row. "
                f"Stopping so a real error is not hidden. See {log_path}.",
                flush=True,
            )
            return False
        print(
            f"[{stamp()}] {annotator}: no progress (likely usage limit). "
            f"Waiting {args.poll_minutes} min (try {stalls}/{args.max_stalls}).",
            flush=True,
        )
        time.sleep(args.poll_minutes * 60)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("persona_files", nargs="+")
    ap.add_argument("--total", type=int, default=720)
    ap.add_argument("--poll-minutes", type=int, default=30)
    ap.add_argument("--max-stalls", type=int, default=24)
    ap.add_argument("--allowed-tools", default="Read Write Bash")
    args = ap.parse_args()

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("Could not find the `claude` command on PATH.", file=sys.stderr)
        return 1

    for pf in args.persona_files:
        ok = run_persona(pathlib.Path(pf), args, claude_bin)
        if not ok:
            return 2
    print(f"[{stamp()}] all personas finished", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
