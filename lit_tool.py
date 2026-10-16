"""Small literature-search helper for MedViHall (stdlib + requests).

Functions
---------
arxiv_search(query, start_date, max_results, cats=None)  -> list[dict]
arxiv_get(arxiv_id)                                      -> dict | None
openalex_search(query, from_date, per_page=25)           -> list[dict]

Every HTTP response is cached under lit_cache/ (keyed by URL+params), so reruns
are free. arXiv calls are spaced >= 3 s apart (only for uncached requests).
"""
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET

import requests

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lit_cache")
ARXIV_URL = "https://export.arxiv.org/api/query"
OPENALEX_URL = "https://api.openalex.org/works"
NS = {"a": "http://www.w3.org/2005/Atom", "ax": "http://arxiv.org/schemas/atom"}
HEADERS = {"User-Agent": "MedViHall-lit-check/1.0 (mailto:anuruddhapaul4@gmail.com)"}
_last_arxiv_call = 0.0


def _cached_get(url, params, is_arxiv):
    """GET with on-disk cache. Returns response text."""
    global _last_arxiv_call
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    path = os.path.join(CACHE_DIR, key + ".txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    if is_arxiv:
        wait = 3.0 - (time.time() - _last_arxiv_call)
        if wait > 0:
            time.sleep(wait)
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=60)
        except (requests.ConnectionError, requests.Timeout):
            if is_arxiv:
                _last_arxiv_call = time.time()
            if attempt == 3:
                raise
            time.sleep(10 * (attempt + 1))
            continue
        if is_arxiv:
            _last_arxiv_call = time.time()
        if r.status_code == 200:
            break
        if r.status_code in (429, 503):
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
    else:
        r.raise_for_status()
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.text)
    return r.text


def _parse_entry(e):
    g = lambda tag: (e.findtext(tag, namespaces=NS) or "").strip()
    full_id = g("a:id")
    m = re.search(r"arxiv\.org/abs/(.+)$", full_id)
    aid_v = m.group(1) if m else full_id
    aid = re.sub(r"v\d+$", "", aid_v)
    ver = re.search(r"v(\d+)$", aid_v)
    doi = e.find("ax:doi", NS)
    jref = e.find("ax:journal_ref", NS)
    comment = e.find("ax:comment", NS)
    return {
        "id": aid,
        "version": int(ver.group(1)) if ver else None,
        "title": re.sub(r"\s+", " ", g("a:title")),
        "authors": [a.findtext("a:name", namespaces=NS).strip() for a in e.findall("a:author", NS)],
        "published": g("a:published"),
        "updated": g("a:updated"),
        "abstract": re.sub(r"\s+", " ", g("a:summary")),
        "categories": [c.get("term") for c in e.findall("a:category", NS)],
        "doi": doi.text.strip() if doi is not None and doi.text else None,
        "journal_ref": jref.text.strip() if jref is not None and jref.text else None,
        "comment": comment.text.strip() if comment is not None and comment.text else None,
        "url": f"https://arxiv.org/abs/{aid}",
    }


def arxiv_search(query, start_date="2026-06-01", max_results=50,
                 cats=("cs.CV", "cs.CL", "cs.AI", "cs.LG", "eess.IV"), end_date=None, start=0):
    """Search arXiv, newest first, restricted to categories and submittedDate >= start_date.

    `query` is an arXiv search_query fragment, e.g. 'abs:"medical" AND abs:hallucination'
    or plain words (wrapped as all:...).
    """
    if not re.search(r"\b(all|ti|abs|au|cat):", query):
        query = " AND ".join(f"all:{w}" for w in query.split())
    q = f"({query})"
    if cats:
        q += " AND (" + " OR ".join(f"cat:{c}" for c in cats) + ")"
    sd = start_date.replace("-", "") + "0000"
    ed = (end_date or "2026-12-31").replace("-", "") + "2359"
    q += f" AND submittedDate:[{sd} TO {ed}]"
    params = {"search_query": q, "start": start, "max_results": max_results,
              "sortBy": "submittedDate", "sortOrder": "descending"}
    root = ET.fromstring(_cached_get(ARXIV_URL, params, True))
    return [_parse_entry(e) for e in root.findall("a:entry", NS)]


def arxiv_get(arxiv_id):
    """Fetch one paper's metadata by arXiv id (version suffix allowed). None if absent."""
    params = {"id_list": arxiv_id, "max_results": 1}
    root = ET.fromstring(_cached_get(ARXIV_URL, params, True))
    entries = root.findall("a:entry", NS)
    if not entries:
        return None
    d = _parse_entry(entries[0])
    if d["title"].lower() == "error" or "api/errors" in entries[0].findtext("a:id", namespaces=NS, default=""):
        return None
    return d


def _abstract_from_inverted(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def openalex_search(query, from_date="2026-06-01", per_page=25):
    """Search OpenAlex works published since from_date (any venue; check `venue` field)."""
    params = {"search": query, "filter": f"from_publication_date:{from_date}",
              "sort": "relevance_score:desc", "per-page": per_page,
              "mailto": "anuruddhapaul4@gmail.com"}
    data = json.loads(_cached_get(OPENALEX_URL, params, False))
    out = []
    for w in data.get("results", []):
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        out.append({
            "openalex_id": w.get("id"),
            "doi": w.get("doi"),
            "title": w.get("title"),
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
            "published": w.get("publication_date"),
            "venue": src.get("display_name"),
            "type": w.get("type"),
            "abstract": _abstract_from_inverted(w.get("abstract_inverted_index")),
            "landing": loc.get("landing_page_url"),
        })
    return out


def doi_get(doi):
    """Fetch registrar metadata for a DOI via doi.org content negotiation (CSL JSON + BibTeX).
    Returns dict {csl, bibtex} or None if the DOI does not resolve."""
    doi = doi.replace("https://doi.org/", "")
    out = {}
    for name, accept in (("csl", "application/vnd.citationstyles.csl+json"), ("bibtex", "application/x-bibtex")):
        url = "https://doi.org/" + doi
        key = hashlib.sha1((url + accept).encode()).hexdigest()
        path = os.path.join(CACHE_DIR, key + ".txt")
        os.makedirs(CACHE_DIR, exist_ok=True)
        if os.path.exists(path):
            txt = open(path, encoding="utf-8").read()
        else:
            r = requests.get(url, headers={**HEADERS, "Accept": accept}, timeout=60, allow_redirects=True)
            if r.status_code != 200:
                return None
            txt = r.text
            open(path, "w", encoding="utf-8").write(txt)
        out[name] = json.loads(txt) if name == "csl" else txt
    return out
