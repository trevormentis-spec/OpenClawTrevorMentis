#!/usr/bin/env python3
"""
Map validated South America feeds → sources_tested.json catalog format.
Merges into the live analyst/meta/sources_tested.json.
"""

import json
import copy
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/ubuntu/.openclaw/workspace")
VALIDATED = REPO / "config/sources/southamerica-feeds-validated.json"
CATALOG = REPO / "analyst/meta/sources_tested.json"
BACKUP = REPO / "analyst/meta/sources_tested.json.bak"

# --- Classification rules ---

def classify_source(name, url, country_code, cms):
    """Return (type, themes, admiralty_source, admiralty_info, poll_interval_minutes)."""

    name_lower = name.lower()
    url_lower = url.lower()

    # Wire services / international broadcasters
    wire_keywords = ["bbc", "dw ", "france 24", "rfi ", "voa", "efe", "sputnik",
                     "telesur", "agência brasil", "agenciabrasil", "andina",
                     "ip agencia", "vtv", "ntn24", "uol", "g1 ", "mercopress"]
    if any(k in name_lower for k in wire_keywords):
        return ("wire_service", ["wire_service"], "B", "1", 30)

    # Major newspapers
    newspaper_keywords = ["clarin", "la nación", "página/12", "ámbito", "perfil",
                          "el cronista", "la prensa", "bae", "tn ", "c5n",
                          "el destape", "tiempo argentino", "eldiarioar",
                          "la capital", "el ciudadano", "aire de santa fe",
                          "el litoral", "la voz", "los andes", "río negro",
                          "la gaceta", "diario de cuyo", "letra p",
                          "el deber", "los tiempos", "la razón", "el diario",
                          "correo del sur", "opinión", "el día", "la patria",
                          "el potosí", "anf", "radio fides", "erbol",
                          "brújula digital", "oxígeno", "bolpress",
                          "folha", "estadão", "o globo", "valor", "veja",
                          "istoé", "carta capital", "correio braziliense",
                          "zero hora", "o povo", "estado de minas",
                          "metrópoles", "poder360", "piauí", "extra",
                          "el mercurio", "la tercera", "lun", "diario financiero",
                          "el mostrador", "publímetro", "el líbero",
                          "the clinic", "diario u.", "resumen",
                          "bío bío", "el desconcierto", "el dínamo", "ex-ante",
                          "el tiempo", "el espectador", "semana",
                          "el colombiano", "el país cali", "el heraldo",
                          "el universal", "vanguardia", "portafolio",
                          "la república", "el nuevo siglo", "cambio",
                          "caracol radio", "blu radio", "rcn radio", "w radio",
                          "caracol tv", "canal 1", "noticias uno",
                          "kien y ke",
                          "el comercio", "el universo", "expreso",
                          "el telégrafo", "la hora", "extra", "diario correo",
                          "metro", "primicias", "ecuavisa", "teleamazonas",
                          "stabroek news", "kaieteur news", "demerara waves",
                          "news source guyana", "guyana chronicle",
                          "abc color", "última hora", "crónica", "hoy",
                          "5dias", "la nación", "telefuturo",
                          "perú21", "trome", "gestión", "el peruano",
                          "caretas", "hildebrandt",
                          "de ware tijd", "starnieuws", "suriname herald",
                          "dagblad suriname",
                          "el país", "el observador", "la diaria", "búsqueda",
                          "brecha", "la mañana", "el telégrafo", "lared21",
                          "sudestada", "montevideo portal", "teledoce",
                          "el pitazo", "runrun", "talcual", "la patilla",
                          "el estímulo", "caraota digital", "diario las américas",
                          "venezuela al día", "punto de corte", "aporrea",
                          "france-guyane", "guyane la 1ère",
                          "radio mitre", "canal 26", "cooperativa",
                          "la gaceta", "revista mate", "indymedia"]
    if any(k in name_lower for k in newspaper_keywords):
        return ("newspaper", ["newspaper"], "B", "1", 30)

    # Investigative journalism / specialized news
    investigative = ["insight crime", "connectas", "occrp", "el faro",
                     "ciper", "idl-reporteros", "ojo público", "convoca",
                     "armando.info", "efecto cocuyo", "la silla vacía",
                     "verdad abierta", "rutas del conflicto", "cuestión pública",
                     "vorágine", "mutante", "cerosetenta", "razón pública",
                     "pacifista", "baudó ap", "la barra espaciadora",
                     "plan v", "gk ", "la posta", "wambra", "4pelagatos",
                     "mil hojas", "la fuente",
                     "sumaúma", "ponte jornalismo", "agência pública",
                     "the intercept brasil", "nexo jornal", "repórter brasil",
                     "mídia ninja", "aos fatos", "lupa",
                     "interferencia", "el faro", "revista anfibia",
                     "cenital", "el cohete a la luna", "la vaca",
                     "el surti", "conexionespy", "el independiente",
                     "wayka", "sudaca", "la mula", "epicentro",
                     "revista ideele", "idehpucp", "iep",
                     "distintas latitudes", "latin american reports",
                     "nodal", "diálogo político", "nueva sociedad",
                     "chequeado", "colombia check", "prodavinci",
                     "crónica.uno", "ipys venezuela", "foro penal",
                     "acceso a la justicia", "transparencia venezuela",
                     "espacio público",
                     "el independiente", "revista anfibia",
                     "mongabay", "salud con lupa"]
    if any(k in name_lower for k in investigative):
        return ("news", ["news", "analysis"], "B", "2", 30)

    # Think tanks / research institutes
    thinktank = ["igarapé", "wola", "resdal", "cries",
                 "inter-american dialogue", "cari", "cippec", "cels",
                 "cedla", "fundación tierra",
                 "fbsp", "fórum brasileiro", "instituto sou da paz",
                 "conectas direitos", "nev", "núcleo de estudos",
                 "cebri", "ipea",
                 "cesc", "athenalab", "paz ciudadana", "flacso chile",
                 "libertad y desarrollo", "cep", "centro de estudios públicos",
                 "indepaz", "fip", "fundación ideas para la paz",
                 "pares", "cinep", "comisión colombiana de juristas",
                 "cerac", "comisión de la verdad", "jep",
                 "ovv", "observatorio venezolano", "provea"]
    if any(k in name_lower for k in thinktank):
        return ("think_tank", ["think_tank", "analysis"], "B", "2", 60)

    # Default fallback
    return ("news", ["news"], "C", "3", 60)


