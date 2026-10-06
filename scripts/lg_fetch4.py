#!/usr/bin/env python3
import re,os,json,hashlib,subprocess,zipfile,time,urllib.request,http.cookiejar,ssl
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
HOSTS=["libgen.vg","libgen.gl","libgen.bz","libgen.la","libgen.li"]
ROOT="tmp/copyright-monitor"
PICKS=[
 ("ullmann-papal-government","4fe88efb057ecf8713f7848b315ce86c","The Growth of Papal Government in the Middle Ages","Ullmann"),
 ("vaughan-philip-the-good","25db114fddbe915da92e50c214cd28c9","Philip the Good","Vaughan"),
 ("vaughan-charles-the-bold","be975575170941ca007923253872195d","Charles the Bold","Vaughan"),
 ("devries-guns-and-men","20612fe47a62bff0436514ef7299cad1","Guns and Men in Medieval Europe","DeVries"),
 ("parker-military-revolution","7a222bbb0df52481be137ff9cb9863d8","The Military Revolution","Parker"),
 ("nicholson-love-war-grail","2077efce518c4d5e6fa98f23b126887b","Love, War and the Grail","Nicholson"),
 ("tierney-conciliar-theory","709c50aa95f0b5ad93a560895324ad5b","Foundations of the Conciliar Theory","Tierney"),
 ("kendall-louis-xi","df7cf493400dffd8108c3b1fd4995f28","Louis XI: The Universal Spider","Kendall"),
 ("venette-chronicle","0f383d07ee1b9475d6a59c0f4d54b46c","The Chronicle of Jean de Venette","Birdsall/Newhall"),
]
def dl(md5):
    for host in HOSTS:
        try:
            cj=http.cookiejar.CookieJar()
            op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                 urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
            base=f"https://{host}/"
            def get(u,ref=base,t=60):
                return op.open(urllib.request.Request(u,headers={"User-Agent":UA,"Referer":ref,"Accept":"text/html,application/xhtml+xml"}),timeout=t).read()
            get(base)  # establish session
            h=get(base+f"ads.php?md5={md5}",ref=base).decode("utf-8","replace")
            m=re.search(r"(get\.php\?md5=[a-f0-9]+&key=[A-Za-z0-9]+)",h)
            if not m: continue
            data=get(base+m.group(1),ref=base+f"ads.php?md5={md5}",t=180)
            if data[:4]==b"%PDF" or data[:2]==b"PK" or len(data)>5000:
                return data,host
        except Exception as e:
            pass
        time.sleep(1)
    return None,"all-hosts-failed"
def inspect(path):
    out={"sha256":hashlib.sha256(open(path,'rb').read()).hexdigest()[:16]}
    ft=subprocess.run(["file","-b",path],capture_output=True,text=True).stdout.strip(); out["type"]=ft
    if "pdf" in ft.lower():
        pi=subprocess.run(["pdfinfo",path],capture_output=True,text=True).stdout
        for k,lab in (("Pages","pages"),("Title","meta_title"),("Author","meta_author")):
            mm=re.search(rf"^{k}:\s+(.*)",pi,re.M); out[lab]=mm.group(1).strip() if mm else ""
        txt=subprocess.run(["pdftotext","-l","2","-q",path,"-"],capture_output=True,text=True).stdout
        out["head"]=re.sub(r"\s+"," ",txt)[:120]
    elif zipfile.is_zipfile(path):
        try:
            z=zipfile.ZipFile(path); opf=[n for n in z.namelist() if n.lower().endswith(".opf")]; out["entries"]=len(z.namelist())
            if opf:
                raw=z.read(opf[0]).decode("utf-8","replace")
                for tag,k in (("title","meta_title"),("creator","meta_author")):
                    mm=re.search(rf"<dc:{tag}[^>]*>(.*?)</dc:{tag}>",raw,re.S)
                    if mm: out[k]=re.sub(r"\s+"," ",mm.group(1)).strip()[:110]
        except Exception as e: out["ziperr"]=str(e)
    return out
for slug,md5,title,author in PICKS:
    d=os.path.join(ROOT,slug); os.makedirs(d,exist_ok=True); dest=os.path.join(d,md5)
    print(f"\n===== {slug} [{md5}]",flush=True)
    if not os.path.exists(dest):
        data,host=dl(md5)
        if not data: print("  DOWNLOAD FAIL:",host,flush=True); time.sleep(2); continue
        open(dest,"wb").write(data); print("  via",host,flush=True)
    try:
        i=inspect(dest)
        print("  bytes",os.path.getsize(dest),"|",i.get("type"),"| pages/entries",i.get("pages") or i.get("entries"),"| mt:",i.get("meta_title"),"| ma:",i.get("meta_author"),flush=True)
        print("  head:",i.get("head"),"| sha",i["sha256"],flush=True)
    except Exception as e: print("  inspect err",e,flush=True)
    time.sleep(3)
