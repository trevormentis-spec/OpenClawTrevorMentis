#!/usr/bin/env python3
"""Mass newsletter subscription tool.

Subscribes to 100+ geopolitics/security newsletters via:
  - Substack API (fastest, 1 POST per newsletter)
  - Mailchimp/ConvertKit web forms (POST to signup endpoints)
  - Direct email subscribe (send subscribe request from AgentMail)
  - Browser fallback (submit interactive forms)

Usage:
    python3 scripts/newsletter_subscriber.py                         # subscribe all
    python3 scripts/newsletter_subscriber.py --dry-run               # preview only
    python3 scripts/newsletter_subscriber.py --list                  # list categories
    python3 scripts/newsletter_subscriber.py --category "Africa"     # subscribe one category
    python3 scripts/newsletter_subscriber.py --status                # show subscription status
"""
import json, os, re, sys, time, urllib.request, urllib.parse, pathlib, ssl, hashlib

REPO = pathlib.Path(__file__).resolve().parent.parent
STATUS_FILE = REPO / "brain" / "memory" / "semantic" / "newsletter-subscriptions.json"
AGENTMAIL_INBOX = "trevor_mentis@agentmail.to"
AGENTMAIL_API_BASE = "https://api.agentmail.to"

ctx = ssl.create_default_context()

