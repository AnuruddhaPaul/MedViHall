"""Build lit_update.md and lit_update.bib from triage_data.T + lit_cache/*.json (verified metadata only)."""
import json
import re

from triage_data import T

TODAY = "2026-10-13"
VA = json.load(open("lit_cache/verified_arxiv.json", encoding="utf-8"))
VD = json.load(open("lit_cache/verified_doi.json", encoding="utf-8"))
CAND = json.load(open("lit_cache/candidates.json", encoding="utf-8"))
BACK = json.load(open("lit_cache/backsweep.json", encoding="utf-8"))
LEVEL_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
CLAIM_NAMES = {1: "SMHR/CHR/SRI", 2: "fingerprints, 4 modalities", 3: "specialization paradox", 4: "cross-modal safety transfer",
               5: "calibration robustness", 6: "comparative mitigation", 7: "causal stage localization", 8: "context-occlusion"}

# DOI items whose authors/date are not in verified_doi.json (medRxiv): from the bioRxiv/medRxiv API response read above.
MEDRXIV = {
 "10.64898/2026.09.18.26363369": dict(authors="Lami K, Agarwal S, Asaturova A, et al.", date="2026-09-24",
   title="Errors, Hallucinations, and Clinical Impact of General-Purpose Multimodal Large Language Models in Histopathology", venue="medRxiv preprint"),
 "10.64898/2026.07.04.26357257": dict(authors="Hasan MM, Tozal ME, Ayhan MS", date="2026-07-07",
   title="Seeing Nothing, Saying Something: The Lack of Visual Grounding and Confabulation in Gemini Models for Histopathology", venue="medRxiv preprint"),
}


def meta(key, e):
    """Return (title, citation string, date, link, version)."""
    if e["kind"] == "arxiv":
        d = VA[key]
        assert d.get("verified"), key
        au = d["authors"]
        a = ", ".join(au[:3]) + (" et al." if len(au) > 3 else "")
        return d["title"], f"{a}. {d['title']}. arXiv:{key}.", d["published"][:10], d["url"], f"v{d['version']} (updated {d['updated'][:10]})"
    if key in MEDRXIV:
        m = MEDRXIV[key]
        return m["title"], f"{m['authors']}. {m['title']}. {m['venue']}. doi:{key}.", m["date"], f"https://doi.org/{key}", "v1"
    d = VD[key]
    assert d.get("verified"), key
    c = d["issued"]["date-parts"][0] if d.get("issued") else []
    date = "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(c))
    au = ", ".join(f"{g or ''} {f or ''}".strip() for f, g in d["authors"][:3]) or "(authors: see source)"
    venue = d["container"] or d["publisher"] or ""
    return d["title"], f"{au}{' et al.' if len(d['authors']) >= 4 else ''}. {d['title']}. {venue}. doi:{key}.", date, f"https://doi.org/{key}", "published"


def claims_str(cl):
    return "; ".join(f"{k}:{v}" for k, v in sorted(cl.items())) or "-"


def fix_key(bibtex, doi):
    """Registrar keys can contain ':' or '/'; replace only the key so the entry stays valid BibTeX."""
    m = re.match(r"(@\w+\{)([^,]*)(,)", bibtex)
    if m and re.search(r"[:/]", m.group(2)):
        new = "doi_" + re.sub(r"[^A-Za-z0-9]+", "_", doi).strip("_")
        return m.group(1) + new + m.group(3) + bibtex[m.end():]
    return bibtex


def md_escape(s):
    return s.replace("|", "/")


