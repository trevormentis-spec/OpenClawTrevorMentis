#!/usr/bin/env python3
"""Download + verify libgen.li book files (fresh session per md5), then inspect locally."""
import re,os,sys,json,hashlib,urllib.request,urllib.parse,http.cookiejar,ssl,subprocess,zipfile

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
ROOT="tmp/copyright-monitor"

PICKS=[
 ("ullmann-papal-government","4fe88efb057ecf8713f7848b315ce86c","The Growth of Papal Government in the Middle Ages","Ullmann"),
 ("vaughan-philip-the-good","25db114fddbe915da92e50c214cd28c9","Philip the Good","Vaughan"),
 ("vaughan-charles-the-bold","be975575170941ca007923253872195d","Charles the Bold","Vaughan"),
 ("inalcik-ottoman-classical-age","9b506cb0e224c808178d73bc34be02d4","The Ottoman Empire: The Classical Age","Inalcik"),
 ("devries-guns-and-men","20612fe47a62bff0436514ef7299cad1","Guns and Men in Medieval Europe","DeVries"),
 ("parker-military-revolution","7a222bbb0df52481be137ff9cb9863d8","The Military Revolution","Parker"),
 ("nicholson-love-war-grail","2077efce518c4d5e6fa98f23b126887b","Love, War and the Grail (Templars/Hospitallers/Teutonic)","Nicholson"),
 ("tierney-conciliar-theory","709c50aa95f0b5ad93a560895324ad5b","Foundations of the Conciliar Theory","Tierney"),
 ("kendall-louis-xi","df7cf493400dffd8108c3b1fd4995f28","Louis XI: The Universal Spider","Kendall"),
 ("venette-chronicle","0f383d07ee1b9475d6a59c0f4d54b46c","The Chronicle of Jean de Venette","Birdsall/Newhall"),
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