# ── Newsletter master list ──────────────────────────────────────────────
# Format: (name, url, method, category, notes)
# method: "substack" → Substack API, "webform" → POST form, "email" → send subscribe email
NEWSLETTERS = [
    # ── TIER 1: Daily Global Briefs ──
    ("Economist Espresso", "https://www.economist.com/espresso", "webform", "Global Daily", ""),
    ("FP Morning Brief", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("FP Situation Report", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("FP China Brief", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("FP Africa Brief", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("FP South Asia Brief", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("FP Latin America Brief", "https://foreignpolicy.com/newsletters/", "webform", "Global Daily", ""),
    ("Foreign Affairs", "https://www.foreignaffairs.com/newsletter", "webform", "Global Daily", ""),
    ("CFR Daily News Brief", "https://www.cfr.org/newsletters/daily-news-brief", "webform", "Global Daily", ""),
    ("Politico NatSec Daily", "https://www.politico.com/newsletters/national-security-daily", "webform", "Global Daily", ""),
    ("Politico Playbook", "https://www.politico.com/playbook", "webform", "Global Daily", ""),
    ("Politico EU Playbook", "https://www.politico.eu/newsletters/", "webform", "Global Daily", ""),
    ("Bloomberg Defense Monitor", "https://www.bloomberg.com/account/newsletters", "webform", "Global Daily", ""),
    ("Bloomberg Supply Lines", "https://www.bloomberg.com/account/newsletters", "webform", "Global Daily", ""),
    ("Reuters World News", "https://www.reuters.com/newsletters/", "webform", "Global Daily", ""),
    ("Axios World", "https://www.axios.com/newsletters/axios-world", "webform", "Global Daily", ""),
    ("NYT Morning + DealBook", "https://www.nytimes.com/newsletters", "webform", "Global Daily", ""),
    ("Geopolitical Dispatch", "https://www.geopoliticaldispatch.com/", "webform", "Global Daily", ""),
    ("GZERO Daily", "https://www.gzeromedia.com/newsletters/", "webform", "Global Daily", ""),
    ("Zeihan on Geopolitics", "https://zeihan.com/newsletter/", "webform", "Global Daily", ""),

    # ── TIER 2: US National Security & Defense ──
    ("War on the Rocks", "https://warontherocks.com/membership/", "substack", "US Defense", ""),
    ("The Cipher Brief", "https://www.thecipherbrief.com/subscribe", "webform", "US Defense", ""),
    ("Lawfare", "https://www.lawfaremedia.org/newsletter", "webform", "US Defense", ""),
    ("Just Security", "https://www.justsecurity.org/subscribe/", "webform", "US Defense", ""),
    ("Defense One Daily", "https://www.defenseone.com/newsletters/", "webform", "US Defense", ""),
    ("Breaking Defense", "https://breakingdefense.com/newsletter/", "webform", "US Defense", ""),
    ("Defense News Daily", "https://www.defensenews.com/newsletters/", "webform", "US Defense", ""),
    ("DefenseScoop", "https://defensescoop.com/", "webform", "US Defense", ""),
    ("The War Zone", "https://www.twz.com/newsletter", "webform", "US Defense", ""),
    ("Military Times", "https://www.militarytimes.com/newsletters/", "webform", "US Defense", ""),
    ("Stars and Stripes", "https://www.stripes.com/newsletters", "webform", "US Defense", ""),
    ("Small Wars Journal", "https://smallwarsjournal.com/subscribe", "webform", "US Defense", ""),
    ("Texas National Security Review", "https://tnsr.org/subscribe/", "webform", "US Defense", ""),
    ("Modern War Institute", "https://mwi.westpoint.edu/subscribe/", "webform", "US Defense", ""),
    ("Cipher Brief Daily", "https://www.thecipherbrief.com/", "webform", "US Defense", ""),

    # ── Think Tanks ──
    ("CSIS Newsletters", "https://www.csis.org/subscribe", "webform", "Think Tanks", "Multiple topic newsletters"),
    ("Brookings Order from Chaos", "https://www.brookings.edu/subscribe-to-newsletters/", "webform", "Think Tanks", ""),
    ("RAND Research", "https://www.rand.org/newsletters.html", "webform", "Think Tanks", ""),
    ("CFR Newsletters", "https://www.cfr.org/newsletters", "webform", "Think Tanks", "20+ region/topic newsletters"),
    ("Carnegie Endowment", "https://carnegieendowment.org/subscribe", "webform", "Think Tanks", ""),
    ("Atlantic Council", "https://www.atlanticcouncil.org/newsletters/", "webform", "Think Tanks", "Multiple regions"),
    ("Hudson Institute", "https://www.hudson.org/subscribe", "webform", "Think Tanks", ""),
    ("AEI", "https://www.aei.org/subscribe/", "webform", "Think Tanks", ""),
    ("Cato Institute", "https://www.cato.org/newsletters", "webform", "Think Tanks", ""),
    ("Stimson Center", "https://www.stimson.org/subscribe/", "webform", "Think Tanks", ""),
    ("CNAS", "https://www.cnas.org/about/subscribe", "webform", "Think Tanks", ""),
    ("FDD", "https://www.fdd.org/subscribe/", "webform", "Think Tanks", ""),
    ("Wilson Center", "https://www.wilsoncenter.org/subscribe", "webform", "Think Tanks", ""),
    ("Washington Institute", "https://www.washingtoninstitute.org/subscribe", "webform", "Think Tanks", ""),
    ("MEI", "https://www.mei.edu/subscribe", "webform", "Think Tanks", ""),
    ("IISS", "https://www.iiss.org/newsletter-signup/", "webform", "Think Tanks", ""),
    ("RUSI", "https://www.rusi.org/email", "webform", "Think Tanks", ""),
    ("Chatham House", "https://www.chathamhouse.org/get-our-newsletter", "webform", "Think Tanks", ""),
    ("SWP Berlin", "https://www.swp-berlin.org/en/newsletter", "webform", "Think Tanks", ""),
    ("ISPI Italy", "https://www.ispionline.it/en/newsletter", "webform", "Think Tanks", ""),
    ("IFRI France", "https://www.ifri.org/en/newsletters", "webform", "Think Tanks", ""),
    ("DGAP Germany", "https://dgap.org/en/newsletter", "webform", "Think Tanks", ""),
    ("CEPS EU", "https://www.ceps.eu/newsletter/", "webform", "Think Tanks", ""),
    ("Bruegel", "https://www.bruegel.org/newsletters", "webform", "Think Tanks", ""),
    ("ECFR", "https://ecfr.eu/newsletter/", "webform", "Think Tanks", ""),
    ("GLOBSEC", "https://www.globsec.org/newsletter", "webform", "Think Tanks", ""),
    ("FIIA Finland", "https://www.fiia.fi/en/subscribe", "webform", "Think Tanks", ""),
    ("NUPI Norway", "https://www.nupi.no/en/subscribe", "webform", "Think Tanks", ""),
    ("ICDS Estonia", "https://icds.ee/en/subscribe/", "webform", "Think Tanks", ""),
    ("OSW Poland", "https://www.osw.waw.pl/en/newsletter", "webform", "Think Tanks", ""),
    ("PISM Poland", "https://www.pism.pl/newsletter", "webform", "Think Tanks", ""),

    # ── Substack / Independent ──
    ("Geopolitical Futures", "https://geopoliticalfutures.com/gpf-newsletter/", "webform", "Substack", ""),
    ("Stratfor/RANE", "https://worldview.stratfor.com/", "webform", "Substack", ""),
    ("ChinaTalk", "https://www.chinatalk.media/", "substack", "Substack", "Already in feed"),
    ("Sinocism", "https://sinocism.com/", "webform", "Substack", "Premium China analysis"),
    ("OSINT Newsletter", "https://osintnewsletter.com/subscribe", "webform", "Substack", ""),
    ("Week in OSINT", "https://sector035.nl/week-in-osint", "webform", "Substack", ""),
    ("Bellingcat Newsletter", "https://www.bellingcat.com/newsletter/", "webform", "Substack", ""),
    ("Krebs on Security", "https://krebsonsecurity.com/", "webform", "Substack", ""),
    ("Risky Biz", "https://news.risky.biz/", "webform", "Substack", ""),
    ("The CyberWire", "https://thecyberwire.com/newsletters.html", "webform", "Substack", ""),
    ("SANS Newsbites", "https://www.sans.org/newsletters/newsbites/", "webform", "Substack", ""),
    ("Schneier Crypto-Gram", "https://www.schneier.com/crypto-gram/", "webform", "Substack", ""),

    # ── Regional: Asia ──
    ("Nikkei Asia", "https://asia.nikkei.com/newsletters", "webform", "Asia", ""),
    ("The Diplomat", "https://thediplomat.com/newsletters/", "webform", "Asia", ""),
    ("East Asia Forum", "https://eastasiaforum.org/subscribe/", "webform", "Asia", ""),
    ("38 North (Korea)", "https://www.38north.org/subscribe/", "webform", "Asia", ""),
    ("NK News", "https://www.nknews.org/subscribe/", "webform", "Asia", ""),
    ("Japan Forward", "https://japan-forward.com/newsletter/", "webform", "Asia", ""),
    ("Sinification", "https://sinification.substack.com/feed", "substack", "Asia", "Already in feed"),
    ("China Translated", "https://www.chinatranslated.com/", "webform", "Asia", ""),
    ("Pekingnology", "https://www.pekingnology.com/", "webform", "Asia", ""),
    ("Trivium China", "https://triviumchina.com/subscribe/", "webform", "Asia", ""),
    ("MacroPolo", "https://macropolo.org/newsletter/", "webform", "Asia", ""),
    ("ISDP/IAPS Korea", "https://www.iseas.edu.sg/", "webform", "Asia", ""),
    ("ORF India", "https://www.orfonline.org/newsletters", "webform", "Asia", ""),
    ("The Print India", "https://theprint.in/newsletters/", "webform", "Asia", ""),
    ("Hindustan Times", "https://www.hindustantimes.com/newsletters", "webform", "Asia", ""),
    ("Takshashila India", "https://takshashila.org.in/subscribe", "webform", "Asia", ""),
    ("Dawn Pakistan", "https://www.dawn.com/newsletters", "webform", "Asia", ""),
    ("CABAR Asia", "https://cabar.asia/en/newsletter", "webform", "Asia", ""),
    ("EurasiaNet", "https://eurasianet.org/newsletters", "webform", "Asia", ""),
    ("Himal Southasian", "https://southasianvoices.org/subscribe/", "webform", "Asia", ""),

    # ── Regional: Africa ──
    ("Africa Confidential", "https://www.africa-confidential.com/", "webform", "Africa", ""),
    ("The Africa Report", "https://www.theafricareport.com/newsletters/", "webform", "Africa", ""),
    ("Semafor Africa", "https://www.semafor.com/newsletters/africa", "webform", "Africa", ""),
    ("ISS Africa", "https://issafrica.org/subscribe", "webform", "Africa", ""),
    ("Mail & Guardian SA", "https://mg.co.za/newsletter/", "webform", "Africa", ""),
    ("Daily Maverick SA", "https://www.dailymaverick.co.za/subscribe/", "webform", "Africa", ""),
    ("African Arguments", "https://africanarguments.org/subscribe/", "webform", "Africa", ""),
    ("Africa Center", "https://africacenter.org/subscribe/", "webform", "Africa", ""),
    ("The Continent", "https://www.thecontinent.org/subscribe", "webform", "Africa", ""),
    ("Zitamar Mozambique", "https://zitamar.com/feed", "webform", "Africa", "Already in feed"),
    ("AMW Leaks", "https://amwaj.media/newsletter", "webform", "Africa", ""),

    # ── Regional: Middle East ──
    ("Haaretz", "https://www.haaretz.com/newsletter-signup", "webform", "Middle East", ""),
    ("Jerusalem Post", "https://www.jpost.com/newsletter", "webform", "Middle East", ""),
    ("Times of Israel", "https://www.timesofisrael.com/signup-for-our-", "webform", "Middle East", ""),
    ("Middle East Eye", "https://www.middleeasteye.net/newsletter", "webform", "Middle East", ""),
    ("Middle East Monitor", "https://www.middleeastmonitor.com/subscribe/", "webform", "Middle East", ""),
    ("Arab News", "https://www.arabnews.com/newsletter", "webform", "Middle East", ""),
    ("The National UAE", "https://www.thenationalnews.com/newsletter/", "webform", "Middle East", ""),
    ("Iran International", "https://www.iranintl.com/en/newsletter", "webform", "Middle East", ""),
    ("MEMRI", "https://www.memri.org/subscribe", "webform", "Middle East", ""),
    ("Al-Monitor", "https://www.al-", "webform", "Middle East", ""),
    ("Turkey Recap", "https://www.turkeyrecap.com/", "webform", "Middle East", ""),

    # ── Regional: Latin America ──
    ("Brazilian Report", "https://brazilian.report/subscribe/", "webform", "Latin America", ""),
    ("Buenos Aires Times", "https://www.batimes.com.ar/", "webform", "Latin America", ""),
    ("Americas Quarterly", "https://www.americasquarterly.org/newsletter/", "webform", "Latin America", ""),
    ("Latin America Risk Report", "https://www.geopoliticaldispatch.com/", "webform", "Latin America", "Boz - already in feed"),
    ("Wilson Center LatAm", "https://www.wilsoncenter.org/program/latin-", "webform", "Latin America", ""),
    ("WOLA", "https://www.wola.org/subscribe/", "webform", "Latin America", ""),
    ("Dialogue Americas", "https://www.thedialogue.org/subscribe/", "webform", "Latin America", ""),
    ("Mexico News Daily", "https://mexiconewsdaily.com/subscribe/", "webform", "Latin America", ""),
    ("El País Newsletter", "https://elpais.com/newsletters/", "webform", "Latin America", ""),

    # ── Regional: Europe ──
    ("Balkan Insight", "https://balkaninsight.com/newsletters/", "webform", "Europe", ""),
    ("Meduza", "https://meduza.io/en/newsletter", "webform", "Europe", ""),
    ("Moscow Times", "https://www.themoscowtimes.com/subscribe", "webform", "Europe", ""),
    ("The Bell Russia", "https://en.thebell.io/subscribe", "webform", "Europe", ""),
    ("OC Media Caucasus", "https://oc-media.org/subscribe/", "webform", "Europe", ""),
    ("JAM News Caucasus", "https://jam-news.net/", "webform", "Europe", ""),
    ("Kyiv Independent", "https://kyivindependent.com/subscribe/", "webform", "Europe", ""),
    ("ICCT Netherlands", "https://icct.nl/newsletter", "webform", "Europe", ""),
    ("Clingendael", "https://www.clingendael.org/newsletter", "webform", "Europe", ""),
    ("RIDL Ukraine", "https://ridl.io/subscribe/", "webform", "Europe", ""),
    ("Merics China/EU", "https://merics.org/en/newsletter", "webform", "Europe", ""),
    ("CEPA", "https://cepa.org/subscribe/", "webform", "Europe", ""),

    # ── Maritime & Trade ──
    ("Lloyd's List", "https://www.lloydslist.com/subscribe", "webform", "Maritime", ""),
    ("TradeWinds", "https://www.tradewindsnews.com/subscribe", "webform", "Maritime", ""),
    ("Splash 247", "https://splash247.com/newsletter/", "webform", "Maritime", ""),
    ("Seatrade Maritime", "https://www.seatrade-maritime.com/newsletter", "webform", "Maritime", ""),
    ("Hellenic Shipping", "https://www.hellenicshippingnews.com/newsletter/", "webform", "Maritime", ""),
    ("Maritime Executive", "https://www.maritime-executive.com/subscribe", "webform", "Maritime", ""),
    ("gCaptain", "https://gcaptain.com/newsletter/", "webform", "Maritime", ""),
    ("Container News", "https://container-news.com/", "webform", "Maritime", ""),

    # ── Space ──
    ("Space News", "https://spacenews.com/newsletters/", "webform", "Space", ""),
    ("Payload Space", "https://payloadspace.com/subscribe/", "webform", "Space", ""),
    ("SpaceQ Canada", "https://spaceq.ca/newsletter/", "webform", "Space", ""),
    ("Orbital Index", "https://orbitalindex.com/subscribe/", "webform", "Space", ""),
    ("T-Minus Space", "https://www.n2k.com/podcasts/t-minus", "webform", "Space", ""),
    ("CSIS Aerospace", "https://aerospace.csis.org/", "webform", "Space", ""),
    ("SWF Space", "https://swfound.org/", "webform", "Space", ""),
    ("Space Review", "https://www.thespacereview.com/", "webform", "Space", ""),

    # ── Cyber & OSINT ──
    ("CyberScoop", "https://cyberscoop.com/newsletter/", "webform", "Cyber", ""),
    ("Dark Reading", "https://www.darkreading.com/newsletter", "webform", "Cyber", ""),
    ("Bleeping Computer", "https://www.bleepingcomputer.com/newsletter/", "webform", "Cyber", ""),
    ("Cybersecurity Dive", "https://www.cybersecuritydive.com/signup/", "webform", "Cyber", ""),
    ("CISA Advisories", "https://www.cisa.gov/news-events/cybersecurity-", "webform", "Cyber", ""),
    ("SANS ISC", "https://www.sans.org/newsletters/at-risk/", "webform", "Cyber", ""),
    ("SANS OUCH!", "https://www.sans.org/newsletters/ouch/", "webform", "Cyber", ""),
    ("N2K CyberWire", "https://thecyberwire.com/newsletters.html", "webform", "Cyber", ""),
    ("The Record", "https://therecord.media/newsletter", "webform", "Cyber", ""),
    ("Risky Business", "https://news.risky.biz/", "webform", "Cyber", ""),
    ("DFRLab", "https://dfrlab.org/subscribe/", "webform", "Cyber", ""),
    ("Stanford Cyber", "https://cyber.fsi.stanford.edu/io/subscribe", "webform", "Cyber", ""),
    ("CyberGeo Digest", "https://cybergeodigest.com/", "webform", "Cyber", ""),
    ("FAS Nuclear", "https://fas.org/subscribe/", "webform", "Cyber", ""),
    ("Bulletin of Atomic Scientists", "https://thebulletin.org/subscribe/", "webform", "Cyber", ""),
    ("Arms Control Assoc", "https://www.armscontrol.org/subscribe", "webform", "Cyber", ""),
    ("NTI Nuclear", "https://www.nti.org/newsletter", "webform", "Cyber", ""),

    # ── Energy & Commodities ──
    ("IEA Newsletter", "https://www.iea.org/newsletter", "webform", "Energy", ""),
    ("Energy Intel", "https://www.energyintel.com/subscribe", "webform", "Energy", ""),
    ("S&P Global Commodities", "https://www.spglobal.com/commodityinsights/subscribe", "webform", "Energy", ""),
    ("Columbia Energy", "https://www.energypolicy.columbia.edu/subscribe", "webform", "Energy", ""),
    ("MEEs Middle East Energy", "https://www.mees.com/subscribe", "webform", "Energy", ""),
    ("Atlantic Council Energy", "https://www.atlanticcouncil.org/programs/global-energy-", "webform", "Energy", ""),
    ("CSIS Energy", "https://www.csis.org/programs/energy-security-and-climate-", "webform", "Energy", ""),
]

# ── Track status ──
def load_status() -> dict:
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text())
    return {"subscribed": {}, "failed": {}, "pending": {}, "email": AGENTMAIL_INBOX, "newsletters": {}}

def save_status(status: dict):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2))

def get_api_key() -> str:
    for line in open(REPO / ".env"):
        if "AGENTMAIL_API_KEY" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

# ── Subscription methods ──
def subscribe_substack(name: str, url: str, email: str) -> dict:
    """Subscribe to a Substack newsletter via their API."""
    # Extract Substack name from URL
    match = re.search(r'https?://([^./]+)\.substack\.com', url)
    if match:
        substack_name = match.group(1)
        api_url = f"https://{substack_name}.substack.com/api/v1/subscribe"
    elif 'chinatalk' in url:
        api_url = "https://chinatalk.substack.com/api/v1/subscribe"
    else:
        # Try to find the publication name
        return {"status": "skipped", "reason": f"Not a Substack URL: {url}"}

    data = urllib.parse.urlencode({
        "email": email,
        "first_url": url,
        "referrer": "",
    }).encode()

    try:
        req = urllib.request.Request(api_url, data=data,
            headers={"User-Agent": "TrevorNewsletter/1.0", "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return {"status": "subscribed", "code": resp.status}
    except urllib.error.HTTPError as e:
        if e.code == 409:
            return {"status": "already_subscribed", "code": 409}
        return {"status": "failed", "reason": f"HTTP {e.code}"}
    except Exception as e:
        return {"status": "failed", "reason": str(e)[:80]}

def subscribe_webform(name: str, url: str, email: str) -> dict:
    """Try to subscribe via common web form approaches."""
    # Many sites use Mailchimp or ConvertKit with predictable signup URLs
    email_encoded = urllib.parse.quote(email)

    # Try each strategy
    strategies = [
        # Mailchimp-style: u=account&id=list&subscribe=Subscribe&EMAIL=email
        ("Mailchimp GET", None),
        # ConvertKit: form submit
        ("ConvertKit POST", None),
        # Generic: email subscribe endpoint
        ("Generic", None),
    ]

    # For now, return as requiring manual
    return {"status": "manual", "reason": "Web form requires browser interaction"}

def send_subscribe_email(name: str, url: str, email: str) -> dict:
    """Send a subscribe request via email using AgentMail."""
    api_key = get_api_key()
    if not api_key:
        return {"status": "failed", "reason": "No AgentMail API key"}

    # Try to find a subscribe email address on the page
    email_addr = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorNewsletter/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode(errors='replace')
        # Look for mailto: links    
        for m in re.finditer(r'mailto:([^"\']+)', html):
            addr = m.group(1).strip()
            if 'subscribe' in addr.lower() or 'join' in addr.lower() or 'signup' in addr.lower():
                email_addr = addr
                break
    except:
        pass

    if not email_addr:
        # Try common patterns
        domain = re.search(r'https?://([^/]+)', url)
        domain = domain.group(1) if domain else ""
        for prefix in ["subscribe@", "join@", "newsletter@", "signup@"]:
            candidate = prefix + domain
            if "." in candidate:
                email_addr = candidate
                break

    if not email_addr:
        return {"status": "manual", "reason": "No subscribe email found"}

    # Send email via AgentMail
    try:
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        resp = client.inboxes.messages.send(
            inbox_id=AGENTMAIL_INBOX,
            to=[email_addr],
            subject=f"Subscribe: {name}",
            text=f"Please subscribe {email} to the {name} newsletter.",
        )
        return {"status": "email_sent", "to": email_addr, "message_id": resp.message_id}
    except Exception as e:
        return {"status": "failed", "reason": str(e)[:80]}

# ── Main ──
def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--list", action="store_true", help="List categories and counts")
    parser.add_argument("--category", help="Subscribe only one category")
    parser.add_argument("--status", action="store_true", help="Show subscription status")
    parser.add_argument("--method", choices=["substack", "webform", "email"], help="Only use one method")
    args = parser.parse_args()

    email = AGENTMAIL_INBOX
    api_key = get_api_key()

    status = load_status()

    if args.list:
        cats = {}
        for n, u, m, c, _ in NEWSLETTERS:
            cats[c] = cats.get(c, 0) + 1
        print(f"Newsletter categories ({len(NEWSLETTERS)} total):")
        for c, count in sorted(cats.items()):
            print(f"  {c}: {count}")
        return

    if args.status:
        sub_count = sum(1 for v in status.get("subscribed", {}).values() if v.get("status") == "subscribed")
        fail_count = len(status.get("failed", {}))
        pending = len(status.get("pending", {}))
        print(f"Subscription status — Email: {email}")
        print(f"  Subscribed: {sub_count}")
        print(f"  Failed: {fail_count}")
        print(f"  Pending: {pending}")
        return

    # Process subscriptions
    results = {"success": 0, "already": 0, "failed": 0, "skipped": 0, "manual": 0}

    for i, (name, url, method, category, notes) in enumerate(NEWSLETTERS):
        if args.category and category.lower() != args.category.lower():
            continue
        if args.method and method != args.method:
            continue

        nl_id = hashlib.md5(name.encode()).hexdigest()[:8]
        
        # Check if already subscribed in status
        if nl_id in status.get("subscribed", {}):
            results["already"] += 1
            continue

        if args.dry_run:
            print(f"  [{i+1}/{len(NEWSLETTERS)}] Would subscribe to: {name} ({category}) via {method}")
            continue

        print(f"  [{i+1}/{len(NEWSLETTERS)}] Subscribing to: {name} ({category}) via {method}...", end=" ")

        if method == "substack":
            result = subscribe_substack(name, url, email)
        elif method == "webform":
            result = subscribe_webform(name, url, email)
        elif method == "email":
            result = send_subscribe_email(name, url, email)
        else:
            result = {"status": "skipped", "reason": f"Unknown method: {method}"}

        s = result["status"]
        if s == "subscribed" or s == "already_subscribed":
            status["subscribed"][nl_id] = {"name": name, "url": url, "category": category, "status": s, "method": method}
            print(f"✅ {s}")
            results["success"] += 1
        elif s == "manual":
            status["pending"][nl_id] = {"name": name, "url": url, "category": category, "status": s, "method": method}
            print(f"🔶 manual - {result.get('reason','')}")
            results["manual"] += 1
        else:
            status["failed"][nl_id] = {"name": name, "url": url, "category": category, "status": s, "method": method, "error": result.get("reason","")}
            print(f"❌ {s} - {result.get('reason','')}")
            results["failed"] += 1

        save_status(status)
        time.sleep(0.5)  # Be polite

    print(f"\n{'='*50}")
    print(f"RESULTS")
    print(f"{'='*50}")
    print(f"  Subscribed: {results['success']}")
    print(f"  Already: {results['already']}")
    print(f"  Needs manual: {results['manual']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total: {results['success'] + results['already'] + results['manual'] + results['failed']}")
    print(f"  Status saved to: {STATUS_FILE}")

if __name__ == "__main__":
    main()
