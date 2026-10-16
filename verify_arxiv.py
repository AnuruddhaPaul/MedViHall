"""Verify shortlisted arXiv ids with arxiv_get (primary-source metadata); save to lit_cache/verified_arxiv.json."""
import json
import sys

import lit_tool as L

SHORT = """2609.31733 2609.22302 2609.00866 2609.29604 2609.03953 2608.27004 2608.17427 2608.12086 2608.10964
2608.04885 2608.02790 2608.28623 2607.27304 2607.21105 2607.18828 2607.03647 2607.01973 2606.28520 2606.27596
2606.27500 2606.27264 2606.27023 2606.26874 2606.24155 2606.24115 2606.22144 2606.21194 2606.19950 2606.18609
2606.16583 2606.15910 2606.13211 2606.28556 2609.24190 2608.07651 2609.33158 2609.17800 2610.00381 2609.06419
2607.09135 2607.15241 2608.26382 2607.18448 2606.17213 2609.04281 2609.38810 2608.24118 2607.26886 2606.30201
2609.32185 2609.00067 2608.23666 2610.11312 2609.33280 2608.07550 2608.01462 2606.10066 2607.15661 2607.25589
2608.30390 2608.11534 2608.00100 2606.20852 2607.00060 2609.28796""".split()
KNOWN = """2605.20469 2606.14697 2509.21979 2406.10185 2502.20780 2412.18947 2604.02543""".split()


def main():
    out = {}
    for aid in KNOWN + SHORT:
        try:
            d = L.arxiv_get(aid)
        except Exception as ex:
            print("ERR", aid, ex)
            out[aid] = {"verified": False, "error": str(ex)}
            continue
        if d is None:
            print("NOT FOUND", aid)
            out[aid] = {"verified": False, "error": "not found in arXiv API"}
        else:
            d["verified"] = True
            out[aid] = d
            print("OK", aid, f"v{d['version']}", d["published"][:10], d["updated"][:10], d["title"][:80])
    json.dump(out, open("lit_cache/verified_arxiv.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
