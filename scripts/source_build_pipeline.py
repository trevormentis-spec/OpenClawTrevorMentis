#!/usr/bin/env python3
"""
Source Build Pipeline — Phase 1-3: Test existing sources, discover new ones,
build tested source catalog. Uses feedparser for robust RSS parsing.
"""

import json
import os
import sys
import time
import urllib.request
import feedparser
import re
import pathlib
from datetime import datetime, timezone

REPO = pathlib.Path("/home/ubuntu/.openclaw/workspace")
SOURCES_PATH = REPO / "analyst/meta/sources.json"
OUTPUT_PATH = REPO / "analyst/meta/sources_tested.json"
NOW = "2026-05-21T17:00:00Z"
DELAY = 0.3

feedparser.USER_AGENT = "TrevorSourceBuilder/1.0 (RSS feed tester)"


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def test_feed(url):
    """Test RSS feed using feedparser. Returns (working, entry_count, bozo_reason)."""
    try:
        parsed = feedparser.parse(url)
        entries = len(parsed.entries)
        bozo = ""
        if entries > 0:
            return True, entries, ""
        # No entries but feed may still be valid
        if parsed.bozo and hasattr(parsed.bozo_exception, '__str__'):
            bozo = str(parsed.bozo_exception)[:80]
        # Check if it at least looks like a feed
        if parsed.version or parsed.feed.get("title"):
            return True, entries, bozo
        return False, 0, bozo or "no content"
    except Exception as e:
        return False, 0, str(e)[:80]


# ============================================================
# COMPREHENSIVE RSS FEED DATABASE — pre-researched high-value feeds
# ============================================================

