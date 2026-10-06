#!/usr/bin/env python3
"""Broader hunt for missing titles.
For each slug: try multiple Libgen query variants + multiple mirrors, filter out
journal rows, and also query Internet Archive (loose + author). Emit a report and
a download list of the best PDF/EPUB candidate per title.
"""
import os, re, sys, json, time, urllib.parse, urllib.request, http.cookiejar, ssl
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
LG=["libgen.li","libgen.vg","libgen.gl","libgen.bz","libgen.la"]
_cj=http.cookiejar.CookieJar()
_op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj),urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
def http(u,ref=None,t=25):
    h={"User-Agent":UA}
    if ref:h["Referer"]=ref
    return _op.open(urllib.request.Request(u,headers=h),timeout=t).read()
JOURNAL=re.compile(r"(?i)\b(vol\.?\s*\d|iss\.?\s*\d|pp\.?\s*\d|review|rezension|journal|quarterly|speculum|historical review|anzeiger)\b")
PUB=re.compile(r"(?i)(press|university|verlag|publishing|routledge|palgrave|cambridge|oxford|yale|princeton|harvard|hopkins|brill|wiley|blackwell|springer|gruyter|manchester|macmillan|longman|clarendon|variorum|ashgate|boydell|osprey)")
def rows_from(html):
    out=[]
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>",html,re.S):
        ids=re.findall(r"md5=([a-fA-F0-9]{32})",r); eid=re.search(r"edition\.php\?id=(\d+)",r)
        txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",r)).strip()
        ext=re.findall(r"(?i)\b(epub|pdf|mobi|azw3|djvu|fb2)\b",r)
        if not (ids or eid) or len(txt)<25: continue
        out.append({"md5":ids[0] if ids else None,"eid":eid.group(1) if eid else None,
                    "ext":list(dict.fromkeys(e.lower() for e in ext))[:4],"text":txt[:190]})
    return out
def lg_search(q):
    for host in LG:
        try:
            base=f"https://{host}/"
            h=http(base+"index.php?"+urllib.parse.urlencode({"req":q}),ref=base).decode("utf-8","replace")
            r=rows_from(h)
            if r: return host,r
        except Exception: continue
    return None,[]
def ia(q, creator=None):
    p=[("q",q)]+[("fl[]","identifier"),("fl[]","title"),("fl[]","creator"),("fl[]","year"),("fl[]","collection"),("fl[]","access-restricted-item"),("rows","10"),("output","json")]
    qq=q+(f' AND creator:("{creator}")' if creator else "")
    try:
        return json.loads(http("https://archive.org/advancedsearch.php?"+urllib.parse.urlencode([("q",qq)]+p[1:])))["response"]["docs"]
    except Exception: return []
FREE=("opensource","digitallibraryindia","americana","community","additional_collections","universallibrary","toronto","europeanlibraries","JaiGyan","cdl")
def score(row,title,author):
    t=row["text"]; s=0
    if not any(e in ("pdf","epub") for e in row["ext"]): s-=2
    jm=JOURNAL.search(t); pm=PUB.search(t)
    if jm and not pm: return -99
    if jm: s-=3
    if pm: s+=2
    sn=author.split(";")[0].split()[-1].lower() if author else ""
    if sn and sn in t.lower(): s+=3
    words=[w for w in re.findall(r"[a-zA-Z]{4,}",title.lower()) if w not in ("the","and","from","with","their","under","during","history","study")]
    s+=min(sum(1 for w in words if w in t.lower()),5)
    return s

TITLES=json.load(open("/tmp/missing_titles.json"))
report=["# Missing-title re-hunt — 2026-09-13\n"]
dl=[]
for i,w in enumerate(TITLES,1):
    slug,title,author=w["slug"],w["title"],w["author"]
    variants=[title, title+" "+author.split(";")[0], " ".join(title.split()[:4])+" "+author.split(";")[0]]
    variants=[re.sub(r"\(.*?\)"," ",v) for v in variants]
    rows=[]
    for v in variants:
        host,r=lg_search(re.sub(r"[;:]"," ",v))
        rows+= [dict(x,host=host) for x in r]
        if rows: break
        time.sleep(0.5)
    scored=sorted((dict(x,sc=score(x,title,author)) for x in rows if x.get("md5")), key=lambda x:-x["sc"])
    good=[x for x in scored if x["sc"]>=2]
    ia_docs=ia(title)
    ia_free=[d for d in ia_docs if any(c in FREE for c in (d.get("collection") if isinstance(d.get("collection"),list) else [d.get("collection")] or [])) and str(d.get("access-restricted-item")).lower()!="true"]
    report.append(f"\n## {i}. {title} — {author}\n")
    if good:
        b=good[0]; report.append(f"- **PICK** md5={b['md5']} {b['ext']} sc={b['sc']} :: {b['text'][:120]}\n")
        dl.append(f"{slug} {b['md5']}")
        for a in good[1:3]: report.append(f"    - alt sc={a['sc']} md5={a['md5']} {a['ext']} :: {a['text'][:100]}\n")
    else:
        report.append(f"- Libgen: none (rows={len(rows)})\n")
    if ia_free:
        report.append(f"- IA free: "+", ".join(f"{d.get('identifier')}" for d in ia_free[:3])+"\n")
    print(f"[{i}/{len(TITLES)}] {slug}: rows={len(rows)} pick={'Y' if good else 'n'} ia_free={len(ia_free)}",flush=True)
    time.sleep(1.2)
open("/tmp/missing_report.md","w").write("".join(report))
open("/tmp/missing_dl.txt","w").write("\n".join(dl)+"\n")
print(f"\npicks: {len(dl)} -> /tmp/missing_dl.txt")
