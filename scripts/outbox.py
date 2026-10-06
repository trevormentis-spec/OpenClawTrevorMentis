#!/usr/bin/env python3
"""Emit MEDIA lines for newly-completed book downloads.
Moves each completed file to exports/cm4/<Author - Title>.<ext> and records it
so it is emitted exactly once. Usage: outbox.py
"""
import os, re, sys, glob, zipfile
WS="/home/ubuntu/.openclaw/workspace"
TSV=f"{WS}/tasks/book-list-2026-09-13.tsv"
SRC=f"{WS}/tmp/copyright-monitor"
DST=f"{WS}/exports/cm4"
REG=f"{WS}/tasks/cm-pushed.txt"
os.makedirs(DST, exist_ok=True)

meta={}
for line in open(TSV):
    p=line.rstrip("\n").split("\t")
    if len(p)>=4: meta[p[0]]={"title":p[2],"author":p[3]}

pushed=set(x.strip() for x in open(REG) if x.strip()) if os.path.exists(REG) else set()

def sniff(f):
    try:
        with open(f,"rb") as fh: b=fh.read(8)
    except OSError:
        return None
    if b[:4]==b"%PDF": return "pdf"
    if b[:2]==b"PK":
        return "epub" if zipfile.is_zipfile(f) else "zip"
    return None

def complete(f):
    if not os.path.isfile(f) or os.path.getsize(f)==0: return False
    k=sniff(f)
    if k=="pdf":
        try:
            with open(f,"rb") as fh:
                fh.seek(max(0,os.path.getsize(f)-8192)); return b"%%EOF" in fh.read()
        except OSError: return False
    return k in ("epub","zip")

def best(slug):
    d=os.path.join(SRC,slug)
    if not os.path.isdir(d): return None
    cands=[f for f in glob.glob(d+"/*") if complete(f) and os.path.getsize(f)>20000]
    if not cands: return None
    cands.sort(key=os.path.getsize, reverse=True)
    return cands[0]

def sane(s):
    s=re.sub(r"[\\/:*?\"<>|]", "-", s); s=re.sub(r"\s+"," ",s).strip()
    return s[:120]

new=[]
for slug in meta:
    if slug in pushed: continue
    f=best(slug)
    if not f: continue
    k=sniff(f); e=".pdf" if k=="pdf" else ".epub"
    name=f"{sane(meta[slug]['author'])} - {sane(meta[slug]['title'])}{e}"
    dest=os.path.join(DST,name)
    if os.path.exists(dest): dest=os.path.join(DST,f"{sane(meta[slug]['title'])}{e}")
    os.replace(f,dest)
    with open(REG,"a") as r: r.write(slug+"\n")
    new.append((slug,dest,os.path.getsize(dest)))

for slug,dest,sz in new:
    print(f"MEDIA:{dest}")
print(f"# NEW={len(new)} pushed_total={len(pushed)+len(new)}", file=sys.stderr)
