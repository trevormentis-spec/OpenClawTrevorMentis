#!/usr/bin/env python3
"""Collector worker for the Daily Intel Brief.

Reads the durable source registry (analyst/meta/sources.json) plus a
short list of major wires and dynamically-loaded catalog feeds from
analyst/meta/sources_tested.json (maintained by the heartbeat source builder).
Pulls the last 24 hours, normalises into incidents tagged by region per
references/regions.json, and writes WORKING_DIR/raw/incidents.json.

This is a *reference implementation* of agents/collector.md. Subagents
that follow that prompt are free to do better, but this script gives a
deterministic floor and a hand-callable smoke test.

Heavy parsing (NER, geocoding, deduplication) is deliberately simple —
the analyst's prompt is robust to imperfect collector output, and the
24h window keeps the volume small.

Usage:

    python3 scripts/collect.py --working-dir <wd> \
        --regions skills/daily-intel-brief/references/regions.json \
        --sources analyst/meta/sources.json [--mock]

`--mock` short-circuits live network and writes a small canned dataset
into raw/incidents.json so the rest of the pipeline can be exercised.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any
from xml.etree import ElementTree as ET

WIRE_FEEDS = [
    # Major wires — used in addition to durable sources to top up regions.
    # Tested live 2026-05-14: Reuters and AP feeds are dead (404/DNS); replaced.
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("FT World", "https://www.ft.com/world?format=rss"),
    ("The Guardian World", "https://www.theguardian.com/world/rss"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml"),

    ("France 24 EN", "https://www.france24.com/en/rss"),
    ("DW News EN", "https://rss.dw.com/rdf/rss-en-world"),
    ("CNBC World", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"),
]

# Local-language / non-English feeds — added 2026-05-13 for multi-language collection.
# Tuple: (name, url, language_code, admiralty_rank)
# These provide region-specific narratives, local reporting, and alternative baselines.
# The collection model (DeepSeek V4 Flash) can handle multi-lingual content.
LOCAL_LANGUAGE_FEEDS = [
    # Persian / Farsi (Iran)

    # Arabic (Gulf / Middle East)

    ("Arab News", "https://www.arabnews.com/rss.xml", "en", ("B", 2)),

    ("The New Arab", "https://www.newarab.com/rss.xml", "en", ("B", 2)),
    # Russian
    ("TASS (English)", "https://tass.com/rss/v2.xml", "en", ("C", 3)),
    ("Meduza (English)", "https://meduza.io/rss/en/all", "en", ("B", 2)),
    ("Meduza (Russian)", "https://meduza.io/rss/all", "ru", ("B", 2)),
    ("Moscow Times", "https://www.themoscowtimes.com/rss/news", "en", ("B", 2)),

    # Chinese
    ("Xinhua (English)", "http://www.xinhuanet.com/english/rss/worldrss.xml", "en", ("C", 3)),
    ("South China Morning Post", "https://www.scmp.com/rss/4/feed", "en", ("B", 2)),

    # Israeli / Hebrew
    ("Ynet (Hebrew)", "https://www.ynet.co.il/Integration/StoryRss2.xml", "he", ("B", 2)),
    ("Jerusalem Post", "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx", "en", ("B", 2)),

    # European
    ("Le Monde (English)", "https://www.lemonde.fr/en/rss/une.xml", "en", ("B", 2)),

    ("El País (Spanish)", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "es", ("B", 2)),
    ("Corriere della Sera (Italian)", "https://xml2.corriereobjects.it/rss/esteri.xml", "it", ("B", 2)),

    # --- EUROPE LOCAL-LANGUAGE / REGIONAL FEEDS (added 2026-05-27) ---
    # 20 key multilingual Europe sources. Validated via Europe RSS feed scanner.
    ("Politico Europe", "https://www.politico.eu/feed", "en", ("B", 2)),
    ("EUobserver", "https://euobserver.com/feed", "en", ("B", 2)),
    ("Euractiv", "https://www.euractiv.com/feed", "en", ("B", 2)),
    ("Euronews", "https://www.euronews.com/rss", "en", ("B", 2)),
    ("Balkan Insight", "https://balkaninsight.com/feed", "en", ("B", 2)),
    ("VSquare", "https://vsquare.org/feed", "en", ("B", 2)),
    ("OCCRP", "https://www.occrp.org/en/feed", "en", ("B", 2)),
    ("Bellingcat", "https://www.bellingcat.com/feed", "en", ("B", 2)),
    ("OSW", "https://www.osw.waw.pl/en/rss.xml", "en", ("A", 2)),
    # Gazeta Wyborcza: no working RSS feed (base URL returns 0 entries) — removed
    ("Denník N", "https://dennikn.sk/feed", "sk", ("B", 2)),
    # Telex: no working RSS feed — removed
    ("Postimees", "https://www.postimees.ee/rss", "et", ("B", 2)),
    ("ERR News", "https://news.err.ee/rss", "en", ("B", 2)),
    ("Dagens Nyheter", "https://www.dn.se/rss", "sv", ("B", 2)),
    ("Aftenposten", "https://www.aftenposten.no/rss", "no", ("B", 2)),
    # Politiken: no working RSS feed — removed
    # Helsingin Sanomat: no working RSS feed — removed
    ("Kyiv Independent", "https://kyivindependent.com", "en", ("B", 2)),
    ("Meduza", "https://meduza.io/rss/all", "ru", ("B", 2)),
    # Asian

    ("Channel News Asia", "https://www.channelnewsasia.com/rssfeeds/8395986", "en", ("B", 2)),
    # Africa — Tier-1 daily baseline (included every brief, never rotated out)
    ("Africanews", "https://www.africanews.com/feed/", "en", ("B", 2)),
    # ISS Africa: RSS feed returns 0 entries — removed (use catalog rotation instead)
    ("The Africa Report", "https://www.theafricareport.com/feed/", "en", ("B", 2)),
    ("Premium Times (Nigeria)", "https://www.premiumtimesng.com/feed", "en", ("B", 2)),
    ("Daily Maverick (SA)", "https://www.dailymaverick.co.za/rss/", "en", ("B", 2)),
    # Daily Nation: 403 Forbidden — removed (use catalog rotation instead)
    ("Mada Masr (Egypt)", "https://www.madamasr.com/en/feed/", "en", ("B", 2)),
    ("Hespress (Morocco)", "https://en.hespress.com/feed/", "en", ("B", 2)),
    ("Radio Dabanga (Sudan)", "https://www.dabangasudan.org/en/feed", "en", ("B", 2)),
    # Addis Standard: 403 Forbidden — removed (use catalog rotation instead)
    ("Actualité.cd (DRC)", "https://actualite.cd/feed/", "fr", ("B", 2)),
    ("Radio Okapi (DRC)", "https://www.radiookapi.net/rss.xml", "fr", ("B", 2)),
    # Cabo Ligado: RSS feed returns 0 entries — removed (use catalog rotation)
    # Garowe Online: 404 Not Found — removed (use catalog rotation instead)
    ("HumAngle (Nigeria/Sahel)", "https://humanglemedia.com/feed/", "en", ("A", 2)),
    ("Jeune Afrique", "https://www.jeuneafrique.com/feed/", "fr", ("B", 2)),

    # South America
    ("MercoPress", "https://en.mercopress.com/rss/latin-america", "en", ("B", 2)),
    ("Buenos Aires Times", "https://www.batimes.com.ar/feed", "en", ("B", 2)),
    # Global Finance & Markets
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "en", ("B", 2)),
    ("ZeroHedge", "https://feeds.feedburner.com/zerohedge/feed", "en", ("C", 3)),
    # --- South East Asia

    ("Vietnam Express", "https://e.vnexpress.net/rss/world.rss", "en", ("B", 2)),

    ("PhilStar (Philippines)", "https://www.philstar.com/rss/headlines", "en", ("B", 2)),
    ("Rappler (Philippines)", "https://www.rappler.com/world/feed", "en", ("B", 2)),

    ("Malay Mail", "https://www.malaymail.com/feed/rss", "en", ("B", 2)),
    ("ASEAN Secretariat News", "https://asean.org/feed", "en", ("B", 2)),
    ("Fulcrum ISEAS (SE Asia)", "https://fulcrum.sg/feed", "en", ("B", 2)),
    ("The Diplomat SE Asia", "https://thediplomat.com/regions/southeast-asia/feed", "en", ("B", 2)),
    # --- Central Asia / India / China

    ("The Diplomat China/Asia", "https://thediplomat.com/regions/china/feed", "en", ("B", 2)),
    ("Dawn (Pakistan)", "https://www.dawn.com/feeds/home", "en", ("B", 2)),

    ("Times of India", "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "en", ("B", 2)),

    ("Asia Times", "https://asiatimes.com/feed", "en", ("B", 2)),
    ("Carnegie India", "https://carnegieindia.org/feed", "en", ("B", 2)),

    ("The News International (Pakistan)", "https://www.thenews.com.pk/rss/1/1", "en", ("B", 2)),
    ("The Kathmandu Post", "https://kathmandupost.com/rss", "en", ("B", 2)),
    ("Carnegie China", "https://carnegiechina.org/feed", "en", ("B", 2)),
    ("Global Voices Central Asia", "https://globalvoices.org/-/world/central-asia-caucasus/feed", "en", ("B", 2)),
    ("Himal Southasian", "https://www.himalmag.com/feed", "en", ("B", 2)),

    ("StratNews Global India", "https://stratnewsglobal.com/feed", "en", ("B", 2)),
    # --- Oceania / Pacific
    ("ASPI The Strategist", "https://www.aspistrategist.org.au/feed", "en", ("B", 2)),

    ("Sydney Morning Herald", "https://www.smh.com.au/rss/national.xml", "en", ("B", 2)),

    ("Radio NZ", "https://www.rnz.co.nz/rss/national.xml", "en", ("B", 2)),

    ("Devpolicy Blog (ANU)", "https://devpolicy.org/feed", "en", ("B", 2)),
    ("Island Business (Pacific)", "https://islandsbusiness.com/feed", "en", ("B", 2)),
    # --- South America
    ("InSight Crime", "https://insightcrime.org/feed", "en", ("B", 2)),
    ("Peru Reports", "https://perureports.com/feed/", "en", ("B", 2)),
    ("La Prensa Latina", "https://www.laprensalatina.com/feed", "en", ("B", 2)),
    ("Global Americans", "https://globalamericans.org/feed", "en", ("B", 2)),
    ("Infobae (Latin America)", "https://www.infobae.com/arc/outboundfeeds/rss/", "en", ("B", 2)),
    ("Dialogo Americas", "https://dialogo-americas.com/feed/", "en", ("B", 2)),
    # South America — country-level major newspapers
    ("Folha de S.Paulo (Portuguese)", "https://feeds.folha.uol.com.br/emcimadahora/rss.xml", "pt", ("B", 2)),
    ("Clarin (Argentina)", "https://www.clarin.com/rss/lo-ultimo/", "es", ("B", 2)),
    ("El Tiempo (Colombia)", "https://www.eltiempo.com/rss/colombia.xml", "es", ("B", 2)),

    ("El Nacional (Venezuela)", "https://www.elnacional.com/feed/", "es", ("B", 2)),
    ("Agência Brasil (Portuguese)", "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "pt", ("B", 2)),
    # --- Central America & Caribbean
    ("Caribbean News Global", "https://www.caribbeannewsglobal.com/feed", "en", ("B", 2)),

    # --- Africa

    ("DefenceWeb (Africa)", "https://www.defenceweb.co.za/feed", "en", ("B", 2)),
    ("HumAngle (Sahel/West Africa)", "https://humanglemedia.com/feed", "en", ("B", 2)),

    ("Zitamar News (Mozambique)", "https://zitamar.com/feed", "en", ("B", 2)),

    ("Mail & Guardian (SA)", "https://mg.co.za/rss", "en", ("B", 2)),
    ("Premium Times (Nigeria)", "https://www.premiumtimesng.com/feed", "en", ("B", 2)),

    ("Sahara Reporters (Nigeria)", "https://saharareporters.com/rss.xml", "en", ("B", 2)),

    ("Ethiopia Insight", "https://www.ethiopia-insight.com/feed", "en", ("B", 2)),

    # --- Prediction Markets (extra)
    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss", "en", ("B", 2)),

    ("Financial Times Markets", "https://www.ft.com/markets?format=rss", "en", ("B", 2)),

    ("OilPrice.com", "https://oilprice.com/rss/main", "en", ("C", 3)),
    # North America
    ("Politico", "https://rss.politico.com/politics-news.xml", "en", ("B", 2)),

    ("CBC News (Canada)", "https://www.cbc.ca/cmlink/rss-world", "en", ("B", 2)),
    ("Mexico News Daily", "https://mexiconewsdaily.com/feed/", "en", ("B", 2)),
    ("Border Report (US-Mexico)", "https://www.borderreport.com/feed/", "en", ("B", 2)),
    # ── Substack: global geopolitics & intelligence ──
    ("ARCLIGHT Africa", "https://arclightafrica.substack.com/feed", "en", ("B", 2)),
    ("ChinaTalk", "https://chinatalk.substack.com/feed", "en", ("B", 2)),

    ("Global Dispatches", "https://globaldispatches.substack.com/feed", "en", ("B", 2)),
    ("In Geopolitics Today", "https://geopol.substack.com/feed", "en", ("B", 2)),
    # ── Substack: regional specialist ──
    ("Latin American Geopolitics", "https://francostachiotti.substack.com/feed", "en", ("B", 2)),
    ("The Asia Cable", "https://theasiacable.substack.com/feed", "en", ("B", 2)),
    ("USCNPM Asia", "https://uscnpm.substack.com/feed", "en", ("B", 2)),
    ("This Week in Africa", "https://thisweekinafrica.substack.com/feed", "en", ("B", 2)),
    ("Yaws Brief Africa", "https://yawboadu.substack.com/feed", "en", ("B", 2)),
    ("Geopolitico", "https://geopolitico.substack.com/feed", "en", ("B", 2)),
    # ── Substack: Australia / Oceania ──
    ("FAO Journal (security)", "https://faoajournal.substack.com/feed", "en", ("B", 2)),
    ("Global Affairs Review", "https://globalaffairsreview.substack.com/feed", "en", ("B", 2)),
    # ── Substack: South America ──
    ("Boz Latin America Risk Report", "https://boz.substack.com/feed", "en", ("B", 2)),
    ("Steep in Latin America", "https://steepinlatinamerica.substack.com/feed", "en", ("B", 2)),
    # ── Substack: India / Central Asia ──
    ("India Inside Out", "https://rohanvenkat.substack.com/feed", "en", ("B", 2)),
    ("Public Policy India", "https://publicpolicy.substack.com/feed", "en", ("B", 2)),
    ("Sinification (China analysis)", "https://sinification.substack.com/feed", "en", ("B", 2)),
    # ── Substack: Africa ──
    ("Geopolitics Report (Africa)", "https://geopoliticsreport.substack.com/feed", "en", ("B", 2)),

    # Additional verified regional feeds
    ("The Mandarin (Australia)", "https://www.themandarin.com.au/feed/", "en", ("B", 2)),
    ("Jamaica Observer", "https://www.jamaicaobserver.com/feed/", "en", ("B", 2)),
    ("Nation News (Barbados)", "https://www.nationnews.com/rss", "en", ("B", 2)),
    ("Mail & Guardian (SA)", "https://mg.co.za/rss/", "en", ("B", 2)),
    ("The Third Pole (Asia)", "https://www.thethirdpole.net/feed/", "en", ("B", 2)),
    ("Vietnam News", "https://vietnamnews.vn/rss/home.rss", "en", ("B", 2)),
    ("PhilStar (Philippines)", "https://www.philstar.com/rss/headlines", "en", ("B", 2)),
    # ── Additional verified Substack + blog sources ──
    ("SitRep (geopolitics)", "https://situationreport.substack.com/feed", "en", ("B", 2)),
    ("Risk Intelligence (global)", "https://riskintel.substack.com/feed", "en", ("B", 2)),

    # ── Substack: working replacements for previously broken feeds (2026-05-22) ──
    # Replaces: Geopolitical Futures, The Cipher Brief, Geopolitical Intel Weekly
    ("Geopolitical Dispatch", "https://www.geopoliticaldispatch.com/feed", "en", ("B", 2)),
    ("The Geopolitical Report", "https://thegeopoliticalreview.substack.com/feed", "en", ("B", 2)),
    ("Unravelling Geopolitics", "https://unravellinggeopolitics.substack.com/feed", "en", ("B", 2)),
    # Replaces: Latin America Weekly Brief, Africa Strategy
    ("Latin America Daily Briefing", "https://latinamericadailybriefing.substack.com/feed", "en", ("B", 2)),

    # Replaces: Eurasia Geopolitics, Asia Geopolitics Review
    ("China-Russia Report", "https://chinarussiareport.substack.com/feed", "en", ("B", 2)),
    ("Interconnected (tech/Asia/geopolitics)", "https://interconnect.substack.com/feed", "en", ("B", 2)),
    # Replaces: Defense & Geopolitics SE Asia
    ("The Southeast Asia Desk", "https://www.thesoutheastasiadesk.com/feed", "en", ("B", 2)),
    # Replaces: Pacific Geopolitics Weekly, China Observers
    ("Vox Pasifika (Pacific geopolitics)", "https://voxpasifika.substack.com/feed", "en", ("B", 2)),
    ("China Strategy", "https://chinastrategy.substack.com/feed", "en", ("B", 2)),
    # Replaces: The Asia Review
    ("The China Project", "https://thechinaproject.substack.com/feed", "en", ("B", 2)),
    # Replaces: Strategic Insight Africa
    ("Timothy Ash EM & Geopolitics", "https://timothyash.substack.com/feed", "en", ("B", 2)),
    # Replaces: PS21, Geopolitics Explained, Pacific Security Scan
    ("TSG Global Monitor (Scowcroft)", "https://scowcroft.substack.com/feed", "en", ("B", 2)),
    ("Indo-Pacific Insights", "https://indopacificinsights.substack.com/feed", "en", ("B", 2)),

    # ── Central America: country-level major newspapers ──
    ("Prensa Libre (Guatemala)", "https://www.prensalibre.com/feed/", "es", ("B", 2)),

    ("La Nación (Costa Rica)", "https://www.nacion.com/rss/", "es", ("B", 2)),

    ("El Diario de Hoy (El Salvador)", "https://www.elsalvador.com/rss/", "es", ("B", 2)),
    ("Diario Más (El Salvador)", "https://www.diariomas.com/rss/", "es", ("B", 2)),
    # ── Caribbean: island-level major newspapers ──

    ("Trinidad and Tobago Newsday", "https://newsday.co.tt/feed/", "en", ("B", 2)),
    # ── Africa: country-level major newspapers ──

    ("Vanguard (Nigeria)", "https://www.vanguardngr.com/feed/", "en", ("B", 2)),
    ("The Punch (Nigeria)", "https://punchng.com/feed/", "en", ("B", 2)),

    ("Times of Zambia", "https://www.times.co.zm/feed/", "en", ("B", 2)),

    ("Jeune Afrique (Francophone Africa)", "https://www.jeuneafrique.com/feed/", "fr", ("B", 2)),

    ("Egypt Independent", "https://egyptindependent.com/feed/", "en", ("B", 2)),
    ("Libya Herald", "https://www.libyaherald.com/feed/", "en", ("B", 2)),

    # ── South East Asia: country-level major newspapers ──

    ("Khaosod English (Thailand)", "https://www.khaosodenglish.com/feed/", "en", ("B", 2)),

    ("Tempo (Indonesia)", "https://www.tempo.co/rss/", "id", ("B", 2)),
    ("Myanmar Now", "https://myanmar-now.org/en/feed/", "en", ("B", 2)),
    ("Khmer Times (Cambodia)", "https://www.khmertimeskh.com/feed/", "en", ("B", 2)),
    ("Vientiane Times (Laos)", "https://www.vientianetimes.org.la/rss.xml", "en", ("B", 2)),
    ("The Borneo Post (Malaysia)", "https://www.theborneopost.com/feed/", "en", ("B", 2)),
    # ── Central Asia: country-level major newspapers ──
    ("The Express Tribune (Pakistan)", "https://tribune.com.pk/feed/", "en", ("B", 2)),
    ("Geo News (Pakistan)", "https://www.geo.tv/rss/1/2", "en", ("B", 2)),
    ("ARY News (Pakistan)", "https://arynews.tv/feed/", "en", ("B", 2)),
    ("TOLOnews (Afghanistan)", "https://tolonews.com/rss.xml", "en", ("B", 2)),
    ("Ariana News (Afghanistan)", "https://www.ariananews.af/feed/", "en", ("B", 2)),
    ("Times of Central Asia", "https://timesca.com/feed/", "en", ("B", 2)),
    ("Tashkent Times (Uzbekistan)", "https://tashkenttimes.uz/feed/", "en", ("B", 2)),
    ("KazInform (Kazakhstan)", "https://www.inform.kz/rss.xml", "en", ("C", 3)),

    ("Trend News Agency (Azerbaijan)", "https://en.trend.az/feed/", "en", ("C", 3)),
    ("Caucasus Watch", "https://caucasuswatch.de/feed/", "en", ("B", 2)),
    # ── Pacific Islands: country-level sources ──
    ("Fiji Times", "https://www.fijitimes.com/feed/", "en", ("B", 2)),
    ("Fiji Village", "https://www.fijivillage.com/rss.xml", "en", ("B", 2)),
    ("Papua New Guinea Post-Courier", "https://www.postcourier.com.pg/feed/", "en", ("B", 2)),
    ("Solomon Star (Solomon Islands)", "https://www.solomonstarnews.com/feed/", "en", ("B", 2)),
    ("Vanuatu Daily Post", "https://www.dailypost.vu/feed/", "en", ("B", 2)),
    ("Samoa Observer", "https://www.samoaobserver.ws/feed/", "en", ("B", 2)),
    ("Tonga World News", "https://www.tongaworldnews.com/feed/", "en", ("B", 2)),
    ("Marianas Variety (Pacific)", "https://www.mvariety.com/rss/", "en", ("B", 2)),
    # ── Middle East: additional country-level ──
    ("Saudi Gazette", "https://www.saudigazette.com.sa/rss/", "en", ("B", 2)),
    ("Kuwait Times", "https://kuwaittimes.com/rss/", "en", ("B", 2)),
    ("Oman Daily Observer", "https://www.omanobserver.om/feed/", "en", ("B", 2)),
    ("Jordan Times", "https://www.jordantimes.com/rss.xml", "en", ("B", 2)),
    ("Daily Sabah (Turkey)", "https://www.dailysabah.com/rss/feed.xml", "en", ("B", 2)),
    ("Hurriyet Daily News (Turkey)", "https://www.hurriyetdailynews.com/rss.aspx", "en", ("B", 2)),
    ("Iraq News", "https://www.iraqinews.com/feed/", "en", ("B", 2)),
    ("Syrian Arab News Agency (SANA)", "https://www.sana.sy/en/rss.xml", "en", ("C", 3)),
    ("Yemen News Agency (SABA)", "https://www.sabanew.net/rss/en.xml", "en", ("C", 3)),

    # ── Telegram channels (via public RSS at t.me/s/CHANNEL) ──
    # DISABLED: ("Telegram: OSINTdefender", "https://t.me/s/OSINTdefender", "en", ("A", 2)),
    # DISABLED: ("Telegram: judean_osint", "https://t.me/s/judean_osint", "en", ("A", 2)),
    # DISABLED: ("Telegram: HormuzMonitor", "https://t.me/s/HormuzMonitor", "en", ("A", 2)),
    # DISABLED: ("Telegram: Intel Crab War Mapper", "https://t.me/s/warmapper", "en", ("B", 2)),
    # DISABLED: ("Telegram: War Mapper", "https://t.me/s/warmonitor", "en", ("B", 2)),
    # DISABLED: ("Telegram: Ukraine War Map", "https://t.me/s/ukraine_map", "en", ("B", 2)),
    # DISABLED: ("Telegram: GeoConfirmed", "https://t.me/s/GeoConfirmed", "en", ("B", 2)),
    # DISABLED: ("Telegram: Special Kherson Cat", "https://t.me/s/SpecialKhersonCat", "en", ("B", 2)),
    # DISABLED: ("Telegram: NOELreports", "https://t.me/s/NOELreports", "en", ("B", 2)),
    # DISABLED: ("Telegram: Liveuamap", "https://t.me/s/liveuamap", "en", ("B", 2)),
    # DISABLED: ("Telegram: Clash Report", "https://t.me/s/clashreport", "en", ("B", 2)),
    # DISABLED: ("Telegram: Middle East Observer", "https://t.me/s/MiddleEastObserver", "en", ("B", 2)),
    # DISABLED: ("Telegram: War in Ukraine", "https://t.me/s/war_in_ukraine", "en", ("B", 2)),
    # DISABLED: ("Telegram: South China Sea OSINT", "https://t.me/s/SCS_OSINT", "en", ("B", 2)),
    # DISABLED: ("Telegram: Navigation Wars (Red Sea/Hormuz)", "https://t.me/s/NavWars", "en", ("B", 2)),
    # DISABLED: ("Telegram: Military Summary", "https://t.me/s/MilitarySummary", "en", ("B", 2)),
    # DISABLED: ("Telegram: Africa Intel", "https://t.me/s/africa_intel", "en", ("B", 2)),
    # DISABLED: ("Telegram: Latin America OSINT", "https://t.me/s/LatAmOSINT", "en", ("B", 2)),

    # ── Multilingual broadcasters & native-language dailies ──
    ("BBC Persian", "https://feeds.bbci.co.uk/persian/rss.xml", "fa", ("B", 2)),
    ("BBC Russian", "https://feeds.bbci.co.uk/russian/rss.xml", "ru", ("B", 2)),
    ("BBC Chinese", "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml", "zh", ("B", 2)),
    ("BBC Mundo (Spanish)", "https://feeds.bbci.co.uk/mundo/rss.xml", "es", ("B", 2)),
    ("BBC Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml", "pt", ("B", 2)),
    ("BBC Arabic", "https://feeds.bbci.co.uk/arabic/rss.xml", "ar", ("B", 2)),
    ("BBC Hindi", "https://feeds.bbci.co.uk/hindi/rss.xml", "hi", ("B", 2)),
    ("BBC Urdu", "https://feeds.bbci.co.uk/urdu/rss.xml", "ur", ("B", 2)),
    ("BBC Swahili", "https://feeds.bbci.co.uk/swahili/rss.xml", "sw", ("B", 2)),
    ("BBC Hausa", "https://feeds.bbci.co.uk/hausa/rss.xml", "ha", ("B", 2)),
    ("BBC Vietnamese", "https://feeds.bbci.co.uk/vietnamese/rss.xml", "vi", ("B", 2)),
    ("BBC Burmese", "https://feeds.bbci.co.uk/burmese/rss.xml", "my", ("B", 2)),
    ("BBC Somali", "https://feeds.bbci.co.uk/somali/rss.xml", "so", ("B", 2)),
    ("BBC Afaan Oromo", "https://feeds.bbci.co.uk/afaanoromoo/rss.xml", "om", ("B", 2)),
    ("BBC Amharic", "https://feeds.bbci.co.uk/amharic/rss.xml", "am", ("B", 2)),
    ("BBC Tigrinya", "https://feeds.bbci.co.uk/tigrinya/rss.xml", "ti", ("B", 2)),
    ("DW Arabic", "https://rss.dw.com/rdf/rss-ar-all", "ar", ("B", 2)),
    ("DW Spanish", "https://rss.dw.com/rdf/rss-es-all", "es", ("B", 2)),
    ("DW Russian", "https://rss.dw.com/rdf/rss-ru-all", "ru", ("B", 2)),
    ("DW Chinese", "https://rss.dw.com/rdf/rss-zh-all", "zh", ("B", 2)),
    ("DW Portuguese (Brasil)", "https://rss.dw.com/rdf/rss-pt-all", "pt", ("B", 2)),
    ("DW French (Afrique)", "https://rss.dw.com/rdf/rss-fr-all", "fr", ("B", 2)),
    ("DW Turkish", "https://rss.dw.com/rdf/rss-tr-all", "tr", ("B", 2)),
    ("DW Persian", "https://rss.dw.com/rdf/rss-fa-all", "fa", ("B", 2)),
    ("DW Hindi", "https://rss.dw.com/rdf/rss-hi-all", "hi", ("B", 2)),
    ("DW Kiswahili", "https://rss.dw.com/rdf/rss-sw-all", "sw", ("B", 2)),
    ("DW Ukrainian", "https://rss.dw.com/rdf/rss-uk-all", "uk", ("B", 2)),
    ("DW Polish", "https://rss.dw.com/rdf/rss-pl-all", "pl", ("B", 2)),
    ("RFE/RL English", "https://www.rferl.org/api/", "en", ("B", 2)),
    ("RFE/RL Svoboda (Russian)", "https://www.svoboda.org/api/", "ru", ("B", 2)),
    ("RFE/RL Ukraine", "https://www.radiosvoboda.org/api/", "uk", ("B", 2)),
    ("RFE/RL Belarus", "https://www.svaboda.org/api/", "be", ("B", 2)),
    ("Radio Farda (Persian)", "https://www.radiofarda.com/api/", "fa", ("B", 2)),
    ("RFE/RL Azadi (Dari/Pashto)", "https://da.azadiradio.com/api/", "fa", ("B", 2)),
    ("VOA Farsi", "https://ir.voanews.com/api/", "fa", ("B", 2)),
    ("VOA Mandarin", "https://www.voachinese.com/api/", "zh", ("B", 2)),
    ("VOA Russian", "https://www.golosameriki.com/api/", "ru", ("B", 2)),
    ("VOA Spanish", "https://www.vozdeamerica.com/api/", "es", ("B", 2)),
    ("VOA Cantonese", "https://www.voacantonese.com/api/", "zh", ("B", 2)),
    ("VOA Vietnamese", "https://www.voatiengviet.com/api/", "vi", ("B", 2)),
    ("VOA Urdu", "https://www.urduvoa.com/api/", "ur", ("B", 2)),
    ("VOA Burmese", "https://burmese.voanews.com/api/", "my", ("B", 2)),
    ("VOA Swahili", "https://www.voaswahili.com/api/", "sw", ("B", 2)),
    ("VOA Indonesian", "https://www.voaindonesia.com/api/", "id", ("B", 2)),
    ("VOA Korean", "https://www.voakorea.com/api/", "ko", ("B", 2)),
    ("France 24 Arabic", "https://www.france24.com/ar/rss", "ar", ("B", 2)),
    ("France 24 Spanish", "https://www.france24.com/es/rss", "es", ("B", 2)),
    ("France 24 French", "https://www.france24.com/fr/rss", "fr", ("B", 2)),
    ("Al Jazeera Arabic", "https://www.aljazeera.net/xml/rss/all.xml", "ar", ("B", 2)),
    ("NHK World Japan", "https://www3.nhk.or.jp/nhkworld/en/news/rss/", "en", ("B", 2)),
    ("NHK News (Japanese)", "https://www3.nhk.or.jp/news/rss/news/rss.xml", "ja", ("B", 2)),
    ("CGTN (Français)", "https://french.cgtn.com/rss", "fr", ("C", 3)),
    ("CGTN (Español)", "https://espanol.cgtn.com/rss", "es", ("C", 3)),
    ("CGTN (الـصينية)", "https://arabic.cgtn.com/rss", "ar", ("C", 3)),
    ("EFE (Spanish)", "https://efe.com/feed/", "es", ("B", 2)),
    ("Kyodo News (English)", "https://english.kyodonews.net/rss/news.xml", "en", ("B", 2)),
    ("Le Monde (French)", "https://www.lemonde.fr/rss/une.xml", "fr", ("B", 2)),
    ("Le Figaro (French)", "https://www.lefigaro.fr/rss/figaro_actualites.xml", "fr", ("B", 2)),
    ("Libération (French)", "https://www.liberation.fr/rss/", "fr", ("B", 2)),
    ("RFI Afrique", "https://www.rfi.fr/fr/afrique/rss", "fr", ("B", 2)),
    ("FAZ (German)", "https://www.faz.net/rss/aktuell/", "de", ("B", 2)),
    ("SZ (German)", "https://rss.sueddeutsche.de/rss/Topthemen", "de", ("B", 2)),
    ("Der Spiegel (German)", "https://www.spiegel.de/schlagzeilen/index.rss", "de", ("B", 2)),
    ("NZZ (German)", "https://www.nzz.ch/recent.rss", "de", ("B", 2)),
    ("Die Zeit (German)", "https://newsfeed.zeit.de/index", "de", ("B", 2)),
    ("Xinhua (Chinese)", "http://www.xinhuanet.com/politics/xhll.xml", "zh", ("C", 3)),
    ("Caixin (Chinese)", "https://rss.caixin.com/caixin.xml", "zh", ("B", 2)),
    ("BBC Zhongwen (Trad)", "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml", "zh", ("B", 2)),
    ("Nikkei (Japanese)", "https://www.nikkei.com/rss/index.do", "ja", ("B", 2)),
    ("Asahi Shimbun", "https://www.asahi.com/rss/asahi/newsheadlines.rdf", "ja", ("B", 2)),
    ("Yomiuri Shimbun", "https://www.yomiuri.co.jp/rss/", "ja", ("B", 2)),
    ("Mainichi Shimbun", "https://mainichi.jp/rss/etc/mainichi-flash.rss", "ja", ("B", 2)),
    ("Yonhap (English)", "https://en.yna.co.kr/RSS/news.xml", "en", ("B", 2)),
    ("Yonhap (Korean)", "https://www.yna.co.kr/RSS/news.xml", "ko", ("B", 2)),
    ("Chosun Ilbo", "https://www.chosun.com/arc/outboundfeeds/rss/", "ko", ("B", 2)),
    ("KBS News", "https://news.kbs.co.kr/rss/rss.jsp?ch=ko", "ko", ("B", 2)),
    ("Al Arabiya (Arabic)", "https://www.alarabiya.net/.mrss/ar.xml", "ar", ("B", 2)),
    ("Asharq Al-Awsat", "https://aawsat.com/feed", "ar", ("B", 2)),
    ("El Khabar (Algeria)", "https://www.elkhabar.com/rss/", "ar", ("B", 2)),
    ("Hespress (Morocco)", "https://www.hespress.com/feed", "ar", ("B", 2)),
    ("Al-Masry Al-Youm", "https://www.almasryalyoum.com/rss/RssFeeds.aspx", "ar", ("B", 2)),
    ("An-Nahar (Lebanon)", "https://www.annahar.com/rss", "ar", ("B", 2)),

    ("Meduza (Russian)", "https://meduza.io/rss/all", "ru", ("B", 2)),
    ("RBC (Russian)", "https://static.rbc.ru/rbc/internal/rss.rbc.ru/rbc.ru/mainnews.rss", "ru", ("B", 2)),
    ("TASS (Russian)", "https://tass.ru/rss/v2.xml", "ru", ("C", 3)),
    ("Novaya Gazeta Europe", "https://novayagazeta.eu/rss/all", "ru", ("B", 2)),
    ("Vedomosti (Russian)", "https://www.vedomosti.ru/rss/news", "ru", ("B", 2)),
    ("El País (Spanish)", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "es", ("B", 2)),
    ("El Mundo (Spanish)", "https://www.elmundo.es/rss/portada.xml", "es", ("B", 2)),
    ("La Vanguardia (Spanish)", "https://www.lavanguardia.com/rss/home.xml", "es", ("B", 2)),
    ("Clarín (Argentina)", "https://www.clarin.com/rss/lo-ultimo/", "es", ("B", 2)),
    ("Infobae (Spanish)", "https://www.infobae.com/arc/outboundfeeds/rss/", "es", ("B", 2)),
    ("El Universal (Mexico)", "https://www.eluniversal.com.mx/rss.xml", "es", ("B", 2)),

    ("El Tiempo (Colombia)", "https://www.eltiempo.com/rss/colombia.xml", "es", ("B", 2)),
    ("Folha de S.Paulo (PT)", "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml", "pt", ("B", 2)),
    ("O Globo (PT)", "https://oglobo.globo.com/rss/ultimas/", "pt", ("B", 2)),
    ("Estadão (PT)", "https://www.estadao.com.br/rss/", "pt", ("B", 2)),
    ("Público (PT)", "https://www.publico.pt/rss", "pt", ("B", 2)),
    ("Jornal de Negócios (PT)", "https://www.jornaldenegocios.pt/rss", "pt", ("B", 2)),
    ("Corriere della Sera (IT)", "https://xml2.corriereobjects.it/rss/homepage.xml", "it", ("B", 2)),
    ("La Repubblica (IT)", "https://www.repubblica.it/rss/homepage/rss2.0.xml", "it", ("B", 2)),
    ("ANSA (IT)", "https://www.ansa.it/sito/ansait_rss.xml", "it", ("B", 2)),
    ("Il Sole 24 Ore (IT)", "https://www.ilsole24ore.com/rss/", "it", ("B", 2)),
    ("Hürriyet (TR)", "https://www.hurriyet.com.tr/rss/anasayfa", "tr", ("B", 2)),
    ("Cumhuriyet (TR)", "https://www.cumhuriyet.com.tr/rss/son_dakika.xml", "tr", ("B", 2)),
    ("Anadolu Agency", "https://www.aa.com.tr/en/rss/default?cat=live", "en", ("B", 2)),
    ("Daily Sabah", "https://www.dailysabah.com/rssFeed/wholeSite", "en", ("B", 2)),
    ("BBC Persian", "https://feeds.bbci.co.uk/persian/rss.xml", "fa", ("B", 2)),

    ("Mehr News (Persian)", "https://www.mehrnews.com/rss", "fa", ("C", 3)),
    ("IRNA (English)", "https://en.irna.ir/rss", "en", ("C", 3)),
    ("Tasnim News", "https://www.tasnimnews.com/en/rss/feed/0/8/0", "en", ("C", 3)),
    ("Haaretz (Hebrew)", "https://www.haaretz.co.il/cmlink/1.1572080", "he", ("B", 2)),
    ("Ynet (Hebrew)", "https://www.ynet.co.il/Integration/StoryRss2.xml", "he", ("B", 2)),
    ("Globes (Hebrew)", "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederRSS", "he", ("B", 2)),
    ("Times of Israel", "https://www.timesofisrael.com/feed/", "en", ("B", 2)),
    # Gazeta Wyborcza (PL): no working RSS feed — removed
    ("Rzeczpospolita (PL)", "https://www.rp.pl/rss/", "pl", ("B", 2)),
    ("Onet (PL)", "https://wiadomosci.onet.pl/rss.xml", "pl", ("B", 2)),
    ("PAP (Polish wire)", "https://www.pap.pl/rss.xml", "pl", ("B", 2)),
    ("Ukrainska Pravda", "https://www.pravda.com.ua/rss/", "uk", ("B", 2)),
    ("Hromadske (Ukrainian)", "https://hromadske.ua/rss.xml", "uk", ("B", 2)),
    ("Kyiv Independent", "https://kyivindependent.com/feed/", "en", ("B", 2)),
    ("NV (Ukrainian)", "https://nv.ua/rss/all.xml", "uk", ("B", 2)),
    ("NDTV India (Hindi)", "https://ndtv.in/rss/feeds", "hi", ("B", 2)),
    ("Dainik Jagran (Hindi)", "https://www.jagran.com/rss/news.xml", "hi", ("B", 2)),
    ("Dainik Bhaskar (Hindi)", "https://www.bhaskar.com/rss/", "hi", ("B", 2)),
    ("The Hindu (Tamil)", "https://tamil.thehindu.com/feeder/default.rss", "ta", ("B", 2)),
    ("Dawn (Urdu)", "https://www.dawnnews.tv/rss/", "ur", ("B", 2)),
    ("Kompas (Indonesian)", "https://www.kompas.com/rss/", "id", ("B", 2)),
    ("Detik (Indonesian)", "https://www.detik.com/rss/", "id", ("B", 2)),
    ("VnExpress (Vietnamese)", "https://vnexpress.net/rss/tin-moi-nhat.rss", "vi", ("B", 2)),
    ("Tuoi Tre (Vietnamese)", "https://tuoitre.vn/rss/tin-moi-nhat.rss", "vi", ("B", 2)),
    ("Bangkok Post (Thai)", "https://www.bangkokpost.com/rss/data/topstories.xml", "en", ("B", 2)),

        # ── Priority add: state broadcaster suite + missing regional pillars ──
    ("Rossiyskaya Gazeta (RU state)", "https://rg.ru/xml/index.xml", "en", ("C", 3)),
    ("Fars News (English)", "https://www.farsnews.ir/en/rss", "en", ("C", 3)),
    ("People's Daily (English)", "http://en.people.cn/rss/politics.xml", "en", ("C", 3)),
    ("OSW Warsaw (Polish)", "https://www.osw.waw.pl/pl/rss", "en", ("C", 3)),
    ("Tempo (Indonesian)", "https://www.tempo.co/rss/", "en", ("C", 3)),
    ("TRT World (Turkish state)", "https://www.trtworld.com/rss", "en", ("C", 3)),
]

# Thematic cross-cutting feeds — added 2026-05-31 per collection audit
# These fill gaps in the regional coverage model with topic-specific sources.
# Tuple: (name, url, language_code, admiralty_rank)
THEMATIC_FEEDS = [
    # Arctic / Northern Sea Route
    ("The Arctic Institute", "https://www.thearcticinstitute.org/feed/", "en", ("B", 2)),
    ("High North News", "https://www.highnorthnews.com/rss.xml", "en", ("B", 2)),

    # Space / Satellite
    ("SpaceNews", "https://spacenews.com/feed/", "en", ("B", 2)),
    ("SpaceWatch.Global", "https://spacewatch.global/feed/", "en", ("B", 2)),

    # Cyber Threat Intelligence
    ("The Record by Recorded Future", "https://therecord.media/feed/", "en", ("B", 2)),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/", "en", ("B", 2)),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/", "en", ("B", 2)),

    # Supply Chain / Trade
    ("Supply Chain Dive", "https://www.supplychaindive.com/feeds/news/", "en", ("B", 2)),
    ("The Loadstar", "https://theloadstar.com/feed/", "en", ("B", 2)),

    # Bio/Health Security
    ("CIDRAP (UMN)", "https://www.cidrap.umn.edu/rss.xml", "en", ("B", 2)),
    ("GISAID Updates", "https://gisaid.org/feed/", "en", ("B", 2)),

    # Disinformation / Information Warfare
    ("EU DisinfoLab", "https://www.disinfo.eu/feed/", "en", ("B", 2)),
    ("DFRLab", "https://medium.com/feed/dfrlab", "en", ("B", 2)),
]
# Gmail intel digest — newsletters from Cipher Brief, Foreign Policy, etc.
NEWS_RAW_PATH = pathlib.Path("/home/ubuntu/.openclaw/workspace/tasks/news_raw.md")

DEFAULT_ADMIRALTY = ("B", 2)  # major wires default; downgrade for state media

USER_AGENT = "TrevorDailyBrief/1.0 (+https://github.com/trevormentis-spec/OpenClawTrevorMentis)"

CATALOG_PATH = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "analyst" / "meta" / "sources_tested.json"

def log(msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[collect {ts}] {msg}", file=sys.stderr, flush=True)

def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())

def load_catalog_feeds(catalog_path: pathlib.Path | None = None,
                       max_per_region: int = 6,
                       run_count: int = 1) -> list[tuple[str, str, str, str, str]]:
    """Load working feeds from sources_tested.json catalog.

    Returns list of (name, url, admiralty_source, admiralty_info, region) tuples.
    Applies per-region rotation so collection doesn't blow up with 300+ feeds.
    """
    path = catalog_path or CATALOG_PATH
    if not path.exists():
        log(f"catalog not found: {path}")
        return []
    try:
        catalog = json.loads(path.read_text())
    except Exception as exc:
        log(f"catalog load failed: {exc}")
        return []

    # Handle both dict {sources: [...]} and flat list [...] formats
    source_list: list[dict]
    if isinstance(catalog, dict):
        source_list = catalog.get("sources", [])
    elif isinstance(catalog, list):
        source_list = catalog
    else:
        source_list = []

    # Group working feeds by region
    working: dict[str, list[dict]] = {}
    for s in source_list:
        if s.get("status") not in ("working", "ok"):
            continue
        # Handle both 'rss' and 'url' field names
        feed_url = s.get("rss", s.get("feed_url", s.get("url", ""))).strip()
        if not feed_url or not feed_url.startswith("http"):
            continue
        region = s.get("region", s.get("source_region", "global"))
        working.setdefault(region, []).append(s)

    # Rotate: pick up to max_per_region feeds per region
    selected: list[tuple[str, str, str, str, str]] = []
    dead_cache = load_dead_feeds()
    dead_skipped = 0
    for region, feeds in sorted(working.items()):
        feeds_sorted = sorted(feeds, key=lambda s: s.get("name", ""))
        # Filter out known-dead feeds — handle both 'rss' and 'url' field names
        def _get_feed_url(s):
            return s.get("rss", s.get("feed_url", s.get("url", "")))
        live_feeds = [s for s in feeds_sorted if not is_dead(_get_feed_url(s), dead_cache)]
        dead_skipped += len(feeds_sorted) - len(live_feeds)
        offset = (run_count * max_per_region) % max(1, len(live_feeds)) if live_feeds else 0
        rotated = live_feeds[offset:] + live_feeds[:offset]
        picked = rotated[:max_per_region]
        for s in picked:
            selected.append((
                s["name"],
                s.get("rss", s.get("feed_url", s.get("url", ""))),
                s.get("admiralty_source", "C"),
                s.get("admiralty_info", "3"),
                region,
            ))

    if dead_skipped:
        log(f"catalog feeds: {len(selected)} selected from {sum(len(v) for v in working.values())} working ({dead_skipped} dead-skipped) across {len(working)} regions")
    else:
        log(f"catalog feeds: {len(selected)} selected from {sum(len(v) for v in working.values())} working across {len(working)} regions")
    return selected

def country_to_region(country: str, regions: dict) -> str | None:
    if not country:
        return None
    overrides = regions.get("country_to_region_overrides", {}) or {}
    if country in overrides:
        return overrides[country]
    for snake, payload in regions["regions"].items():
        if country in (payload.get("countries") or []):
            return snake
    return None

# ── Dead-feed cache ──────────────────────────────────────────────
# Avoids wasting 30s+ on feeds that consistently fail.
# Skips feeds with ≥3 consecutive failures, retests after 48h.
import atexit as _atexit

DEAD_FEED_PATH = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "brain" / "memory" / "semantic" / "dead-feeds.json"
DEAD_FEED_THRESHOLD = 3      # consecutive failures before we skip
DEAD_FEED_RETEST_HOURS = 48  # retest after this many hours
FETCH_TIMEOUT = 8            # seconds (down from 15 — dead feeds waste too much time)
FETCH_RETRIES = 1            # one retry max

_dead_cache_dirty = False
_dead_cache: dict[str, dict] = {}

def _save_on_exit():
    """atexit handler — ensures dead-feed cache is persisted even on crash."""
    global _dead_cache_dirty, _dead_cache
    if _dead_cache_dirty and _dead_cache:
        try:
            DEAD_FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEAD_FEED_PATH.write_text(json.dumps(_dead_cache, indent=2))
        except Exception:
            pass  # last-ditch save — can't log during interpreter shutdown

_atexit.register(_save_on_exit)

def load_dead_feeds() -> dict[str, dict]:
    """Load the dead-feed cache. Returns {url: {failures, last_failed_at}}."""
    try:
        if DEAD_FEED_PATH.exists():
            return json.loads(DEAD_FEED_PATH.read_text())
    except Exception:
        pass
    return {}

def save_dead_feeds(cache: dict[str, dict]) -> None:
    """Persist the dead-feed cache."""
    DEAD_FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEAD_FEED_PATH.write_text(json.dumps(cache, indent=2))

def is_dead(url: str, cache: dict[str, dict]) -> bool:
    """Check if a URL should be skipped based on cache."""
    entry = cache.get(url)
    if not entry:
        return False
    failures = entry.get("failures", 0)
    if failures < DEAD_FEED_THRESHOLD:
        return False
    last_failed = entry.get("last_failed_at", "")
    if last_failed:
        try:
            failed_dt = dt.datetime.fromisoformat(last_failed)
            age_hours = (dt.datetime.now(dt.timezone.utc) - failed_dt).total_seconds() / 3600
            if age_hours > DEAD_FEED_RETEST_HOURS:
                return False  # expired — retest
        except Exception:
            pass
    return True

def record_feed_failure(url: str, cache: dict[str, dict]) -> None:
    """Record a fetch failure in the dead-feed cache."""
    global _dead_cache_dirty
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = cache.get(url, {"failures": 0, "last_failed_at": now})
    entry["failures"] = entry.get("failures", 0) + 1
    entry["last_failed_at"] = now
    cache[url] = entry
    _dead_cache_dirty = True

def record_feed_success(url: str, cache: dict[str, dict]) -> None:
    """Reset failure count on successful fetch."""
    global _dead_cache_dirty
    if url in cache:
        del cache[url]
        _dead_cache_dirty = True
# ── end dead-feed cache ─────────────────────────────────────────

def fetch(url: str, timeout: int = FETCH_TIMEOUT, max_retries: int = FETCH_RETRIES) -> str | None:
    """Fetch a URL with retry. Short timeout — dead feeds waste pipeline time."""
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            t = timeout * (attempt + 1)  # 8s first, 16s retry
            with urllib.request.urlopen(req, timeout=t) as resp:
                data = resp.read()
                try:
                    return data.decode("utf-8", errors="replace")
                except Exception:
                    return None
        except Exception as exc:
            if attempt < max_retries:
                log(f"fetch attempt {attempt+1} failed for {url}: {exc}, retrying...")
            else:
                log(f"fetch failed for {url}: {exc}")
    return None

def parse_rss(xml_text: str, source_name: str, default_admiralty=DEFAULT_ADMIRALTY) -> list[dict]:
    """Very tolerant RSS/Atom parser. Returns a list of normalized items."""
    items: list[dict] = []
    if not xml_text:
        return items
    try:
        # Some feeds embed un-escaped XML; ElementTree is strict — try a
        # forgiving cleanup first.
        cleaned = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", xml_text)
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        log(f"RSS parse error for {source_name}: {exc}")
        return items

    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        items.append({
            "title": title, "link": link, "summary": desc, "pub": pub,
            "source": source_name, "admiralty": default_admiralty,
        })

    # Atom
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        link = (link_el.get("href") if link_el is not None else "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        pub = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        if not title:
            continue
        items.append({
            "title": title, "link": link, "summary": summary, "pub": pub,
            "source": source_name, "admiralty": default_admiralty,
        })

    return items

COUNTRY_REGEX_CACHE: dict[str, re.Pattern] = {}

def detect_country(text: str, regions: dict) -> str | None:
    """Cheap country detection: longest matching country name in text."""
    if not text:
        return None
    text_l = text.lower()
    candidates: list[str] = []
    for region in regions["regions"].values():
        for c in region.get("countries", []):
            if not c:
                continue
            if c not in COUNTRY_REGEX_CACHE:
                COUNTRY_REGEX_CACHE[c] = re.compile(rf"\b{re.escape(c.lower())}\b")
            if COUNTRY_REGEX_CACHE[c].search(text_l):
                candidates.append(c)
    if not candidates:
        return None
    candidates.sort(key=len, reverse=True)
    return candidates[0]

def parse_pubdate(pub: str) -> str | None:
    if not pub:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            d = dt.datetime.strptime(pub, fmt)
            return d.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    return None

SECURITY_KEYWORDS = re.compile(
    r"\b(strike|attack|killed|wounded|missile|drone|sanction|coup|protest|"
    r"clashes|operation|raid|airstrike|shelling|siege|treaty|election|"
    r"summit|withdrawal|sovereign|default|downgrade|hijack|hostage|cyber|"
    r"ransomware|phishing|breach|cartel|trafficking|seize)\b",
    re.IGNORECASE,
)

def is_security_relevant(item: dict) -> bool:
    text = f"{item.get('title','')} {item.get('summary','')}"
    return bool(SECURITY_KEYWORDS.search(text))

def categorise(item: dict) -> str:
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    if any(k in text for k in ("strike", "missile", "shelling", "airstrike", "raid", "clashes", "casualt")):
        return "kinetic"
    if any(k in text for k in ("cyber", "ransomware", "phishing", "breach", "hack")):
        return "cyber"
    if any(k in text for k in ("vessel", "tanker", "ais", "ukmto", "maritime", "hijack")):
        return "maritime"
    if any(k in text for k in ("flight", "aircraft", "airspace", "ads-b", "no-fly")):
        return "aviation"
    if any(k in text for k in ("aid", "famine", "refugee", "humanitarian", "displaced")):
        return "humanitarian"
    if any(k in text for k in ("inflation", "rate", "fx", "yield", "default", "downgrade", "central bank", "imf")):
        return "economic"
    return "political"

def make_id(occurred: str, country: str, headline: str) -> str:
    h = hashlib.md5(f"{occurred}|{country}|{headline}".encode()).hexdigest()[:4]
    return f"i-{occurred[:10]}-{h}"

def parse_news_raw(path: pathlib.Path) -> list[dict]:
    """Parse news_raw.md into collector-compatible items.

    Handles two formats:
      1. Global News items (### Headline → Source/Summary/Link)
      2. Gmail intel digest (## Newsletter → key development bullets)
    """
    items: list[dict] = []
    if not path.exists():
        return items

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Format 1: ### Headline block
        if line.startswith("### ") and not line.startswith("#### "):
            headline = line[4:].strip()
            source = ""
            summary = ""
            link = ""
            j = i + 1
            while j < len(lines) and j < i + 10:
                s = lines[j].strip()
                if s.startswith("- **Source:**"):
                    source = s.split("**Source:**", 1)[-1].strip()
                elif s.startswith("- **Summary:**"):
                    summary = s.split("**Summary:**", 1)[-1].strip()
                elif s.startswith("- **Link:**"):
                    link = s.split("**Link:**", 1)[-1].strip()
                elif s.startswith("### ") or s.startswith("## "):
                    break
                j += 1
            if source:
                items.append({
                    "title": headline, "link": link,
                    "summary": summary, "pub": "",
                    "source": source.strip(),
                    "admiralty": ("B", 2),
                    "_bypass_filter": True,
                })
            i = j
            continue

        # Format 2: ## Newsletter section
        if line.startswith("## ") and "\u2014" in line:
            section_title = line[3:].strip()
            bullet_source = section_title.split("\u2014")[0].strip()
            j = i + 1
            bullets = []
            while j < len(lines):
                s = lines[j]
                if s.startswith("## ") and s != line:
                    break
                stripped = s.strip()
                if stripped.startswith("- ") and len(stripped) > 20:
                    if not any(stripped.startswith(x) for x in [
                        "- **Source:**", "- **Date:**", "- **Mentions:**"
                    ]):
                        bullets.append(stripped[2:].strip())
                j += 1
            for b in bullets:
                items.append({
                    "title": f"[Intel] {b[:120]}", "link": "",
                    "summary": f"{b} (via {section_title})",
                    "pub": "",
                    "source": bullet_source,
                    "admiralty": ("C", 2),
                    "_bypass_filter": True,
                })
            i = j
            continue

        i += 1

    log(f"news_raw: {len(items)} items ({len([x for x in items if x['admiralty'][0]=='B'])} global + {len([x for x in items if x['admiralty'][0]=='C'])} intel)")
    return items

def collect_live(regions: dict, sources: dict,
                  feeds_to_try: list[tuple[str, str]] | None = None,
                  dead_cache: dict[str, dict] | None = None
                  ) -> tuple[list[dict], list[str], dict[str, dict]]:
    raw: list[dict] = []
    gaps: list[str] = []
    if dead_cache is None:
        dead_cache = load_dead_feeds()
    dead_before = {u for u in dead_cache if is_dead(u, dead_cache)}
    durable = sources.get("durable_sources", []) or []
    if feeds_to_try is None:
        feeds_to_try = WIRE_FEEDS[:]
    # Durable sources without explicit feed URLs are skipped programmatically;
    # the collector subagent prompt explains how to do better with web_fetch
    # when a richer harness is available.
    skipped_dead = 0
    for fname, furl in feeds_to_try:
        # Skip known-dead feeds (saves 8-16s per dead feed)
        if is_dead(furl, dead_cache):
            skipped_dead += 1
            continue
        log(f"fetching {fname}")
        body = fetch(furl)
        if not body:
            gaps.append(f"feed unreachable: {fname}")
            record_feed_failure(furl, dead_cache)
            continue
        record_feed_success(furl, dead_cache)
        raw.extend(parse_rss(body, fname))
    if skipped_dead:
        log(f"skipped {skipped_dead} known-dead feeds (cache)")
    raw.extend(parse_news_raw(NEWS_RAW_PATH))
    log(f"raw items: {len(raw)}")
    return raw, gaps, dead_cache

def normalise(items: list[dict], regions: dict, window_hours: int = 24) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=window_hours)
    out: list[dict] = []
    for it in items:
        if not is_security_relevant(it) and not it.get("_bypass_filter"):
            continue
        country = detect_country(f"{it.get('title','')} {it.get('summary','')}", regions)
        region = country_to_region(country or "", regions) if country else None
        # Finance-relevant items without a country fall into prediction_markets
        if not region:
            text = f"{it.get('title','')} {it.get('summary','')}".lower()
            if any(k in text for k in ("inflation", "rate", "yield", "default", "downgrade", "central bank", "fx", "oil", "brent")):
                region = "prediction_markets"
        if not region:
            continue
        occurred = parse_pubdate(it.get("pub", "")) or now.isoformat().replace("+00:00", "Z")
        try:
            occ_dt = dt.datetime.fromisoformat(occurred.replace("Z", "+00:00"))
        except ValueError:
            occ_dt = now
        if occ_dt < cutoff:
            continue
        rel, cred = it["admiralty"]
        out.append({
            "id": make_id(occurred, country or region, it["title"]),
            "region": region,
            "country": country,
            "lat": None, "lon": None,
            "occurred_at_utc": occurred,
            "actors": [],
            "category": categorise(it),
            "headline": it["title"],
            "summary": (it.get("summary") or "")[:600],
            "url": it.get("link", ""),
            "sources": [{
                "name": it["source"],
                "url": it.get("link"),
                "admiralty_reliability": rel,
                "admiralty_credibility": cred,
                "retrieved_at_utc": now.isoformat().replace("+00:00", "Z"),
            }],
            "single_source": True,
            "confidence_collector": "medium",
        })
    return out

def deduplicate(items: list[dict]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for it in items:
        key = (it["region"], it.get("country"),
               it["headline"][:60].lower())
        if key not in by_key:
            by_key[key] = it
            continue
        existing = by_key[key]
        if it["sources"][0] not in existing["sources"]:
            existing["sources"].extend(it["sources"])
            existing["single_source"] = False
    return list(by_key.values())

def cap_per_region(items: list[dict], cap: int = 8) -> list[dict]:
    items.sort(key=lambda x: x["occurred_at_utc"], reverse=True)
    out: list[dict] = []
    counts: dict[str, int] = {}
    for it in items:
        c = counts.get(it["region"], 0)
        if c >= cap:
            continue
        counts[it["region"]] = c + 1
        out.append(it)
    return out

def mock_incidents(regions: dict) -> list[dict]:
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    base = [
        ("europe", "Ukraine", 50.45, 30.52, "kinetic",
         "Drone strikes reported in Kyiv overnight"),
        ("europe", "United Kingdom", 51.50, -0.12, "political",
         "Government tables Russia sanctions extension bill"),
        ("central_asia", "Taiwan", 25.03, 121.56, "political",
         "Three PLA naval vessels enter ADIZ near Taipei"),
        ("central_asia", "Japan", 35.68, 139.69, "economic",
         "BOJ policy statement leaves rates unchanged"),
        ("middle_east", "Lebanon", 33.85, 35.50, "kinetic",
         "Reported IDF strike on Hezbollah depot in southern Beirut"),
        ("middle_east", "Iran", 35.69, 51.42, "political",
         "IRGC announces naval exercise in Strait of Hormuz"),
        ("north_america", "Mexico", 32.51, -117.04, "kinetic",
         "Cartel clash in Tijuana leaves multiple dead"),
        ("north_america", "United States", 38.90, -77.04, "political",
         "Senate vote scheduled on Israel security supplemental"),
        ("central_america_caribbean", "Haiti", 18.59, -72.31, "humanitarian",
         "UN reports gang displacement in Port-au-Prince"),
        ("south_america", "Venezuela", 10.49, -66.88, "political",
         "Opposition rally banned ahead of regional election"),
        ("prediction_markets", None, None, None, "economic",
         "Brent crude up 3.2% on Hormuz exercise headlines"),
        ("prediction_markets", None, None, None, "economic",
         "10-year UST yield +12bp on hot CPI print"),
    ]
    out = []
    for i, (region, country, lat, lon, cat, headline) in enumerate(base):
        out.append({
            "id": f"i-mock-{i:04d}",
            "region": region, "country": country,
            "lat": lat, "lon": lon,
            "occurred_at_utc": now,
            "actors": [],
            "category": cat,
            "headline": headline,
            "summary": headline + " (mock data for dry-run; not from live wires).",
            "sources": [{
                "name": "Mock Wire",
                "url": "https://example.invalid/mock",
                "admiralty_reliability": "B",
                "admiralty_credibility": 2,
                "retrieved_at_utc": now,
            }],
            "single_source": True,
            "confidence_collector": "high",
        })
    return out

def main() -> int:
    # Load .env for BRAVE_API_KEY and other secrets
    _env = pathlib.Path("/home/ubuntu/.openclaw/workspace/.env")
    if _env.exists():
        for _line in _env.read_text().splitlines():
            if _line.startswith("BRAVE_API_KEY="):
                os.environ.setdefault("BRAVE_API_KEY", _line.split("=", 1)[1].strip())
                break

    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--regions", required=True)
    parser.add_argument("--sources", required=True, action="append",
                        help="path to sources JSON (may be specified multiple times to merge)")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--cap-per-region", type=int, default=8,
                        help="uniform cap override (if no adaptive state provided)")
    parser.add_argument("--adaptive-caps", default="",
                        help="path to collection state JSON with adaptive per-region caps")
    parser.add_argument("--feed-priorities", default="",
                        help="path to feed priorities JSON from collection_state.py --feed-priorities")
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    raw_dir = wd / "raw"; raw_dir.mkdir(parents=True, exist_ok=True)
    regions = load_json(pathlib.Path(args.regions))

    # Merge multiple --sources files (global + Mexico-specific sources)
    source_paths = args.sources if isinstance(args.sources, list) else [args.sources]
    merged = {"durable_sources": [], "wire_sources": []}
    for sp in source_paths:
        try:
            data = json.loads(pathlib.Path(sp).read_text())
            for key in ("durable_sources", "wire_sources"):
                merged.setdefault(key, []).extend(data.get(key, []))
            log(f"loaded sources from {sp}: {len(data.get('durable_sources',[]))} durable, {len(data.get('wire_sources',[]))} wire")
        except Exception as exc:
            log(f"failed to load sources from {sp}: {exc}")
    sources = merged
    log(f"merged sources: {len(sources['durable_sources'])} durable total")

    # Adaptive caps: load per-region caps from collection state if available
    caps = {r: args.cap_per_region for r in ["europe", "north_america", "central_america_caribbean",
              "south_america", "africa", "middle_east", "central_asia",
              "south_east_asia", "east_asia", "south_asia", "oceania", "prediction_markets"]}
    if args.adaptive_caps and os.path.exists(args.adaptive_caps):
        try:
            state_data = json.loads(pathlib.Path(args.adaptive_caps).read_text())
            adaptive = state_data.get("per_region_cap", {})
            if isinstance(adaptive, dict):
                for r in caps:
                    if r in adaptive:
                        caps[r] = max(3, min(20, int(adaptive[r])))
            log(f"adaptive caps loaded: {caps}")
        except Exception as exc:
            log(f"adaptive caps failed to load ({exc}), using uniform cap={args.cap_per_region}")

    # Feed priority filtering — skip TIER-3, alternate TIER-2
    feeds_to_try = WIRE_FEEDS[:]
    skipped_feeds = []
    if args.feed_priorities and os.path.exists(args.feed_priorities):
        try:
            priority_data = json.loads(pathlib.Path(args.feed_priorities).read_text())
            feed_priorities = priority_data.get("feed_priorities", {})
            run_count = priority_data.get("run_count", 1)
            filtered = []
            for fname, furl in WIRE_FEEDS:
                pri = feed_priorities.get(fname, {})
                tier = pri.get("tier", 1)
                if tier >= 3:
                    skipped_feeds.append(fname)
                    log(f"  ⏭ skip {fname}: tier-3 (quality={pri.get('quality_score',0):.2f}, {pri.get('consecutive_zero',0)} zero-citation runs)")
                    continue
                elif tier == 2:
                    if run_count % 2 == 0:
                        skipped_feeds.append(fname)
                        log(f"  ⏭ skip {fname}: tier-2 (alternating even run)")
                        continue
                    else:
                        log(f"  ✓ fetch {fname}: tier-2 (odd run)")
                else:
                    log(f"  ✓ fetch {fname}: tier-1 (high priority)")
                filtered.append((fname, furl))
            feeds_to_try = filtered
            log(f"feed priorities: {len(filtered)} active of {len(WIRE_FEEDS)} total")
            if skipped_feeds:
                log(f"skipped: {', '.join(skipped_feeds)}")
        except Exception as exc:
            log(f"feed priorities failed to load ({exc}), fetching all feeds")

    # Add local-language feeds (non-English) — always fetch to fill linguistic gap
    # These use tuple format (name, url, language, admiralty) — extra fields ignored by collect_live
    local_feeds = [(f[0], f[1]) for f in LOCAL_LANGUAGE_FEEDS]
    feeds_to_try = feeds_to_try + local_feeds

    # Add thematic cross-cutting feeds (topic-specific sources covering Arctic, Space, Cyber, Supply Chain, Bio, Disinfo)
    thematic_feeds = [(f[0], f[1]) for f in THEMATIC_FEEDS]
    feeds_to_try = feeds_to_try + thematic_feeds

    # --- Dynamic catalog feeds (sources_tested.json) ---
    # Load working feeds from the heartbeat-maintained catalog.
    # Rotation keeps per-region count manageable; dedup avoids double-fetching
    # feeds already in WIRE_FEEDS or LOCAL_LANGUAGE_FEEDS.
    existing_urls = {url for _, url in feeds_to_try}
    _run_count = 1
    if args.feed_priorities and os.path.exists(args.feed_priorities):
        try:
            _pd = json.loads(pathlib.Path(args.feed_priorities).read_text())
            _run_count = _pd.get("run_count", 1)
        except Exception:
            pass
    catalog_feeds_raw = load_catalog_feeds(
        catalog_path=CATALOG_PATH,
        max_per_region=6,
        run_count=_run_count,
    )
    catalog_added = 0
    for name, url, _adm_src, _adm_info, _region in catalog_feeds_raw:
        if url in existing_urls:
            continue
        existing_urls.add(url)
        feeds_to_try.append((name, url))
        catalog_added += 1
    log(f"+{catalog_added} catalog feeds (dynamic) — {len(feeds_to_try)} total feeds to fetch")
    # ---- end catalog feeds ----

    if args.mock:
        log("running in mock mode")
        incidents = mock_incidents(regions)
        gaps = ["mock mode: no live collection performed"]
    else:
        # Load dead-feed cache to skip known-bad URLs
        dead_cache = load_dead_feeds()
        dead_count = sum(1 for u in dead_cache if is_dead(u, dead_cache))
        if dead_count:
            log(f"dead-feed cache: {dead_count} feeds skipped, {len(dead_cache)} total tracked")
        raw, gaps, dead_cache = collect_live(regions, sources,
                                              feeds_to_try=feeds_to_try,
                                              dead_cache=dead_cache)
        # Persist updated cache
        try:
            save_dead_feeds(dead_cache)
            dead_after = sum(1 for u in dead_cache if is_dead(u, dead_cache))
            log(f"dead-feed cache saved: {dead_after} feeds now dead, {len(dead_cache)} total tracked")
        except Exception as exc:
            log(f"dead-feed cache save failed: {exc}")
        incidents = normalise(raw, regions)
        incidents = deduplicate(incidents)
        # Web search fallback: fill region gaps (<3 items) via Brave Search
        incidents = web_search_fallback(incidents, regions)
        # Social media collection: Brave Search primary, Sonar fallback for gap regions
        # [DISABLED] social pipeline paused — principal directive 2026-05-22
        social_results = []
        # Use adaptive per-region caps if available, else uniform cap
        if caps and any(c != args.cap_per_region for c in caps.values()):
            # Apply per-region caps
            region_counts: dict[str, int] = {}
            filtered = []
            for inc in incidents:
                region = inc["region"]
                max_for_region = caps.get(region, args.cap_per_region)
                region_counts[region] = region_counts.get(region, 0) + 1
                if region_counts[region] <= max_for_region:
                    filtered.append(inc)
            incidents = filtered
            log(f"adaptive caps: {[(r, caps[r]) for r in caps]}")
        else:
            incidents = cap_per_region(incidents, cap=args.cap_per_region)
            log(f"uniform cap_per_region={args.cap_per_region}")

    # Strip internal-only keys from output
    for inc in incidents:
        inc.pop("_bypass_filter", None)

    out = {
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "window_hours": 24,
        "regions_covered": ["europe", "north_america", "central_america_caribbean",
                            "south_america", "africa", "middle_east",
                            "central_asia", "south_east_asia", "east_asia", "south_asia",
                            "oceania",
                            "prediction_markets"],
        "incidents": incidents,
        "collection_gaps": gaps,
    }
    out_path = raw_dir / "incidents.json"
    out_path.write_text(json.dumps(out, indent=2))
    log(f"wrote {out_path} ({len(incidents)} incidents)")
    return 0

# ── Web search fallback for region gaps ───────────────────────────────

WEB_SEARCH_REGIONS = {
    "europe": ["Europe news", "Russia Ukraine war latest", "European Union politics"],
    "central_asia": ["Central Asia news", "Kazakhstan Uzbekistan Kyrgyzstan latest", "Tajikistan Turkmenistan news"],
    "middle_east": ["Middle East news", "Iran Gulf latest", "Israel Palestine news"],
    "north_america": ["North America news", "US politics latest", "Mexico Canada news"],
    "south_america": ["South America news", "Latin America news", "Venezuela Brazil latest"],
    "central_america_caribbean": ["Central America news", "Caribbean news", "Mexico security"],
    "africa": ["Africa news", "North Africa latest", "Sub-Saharan Africa security"],
    "south_east_asia": ["South East Asia news", "ASEAN latest", "Pacific security"],
    "east_asia": ["East Asia news", "China Japan South Korea latest", "Taiwan strait security", "North Korea latest"],
    "south_asia": ["South Asia news", "India Pakistan latest", "Bangladesh Sri Lanka Nepal news"],
    "oceania": ["Oceania news", "Australia Pacific latest"],
    "prediction_markets": ["Global finance markets news", "Oil prices commodities", "IMF World Bank latest"],
}

def _brave_search(query: str, brave_key: str, timeout: int = 10) -> list[dict]:
    """Search Brave Web Search API — delegates to shared utility."""
    from scripts.shared_brave import brave_search
    results = brave_search(query)
    out = []
    for r in results[:5]:
        title = r.get("title", "")
        url_out = r.get("url", "")
        age = r.get("age", "")
        if title:
            out.append({
                "title": title,
                "summary": title,
                "link": url_out,
                "source": "Brave Search",
                "pub": age,
                "admiralty": ("B", 2),
                "_bypass_filter": True,
            })
    return out

def web_search_fallback(incidents: list[dict], regions: dict) -> list[dict]:
    """Fill region gaps using Brave Search when RSS feeds return zero or near-zero items."""
    brave_key = os.environ.get("BRAVE_API_KEY", "")
    if not brave_key:
        return incidents

    # Count items per region
    region_counts: dict[str, int] = {}
    for inc in incidents:
        r = inc.get("region", "unknown")
        region_counts[r] = region_counts.get(r, 0) + 1

    # Find regions with gaps (less than 3 items)
    gap_regions = [r for r in WEB_SEARCH_REGIONS if region_counts.get(r, 0) < 3]
    if not gap_regions:
        return incidents

    log(f"Region gaps detected (fewer than 3 items): {', '.join(gap_regions)} — querying Brave Search")

    new_raw: list[dict] = []
    for region in gap_regions:
        queries = WEB_SEARCH_REGIONS[region]
        for query in queries:
            try:
                results = _brave_search(query, brave_key)
                if results:
                    log(f"  Brave Search '{query}': {len(results)} results")
                    new_raw.extend(results)
            except Exception as exc:
                log(f"  Brave Search failed for '{query}': {exc}")

    if not new_raw:
        return incidents

    # Normalise the Brave Search results into incidents
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=24)
    for item in new_raw:
        country = detect_country(f"{item.get('title','')} {item.get('summary','')}", regions)
        rg = country_to_region(country or "", regions) if country else None
        if not rg:
            # Finance fallback
            text = f"{item.get('title','')} {item.get('summary','')}".lower()
            if any(k in text for k in ("inflation", "rate", "yield", "default", "downgrade", "central bank", "fx", "oil", "brent", "market", "trade")):
                rg = "prediction_markets"
        if not rg:
            continue
        occurred = now.isoformat().replace("+00:00", "Z")
        out_item = {
            "id": make_id(occurred, country or rg, item["title"]),
            "region": rg,
            "country": country,
            "lat": None, "lon": None,
            "occurred_at_utc": occurred,
            "actors": [],
            "category": "web_search",
            "headline": item["title"],
            "summary": (item.get("summary") or "")[:600],
            "url": item.get("link", ""),
            "sources": [{
                "name": item["source"],
                "url": item.get("link"),
                "admiralty_reliability": item["admiralty"][0],
                "admiralty_credibility": item["admiralty"][1],
                "retrieved_at_utc": now.isoformat().replace("+00:00", "Z"),
            }],
            "single_source": True,
            "confidence_collector": "low",
        }
        incidents.append(out_item)

    log(f"Web search fallback added {len(new_raw)} items across {len(gap_regions)} gap regions")
    return incidents

# ── Social media collection (cost-conscious) ────────────────────────────────

SOCIAL_MEDIA_QUERIES = {
    "middle_east": [
        "site:twitter.com Iran war latest ceasefire OR Hormuz OR blockade",
        "site:reddit.com Iran war geopolitics discussion",
        "site:x.com strait of hormuz tanker traffic",
    ],
    "north_africa": [
        "site:twitter.com North Africa security latest",
        "site:reddit.com North Africa geopolitics",
        "site:x.com Maghreb Sahel security",
    ],
    "sub_saharan_africa": [
        "site:twitter.com Sub-Saharan Africa security conflict",
        "site:reddit.com Africa geopolitics",
        "site:x.com West Africa coup OR terrorism",
    ],
    "south_america": [
        "site:twitter.com Latin America politics security latest",
        "site:reddit.com Latin America news",
        "site:x.com Brazil Venezuela Colombia crisis",
    ],
    "central_america_caribbean": [
        "site:twitter.com Central America security news",
        "site:reddit.com Caribbean news",
        "site:x.com Haiti crisis OR Nicaragua OR Guatemala",
    ],
    "europe": [
        "site:twitter.com Europe security NATO latest",
        "site:reddit.com European Union news",
        "site:x.com Ukraine war Russia update",
    ],
    "central_asia": [
        "site:twitter.com Central Asia Kazakhstan security",
        "site:reddit.com Central Asia geopolitics",
        "site:x.com Kazakhstan Uzbekistan Kyrgyzstan latest",
    ],
    "south_east_asia": [
        "site:twitter.com Southeast Asia security latest",
        "site:reddit.com ASEAN Myanmar news",
        "site:x.com South China Sea Philippines",
    ],
    "oceania": [
        "site:twitter.com Pacific Islands security",
        "site:reddit.com Australia New Zealand news",
        "site:x.com China Pacific influence",
    ],
    "north_america": [
        "site:twitter.com US politics security latest",
        "site:reddit.com US politics Canada",
        "site:x.com US Mexico border security",
    ],
    "prediction_markets": [
        "site:twitter.com oil markets shipping latest",
        "site:reddit.com wallstreetbets commodities",
        "site:x.com crude oil Brent hormone",
    ],
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def _sonar_sonar(query: str, sonar_model: str = "perplexity/sonar") -> list[dict]:
    """Call Perplexity Sonar via OpenRouter (cost-conscious — use sparingly)."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return []
    payload = json.dumps({
        "model": sonar_model,
        "messages": [
            {"role": "system", "content": "You are a social media intelligence collector. Search for breaking news, crisis developments, and security-related discussions on social media platforms. Return concrete findings with sources. Keep responses under 500 words."},
            {"role": "user", "content": query},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return []
            return [{
                "title": f"Sonar: {query[:60]}",
                "summary": content[:800],
                "link": "",
                "source": f"Perplexity Sonar ({sonar_model})",
                "pub": "",
                "admiralty": ("C", 2),
                "_bypass_filter": True,
            }]
    except Exception as exc:
        log(f"Sonar query failed: {exc}")
        return []

def social_media_collect(incidents: list[dict], regions: dict) -> list[dict]:
    """Collect social media intelligence using Brave Search primary + Sonar fallback.

    Uses Brave Search with social-media-specific queries (site:twitter.com / site:x.com / site:reddit.com)
    as the primary cost-free path. Falls back to Perplexity Sonar (which costs ~$0.05-0.15 per call)
    only when Brave returns zero results for a region.
    """
    brave_key = os.environ.get("BRAVE_API_KEY", "")
    if not brave_key:
        log("BRAVE_API_KEY not set — social media collection requires it")
        return incidents

    # Count items per region to see if we need social media augmentation
    region_counts: dict[str, int] = {}
    for inc in incidents:
        r = inc.get("region", "unknown")
        region_counts[r] = region_counts.get(r, 0) + 1

    # Only collect social for regions with fewer than 5 items
    social_regions = [r for r in SOCIAL_MEDIA_QUERIES if region_counts.get(r, 0) < 5]
    if not social_regions:
        return incidents

    log(f"Social media collection needed for: {', '.join(social_regions)} — querying Brave Search")

    new_raw: list[dict] = []
    sonar_needed: list[str] = []

    for region in social_regions:
        queries = SOCIAL_MEDIA_QUERIES[region]
        region_results: list[dict] = []
        for query in queries:
            try:
                results = _brave_search(query, brave_key, timeout=12)
                if results:
                    log(f"  Brave social '{query[:50]}': {len(results)} results")
                    region_results.extend(results)
            except Exception as exc:
                log(f"  Brave social search failed for '{query[:30]}': {exc}")

        if region_results:
            new_raw.extend(region_results)
        else:
            # Brave found nothing for this region — try Sonar as fallback (cost-conscious)
            sonar_needed.append(region)

    # Use Sonar sparingly — only for regions where Brave returned zero
    if sonar_needed:
        log(f"Sonar fallback needed for {len(sonar_needed)} regions (Brave returned zero): {sonar_needed}")
        for region in sonar_needed:
            # Use a single combined query per region to minimize calls
            region_label = region.replace("_", " ").title()
            combined_query = (
                f"What are the breaking social media discussions about security, conflict, "
                f"and geopolitics in {region_label} today? Focus on X/Twitter, Reddit, and Telegram. "
                f"Cite specific posts when possible."
            )
            results = _sonar_sonar(combined_query, "perplexity/sonar")
            if results:
                log(f"  Sonar '{region_label}': obtained results")
                new_raw.extend(results)
            else:
                log(f"  Sonar '{region_label}': no results")

    if not new_raw:
        return incidents

    # Normalise results into incidents
    now = dt.datetime.now(dt.timezone.utc)
    for item in new_raw:
        country = detect_country(f"{item.get('title','')} {item.get('summary','')}", regions)
        rg = country_to_region(country or "", regions) if country else None
        if not rg:
            # Try to infer from social media queries
            text = f"{item.get('title','')} {item.get('summary','')}".lower()
            for possible_region in SOCIAL_MEDIA_QUERIES:
                if possible_region.replace("_", " ") in text:
                    rg = possible_region
                    break
        if not rg:
            continue
        occurred = now.isoformat().replace("+00:00", "Z")
        out_item = {
            "id": make_id(occurred, country or rg, item["title"] or "social"),
            "region": rg,
            "country": country,
            "lat": None, "lon": None,
            "occurred_at_utc": occurred,
            "actors": [],
            "category": "social_media",
            "headline": item["title"],
            "summary": (item.get("summary") or "")[:600],
            "url": item.get("link", ""),
            "sources": [{
                "name": item["source"],
                "url": item.get("link", ""),
                "admiralty_reliability": item["admiralty"][0],
                "admiralty_credibility": item["admiralty"][1],
                "retrieved_at_utc": now.isoformat().replace("+00:00", "Z"),
            }],
            "single_source": True,
            "confidence_collector": "low",
        }
        incidents.append(out_item)

    sonar_used = len(sonar_needed)
    log(f"Social media collection: {len(new_raw)} items added across {len(social_regions)} regions (Sonar used: {sonar_used})")
    return incidents

if __name__ == "__main__":
    sys.exit(main())
