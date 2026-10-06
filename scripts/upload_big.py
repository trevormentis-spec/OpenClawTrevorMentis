#!/usr/bin/env python3
import os, sys, time, subprocess, urllib.parse
d="/home/ubuntu/.openclaw/workspace/exports/cm4"
binname="trevor-hy4-"+str(int(time.time()))
files=[
 "Frederic C. Lane - Venice- A Maritime Republic.pdf",
 "Adrian Johns - The Nature of the Book- Print and Knowledge in the Making.pdf",
 "Ralph A. Griffiths - The Reign of King Henry VI.pdf",
 "J. R. Lander - Crown and Nobility 1450-1509.pdf",
 "Thomas A. Brady; Heiko A. Oberman; James D. Tracy - Handbook of European History 1400-1600.pdf",
 "Elizabeth L. Eisenstein - The Printing Press as an Agent of Change.pdf",
]
print("BIN",binname,flush=True)
for f in files:
    p=os.path.join(d,f)
    if not os.path.exists(p): print("MISS",f,flush=True); continue
    url="https://filebin.net/%s/%s"%(binname, urllib.parse.quote(f))
    r=subprocess.run(["curl","-s","-m","1200","-X","POST","--data-binary","@"+p,
                      "-H","Content-Type: application/pdf","-H","filename: "+f,
                      url,"-o","/dev/null","-w","%{http_code}"],capture_output=True,text=True)
    print(r.stdout.strip(), f, flush=True)
print("UPLOAD_DONE",binname,flush=True)
