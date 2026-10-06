#!/usr/bin/env python3
"""Download + verify libgen.li book files (fresh session per md5), then inspect locally."""
import re,os,sys,json,hashlib,urllib.request,urllib.parse,http.cookiejar,ssl,subprocess,zipfile

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
ROOT="tmp/copyright-monitor"

PICKS=[
 ("strayer-medieval-origins","dbe58cb4549beea0c629f861634d2c78","On the Medieval Origins of the Modern State","Strayer"),
 ("kafadar-between-two-worlds","9d2e7102ae285158eab8aab4576abe79","Between Two Worlds","Kafadar"),
 ("hall-weapons-warfare-renaissance","732f74ff50088e84fd76bc3cd6123ab9","Weapons and Warfare in Renaissance Europe","Hall"),
 ("rogers-military-revolution-debate","3e7cfec6a6ceac0ff5f5618ec28573c5","The Military Revolution Debate","Rogers"),
 ("zielonka-europe-as-empire","21af490b9e1c79ad61363cef44ddfb69","Europe as Empire","Zielonka"),
 ("elliott-imperial-spain","ea67f15c2cc97c68a9225dd14cc1f920","Imperial Spain 1469-1716","Elliott"),
 ("tilly-coercion-capital","c8b0ec2ed22c33b82d8d316b51afe414","Coercion, Capital and European States","Tilly"),
 ("andrade-gunpowder-age","2a2e1c8867081c1d0053de286d11af6d","The Gunpowder Age","Andrade"),
 ("sharman-empires-of-the-weak","9fc41384ca9418712b6c227dd568a645","Empires of the Weak","Sharman"),
 ("parrott-business-of-war","910ca73823130f0ed1dfa41dba8d268b","The Business of War","Parrott"),
 ("spruyt-sovereign-state","02f6b21716d0e66806d781289ad6dd25","The Sovereign State and Its Competitors","Spruyt"),
 ("scheidel-escape-from-rome","d479ebd4ad0707dab1e844b0bf73d5eb","Escape from Rome","Scheidel"),
 ("hoffman-why-europe-conquer","62c1675d09c1e1c22dadcf37bab74076","Why Did Europe Conquer the World","Hoffman"),
 ("freedman-future-of-war","5ecd396725c2bd2d99c3f32389baddc0","The Future of War: A History","Freedman"),
 ("miller-chip-war","45eb3bf833e44bf0ae7a380582bfe42e","Chip War","Miller"),
]

def dl(md5):
    cj=http.cookiejar.CookieJar()
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
         urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    def get(u,ref="https://libgen.li/"):
        return op.open(urllib.request.Request(u,headers={"User-Agent":UA,"Referer":ref}),timeout=120).read()
    h=get(f"https://libgen.li/ads.php?md5={md5}").decode("utf-8","replace")
    m=re.search(r"(get\.php\?md5=[a-f0-9]+&key=[A-Za-z0-9]+)",h)
    if not m: return None,"no-key"
    data=get(f"https://libgen.li/{m.group(1)}",ref=f"https://libgen.li/ads.php?md5={md5}")
    return data,None

def inspect(path,title,author):
    out={"file":path,"sha256":hashlib.sha256(open(path,'rb').read()).hexdigest()[:16]}
    ft=subprocess.run(["file","-b",path],capture_output=True,text=True).stdout.strip()
    out["type"]=ft
    low=ft.lower()
    if "pdf" in low:
        pi=subprocess.run(["pdfinfo",path],capture_output=True,text=True).stdout
        pg=re.search(r"Pages:\s+(\d+)",pi); ti=re.search(r"Title:\s+(.*)",pi); au=re.search(r"Author:\s+(.*)",pi)
        out["pages"]=pg.group(1) if pg else "?"
        out["meta_title"]=(ti.group(1).strip() if ti else "")
        out["meta_author"]=(au.group(1).strip() if au else "")
        txt=subprocess.run(["pdftotext","-l","2","-q",path,"-"],capture_output=True,text=True).stdout
        out["head"]=re.sub(r"\s+"," ",txt)[:160]
    elif zipfile.is_zipfile(path) or "epub" in low:
        try:
            z=zipfile.ZipFile(path); opf=[n for n in z.namelist() if n.lower().endswith(".opf")]
            out["entries"]=len(z.namelist())
            if opf:
                raw=z.read(opf[0]).decode("utf-8","replace")
                for tag,k in (("title","meta_title"),("creator","meta_author")):
                    mm=re.search(rf"<dc:{tag}[^>]*>(.*?)</dc:{tag}>",raw,re.S)
                    if mm: out[k]=re.sub(r"\s+"," ",mm.group(1)).strip()[:120]
        except Exception as e: out["ziperr"]=str(e)
    else:
        out["head"]=""
    # crude keyword check
    return out

os.makedirs(ROOT,exist_ok=True)
for slug,md5,title,author in PICKS:
    d=os.path.join(ROOT,slug); os.makedirs(d,exist_ok=True)
    dest=os.path.join(d,md5)
    print(f"\n===== {slug} :: {title} — {author} [{md5}]")
    if os.path.exists(dest):
        print("  (already have)")
    else:
        try:
            data,err=dl(md5)
        except Exception as e:
            data,err=None,str(e)
        if not data:
            print("  DOWNLOAD FAIL:",err); continue
        open(dest,"wb").write(data)
    try:
        info=inspect(dest,title,author)
        print("  bytes",os.path.getsize(dest),"| type",info.get("type"),"|",info.get("pages") or info.get("entries"),"| meta_title",info.get("meta_title"),"| meta_author",info.get("meta_author"))
        print("  head:",info.get("head"))
        print("  sha256",info["sha256"])
    except Exception as e:
        print("  inspect err",e)
