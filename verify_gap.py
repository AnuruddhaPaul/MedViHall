import json, lit_tool as L
ids = """2601.14774 2604.09841 2604.27720 2511.09195 2605.04098 2508.00171 2602.07319 2505.00744 2401.05827 2406.06007 2503.02157
2502.15040 2407.05131 2604.03376 2405.03595 2604.16383 2604.02359 2509.18030 2411.00299 2412.15264 2410.01620 2509.25620 2401.16355
2503.12990 2406.16845 2507.19024 2606.21517 2608.31016 2408.03361 2601.11488 2609.27607""".split()
v = json.load(open('lit_cache/verified_arxiv.json', encoding='utf-8'))
for a in ids:
    d = v.get(a) if v.get(a, {}).get('verified') else None
    if not d:
        d = L.arxiv_get(a)
        if d: d['verified'] = True
        v[a] = d or {'verified': False}
    if d: print(f"\n### {a} v{d['version']} {d['published'][:10]} upd {d['updated'][:10]} | {d['title']}\n{', '.join(d['authors'][:3])}{' et al.' if len(d['authors'])>3 else ''} | {d['comment']} | jref={d['journal_ref']}\n{d['abstract'][:950]}")
    else: print("\nNOT FOUND", a)
json.dump(v, open('lit_cache/verified_arxiv.json', 'w', encoding='utf-8'), indent=1)
