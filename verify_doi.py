import json
import lit_tool as L
DOIS = """10.1609/aies.v9i4.43348 10.1609/aies.v9i4.43343 10.1038/s41598-026-71999-w 10.64898/2026.09.18.26363369
10.1007/978-3-032-38098-2_52 10.1038/s41746-026-03191-3 10.5281/zenodo.22245989 10.24963/ijcai.2026/761
10.3389/fdgth.2026.1904053 10.1109/chase69719.2026.00073 10.5281/zenodo.21310010 10.64898/2026.07.04.26357257
10.3390/app16126064 10.20944/preprints202609.0962.v1 10.48448/ydvs-p287 10.5281/zenodo.20807946
10.1038/s41598-026-74077-3 10.1136/bjo-2025-328992 10.3389/fmed.2026.1934968 10.5281/zenodo.20513746
10.1007/978-3-032-37654-1_30""".split()
out = {}
for d in DOIS:
    try:
        r = L.doi_get(d)
    except Exception as ex:
        r = None; print("ERR", d, ex)
    if not r:
        out[d] = {"verified": False}; print("UNRESOLVED", d); continue
    c = r["csl"]
    out[d] = {"verified": True, "title": c.get("title"), "container": c.get("container-title"), "publisher": c.get("publisher"),
              "issued": c.get("issued"), "type": c.get("type"), "authors": [(a.get("family"), a.get("given")) for a in c.get("author", [])][:4],
              "abstract": (c.get("abstract") or "")[:600], "bibtex": r["bibtex"]}
    print("OK", d, "|", (c.get("title") or "")[:80], "|", c.get("container-title"), "|", c.get("issued", {}).get("date-parts"))
json.dump(out, open("lit_cache/verified_doi.json", "w", encoding="utf-8"), indent=1)