# Each entry: (display_name, short_label, url, region, source_type, admiralty_rel, admiralty_cred)
FEED_DATABASE = [
    # ===== WIRE SERVICES & MAJOR GLOBAL NEWS =====
    ("BBC World News",           "BBC World",     "https://feeds.bbci.co.uk/news/world/rss.xml",             "global",        "wire_service", "A", "1"),
    ("BBC Top Stories",          "BBC Top",       "https://feeds.bbci.co.uk/news/rss.xml",                   "global",        "wire_service", "A", "1"),
    ("BBC Europe",               "BBC EU",        "https://feeds.bbci.co.uk/news/world/europe/rss.xml",      "europe",        "wire_service", "A", "1"),
    ("BBC Middle East",          "BBC ME",        "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "middle_east",   "wire_service", "A", "1"),
    ("BBC Asia",                 "BBC Asia",      "https://feeds.bbci.co.uk/news/world/asia/rss.xml",        "asia",          "wire_service", "A", "1"),
    ("BBC Africa",               "BBC Africa",    "https://feeds.bbci.co.uk/news/world/africa/rss.xml",      "africa",        "wire_service", "A", "1"),
    ("BBC Latin America",        "BBC LA",        "https://feeds.bbci.co.uk/news/world/latin_america/rss.xml","south_central_america","wire_service", "A", "1"),
    ("BBC Business",             "BBC Biz",       "https://feeds.bbci.co.uk/news/business/rss.xml",          "global_finance","wire_service", "A", "1"),
    ("Al Jazeera All",           "AJ All",        "https://www.aljazeera.com/xml/rss/all.xml",               "global",        "wire_service", "A", "1"),
    ("Al Jazeera Middle East",   "AJ ME",         "https://www.aljazeera.com/xml/rss/middle-east.xml",       "middle_east",   "wire_service", "A", "1"),
    ("The Guardian World",       "Guardian",      "https://www.theguardian.com/world/rss",                   "global",        "newspaper",    "A", "2"),
    ("The Guardian UK",          "Guardian UK",   "https://www.theguardian.com/uk/rss",                      "europe",        "newspaper",    "A", "2"),
    ("The Guardian Business",    "Guardian Biz",  "https://www.theguardian.com/business/rss",               "global_finance","newspaper",    "A", "2"),
    ("NPR World",                "NPR World",     "https://feeds.npr.org/1004/rss.xml",                      "global",        "wire_service", "A", "2"),
    ("France 24 EN",             "F24 EN",        "https://www.france24.com/en/rss",                          "europe",        "wire_service", "A", "2"),
    ("France 24 Middle East",    "F24 ME",        "https://www.france24.com/en/middle-east/rss",             "middle_east",   "wire_service", "A", "2"),
    ("DW World",                 "DW World",      "https://rss.dw.com/rdf/rss-en-world",                     "europe",        "wire_service", "A", "2"),
    ("Sky News World",           "Sky News",      "https://feeds.skynews.com/feeds/rss/world.xml",           "global",        "wire_service", "A", "2"),
    ("ABC News (AU)",            "ABC AU",        "https://www.abc.net.au/news/feed/46078/rss.xml",          "asia",          "wire_service", "A", "2"),
    ("CNBC Top News",            "CNBC Top",      "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362", "global_finance", "financial", "A", "2"),
    ("CBC Top Stories",          "CBC Top",       "https://www.cbc.ca/cmlink/rss-topstories",                "north_america", "wire_service", "A", "2"),
    ("CBC World",                "CBC World",     "https://www.cbc.ca/cmlink/rss-world",                     "north_america", "wire_service", "A", "2"),
    ("NYT World",                "NYT World",     "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",  "global",        "newspaper",    "A", "2"),
    ("NYT Home Page",            "NYT Home",      "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml","global",       "newspaper",    "A", "2"),
    ("Reuters Top News",         "Reuters",       "https://www.reuters.com/arc/outboundfeeds/v3/all/?outputType=xml&size=20", "global", "wire_service", "A", "1"),
    ("USA Today Top",            "USA Today",     "https://rssfeeds.usatoday.com/usatoday-NewsTopStories",    "north_america", "newspaper",    "B", "2"),
    ("EuroNews",                 "EuroNews",      "https://www.euronews.com/rss",                             "europe",        "news",         "A", "2"),

    # ===== MIDDLE EAST =====
    ("Gulf News",                "Gulf News",     "https://gulfnews.com/rss-feeds",                           "middle_east",   "newspaper",    "B", "2"),
    ("The National UAE",         "Nat UAE",       "https://www.thenationalnews.com/arc/outboundfeeds/rss/",    "middle_east",   "newspaper",    "B", "2"),
    ("Arab News",                "Arab News",     "https://www.arabnews.com/rss.xml",                         "middle_east",   "newspaper",    "B", "2"),
    ("Middle East Eye",          "MEE",           "https://www.middleeasteye.net/rss",                        "middle_east",   "news",         "B", "2"),
    ("The New Arab",             "New Arab",      "https://www.newarab.com/rss.xml",                          "middle_east",   "news",         "B", "2"),
    ("Haaretz EN",               "Haaretz",       "https://www.haaretz.com/srv/haaretz-latest-news-xml",      "middle_east",   "newspaper",    "B", "2"),
    ("Times of Israel",          "ToI",           "https://www.timesofisrael.com/feed/",                      "middle_east",   "newspaper",    "B", "2"),
    ("Jerusalem Post",           "JPost",         "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx",        "middle_east",   "newspaper",    "B", "2"),
    ("Al-Monitor",               "Al-Monitor",    "https://www.al-monitor.com/rss/feeds",                     "middle_east",   "news",         "B", "2"),
    ("Iran International",        "Iran Intl",     "https://www.iranintl.com/en/rss.xml",                     "middle_east",   "news",         "B", "2"),
    ("Saudi Gazette",            "S Gaz",         "https://saudigazette.com.sa/rss",                         "middle_east",   "newspaper",    "B", "2"),
    ("Al Arabiya EN",            "Arabiya EN",    "https://english.alarabiya.net/feed/rss2/en.xml",           "middle_east",   "news",         "B", "2"),
    ("Asharq Al-Awsat EN",       "Asharq EN",     "https://english.aawsat.com/rss.xml",                      "middle_east",   "newspaper",    "B", "2"),
    ("i24 News EN",              "i24",           "https://www.i24news.tv/en/rss",                           "middle_east",   "news",         "B", "2"),

    # ===== EUROPE =====
    ("Le Monde EN",              "Le Monde EN",   "https://www.lemonde.fr/en/rss/une.xml",                   "europe",        "newspaper",    "A", "2"),
    ("El Pais EN",               "El Pais EN",    "https://feeds.elpais.com/mrss-s/pages/ep-english/site/elpais.com/portada", "europe", "newspaper", "A", "2"),
    ("Der Spiegel Intl",         "Spiegel",       "https://www.spiegel.de/international/index.rss",           "europe",        "newspaper",    "A", "2"),
    ("Politico EU",              "Politico EU",   "https://www.politico.eu/feed/",                            "europe",        "news",         "A", "2"),
    ("EU Observer",              "EU Obs",        "https://euobserver.com/rss.xml",                           "europe",        "news",         "A", "2"),
    ("The Local EU",             "Local EU",      "https://feeds.thelocal.com/feeds/feeds/rss/en/all",        "europe",        "news",         "B", "2"),
    ("Corriere della Sera",      "Corriere",      "https://xml2.corriereobjects.it/rss/esteri.xml",           "europe",        "newspaper",    "B", "2"),
    ("Moscow Times",             "Moscow T",      "https://www.themoscowtimes.com/rss/news",                  "europe",        "newspaper",    "B", "2"),
    ("Meduza EN",                "Meduza EN",     "https://meduza.io/rss/en/all",                             "europe",        "news",         "B", "2"),
    ("Meduza RU",                "Meduza RU",     "https://meduza.io/rss/all",                                "europe",        "news",         "C", "3"),
    ("TASS EN",                  "TASS",          "https://tass.com/rss/v2.xml",                              "europe",        "wire_service", "C", "3"),
    ("Kommersant",               "Kommersant",    "https://www.kommersant.ru/RSS/main.xml",                   "europe",        "newspaper",    "C", "3"),
    ("FT World",                 "FT",            "https://www.ft.com/world?format=rss",                     "global_finance","newspaper",    "A", "1"),
    ("BBC Europe",               "BBC EU",        "https://feeds.bbci.co.uk/news/world/europe/rss.xml",       "europe",        "wire_service", "A", "1"),

    # ===== ASIA =====
    ("Nikkei Asia",              "Nikkei",        "https://asia.nikkei.com/rss/feed",                         "asia",          "newspaper",    "B", "2"),
    ("SCMP",                     "SCMP",          "https://www.scmp.com/rss/4/feed",                          "asia",          "newspaper",    "B", "2"),
    ("Japan Times",              "JT",            "https://www.japantimes.co.jp/feed/top",                    "asia",          "newspaper",    "B", "2"),
    ("The Hindu",                "Hindu",         "https://www.thehindu.com/news/feeder/default.rss",         "asia",          "newspaper",    "B", "2"),
    ("Korea Herald",             "Korea Herald",  "http://www.koreaherald.com/rssxml/HeraldNews.xml",        "asia",          "newspaper",    "B", "2"),
    ("CNA Singapore",            "CNA",           "https://www.channelnewsasia.com/rssfeeds/8395986",         "asia",          "news",         "B", "2"),
    ("China Daily World",        "China Daily",   "https://www.chinadaily.com.cn/rss/world_rss.xml",          "asia",          "newspaper",    "C", "3"),
    ("Global Times",             "Global T",      "https://www.globaltimes.cn/rss",                           "asia",          "newspaper",    "C", "3"),
    ("Xinhua World",             "Xinhua",        "http://www.xinhuanet.com/english/rss/worldrss.xml",       "asia",          "wire_service", "C", "3"),
    ("Times of India",           "TOI",           "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms","asia",         "newspaper",    "B", "2"),
    ("The Diplomat",             "Diplomat",      "https://thediplomat.com/feed/",                            "asia",          "magazine",     "B", "2"),
    ("NHK World",                "NHK",           "https://www3.nhk.or.jp/nhkworld/rss/world.xml",            "asia",          "wire_service", "A", "2"),
    ("Straits Times",            "Straits T",     "https://www.straitstimes.com/news/asia/rss.xml",           "asia",          "newspaper",    "B", "2"),
    ("Dawn Pakistan",            "Dawn",          "https://www.dawn.com/feeds/feeds/rss.xml",                 "asia",          "newspaper",    "B", "2"),

    # ===== AFRICA =====
    ("allAfrica",                "allAfrica",     "https://allafrica.com/tools/headlines/rss/latest/headlines.rdf", "africa",   "aggregator",   "B", "2"),
    ("Africanews",               "Africanews",    "https://www.africanews.com/feed/",                         "africa",        "news",         "B", "2"),
    ("Daily Maverick",           "Maverick",      "https://www.dailymaverick.co.za/feed/",                    "africa",        "newspaper",    "B", "2"),
    ("The East African",         "E African",     "https://www.theeastafrican.co.ke/rss/",                    "africa",        "newspaper",    "B", "2"),
    ("African Arguments",        "Afr Arg",       "https://africanarguments.org/feed/",                       "africa",        "news",         "B", "2"),
    ("The Africa Report",        "Afr Report",    "https://www.theafricareport.com/feed/",                    "africa",        "news",         "B", "2"),
    ("ISS Africa",               "ISS Africa",    "https://issafrica.org/feed/",                              "africa",        "think_tank",   "A", "2"),

    # ===== LATIN AMERICA =====
    ("Buenos Aires Times",       "BA Times",      "https://www.batimes.com.ar/feed",                          "south_central_america","newspaper","B", "2"),
    ("MercoPress",               "MercoPress",    "https://en.mercopress.com/rss.xml",                        "south_central_america","news",     "B", "2"),
    ("Americas Quarterly",       "Am Q",          "https://americasquarterly.org/feed/",                      "south_central_america","magazine", "B", "2"),
    ("Dialogo Americas",         "Dialogo",       "https://dialogo-americas.com/feed/",                       "south_central_america","news",     "B", "2"),

    # ===== THINK TANKS =====
    ("CSIS Analysis",            "CSIS",          "https://www.csis.org/rss/analysis.xml",                    "global",        "think_tank",   "A", "2"),
    ("CFR",                      "CFR",           "https://www.cfr.org/rss.xml",                              "global",        "think_tank",   "A", "2"),
    ("Chatham House",            "Chatham",       "https://www.chathamhouse.org/rss.xml",                     "global",        "think_tank",   "A", "2"),
    ("RUSI",                     "RUSI",          "https://rusi.org/rss.xml",                                 "global",        "think_tank",   "A", "2"),
    ("Carnegie Endowment",       "Carnegie",      "https://carnegieendowment.org/rss.xml",                    "global",        "think_tank",   "A", "2"),
    ("Brookings",                "Brookings",     "https://www.brookings.edu/feed/",                          "global",        "think_tank",   "A", "2"),
    ("AEI",                      "AEI",           "https://www.aei.org/rss/all/",                             "global",        "think_tank",   "A", "2"),
    ("Atlantic Council",         "Atl Council",   "https://www.atlanticcouncil.org/feed/",                    "global",        "think_tank",   "A", "2"),
    ("Wilson Center",            "Wilson",        "https://www.wilsoncenter.org/rss.xml",                     "global",        "think_tank",   "A", "2"),
    ("MEI",                      "MEI",           "https://www.mei.edu/rss.xml",                              "middle_east",   "think_tank",   "A", "2"),
    ("Hudson Institute",         "Hudson",        "https://www.hudson.org/rss.xml",                           "global",        "think_tank",   "A", "2"),
    ("RAND Corp",                "RAND",          "https://www.rand.org/rss/rand.xml",                        "global",        "think_tank",   "A", "2"),
    ("ISW/UnderstandingWar",     "ISW",           "https://www.understandingwar.org/rss.xml",                 "global",        "think_tank",   "A", "2"),
    ("IISS",                     "IISS",          "https://www.iiss.org/rss/press.xml",                       "global",        "think_tank",   "A", "2"),
    ("Quincy Institute",         "Quincy",        "https://quincyinst.org/feed/",                             "global",        "think_tank",   "A", "2"),
    ("Stimson Center",           "Stimson",       "https://www.stimson.org/feed/",                            "global",        "think_tank",   "A", "2"),
    ("FPRI",                     "FPRI",          "https://www.fpri.org/feed/",                              "global",        "think_tank",   "A", "2"),
    ("Cato Institute",           "Cato",          "https://www.cato.org/rss/",                                "global",        "think_tank",   "A", "2"),
    ("Heritage Foundation",      "Heritage",      "https://www.heritage.org/rss.xml",                         "global",        "think_tank",   "A", "2"),
    ("Washington Institute",     "Wash Inst",     "https://www.washingtoninstitute.org/rss.xml",               "middle_east",   "think_tank",   "A", "2"),
    ("INSS Israel",              "INSS",          "https://www.inss.org.il/feed/",                           "middle_east",   "think_tank",   "A", "2"),
    ("CNAS",                     "CNAS",          "https://www.cnas.org/rss.xml",                             "global",        "think_tank",   "A", "2"),
    ("CSBA",                     "CSBA",          "https://csbaonline.org/rss.xml",                           "global",        "think_tank",   "A", "2"),
    ("Soufan Center",            "Soufan",        "https://thesoufancenter.org/feed/",                        "global",        "think_tank",   "A", "2"),
    ("ECFR",                     "ECFR",          "https://ecfr.eu/feed/",                                   "europe",        "think_tank",   "A", "2"),
    ("Crisis Group Latest",      "Crisis G",      "https://www.crisisgroup.org/rss/latest.xml",               "global",        "think_tank",   "A", "2"),
    ("Crisis Group Africa",      "Crisis Afr",    "https://www.crisisgroup.org/rss/africa.xml",               "africa",        "think_tank",   "A", "2"),
    ("Crisis Group Asia",        "Crisis Asia",   "https://www.crisisgroup.org/rss/asia.xml",                 "asia",          "think_tank",   "A", "2"),
    ("Crisis Group ME",          "Crisis ME",     "https://www.crisisgroup.org/rss/middle-east-north-africa.xml","middle_east","think_tank",  "A", "2"),
    ("Crisis Group Europe",      "Crisis EU",     "https://www.crisisgroup.org/rss/europe-central-asia.xml",  "europe",        "think_tank",   "A", "2"),
    ("Jamestown Foundation",     "Jamestown",     "https://jamestown.org/feed/",                              "global",        "think_tank",   "A", "2"),
    ("ACLED",                    "ACLED",         "https://acleddata.com/feed/",                              "global",        "conflict_data","A", "2"),
    ("ORF Online",               "ORF",           "https://www.orfonline.org/feed/",                          "asia",          "think_tank",   "A", "2"),
    ("East Asia Forum",          "E Asia F",      "https://eastasiaforum.org/feed/",                          "asia",          "think_tank",   "A", "2"),
    ("SIPRI",                    "SIPRI",         "https://www.sipri.org/rss.xml",                            "global",        "think_tank",   "A", "2"),
    ("Alma Research",            "Alma",          "https://israel-alma.org/feed/",                            "middle_east",   "think_tank",   "A", "2"),
    ("BESA Center",              "BESA",          "https://besacenter.org/feed/",                             "middle_east",   "think_tank",   "A", "2"),
    ("JCSS/Tau INSS",            "INSS",          "https://www.inss.org.il/feed/",                           "middle_east",   "think_tank",   "A", "2"),

    # ===== CYBERSECURITY & THREAT INTEL =====
    ("Recorded Future",          "Rec Future",    "https://www.recordedfuture.com/feed/",                     "global",        "cyber",        "A", "2"),
    ("Unit 42",                  "Unit 42",       "https://unit42.paloaltonetworks.com/feed/",                "global",        "cyber",        "A", "2"),
    ("Krebs on Security",        "Krebs",         "https://krebsonsecurity.com/feed/",                        "global",        "cyber",        "B", "2"),
    ("Bleeping Computer",        "BleepComp",     "https://www.bleepingcomputer.com/feed/",                   "global",        "cyber",        "B", "2"),
    ("The Hacker News",          "THN",           "https://feeds.feedburner.com/TheHackersNews",              "global",        "cyber",        "B", "2"),
    ("SANS ISC",                 "SANS ISC",      "https://isc.sans.edu/dailypage.xml",                       "global",        "cyber",        "B", "2"),
    ("Talos Intel",              "Talos",         "https://blog.talosintelligence.com/feed/",                 "global",        "cyber",        "A", "2"),
    ("Mandiant",                 "Mandiant",      "https://www.mandiant.com/resources/blog/rss.xml",          "global",        "cyber",        "A", "2"),
    ("Dark Reading",             "Dark Read",     "https://www.darkreading.com/rss.xml",                      "global",        "cyber",        "B", "2"),
    ("Threatpost",               "Threatpost",    "https://threatpost.com/feed/",                             "global",        "cyber",        "B", "2"),
    ("SecurityWeek",             "SecWeek",       "https://www.securityweek.com/feed/",                       "global",        "cyber",        "B", "2"),
    ("CyberScoop",               "CyberScoop",    "https://cyberscoop.com/feed/",                             "global",        "cyber",        "B", "2"),
    ("CISA Alerts",              "CISA",          "https://www.cisa.gov/sites/default/files/feeds/alerts.xml", "global",      "cyber_gov",    "A", "1"),

    # ===== SPACE & TECHNOLOGY =====
    ("SpaceNews",                "SpaceNews",     "https://spacenews.com/feed/",                              "global",        "space",        "B", "2"),
    ("Ars Technica",             "Ars Tech",      "https://feeds.arstechnica.com/arstechnica/index",           "global",        "tech",         "B", "2"),
    ("TechCrunch",               "TechCrunch",    "https://techcrunch.com/feed/",                             "global",        "tech",         "B", "2"),
    ("IEEE Spectrum",            "IEEE",          "https://spectrum.ieee.org/rss/fulltext.xml",               "global",        "tech",         "B", "2"),
    ("NASA Breaking News",       "NASA",          "https://www.nasa.gov/rss/dyn/breaking_news.rss",           "global",        "space",        "A", "1"),
    ("ESA Activities",           "ESA",           "https://www.esa.int/rssfeed/Our_Activities",               "europe",        "space",        "A", "2"),
    ("Payload Space",            "Payload",       "https://payloadspace.com/feed/",                           "global",        "space",        "B", "2"),
    ("Via Satellite",            "ViaSat",        "https://www.satellitetoday.com/feed/",                     "global",        "space",        "B", "2"),
    ("SpaceWatch.Global",        "SpaceWatch",    "https://spacewatch.global/feed/",                          "global",        "space",        "B", "2"),
    ("Wired",                    "Wired",         "https://www.wired.com/feed/rss",                            "global",        "tech",         "B", "2"),
    ("The Verge",                "Verge",         "https://www.theverge.com/rss/index.xml",                   "global",        "tech",         "B", "2"),
    ("MIT Tech Review",          "MIT TR",        "https://www.technologyreview.com/feed/",                   "global",        "tech",         "B", "2"),
    ("Nature News",              "Nature",        "https://feeds.nature.com/nature/rss/current",              "global",        "science",      "A", "2"),
    ("Science Daily",            "Sci Daily",     "https://www.sciencedaily.com/rss/all.xml",                 "global",        "science",      "B", "2"),
    ("New Scientist",            "New Sci",       "https://www.newscientist.com/feed/home",                   "global",        "science",      "B", "2"),

    # ===== GOVERNMENT & OFFICIAL =====
    ("State Dept Press Briefings","State Dept",   "https://www.state.gov/feed/",                              "global",        "gov",          "A", "1"),
    ("Pentagon News",            "Pentagon",      "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?Max=20&Site=945", "north_america","gov","A","1"),
    ("EU Commission Press",      "EU Press",      "https://ec.europa.eu/commission/presscorner/rss/en",        "europe",        "gov",          "A", "1"),
    ("UN News",                  "UN News",       "https://www.un.org/feeds/news/latest_news.xml",             "global",        "gov",          "A", "1"),
    ("IAEA Press Releases",      "IAEA",          "https://www.iaea.org/rss/press-releases.xml",               "global",        "gov",          "A", "1"),
    ("IEA News",                 "IEA",           "https://www.iea.org/feeds/news.xml",                       "global_finance","gov",          "A", "1"),
    ("OPEC Press Room",          "OPEC",          "https://www.opec.org/opec_web/en/rss/pressroom.xml",        "global_finance","gov",          "A", "1"),
    ("UK Gov News",              "UK Gov",        "https://www.gov.uk/government/feed",                        "europe",        "gov",          "A", "1"),
    ("Canada Gov News",          "Canada Gov",    "https://www.canada.ca/en/news/rss.xml",                    "north_america", "gov",          "A", "2"),
    ("NATO News",                "NATO",          "https://www.nato.int/rss/news.xml",                         "europe",        "gov",          "A", "1"),
    ("UNHCR Latest",             "UNHCR",         "https://www.unhcr.org/rss/latest.rss",                      "global",        "gov",          "A", "2"),
    ("WFP News",                 "WFP",           "https://www.wfp.org/rss/news",                             "global",        "gov",          "A", "2"),

    # ===== FINANCE & ECONOMICS =====
    ("MarketWatch Top",          "MktWatch",      "https://feeds.marketwatch.com/marketwatch/topstories/",     "global_finance","financial",    "B", "2"),
    ("Bloomberg Markets",        "Bloomberg",     "https://feeds.bloomberg.com/markets/news.rss",              "global_finance","financial",    "A", "2"),
    ("Trading Economics",        "TradEcon",      "https://feeds.tradingeconomics.com/rss/news.xml",           "global_finance","financial",    "B", "2"),
    ("FRED Blog",                "FRED",          "https://fredblog.stlouisfed.org/feed/",                    "global_finance","financial",    "A", "2"),
    ("EIA Today In Energy",      "EIA",           "https://www.eia.gov/todayinenergy/index.php?rss",           "global_finance","gov",         "A", "1"),
    ("EIA Weekly Petroleum",     "EIA WPSR",      "https://ir.eia.gov/wpsr/wpsrsummary.rss",                  "global_finance","gov",         "A", "1"),
    ("IMF Blog",                 "IMF",           "https://www.imf.org/en/Blogs/RSS",                          "global_finance","financial",    "A", "2"),
    ("World Bank News",          "World Bank",    "https://www.worldbank.org/en/news/rss",                     "global_finance","financial",    "A", "2"),
    ("St. Louis Fed",            "STL Fed",       "https://www.stlouisfed.org/rss/",                           "global_finance","financial",    "A", "2"),
    ("Investing.com",            "Investing",     "https://www.investing.com/rss/news.rss",                    "global_finance","financial",    "B", "2"),
    ("BIS News",                 "BIS",           "https://www.bis.org/rss/feeds_news.rss",                    "global_finance","financial",    "A", "2"),

    # ===== MARITIME =====
    ("Maritime Executive",       "MarExec",       "https://www.maritime-executive.com/rss.xml",               "global",        "maritime",     "B", "2"),
    ("Safety4Sea",               "S4S",           "https://safety4sea.com/feed/",                             "global",        "maritime",     "B", "2"),
    ("gCaptain",                 "gCaptain",      "https://gcaptain.com/feed/",                               "global",        "maritime",     "B", "2"),
    ("Marine Link",              "MarineLink",    "https://www.marinelink.com/rss/news",                       "global",        "maritime",     "B", "2"),
    ("Hellenic Shipping News",   "HellShip",      "https://www.hellenicshippingnews.com/feed/",               "global",        "maritime",     "B", "2"),
    ("Ship & Bunker",            "ShipBunker",    "https://shipandbunker.com/rss/news",                       "global_finance","maritime",     "B", "2"),

    # ===== DEFENSE & SECURITY =====
    ("USNI News",                "USNI",          "https://news.usni.org/feed",                               "global",        "defense",      "A", "2"),
    ("Breaking Defense",         "BreakDef",      "https://breakingdefense.com/feed/",                        "global",        "defense",      "A", "2"),
    ("Defense One",              "DefOne",        "https://www.defenseone.com/feed/",                          "north_america", "defense",      "A", "2"),
    ("War on the Rocks",         "WotR",          "https://warontherocks.com/feed/",                          "global",        "defense",      "A", "2"),
    ("The Drive War Zone",       "War Zone",      "https://www.thedrive.com/the-war-zone/rss",                "global",        "defense",      "B", "2"),
    ("Naval News",               "NavalNews",     "https://www.navalnews.com/feed/",                          "global",        "defense",      "A", "2"),
    ("SOFREP",                   "SOFREP",        "https://sofrep.com/feed/",                                 "global",        "defense",      "B", "2"),
    ("The Cipher Brief",         "Cipher",        "https://www.thecipherbrief.com/feed",                       "global",        "intel",        "A", "2"),

    # ===== ENERGY =====
    ("OilPrice.com",             "OilPrice",      "https://oilprice.com/rss/main",                            "global_finance","energy",       "B", "2"),
    ("Energy Voice",             "EnergyV",       "https://www.energyvoice.com/feed/",                        "global_finance","energy",       "B", "2"),
    ("Rigzone",                  "Rigzone",       "https://www.rigzone.com/news/rss/rigzone_latest.xml",       "global_finance","energy",       "B", "2"),
    ("Natural Gas World",        "NGW",           "https://www.naturalgasworld.com/rss",                      "global_finance","energy",       "B", "2"),

    # ===== OSINT =====
    ("Bellingcat",               "Bellingcat",    "https://www.bellingcat.com/feed/",                         "global",        "osint",        "A", "2"),
    ("Oryx Blog",                "Oryx",          "https://www.oryxspioenkop.com/feeds/posts/default",         "global",        "osint",        "B", "2"),
    ("OSINT Combine",            "OSINT Com",     "https://www.osintcombine.com/feed/",                        "global",        "osint",        "B", "2"),

    # ===== WATCHDOG =====
    ("HRW Latest",               "HRW",           "https://www.hrw.org/rss/latest.xml",                       "global",        "watchdog",     "A", "2"),
    ("HRW Middle East",          "HRW ME",        "https://www.hrw.org/rss/middle-east.xml",                  "middle_east",   "watchdog",     "A", "2"),
    ("HRW Asia",                 "HRW Asia",      "https://www.hrw.org/rss/asia.xml",                         "asia",          "watchdog",     "A", "2"),
    ("HRW Africa",               "HRW Africa",    "https://www.hrw.org/rss/africa.xml",                       "africa",        "watchdog",     "A", "2"),
    ("Amnesty Intl",             "Amnesty",       "https://www.amnesty.org/en/rss/",                          "global",        "watchdog",     "A", "2"),
    ("Transparency Intl",        "TI",            "https://www.transparency.org/en/rss",                      "global",        "watchdog",     "A", "2"),

    # ===== US POLITICS =====
    ("Axios",                    "Axios",         "https://www.axios.com/feed/",                              "north_america", "news",         "B", "2"),
    ("Politico US",              "Politico US",   "https://www.politico.com/rss/politicopicks.xml",            "north_america", "news",         "B", "2"),
    ("The Hill",                 "The Hill",      "https://thehill.com/rss/syndication/feed.xml",              "north_america", "news",         "B", "2"),
    ("Newsweek",                 "Newsweek",      "https://www.newsweek.com/rss",                             "north_america", "news",         "B", "2"),
    ("NBC News",                 "NBC",           "https://feeds.nbcnews.com/nbcnews/public/news",            "north_america", "news",         "B", "2"),
    ("ABC News US",              "ABC US",        "https://abcnews.go.com/abcnews/topstories",                "north_america", "news",         "B", "2"),
    ("CBS News",                 "CBS",           "https://www.cbsnews.com/latest/rss/main",                  "north_america", "news",         "B", "2"),
    ("The Economist",            "Economist",     "https://www.economist.com/feeds/print-sections/77/business.xml","global_finance","newspaper", "A", "2"),
]


def build_catalog():
    log("=" * 60)
    log("SOURCE BUILD PIPELINE — feedparser mode")
    log("=" * 60)

    # Build from known feed database
    log(f"\n📡 Testing {len(FEED_DATABASE)} RSS feeds from database...")
    
    catalog = []
    seen_urls = set()
    working = 0
    failed = 0
    
    for entry in FEED_DATABASE:
        display_name, short_label, url, region, stype, adm_rel, adm_cred = entry
        
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        feed_works, entry_count, bozo = test_feed(url)
        
        entry = {
            "name": display_name,
            "shortname": short_label,
            "type": stype,
            "url": url,
            "rss": url if feed_works else None,
            "region": region,
            "themes": [stype],
            "admiralty_source": adm_rel,
            "admiralty_info": adm_cred,
            "tested": True,
            "tested_at": NOW,
            "status": "working" if feed_works else "feed_failed",
            "fetched_sample": True if feed_works else False,
            "sample_entry_count": entry_count,
        }
        catalog.append(entry)
        
        if feed_works:
            working += 1
            log(f"  ✅ {display_name}: {entry_count} entries")
        else:
            failed += 1
        
        time.sleep(DELAY)
    
    # ===== TEST SUBSTACK FEEDS FROM EXISTING SOURCES =====
    log(f"\n📬 Testing Substack RSS feeds from existing sources...")
    sources = json.loads(SOURCES_PATH.read_text())
    durable = sources.get("durable_sources", [])
    
    substack_pattern = re.compile(r'https://([a-z0-9-]+)\.substack\.com')
    substack_found = 0
    substack_working = 0
    
    for s in durable:
        url = s.get("url", "")
        name = s.get("name", "")
        m = substack_pattern.match(url)
        if not m:
            continue
        
        rss_url = url.rstrip("/") + "/feed"
        if rss_url in seen_urls:
            continue
        seen_urls.add(rss_url)
        
        feed_works, entry_count, bozo = test_feed(rss_url)
        substack_found += 1
        
        if feed_works:
            entry = {
                "name": name,
                "shortname": name[:35],
                "type": "substack",
                "url": url,
                "rss": rss_url,
                "region": "global",
                "themes": ["geopolitics", "analysis"],
                "admiralty_source": "C",
                "admiralty_info": "2",
                "tested": True,
                "tested_at": NOW,
                "status": "working",
                "fetched_sample": True,
                "sample_entry_count": entry_count,
            }
            catalog.append(entry)
            substack_working += 1
            working += 1
            log(f"  ✅ {name}: {entry_count} entries")
        else:
            failed += 1
        
        time.sleep(DELAY)
    
    log(f"  Substack: {substack_working}/{substack_found} working")
    
    # ===== TEST PRE-CONFIGURED RSS FEEDS FROM SOURCES.JSON =====
    log(f"\n🔍 Testing pre-configured RSS feeds from sources.json...")
    config_found = 0
    config_working = 0
    
    for s in durable:
        rss = s.get("rss", "")
        url = s.get("url", "")
        name = s.get("name", "")
        if not rss:
            continue
        if rss in seen_urls:
            continue
        seen_urls.add(rss)
        
        feed_works, entry_count, bozo = test_feed(rss)
        config_found += 1
        
        if feed_works:
            entry = {
                "name": name,
                "shortname": name[:35],
                "type": s.get("type", "unknown"),
                "url": url,
                "rss": rss,
                "region": "global",
                "themes": [],
                "admiralty_source": "B",
                "admiralty_info": "2",
                "tested": True,
                "tested_at": NOW,
                "status": "working",
                "fetched_sample": True,
                "sample_entry_count": entry_count,
            }
            catalog.append(entry)
            config_working += 1
            working += 1
            log(f"  ✅ {name}: {entry_count} entries")
        else:
            failed += 1
        
        time.sleep(DELAY)
    
    log(f"  Pre-configured RSS: {config_working}/{config_found} working")
    
    # ===== FINAL SUMMARY =====
    total = len(catalog)
    log(f"\n{'='*60}")
    log(f"📊 FINAL CATALOG SUMMARY")
    log(f"{'='*60}")
    log(f"  Total entries: {total}")
    log(f"  Working feeds: {working}")
    log(f"  Failed feeds: {failed}")
    log(f"  Feed URLs tested: {len(seen_urls)}")
    
    # By region
    regions = {}
    for s in catalog:
        if s["status"] == "working":
            r = s["region"]
            regions[r] = regions.get(r, 0) + 1
    log(f"\n  By region (working only):")
    for r, c in sorted(regions.items(), key=lambda x: -x[1]):
        log(f"    {r}: {c}")
    
    # By type
    types = {}
    for s in catalog:
        if s["status"] == "working":
            t = s["type"]
            types[t] = types.get(t, 0) + 1
    log(f"\n  By type:")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        log(f"    {t}: {c}")
    
    # Write catalog
    log(f"\n💾 Writing catalog to {OUTPUT_PATH}...")
    catalog_data = {
        "total_entries": total,
        "working_feeds": working,
        "failed_feeds": failed,
        "generated_at": NOW,
        "regions_breakdown": regions,
        "types_breakdown": types,
        "sources": catalog,
    }
    OUTPUT_PATH.write_text(json.dumps(catalog_data, indent=2))
    log(f"  Done! Written {total} sources to {OUTPUT_PATH}")
    
    return working, total


if __name__ == "__main__":
    working, total = build_catalog()
    print(f"\n✅ Pipeline completed. {working}/{total} working sources written to analyst/meta/sources_tested.json")