def get_poll_interval(cms):
    """Rate-limit aware poll intervals."""
    if cms == "arc":
        return 15  # Arc Publishing throttles aggressively
    elif cms == "wordpress":
        return 30
    else:
        return 60  # default conservative


def shortname(name, country_code):
    """Generate a shortname from source name."""
    # Remove country qualifiers
    short = name.replace("(Quito)", "").replace("(Guayaquil)", "").replace("(Medellín)", "")
    short = short.replace("(Cochabamba)", "").replace("(Santa Cruz)", "").replace("(Oruro)", "")
    short = short.replace("(Barranquilla)", "").replace("(Cartagena)", "").replace("(Bucaramanga)", "")
    short = short.replace("(Córdoba)", "").replace("(Mendoza)", "").replace("(Tucumán)", "")
    short = short.replace("(Rosario)", "").replace("(Paysandú)", "").replace("(Ceará)", "")
    short = short.strip()
    # Truncate reasonably
    if len(short) > 35:
        short = short[:32] + "..."
    return short


def main():
    # Load validated results
    with open(VALIDATED) as f:
        validated = json.load(f)

    # Load existing catalog
    with open(CATALOG) as f:
        catalog = json.load(f)

    # Backup
    with open(BACKUP, "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Backup → {BACKUP}")

    # Build set of existing RSS URLs to avoid duplicates
    existing_urls = set()
    existing_names = set()
    for s in catalog["sources"]:
        if s.get("rss"):
            existing_urls.add(s["rss"])
        existing_names.add(s["name"].lower())

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_entries = []
    skipped = 0
    merged = 0

    for r in validated["results"]:
        # Skip non-usable feeds
        if r["status"] not in ("OK", "STALE"):
            continue

        url = r["feed_url"]

        # Skip duplicates (already in catalog)
        if url in existing_urls:
            skipped += 1
            continue

        # Classify
        source_type, themes, admiralty_source, admiralty_info, default_poll = \
            classify_source(r["source"], url, r["country_code"], r["cms"])

        # CMS-aware poll interval overrides default
        poll_interval = get_poll_interval(r["cms"])

        entry = {
            "name": r["source"],
            "shortname": shortname(r["source"], r["country_code"]),
            "type": source_type,
            "url": url,
            "rss": url,
            "region": "south_america",
            "country": r["country_code"],
            "themes": themes,
            "admiralty_source": admiralty_source,
            "admiralty_info": admiralty_info,
            "tested": True,
            "tested_at": now,
            "status": "working" if r["status"] == "OK" else r["status"].lower(),
            "fetched_sample": r["status"] == "OK",
            "sample_entry_count": r.get("entry_count", 0),
            "latest_entry_date": r.get("latest_entry_date"),
            "freshness": r.get("freshness"),
            "poll_interval_minutes": poll_interval,
            "cms": r["cms"],
            "language": "es" if r["country_code"] != "BR" else "pt",
        }
        new_entries.append(entry)
        merged += 1

    # Add to catalog
    catalog["sources"].extend(new_entries)

    # Update stats
    sa_count = sum(1 for s in catalog["sources"] if s.get("region") == "south_america")
    catalog["total_entries"] = len(catalog["sources"])
    working = sum(1 for s in catalog["sources"] if s.get("status") == "working")
    failed = catalog["total_entries"] - working
    catalog["working_feeds"] = working
    catalog["failed_feeds"] = failed

    # Update regions breakdown
    regions = {}
    for s in catalog["sources"]:
        r = s.get("region", "unknown")
        regions[r] = regions.get(r, 0) + 1
    catalog["regions_breakdown"] = regions

    # Update types breakdown
    types = {}
    for s in catalog["sources"]:
        t = s.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    catalog["types_breakdown"] = types

    catalog["generated_at"] = now

    # Write
    with open(CATALOG, "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Merged: {merged} new South America entries")
    print(f"Skipped: {skipped} duplicates")
    print(f"Catalog now: {catalog['total_entries']} total, {catalog['working_feeds']} working")
    print(f"South America region: {sa_count} feeds")
    print(f"\nBy type:")
    for t in sorted(types.keys(), key=lambda x: types[x], reverse=True):
        print(f"  {t}: {types[t]}")
    print(f"\nUpdated catalog → {CATALOG}")

    return catalog


if __name__ == "__main__":
    main()
