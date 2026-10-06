#!/usr/bin/env python3
"""Archive-wide probe: Internet Archive advancedsearch across a set of works.
Prints candidate items with collection + restricted flags so we can spot
freely-downloadable scans (opensource / digitallibraryindia / americana / community)."""
import json, sys, time, urllib.parse, urllib.request

WORKS = {
    "wolfe-fiscal-renaissance": 'title:("fiscal system of renaissance france")',
    "henneman-royal-taxation": 'title:("royal taxation in fourteenth-century france") OR (title:(henneman) AND title:(taxation))',
    "major-representative-gov": 'title:("representative government in early modern france")',
    "vale-charles-vii": 'title:("charles vii") AND creator:("vale")',
    "chernow-titan": 'title:(titan) AND creator:("chernow")',
    "yergin-the-prize": 'title:(prize) AND creator:("yergin")',
    "bringhurst-antitrust-oil": 'title:("antitrust and the oil monopoly")',
    "childs-texas-railroad": 'title:("texas railroad commission")',
    "howard-war-european-history": 'title:("war in european history")',
    "basin-histoire-charles-vii": 'title:("histoire de charles vii") AND creator:(basin)',
    "ordonnances-roys-france": 'title:("ordonnances des roys de france")',
    "recouvrement-normendie": 'title:("recouvrement de normendie") OR title:("recouvrement de normandie")',
    "bratton-the-stack": 'title:("the stack") AND creator:("bratton")',
}
FL = ["identifier","title","creator","year","collection","access-restricted-item","mediatype","language"]
FREE_HINTS = ("opensource","digitallibraryindia","americana","community","additional_collections","toronto","europeanlibraries","JaiGyan","universallibrary","cdl")

def search(q, rows=25):
    params = [("q", q)] + [("fl[]", f) for f in FL] + [("rows", str(rows)), ("page","1"), ("output","json")]
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params)
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.load(r)["response"]["docs"]
        except Exception as e:
            err = e; time.sleep(2)
    print("  ERR", err); return []

for key, q in WORKS.items():
    print(f"\n===== {key} =====")
    docs = search(q)
    if not docs:
        print("  (no IA items)")
    for d in docs:
        coll = d.get("collection")
        coll = coll if isinstance(coll, list) else ([coll] if coll else [])
        restricted = d.get("access-restricted-item")
        free = any(c in FREE_HINTS for c in coll) and str(restricted).lower() != "true"
        flag = "FREE?" if free else ("restricted" if str(restricted).lower()=="true" else "-")
        print(f"  [{flag}] {d.get('identifier')} | {d.get('year')} | {','.join(coll)[:60]} | {str(d.get('title'))[:55]}")
    time.sleep(0.7)
