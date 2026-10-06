#!/usr/bin/env python3
"""Libgen book picker: for each work, search libgen, reject scimag/journal rows,
score remaining rows as book candidates, emit high-confidence md5 picks + alternatives.
Reads works TSV. Writes /tmp/book_dl_list.txt, /tmp/book_picks.json, exports/book-picks.md
"""
import sys, json, re, time, urllib.parse, urllib.request, http.cookiejar, ssl
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
LG_HOSTS=["libgen.li","libgen.vg","libgen.gl","libgen.bz","libgen.la"]
_cj=http.cookiejar.CookieJar()
_op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj),
      urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
def http(u,ref=None,t=30):
    h={"User-Agent":UA}
    if ref:h["Referer"]=ref
    return _op.open(urllib.request.Request(u,headers=h),timeout=t).read()

JOURNAL=re.compile(r"(?i)\b(vol\.?\s*\d|iss\.?\s*\d|pp\.?\s*\d|review|rezension|compte rendu|journal|quarterly|speculum|historical review|american historical|ehr\b)")
PUBLISHER=re.compile(r"(?i)(press|university|verlag|publishing|routledge|palgrave|cambridge|oxford|yale|princeton|harvard|johns hopkins|brill|wiley|blackwell|springer|de gruyter|manchester|macmillan|longman|clarendon|variorum|ashgate|boydell)")
DIGITAL=re.compile(r"^10\.\d{4,}")

def parse_rows(html):
    out=[]
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        ids=re.findall(r"md5=([a-fA-F0-9]{32})", r)
        eid=re.search(r"edition\.php\?id=(\d+)", r)
        txt=re.sub(r"\s+"," ", re.sub(r"<[^>]+>"," ", r)).strip()
        ext=re.findall(r"(?i)\b(epub|pdf|mobi|azw3|djvu|fb2)\b", r)
        if not (ids or eid) or len(txt)<25: continue
        out.append({"md5":ids[0] if ids else None,"eid":eid.group(1) if eid else None,
                    "ext":list(dict.fromkeys(e.lower() for e in ext))[:4],"text":txt[:200]})
    return out

def search(title,author):
    q=title+(" "+author.split(";")[0] if author else "")
    q=re.sub(r"\(.*?\)"," ",q); q=re.sub(r"[;:,]"," ",q); q=re.sub(r"\s+"," ",q).strip()
    for host in LG_HOSTS:
        try:
            base=f"https://{host}/"
            html=http(base+"index.php?"+urllib.parse.urlencode({"req":q}),ref=base,t=25).decode("utf-8","replace")
            rows=parse_rows(html)
            if rows: return host,rows
        except Exception as e:
            last=str(e); continue
    return None,[]

def score(row, title, author):
    t=row["text"]; s=0
    has_pdf=any(e in ("pdf","epub") for e in row["ext"])
    if not has_pdf: s-=2
    jm=JOURNAL.search(t); pm=PUBLISHER.search(t)
    if jm and not pm: return -99          # journal review/article
    if jm: s-=3
    if pm: s+=3
    if DIGITAL.match(t): s-=1             # DOI-named file: mild negative, not fatal
    surname=author.split(";")[0].split()[-1].lower() if author else ""
    if surname and surname in t.lower(): s+=3
    tl=[w for w in re.findall(r"[a-zA-Z]{4,}", title.lower()) if w not in ("the","and","from","with","their","under","during","history")]
    hits=sum(1 for w in tl if w in t.lower())
    s+=min(hits,5)
    return s

works=[]
for line in open(sys.argv[1]):
    p=line.rstrip("\n").split("\t")
    if len(p)>=4: works.append({"slug":p[0],"prio":p[1],"title":p[2],"author":p[3]})

picks=[]; report=["# Book picks (filtered) — 2026-09-13\n"]
for i,w in enumerate(works,1):
    host,rows=search(w["title"],w["author"])
    scored=sorted(({"score":score(r,w["title"],w["author"]),**r} for r in rows), key=lambda x:-x["score"])
    good=[r for r in scored if r["score"]>=3 and r["md5"]]
    alts=[r for r in scored if r["md5"]][:3]
    best=good[0] if good else None
    picks.append({"slug":w["slug"],"prio":w["prio"],"title":w["title"],"author":w["author"],
                  "host":host,"best":best,"alts":alts})
    report.append(f"\n## {i}. {w['title']} — {w['author']} [{w['prio']}]\n")
    if best:
        report.append(f"- **PICK** md5={best['md5']} {best['ext']} score={best['score']} :: {best['text'][:120]}\n")
    else:
        report.append(f"- no confident book match (host={host}, rows={len(rows)})\n")
    for a in alts[:3]:
        report.append(f"    - alt score={a['score']} md5={a['md5']} {a['ext']} :: {a['text'][:110]}\n")
    print(f"[{i}/{len(works)}] {w['slug']}: rows={len(rows)} pick={'Y' if best else 'n'}", flush=True)
    time.sleep(1.2)

json.dump(picks,open("/tmp/book_picks.json","w"),ensure_ascii=False,indent=1)
with open("/tmp/book_dl_list.txt","w") as f:
    for p in picks:
        if p["best"]: f.write(f"{p['slug']} {p['best']['md5']}\n")
open("exports/book-picks.md","w").write("".join(report))
n=sum(1 for p in picks if p["best"])
print(f"\nconfident picks: {n}/{len(works)} -> /tmp/book_dl_list.txt ; report exports/book-picks.md")
