#!/usr/bin/env python3
"""Rejoin a file that make_release.py split into <file>.parts/ and verify its SHA-256.

    python rejoin_chunks.py path/to/file.jsonl.parts        # writes path/to/file.jsonl
    python rejoin_chunks.py --all .                         # rejoin every *.parts folder below .
"""
import hashlib, json, os, sys


def rejoin(pdir):
    with open(os.path.join(pdir, "MANIFEST.json")) as f:
        m = json.load(f)
    out = os.path.join(os.path.dirname(os.path.abspath(pdir)), m["original"])
    h = hashlib.sha256()
    with open(out, "wb") as o:
        for p in m["parts"]:
            with open(os.path.join(pdir, p["name"]), "rb") as f:
                buf = f.read()
            if hashlib.sha256(buf).hexdigest() != p["sha256"]:
                sys.exit("checksum mismatch in " + p["name"])
            h.update(buf); o.write(buf)
    if h.hexdigest() != m["sha256"]:
        sys.exit("final checksum mismatch for " + out)
    print("OK", out, m["bytes"], "bytes")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        for r, ds, _ in os.walk(sys.argv[2]):
            for d in ds:
                if d.endswith(".parts"):
                    rejoin(os.path.join(r, d))
    elif len(sys.argv) == 2:
        rejoin(sys.argv[1])
    else:
        sys.exit(__doc__)
