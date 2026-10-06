#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse,http.cookiejar,ssl,time
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
_cj=http.cookiejar.CookieJar()
_op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj),
      urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
def http(u,ref="https://libgen.li/",t=60):
    return _op.open(urllib.request.Request(u,headers={"User-Agent":UA,"Referer":ref}),timeout=t).read()

WORKS=[
 ("Ullmann - Growth of Papal Government",'growth of papal government in the middle ages ullmann'),
 ("Famiglietti - Royal Intrigue Charles VI",'royal intrigue crisis at the court of charles vi famiglietti'),
 ("Vaughan - John the Fearless",'john the fearless growth of burgundian power vaughan'),
 ("Vaughan - Philip the Good",'philip the good apogee of burgundy vaughan'),
 ("Vaughan - Charles the Bold",'charles the bold last valois duke of burgundy vaughan'),
 ("Inalcik - Ottoman Empire Classical Age",'ottoman empire the classical age 1300-1600 inalcik'),
 ("DeVries - Guns and Men in Medieval Europe",'guns and men in medieval europe devries'),
 ("Vale - War and Chivalry",'war and chivalry malcolm vale'),
 ("Parker - The Military Revolution",'the military revolution military innovation and the rise of the west parker'),
 ("Nicholson - Templars Hospitallers Teutonic Knights",'templars hospitallers and teutonic knights nicholson'),
 ("Tierney - Foundations of the Conciliar Theory",'foundations of the conciliar theory tierney'),
 ("Kendall - Louis XI The Universal Spider",'louis xi the universal spider kendall'),
 ("Jean de Venette - Chronicle",'the chronicle of jean de venette newhall birdsall'),
 ("Fortescue - Governance of England Plummer",'the governance of england fortescue plummer 1885'),
]
def libgen(q):
    h=http("https://libgen.li/index.php?"+urllib.parse.urlencode({"req":q})).decode("utf-8","replace")
    out=[]
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>",h,re.S):
        ids=re.findall(r"md5=([a-fA-F0-9]{32})",r); eid=re.search(r"edition\.php\?id=(\d+)",r)
        txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",r)).strip()
        ext=re.findall(r"(?i)\b(epub|pdf|mobi|azw3|fb2|djvu|zip|rtf)\b",r)
        if not (ids or eid) or len(txt)<40: continue
        if re.search(r"(?i)review|journal|vol\.|iss\.|pp\.|compte|rezension",txt) and not re.search(r"(?i)press|university|edition",txt):
            continue
        out.append({"md5":ids[0] if ids else None,"eid":eid.group(1) if eid else None,"ext":list(dict.fromkeys(e.lower() for e in ext))[:3],"text":txt[:120]})
    return out[:5]
def ia(q):
    p=[("q",q)]+[("fl[]","identifier"),("fl[]","title"),("fl[]","collection"),("fl[]","access-restricted-item"),("rows","10"),("output","json")]
    try: return json.load(urllib.request.urlopen("https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(p),timeout=45))["response"]["docs"]
    except Exception as e: return [{"err":str(e)}]
FREE=("opensource","digitallibraryindia","americana","community","additional_collections","universallibrary")
for name,q in WORKS:
    print(f"\n===== {name}")
    try: lg=libgen(q)
    except Exception as e: lg=[]; print("  LG err",e)
    if lg:
        for x in lg: print(f"  LG md5={x['md5']} eid={x['eid']} ext={x['ext']} :: {x['text']}")
    else: print("  LG: none")
    try: rr=ia(f'title:("{q.split(" - ")[0]}")')
    except Exception as e: rr=[]; print("  ia err",e)
    free=[d for d in rr if isinstance(d,dict) and "identifier" in d and any(c in (d.get("collection") if isinstance(d.get("collection"),list) else [d.get("collection")]) for c in FREE) and str(d.get("access-restricted-item")).lower()!="true"]
    for d in free[:3]: print(f"  IA FREE {d['identifier']} | {str(d.get('title'))[:52]}")
    time.sleep(0.3)
