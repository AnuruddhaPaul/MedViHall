"""List works citing the known papers (OpenAlex cites: filter), published since 2026-06-01. Cached via lit_tool."""
import json
import lit_tool as L

KNOWN = {"2605.20469": "HalluCXR", "2606.14697": "ClinHallu", "2509.21979": "Sycophancy-Med-VLM",
         "2406.10185": "Med-HallMark", "2502.20780": "MedHallTune", "2412.18947": "MedHallBench", "2604.02543": "Byun-calibration"}
out = {}
for aid, name in KNOWN.items():
    w = json.loads(L._cached_get(f"https://api.openalex.org/works/https://doi.org/10.48550/arxiv.{aid}", {"mailto": "anuruddhapaul4@gmail.com"}, False))
    wid = w["id"].split("/")[-1]
    page = json.loads(L._cached_get("https://api.openalex.org/works",
        {"filter": f"cites:{wid},from_publication_date:2026-06-01", "per-page": 100, "sort": "publication_date:desc",
         "mailto": "anuruddhapaul4@gmail.com"}, False))
    print(f"\n== {name} ({aid}) openalex={wid} cited_by_total={w.get('cited_by_count')} citing_since_0601={page['meta']['count']}")
    out[aid] = []
    for r in page["results"]:
        loc = r.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name")
        print(" ", r["publication_date"], "|", (src or "")[:30], "|", (r["title"] or "")[:100], "|", r.get("doi"))
        out[aid].append({"date": r["publication_date"], "venue": src, "title": r["title"], "doi": r.get("doi")})
json.dump(out, open("lit_cache/citing.json", "w", encoding="utf-8"), indent=1)
