#!/usr/bin/env python3
"""Book acquisition search: for each work in a TSV list, find candidate copies.
Sources: Internet Archive (advancedsearch + metadata for direct PDF) and Libgen.
Read-only. Outputs a markdown report + JSONL of candidates.
Usage: book_search.py <list.tsv> <out_prefix>
"""
import sys, json, time, re, urllib.parse, urllib.request, http.cookiejar, ssl

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
FREE_HINTS = ("opensource","digitallibraryindia","americana","community","additional_collections",
              "universallibrary","cdl","europeanlibraries","JaiGyan","toronto","librarygenesis")
LG_HOSTS = ["libgen.li","libgen.vg","libgen.gl","libgen.bz","libgen.la"]

_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj),
                                  urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))

def http(url, ref=None, t=45):
    hdr = {"User-Agent": UA}
    if ref: hdr["Referer"] = ref
    return _op.open(urllib.request.Request(url, headers=hdr), timeout=t).read()

def ia_search(title, author):
    fl = ["identifier","title","creator","year","collection","access-restricted-item","mediatype"]
    q = f'title:("{title}")'
    if author:
        a = author.split(";")[0]
        a = re.sub(r"\(.*?\)", "", a).strip()
        q += f' AND creator:("{a}")'
    p = [("q", q)] + [("fl[]", f) for f in fl] + [("rows","12"), ("output","json")]
    try:
        docs = json.loads(http("https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p)))["response"]["docs"]
    except Exception as e:
        return {"error": str(e)}
    out = []
    for d in docs:
        coll = d.get("collection"); coll = coll if isinstance(coll, list) else ([coll] if coll else [])
        restricted = str(d.get("access-restricted-item")).lower() == "true"
        free = (not restricted) and any(c in FREE_HINTS for c in coll)
        out.append({"id": d.get("identifier"), "year": d.get("year"),
                    "title": str(d.get("title"))[:90], "collections": coll[:4],
                    "restricted": restricted, "free": free, "mediatype": d.get("mediatype")})
    return {"items": out}

def ia_pdf(identifier):
    """Return direct download URL for a PDF in an IA item, if any."""
    try:
        m = json.loads(http(f"https://archive.org/metadata/{identifier}"))
    except Exception:
        return None
    files = m.get("files", [])
    pdfs = [f for f in files if f.get("name","").lower().endswith(".pdf")]
    if not pdfs: return None
    def kb(f):
        try: return int(f.get("size", 0))
        except: return 0
    pdfs.sort(key=kb, reverse=True)
    best = pdfs[0]
    return f"https://archive.org/download/{identifier}/{urllib.parse.quote(best['name'])}"

def lg_search(title, author):
    q = title + (" " + author.split(";")[0] if author else "")
    q = re.sub(r"\(.*?\)", " ", q).strip()
    q = re.sub(r"[:;,]|\b(ed|eds|tr)\.?\b", " ", q)
    q = re.sub(r"\s+", " ", q)
    for host in LG_HOSTS:
        try:
            base = f"https://{host}/"
            html = http(base+"index.php?"+urllib.parse.urlencode({"req": q}), ref=base, t=25).decode("utf-8","replace")
            rows = []
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
                ids = re.findall(r"md5=([a-fA-F0-9]{32})", r)
                eid = re.search(r"edition\.php\?id=(\d+)", r)
                txt = re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ", r)).strip()
                ext = re.findall(r"(?i)\b(epub|pdf|mobi|azw3|djvu|fb2)\b", r)
                if not (ids or eid) or len(txt) < 30: continue
                rows.append({"md5": ids[0] if ids else None, "eid": eid.group(1) if eid else None,
                             "ext": list(dict.fromkeys(e.lower() for e in ext))[:3], "text": txt[:130]})
                if len(rows) >= 6: break
            return {"host": host, "rows": rows}
        except Exception as e:
            last = str(e); continue
    return {"host": None, "rows": [], "error": last}

def main():
    lst, prefix = sys.argv[1], sys.argv[2]
    works = []
    for line in open(lst):
        line = line.rstrip("\n")
        if not line.strip(): continue
        parts = line.split("\t")
        if len(parts) < 4: continue
        works.append({"slug": parts[0], "prio": parts[1], "title": parts[2], "author": parts[3]})
    md = ["# Book acquisition search — 2026-09-13\n", f"Works: {len(works)}\n"]
    with open(prefix+".jsonl","w") as jl:
        for i, w in enumerate(works, 1):
            ia = ia_search(w["title"], w["author"])
            free = [it for it in ia.get("items",[]) if it.get("free")]
            freepdf = None
            if free:
                freepdf = ia_pdf(free[0]["id"])
            lg = lg_search(w["title"], w["author"])
            rec = {"slug": w["slug"], "prio": w["prio"], "title": w["title"], "author": w["author"],
                   "ia_free": free[:4], "ia_direct_pdf": freepdf, "libgen": lg}
            jl.write(json.dumps(rec, ensure_ascii=False)+"\n"); jl.flush()
            md.append(f"\n## {i}. {w['title']} — {w['author']}  [{w['prio']}]\n")
            md.append(f"- slug: `{w['slug']}`\n")
            if freepdf:
                md.append(f"- **IA FREE PDF:** {freepdf}\n")
            elif free:
                md.append(f"- IA free (no direct pdf): {', '.join(it['id'] or '?' for it in free[:3])}\n")
            else:
                bad = ia.get("error")
                md.append(f"- IA: none{(' ('+bad+')') if bad else ''}\n")
            if lg.get("rows"):
                md.append(f"- **Libgen ({lg['host']}):**\n")
                for r in lg["rows"][:4]:
                    md.append(f"    - md5={r['md5']} {r['ext']} :: {r['text']}\n")
            else:
                md.append(f"- Libgen: none{(' ('+str(lg.get('error'))+')') if lg.get('error') else ''}\n")
            print(f"[{i}/{len(works)}] {w['slug']}: IAfree={len(free)} IApdf={'Y' if freepdf else 'n'} LG={len(lg.get('rows',[]))}", flush=True)
            time.sleep(1.5)
    open(prefix+".md","w").write("".join(md))
    print("DONE ->", prefix+".md", prefix+".jsonl")

if __name__ == "__main__":
    main()
