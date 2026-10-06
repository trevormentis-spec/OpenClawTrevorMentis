#!/usr/bin/env python3
"""Probe libgen.li + Internet Archive for a list of works. Prints compact candidates."""
import json,sys,re,urllib.request,urllib.parse,http.cookiejar,ssl,time

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
_cj=http.cookiejar.CookieJar()
_op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj),
      urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
def http(u,ref="https://libgen.li/",t=60):
    return _op.open(urllib.request.Request(u,headers={"User-Agent":UA,"Referer":ref}),timeout=t).read()

WORKS=[
 ("Strayer - On the Medieval Origins of the Modern State",'on the medieval origins of the modern state strayer'),
 ("Kafadar - Between Two Worlds Ottoman State",'between two worlds construction of the ottoman state kafadar'),
 ("Hall - Weapons and Warfare in Renaissance Europe",'weapons and warfare in renaissance europe bert hall'),
 ("Rogers - The Military Revolution Debate",'the military revolution debate rogers'),
 ("Zielonka - Europe as Empire",'europe as empire zielonka'),
 ("Elliott - Imperial Spain 1469-1716",'imperial spain 1469-1716 elliott'),
 ("Tilly - Coercion Capital and European States",'coercion capital and european states tilly'),
 ("Andrade - The Gunpowder Age",'the gunpowder age andrade'),
 ("Sharman - Empires of the Weak",'empires of the weak sharman'),
 ("Parrott - The Business of War",'the business of war parrott military enterprise'),
 ("Bobbitt - The Shield of Achilles",'shield of achilles bobbitt'),
 ("Spruyt - The Sovereign State and Its Competitors",'the sovereign state and its competitors spruyt'),
 ("Scheidel - Escape from Rome",'escape from rome scheidel'),
 ("Hoffman - Why Did Europe Conquer the World",'why did europe conquer the world hoffman'),
 ("Smith & DeVries - Artillery of the Dukes of Burgundy",'artillery of the dukes of burgundy smith devries'),
 ("Holsinger - Neomedievalism Neoconservatism War on Terror",'neomedievalism neoconservatism holsinger'),
 ("Freedman - The Future of War",'the future of war a history freedman'),
 ("Miller - Chip War",'chip war chris miller'),
]

def libgen(q):
    h=http("https://libgen.li/index.php?"+urllib.parse.urlencode({"req":q})).decode("utf-8","replace")
    rows=re.findall(r"<tr[^>]*>(.*?)</tr>",h,re.S)
    out=[]
    for r in rows:
        ids=re.findall(r"md5=([a-fA-F0-9]{32})",r)
        eid=re.search(r"edition\.php\?id=(\d+)",r)
        txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",r)).strip()
        ext=re.findall(r"(?i)\b(epub|pdf|mobi|azw3|fb2|djvu|zip|rtf|txt)\b",r)
        if not (ids or eid): continue
        if not re.search(r"(?i)bobbitt|strayer|kafadar|hall|rogers|zielonka|elliott|tilly|andrade|sharman|parrott|spruyt|scheidel|hoffman|smith|holsinger|freedman|miller",txt) \
           and not re.search(r"(?i)medieval|ottoman|renaissance|military revolution|empire|imperial spain|coercion|gunpowder|weak|business of war|achilles|sovereign state|rome|conquer|burgundy|neomedieval|future of war|chip war",txt):
            continue
        out.append({"md5":ids[0] if ids else None,"eid":eid.group(1) if eid else None,
                    "ext":list(dict.fromkeys(e.lower() for e in ext))[:4],"text":txt[:110]})
    return out[:4]

def ia(q):
    p=[("q",q)]+[("fl[]","identifier"),("fl[]","title"),("fl[]","collection"),("fl[]","access-restricted-item"),("rows","12"),("output","json")]
    url="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p)
    try:
        docs=json.load(urllib.request.urlopen(url,timeout=45))["response"]["docs"]
    except Exception as e:
        return [{"err":str(e)}]
    FREE=("opensource","digitallibraryindia","americana","community","additional_collections","universallibrary")
    res=[]
    for d in docs:
        coll=d.get("collection"); coll=coll if isinstance(coll,list) else [coll]
        free=any(c in FREE for c in coll) and str(d.get("access-restricted-item")).lower()!="true"
        res.append({"id":d.get("identifier"),"free":free,"restr":str(d.get("access-restricted-item")).lower()=="true","coll":",".join(coll)[:40],"title":str(d.get("title"))[:50]})
    return res

for name,q in WORKS:
    print(f"\n===== {name}")
    try:
        lg=libgen(q)
    except Exception as e:
        lg=[]; print("  libgen err:",e)
    if lg:
        for x in lg: print(f"  LG md5={x['md5']} eid={x['eid']} ext={x['ext']} :: {x['text']}")
    else:
        print("  LG: (no parsed rows)")
    try:
        rr=ia(f'title:("{q.split(" - ")[0]}")')
    except Exception as e:
        rr=[]; print("  ia err:",e)
    frees=[x for x in rr if x.get("free")]
    if frees:
        for x in frees[:3]: print(f"  IA FREE {x['id']} | {x['coll']} | {x['title']}")
    time.sleep(0.4)