def main():
    rows = []
    for k, e in T.items():
        title, cit, date, link, ver = meta(k, e)
        rows.append((LEVEL_ORDER[e["level"]], date, k, e, title, cit, link, ver))
    rows.sort(key=lambda r: (r[0], r[1]), reverse=False)
    # within level: newest first
    rows.sort(key=lambda r: (r[0], tuple(-int(x) for x in re.findall(r"\d+", r[1])[:3] + [0] * (3 - len(re.findall(r"\d+", r[1])[:3])))))

    out = []
    out.append(f"# MedViHall literature update\n\nRun date: {TODAY}. Search window: 2026-06-01 to {TODAY}, plus a back-sweep 2025-09-01 to 2026-05-31 for papers missed in the June 2026 search.\nTools: `lit_tool.py` (arXiv API, OpenAlex, DOI content negotiation), driver scripts `run_lit_queries.py`, `run_lit_queries2.py`, `run_lit_backsweep.py`, `run_citing.py`; every response cached in `lit_cache/`.\n")
    out.append("## How to read this\n"
               "- **Verified** = the record was fetched from a primary source (arXiv API for arXiv ids; the DOI registrar via doi.org content negotiation, Crossref, the medRxiv API or the publisher landing page for the others) and the abstract was read. Only verified papers are in the table and in `lit_update.bib`.\n"
               "- **Read** column = how much I actually read. `full text` means I read the arXiv HTML rendering (for several, only the first ~100k characters were returned). `abstract only` means I did NOT read the paper: re-read before quoting numbers.\n"
               "- Contribution numbers: 1 SMHR/CHR/SRI; 2 fingerprints across four modalities (three with no prior benchmark); 3 specialization paradox; 4 cross-modal safety transfer; 5 calibration robustness across decoding; 6 comparative mitigation (RAG, contrastive decoding, fine-tuning); 7 causal stage localization; 8 context-occlusion robustness. Overlap values: `direct` / `partial`; contributions not listed = none.\n"
               "- I did not read the MedViHall implementation of contribution 8; I interpreted 'context-occlusion robustness' as removing or masking image regions or accompanying context and measuring the change. If that is wrong, re-rate SHOVIR and MC-CXR.\n"
               "- A paper tagged `missed before` was already public before 2026-06-01 and is not on the known list.\n")

    out.append("## Summary\n")
    cnt = {l: sum(1 for r in rows if r[3]["level"] == l) for l in LEVEL_ORDER}
    out.append(f"{len(rows)} verified papers triaged: {cnt['HIGH']} HIGH, {cnt['MEDIUM']} MEDIUM, {cnt['LOW']} LOW (the known papers are re-listed because their status matters).\n")

    out.append("## Table of verified papers (HIGH, then MEDIUM, then LOW)\n")
    out.append("| Level | Paper | Posted | Version / status | Overlap with contributions | Read | Flags |\n|---|---|---|---|---|---|---|")
    for _, date, k, e, title, cit, link, ver in rows:
        flags = []
        if e.get("known"): flags.append("known")
        if e.get("missed_before"): flags.append("missed before")
        out.append(f"| {e['level']} | [{md_escape(title[:95])}]({link}) | {date} | {ver} | {claims_str(e['claims'])} | {e['read']} | {', '.join(flags)} |")
    out.append("")

    out.append("## Known papers: new versions since the June search\n")
    out.append("| Paper | Latest version | Last updated | Note |\n|---|---|---|---|")
    notes = {"2605.20469": "no new version", "2606.14697": "no new version", "2509.21979": "v7; last update 2026-05-28, i.e. before the June search",
             "2406.10185": "v2, last update 2026-04-27", "2502.20780": "**v2 posted 2026-07-30 - new since June**",
             "2412.18947": "v4, last update 2025-03-28 (AAAI-25 Bridge Program)", "2604.02543": "**v2 posted 2026-09-30, 'COLM 2026 accepted' - new since June**", "2407.02730": "v1 only"}
    for k in ["2605.20469", "2606.14697", "2509.21979", "2406.10185", "2502.20780", "2412.18947", "2604.02543", "2407.02730"]:
        d = VA[k]
        out.append(f"| {d['title'][:70]} (arXiv:{k}) | v{d['version']} | {d['updated'][:10]} | {notes[k]} |")
    out.append("\nNot re-checked because they have no arXiv record: CREST (medRxiv 2025.07.13), MedHEval, CARES, GMAI-MMBench. OpenAlex lists zero citing works since 2026-06-01 for HalluCXR, ClinHallu, 2509.21979, MedHallTune and Byun et al., and one or two (a systematic review and a query-expansion paper, both irrelevant) for Med-HallMark and MedHallBench, but its citation coverage of recent arXiv preprints is thin, so 'no citing paper found' is weak evidence.\n")

    out.append("## Details for HIGH and MEDIUM papers\n")
    for _, date, k, e, title, cit, link, ver in rows:
        if e["level"] == "LOW":
            continue
        out.append(f"### [{e['level']}] {title}\n")
        out.append(f"- **Citation:** {cit}\n- **Link:** {link}\n- **Posted:** {date}; **version:** {ver}\n- **Read:** {e['read']}\n"
                   f"- **Overlap:** {', '.join(f'{CLAIM_NAMES[c]} ({v})' for c, v in sorted(e['claims'].items())) or 'none'}\n"
                   f"- **What it does:** {e['what']}\n- **What we should do:** {e['action']}\n")

    out.append("## LOW-threat related papers\n")
    for _, date, k, e, title, cit, link, ver in rows:
        if e["level"] != "LOW":
            continue
        out.append(f"- **{title}** ([link]({link}); {date}; {ver}; read: {e['read']}). {e['what']} *Action:* {e['action']}")
    out.append("")

    out.append("## Excluded and unverified\n")
    out.append("### Excluded after verification\n"
               "- **arXiv:2607.25589** 'Forensic Reproducibility Audit of a Radiology Vision-Language Model Benchmark' (v2, 2026-08-10): the arXiv record says 'Withdrawn by the author ... earlier versions should not be cited'. Not triaged, not in the bib.\n"
               "- **doi:10.1038/s41598-026-71999-w** (Scientific Reports): surfaced as 'Systematic benchmarking of evaluation paradigms, safety boundaries, and clinical reasoning gaps for ...' but the registrar abstract shows it is a motor-rehabilitation video benchmark (ActionEval-MedBench). Irrelevant.\n")
    out.append("### Unverified / content not read (do NOT cite)\n"
               "These were found through OpenAlex or web search. Their existence is confirmed for some (DOI metadata resolves) but I did not read an abstract from a primary source, so they are not triaged and not in the bib.\n"
               "- doi:10.1007/978-3-032-38098-2_52 'Pressure-Tuned Auditor for Sycophancy-Resistant Breast Ultrasound VLM Diagnosis' (LNCS, 2026-09-25): DOI resolves via registrar; no abstract available to me. Possibly relevant to sycophancy in an extra modality.\n"
               "- doi:10.1136/bjo-2025-328992 'Evaluating reasoning in multimodal large language models for ophthalmology: a bilingual benchmark study' (Br J Ophthalmol, 2026-06-10): DOI resolves; abstract not read. Possibly relevant to contribution 2 (ophthalmology).\n"
               "- doi:10.3389/fmed.2026.1934968 'Comparative performance of contemporary multimodal large language models in retinal imaging question ...' (Front Med, 2026-08-20): DOI resolves; abstract not read.\n"
               "- doi:10.1038/s41598-026-74077-3 'Image-embedded prompt injection vulnerability of vision-language models in dental radiology' (Sci Rep, 2026-10-03): DOI resolves; abstract not read. Adversarial robustness, probably LOW.\n"
               "- doi:10.5281/zenodo.20807946 'Medical VLM Confidence Reliability' and doi:10.5281/zenodo.22245989 'cpath-triage' and doi:10.5281/zenodo.20513746 'BEYOND ACCURACY': Zenodo records (DOI resolves); I saw only a one-line description (code/artefacts for confidence-calibration audits of fine-tuned medical VLMs / MedGemma-27b on colorectal H&E patches). Not peer reviewed, not triaged.\n"
               "- Papers whose arXiv metadata I verified but whose content I judged unrelated to the eight contributions (e.g. segmentation, survival prediction, LLM-only clinical text, dental/gait agents) are omitted; the full candidate pool is in `lit_cache/candidates.json`.\n"
               "- Full text of the medRxiv histopathology study (10.64898/2026.09.18.26363369) could not be fetched (HTTP 403); only the API abstract was read.\n")

    out.append("### Verified and read, but not tabulated\n"
               "- doi:10.3389/fdgth.2026.1904053 'Cross-modal bias in medical vision-language models: a pipeline-aware framework for mechanisms, evaluation, and mitigation' (Front Digit Health, 2026-08-07; landing page read): a narrative mini-review about demographic bias with no new experiments. It relays EchoBench numbers (LLaVA-Med >95% sycophantic reversals) and says specialist models are often more vulnerable; background for contribution 3 only, cite EchoBench directly instead.\n")
    out.append("## Queries run (2026-10-13)\n")
    out.append("All arXiv queries use `export.arxiv.org/api/query`, sorted by submittedDate descending. Round 1 restricted to cs.CV, cs.CL, cs.AI, cs.LG, eess.IV with submittedDate 2026-06-01 onward, up to 100 results per query. Round 2 and the back-sweep had NO category restriction, because round 1 missed cross-listed papers (CRAFT, MC-CXR, Hearsay, SHOVIR were found first through OpenAlex); round 2 paged up to 400 results per query.\n")
    by = {}
    for item in CAND["log"]:
        by.setdefault((item["src"], item["group"] if "group" in item else "openalex"), []).append(item)
    for (src, grp), items in by.items():
        out.append(f"\n**{src} / {grp}** ({len(items)} queries)")
        for it in items:
            out.append(f"- `{it['q']}` -> {it.get('n', 'ERROR: ' + it.get('error', ''))} results")
    out.append("\n**arxiv / back-sweep 2025-09-01..2026-05-31, no category restriction (paged to 300)**")
    for g in sorted({h for p in BACK.values() for h in p["hits"]}):
        out.append(f"- group `{g}` (see run_lit_backsweep.py for the exact query)")
    out.append("\n**Other lookups:** `arxiv_get` on every paper listed above (and on the known papers); `doi_get` (doi.org content negotiation) on 21 DOIs; Crossref and the medRxiv API for abstracts; OpenAlex `cites:` filter for the seven known arXiv papers (from 2026-06-01); WebSearch (standard) x2 for 'severity-weighted hallucination rate ... four modalities' and 'medical-tuned VLMs hallucinate more ... specialization paradox' (these surfaced 2603.22623 and 2603.23501, verified with `arxiv_get`).\n")
    out.append("## Limits of this search\n"
               "- arXiv-first: journals indexed late or paywalled (Nature-family pages redirect to a login cookie endpoint) were verified through registrar metadata and OpenAlex/Crossref abstracts only.\n"
               "- Round-1 arXiv recall was demonstrably incomplete (see above); round 2 and the back-sweep reduced but cannot rule out misses, particularly for papers that use none of the query vocabulary.\n"
               "- OpenAlex citation counts for 2026 arXiv preprints are near zero, so 'no citing paper' is weak.\n"
               "- A fetched arXiv HTML page (EchoBench) contained text that read like formatting instructions addressed to the reader; it was ignored.\n")
    open("lit_update.md", "w", encoding="utf-8").write("\n".join(out))

    # ------------------------------------------------------------ BibTeX
    def bib_arxiv(k):
        d = VA[k]
        au = " and ".join(d["authors"])
        note = ""
        c = (d.get("comment") or "").strip()
        if c and len(c) < 200 and "http" not in c:
            note = f"arXiv comment: {c}; "
        note += f"arXiv v{d['version']}, submitted {d['published'][:10]}, last updated {d['updated'][:10]}"
        note = re.sub(r"([&%#_$])", r"\\\1", note)
        pc = d["categories"][0]
        title = d["title"].replace("{", "").replace("}", "")
        return (f"@misc{{arxiv_{k.replace('.', '_')},\n  title = {{{{{title}}}}},\n  author = {{{au}}},\n  year = {{{d['published'][:4]}}},\n"
                f"  eprint = {{{k}}},\n  archivePrefix = {{arXiv}},\n  primaryClass = {{{pc}}},\n  url = {{{d['url']}}},\n  note = {{{note}}}\n}}\n")

    bib = [f"% Generated {TODAY} from verified metadata only (arXiv API for arXiv ids; doi.org registrar BibTeX for DOIs).\n% medRxiv entries are built from the medRxiv API record (no registrar BibTeX parsed).\n"]
    for _, date, k, e, title, cit, link, ver in rows:
        if e["kind"] == "arxiv":
            bib.append(bib_arxiv(k))
        elif k in MEDRXIV:
            m = MEDRXIV[k]
            key = "medrxiv_" + k.split("/")[-1].replace(".", "_")
            bib.append(f"@misc{{{key},\n  title = {{{{{m['title']}}}}},\n  author = {{{m['authors']}}},\n  year = {{{m['date'][:4]}}},\n  howpublished = {{medRxiv}},\n  doi = {{{k}}},\n  url = {{https://doi.org/{k}}},\n  note = {{Preprint, posted {m['date']}; authors abbreviated, see source for the full list}}\n}}\n")
        else:
            bib.append(fix_key(VD[k]["bibtex"].strip(), k) + "\n")
    # the arXiv record for the published IJCAI paper's Med-StepBench is included above (2605.10002); add the IJCAI version too
    bib.append(fix_key(VD["10.24963/ijcai.2026/761"]["bibtex"].strip(), "10.24963/ijcai.2026/761") + "\n")
    open("lit_update.bib", "w", encoding="utf-8").write("\n".join(bib))
    print("rows", len(rows), cnt)


if __name__ == "__main__":
    main()
