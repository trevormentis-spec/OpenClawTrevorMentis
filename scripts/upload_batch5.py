#!/usr/bin/env python3
import os,subprocess
D="/home/ubuntu/.openclaw/workspace/exports/batch5"
BIN="trevor-hy4-1789309348"
files=[
 ("James C Scott - Seeing Like a State.pdf","Scott-Seeing-Like-a-State.pdf"),
 ("Tim Wu - The Master Switch.epub","Wu-The-Master-Switch.epub"),
 ("Farrell & Newman - Underground Empire.epub","Farrell-Newman-Underground-Empire.epub"),
 ("Stephen D. Krasner - Sovereignty, Organized Hypocrisy.pdf","Krasner-Sovereignty-Organized-Hypocrisy.pdf"),
 ("Carl Schmitt - The Nomos of the Earth.pdf","Schmitt-The-Nomos-of-the-Earth.pdf"),
 ("David Stasavage - States of Credit.epub","Stasavage-States-of-Credit.epub"),
 ("Thomas Ertman - Birth of the Leviathan.pdf","Ertman-Birth-of-the-Leviathan.pdf"),
 ("Philippe de Commynes - Memoires (Calmette ed.).pdf","Commynes-Memoires-Calmette.pdf"),
 ("Tai Ming Cheung - Innovate to Dominate.pdf","Cheung-Innovate-to-Dominate.pdf"),
 ("Farrell & Newman - Weaponized Interdependence (Intl Security 2019).pdf","Farrell-Newman-Weaponized-Interdependence.pdf"),
 ("Ruggie - Territoriality and Beyond (Intl Organization 1993).pdf","Ruggie-Territoriality-and-Beyond.pdf"),
 ("Chastellain - Oeuvres (Kervyn de Lettenhove ed.) vol 01.pdf","Chastellain-Oeuvres-vol01.pdf"),
 ("Chastellain - Oeuvres vol 09.pdf","Chastellain-Oeuvres-vol09.pdf"),
 ("Chastellain - Oeuvres vol 11.pdf","Chastellain-Oeuvres-vol11.pdf"),
 ("Chastellain - Oeuvres vol 15.pdf","Chastellain-Oeuvres-vol15.pdf"),
]
for src,dst in files:
    p=os.path.join(D,src)
    if not os.path.exists(p): print("MISS",src); continue
    r=subprocess.run(["curl","-s","-m","1200","-X","POST","--data-binary","@"+p,
                      "-H","Content-Type: application/octet-stream",
                      f"https://filebin.net/{BIN}/{dst}","-o","/dev/null","-w","%{http_code}"],capture_output=True,text=True)
    print(r.stdout.strip(), dst, flush=True)
print("DONE")
