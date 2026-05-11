"""Compose the final security brief PDF — ThruDark-inspired dark edition.

Style: tactical/operational. Warm off-black ground (#161616), all-caps
condensed display (Bebas Neue), monospaced labels at wide tracking
(JetBrains Mono), light-weight body (Inter Light) at #97999b. Single
military-olive accent (#7b7356) used sparingly. Hairline rules in #212121.
Sharp corners, zero rounding, edge-to-edge imagery.

Six theatres + prediction markets section + method note.
"""
import os
import re
import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
    Paragraph, Spacer, PageBreak, Image, KeepTogether,
    HRFlowable, Table, TableStyle, FrameBreak, CondPageBreak,
)
from reportlab.platypus.flowables import Flowable

# ---------- Fonts (portable — loads from trevor_fonts with graceful fallback) ----------
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from trevor_fonts import register_fonts, ensure_fonts_downloaded

# Try to download missing fonts (non-blocking), then register what's available
ensure_fonts_downloaded()
reg = register_fonts()

# ---------- Log any font registrations that fell back to system fonts ----------
for name, resolved in reg.items():
    if 'DejaVu' in str(resolved) or resolved in ('Helvetica','Helvetica-Bold','Helvetica-Oblique','Courier','Courier-Bold'):
        print(f"[build_pdf] Font '{name}' using fallback: {resolved}", file=sys.stderr)

# ---------- ThruDark palette ----------
BG        = HexColor("#161616")  # warm off-black — page background
BG_DEEP   = HexColor("#030000")  # near-pure black for footer/strips
BRAND_DK  = HexColor("#242424")  # subtle step lighter than bg
BRAND_LT  = HexColor("#373737")  # interactive dark
RULE      = HexColor("#212121")  # hairlines (barely visible)
RULE_LT   = HexColor("#2c2c2c")  # slightly lighter rules
FG        = HexColor("#f4f4f4")  # primary text
FG_2      = HexColor("#97999b")  # body text (dimmed)
FG_3      = HexColor("#787878")  # captions / de-emphasised
FG_LITE   = HexColor("#cfcfcf")  # secondary heading text
ACCENT    = HexColor("#7b7356")  # military olive — used sparingly
ACCENT_LT = HexColor("#9a916d")  # lighter olive for hover/highlights
RED_ALERT = HexColor("#eb5757")  # error/alert only

# ---------- Page geometry ----------
PAGE_W, PAGE_H = letter
LM, RM, TM, BM = 0.65*inch, 0.65*inch, 0.95*inch, 0.65*inch
GUTTER = 0.30*inch
COL_W = (PAGE_W - LM - RM - GUTTER) / 2

# ---------- Styles ----------
styles = getSampleStyleSheet()

# Cover masthead (HUGE display)
H_MAST = ParagraphStyle("HMast", parent=styles["Title"],
                         fontName="Display", fontSize=64, leading=64,
                         textColor=FG, spaceAfter=2, alignment=0)
H_MAST_SUB = ParagraphStyle("HMastSub", parent=styles["Normal"],
                             fontName="Body", fontSize=11, leading=16,
                             textColor=FG_2, spaceAfter=12)

# Mono label / eyebrow / kicker — wide letter-spacing simulation
EYEBROW = ParagraphStyle("Eyebrow", parent=styles["Normal"],
                          fontName="Mono", fontSize=8, leading=12,
                          textColor=ACCENT_LT, spaceAfter=4, alignment=0)

EYEBROW_FG = ParagraphStyle("EyebrowFG", parent=EYEBROW,
                             textColor=FG_LITE)

# Display headline
H_HEADLINE = ParagraphStyle("HHeadline", parent=styles["Title"],
                             fontName="Display", fontSize=44, leading=44,
                             textColor=FG, spaceBefore=4, spaceAfter=8, alignment=0)

# Dek / standfirst
DEK = ParagraphStyle("Dek", parent=styles["Normal"],
                      fontName="Body", fontSize=12, leading=17,
                      textColor=FG_LITE, spaceBefore=4, spaceAfter=10)

# Section subhead within body
H_SUB = ParagraphStyle("HSub", parent=styles["Heading2"],
                        fontName="Display", fontSize=18, leading=20,
                        textColor=FG, spaceBefore=12, spaceAfter=4)

# Body text — Inter Light, dimmed colour, slightly tracked
BODY = ParagraphStyle("Body", parent=styles["Normal"],
                       fontName="Body", fontSize=9, leading=13.5,
                       textColor=FG_2, spaceAfter=6, alignment=4,
                       firstLineIndent=0)

BODY_LEAD = ParagraphStyle("BodyLead", parent=BODY,
                            fontSize=9.2, leading=14)

# Key Judgment bullet
KJ = ParagraphStyle("KJ", parent=BODY,
                     fontName="Body", fontSize=9, leading=13.5,
                     leftIndent=12, bulletIndent=2, spaceAfter=6,
                     textColor=FG_2)

# Pull quote — mono, all caps, breaks the column grid
PULL = ParagraphStyle("Pull", parent=BODY,
                       fontName="Mono", fontSize=11, leading=17,
                       textColor=FG, alignment=0,
                       spaceBefore=8, spaceAfter=8,
                       leftIndent=0, rightIndent=0)

# Caption — small, mono, dimmed
CAPTION = ParagraphStyle("Caption", parent=styles["Normal"],
                          fontName="Body", fontSize=8, leading=11,
                          textColor=FG_3, spaceBefore=4, spaceAfter=4,
                          alignment=0)

# Image credit — uppercase mono
CREDIT = ParagraphStyle("Credit", parent=styles["Normal"],
                         fontName="Mono", fontSize=6.5, leading=8.5,
                         textColor=FG_3, spaceAfter=10, alignment=0)

# Footnote / sources — mono
FOOTNOTE = ParagraphStyle("Footnote", parent=BODY,
                           fontName="Body", fontSize=7.2, leading=10,
                           textColor=FG_3, spaceAfter=2, alignment=0)

# Cover meta
COVER_META = ParagraphStyle("CoverMeta", parent=styles["Normal"],
                             fontName="Mono", fontSize=9, leading=13,
                             textColor=FG_2, spaceAfter=3)

# Table cell body (light)
TABLE_BODY = ParagraphStyle("TableBody", parent=BODY,
                             fontName="Body", fontSize=8.2, leading=11.5,
                             textColor=FG_2, spaceAfter=0, alignment=0)

# BLUF body — distinct style with NO background colour (drawn manually)
BLUF_BODY = ParagraphStyle("BlufBody", parent=BODY,
                            fontName="Body-Reg", fontSize=9.5, leading=14,
                            textColor=FG, spaceBefore=0, spaceAfter=0,
                            leftIndent=0, rightIndent=0)

# ---------- Section data ----------
SECTIONS = [
    {"key": "europe",         "label": "EUROPE", "n": "01"},
    {"key": "africa",         "label": "AFRICA", "n": "02"},
    {"key": "asia",           "label": "SOUTH ASIA",   "n": "03"},
    {"key": "middle_east",    "label": "MIDDLE EAST", "n": "04"},
    {"key": "north_america",  "label": "NORTH AMERICA", "n": "05"},
    {"key": "south_america",  "label": "SOUTH AMERICA", "n": "06"},
]

# Portable path resolution
_SKILL_DIR = Path(__file__).resolve().parent.parent
_BASE = _SKILL_DIR  # daily_intel skill directory
_MAPS_DIR = _BASE / 'maps'
_INFO_DIR = _BASE / 'infographics'
_IMAGES_DIR = _BASE / 'images'
_ASSESS_DIR = _BASE / 'assessments'

_MAPS_DIR.mkdir(parents=True, exist_ok=True)
_INFO_DIR.mkdir(parents=True, exist_ok=True)
_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MAP_FILES = {k: str(_MAPS_DIR / f"{i:02d}_{k}.png")
             for i, k in enumerate(["europe","africa","asia","middle_east",
                                     "north_america","south_america"], 1)}
INFO_FILES = {k: str(_INFO_DIR / f"{i:02d}_{k}.png")
              for i, k in enumerate(["europe","africa","asia","middle_east",
                                      "north_america","south_america"], 1)}
# Generate dynamic image paths from today's date
_TODAY = datetime.date.today().isoformat()
PHOTO_FILES = {
    "europe":        str(_IMAGES_DIR / f"{_TODAY}_europe.jpg"),
    "africa":        str(_IMAGES_DIR / f"{_TODAY}_africa.jpg"),
    "asia":          str(_IMAGES_DIR / f"{_TODAY}_asia.jpg"),
    "middle_east":   str(_IMAGES_DIR / f"{_TODAY}_middle_east.jpg"),
    "north_america": str(_IMAGES_DIR / f"{_TODAY}_north_america.jpg"),
    "south_america": str(_IMAGES_DIR / f"{_TODAY}_south_america.jpg"),
}

EDITORIAL = {
    "europe": {
        "kicker":  "RUSSIA / UKRAINE",
        "headline": "MOSCOW FORTRESS",
        "dek": "Russia ignored Zelensky's midnight 5–6 May counter-truce, conducting at least 20 airstrikes with 70+ glide bombs through the morning of 6 May. ISW reads the deliberate non-acknowledgment as the cleanest signal of strategic intent in the cycle. Ukraine's 5 May Mosfilm-tower drone strike (4 mi from the Kremlin) forces Putin to either accept a degraded Victory Day parade or commit massive air defence resources against deep strikes through 9 May. Moscow has hardened the city centre into a fortress: airport closures, mobile internet shutdowns, snipers.",
        "photo_caption": "The Mosfilm residential tower in western Moscow, struck by a Ukrainian drone on 5 May 2026 — less than 10 km from the Kremlin and adjacent to a district housing major foreign embassies. Ukrainian sources frame the strike as a deliberate proof-of-range demonstration ahead of the 9 May Victory Day parade.",
        "photo_credit": "PHOTO  ·  BBC NEWS / SOCIAL MEDIA HANDOUT",
    },
    "africa": {
        "kicker":  "SAHEL",
        "headline": "JNIM OFFENSIVE CONFIRMED",
        "dek": "NYT, Al Jazeera, NPR and Critical Threats Project independently confirm the 25–26 April JNIM offensive — coordinated assaults on Bamako airport, the Kati military headquarters, the Defence Minister's residence, and Mopti, Sevare and Gao. JNIM has now demonstrated the capacity to strike multiple regional capitals simultaneously, validating Shurkin's 29 April ‘very high coup risk’ assessment. ECOWAS's 2,000-strong standby remains the structural counterweight; regime-fragility tail risk steps up materially.",
        "photo_caption": "Critical Threats Project battlemap of West Africa as of 30 April 2026, showing the geographic distribution of JNIM operations during the late-April offensive — the first time the group has demonstrated simultaneous strike capacity against Bamako, Kati, Mopti, Sevare and Gao.",
        "photo_credit": "MAP  ·  CRITICAL THREATS PROJECT (AEI &amp; ISW)",
    },
    "asia": {
        "kicker":  "INDIA / PAKISTAN",
        "headline": "INDIA FORGIVES NOTHING",
        "dek": "Sindoor anniversary day-of. The Indian Air Force released a high-production-value commemorative video at 1:05 AM IST on 7 May titled ‘India Forgives Nothing’, celebrating the 2025 strikes on nine terror sites in Pakistan. The Diplomat's anniversary essay frames the year as one of ‘rising risks and deepening instability’. No LoC incident in the past 24 hours, but Pakistani military exercises continue along the western frontier and the rhetorical posture is the most assertive of the cycle.",
        "photo_caption": "Indian Air Force still released for the 7 May 2026 anniversary of Operation Sindoor, accompanying the commemorative video ‘India Forgives Nothing’. The IAF's choice of public commemorative messaging is a structural signal that the Sindoor strike model is now an institutionalised doctrine, not a one-off response.",
        "photo_credit": "PHOTO  ·  INDIAN AIR FORCE / SOCIAL MEDIA RELEASE",
    },
    "middle_east": {
        "kicker":  "IRAN",
        "headline": "MOU INSIDE 48 HOURS",
        "dek": "Axios, Reuters and Turkiye Today report the White House expects Iran's response to a one-page, 14-point MoU within 48 hours. Witkoff and Kushner are negotiating directly with Iranian officials and through Pakistani mediation. Rubio formally announced the conclusion of Operation Epic Fury. Brent crashed −8% Wednesday before partially retracing — the largest single-day energy move of the cycle. Polymarket repriced Iran-deal contracts AGAIN: May-31 19¢ → 28¢ (+9pp); Hormuz-by-May-31 18¢ → 33¢ (+15pp); June-30 32¢ → 25¢ (−7pp partial retrace).",
        "photo_caption": "US Special Envoy Steve Witkoff at an earlier round of US–Iran nuclear talks. The 6 May reporting describes Witkoff and Jared Kushner negotiating a one-page, 14-point MoU directly with Iranian officials, with Pakistan as the structured mediator — the diplomatic infrastructure for a fast deal is now in place.",
        "photo_credit": "PHOTO  ·  REUTERS",
    },
    "north_america": {
        "kicker":  "MEXICO",
        "headline": "FALLOUT SETTLES",
        "dek": "The political-fallout phase is settling: Sinaloa Governor Rocha Moyá and Mazatlán Mayor stepped down following US indictments; PBS NewsHour and the NYT independently confirm. Sheinbaum's ‘we will never accept joint operations’ posture (30 April) holds. The NYT's 1 May ‘We Have Always Known’ reframing depoliticises the indictment domestically while structurally locking in the kingpin-strategy logic. Cartel-war markets stable: US-invasion contract 8¢, Sheinbaum-out 8¢. The unilateral-US-kinetic tail remains underpriced.",
        "photo_caption": "ACLED map of violent events involving the Sinaloa Cartel and affiliates across northwestern Mexico. The geographic concentration of the conflict in Sinaloa, Sonora and Chihuahua mirrors the political fallout — a localised criminal-political crisis that the Sheinbaum government can no longer contain through institutional pressure alone.",
        "photo_credit": "MAP  ·  ACLED (ARMED CONFLICT LOCATION &amp; EVENT DATA PROJECT)",
    },
    "south_america": {
        "kicker":  "VENEZUELA",
        "headline": "TREASURY LICENSES",
        "dek": "On 14 April Acting President Delcy Rodríguez delivered a ‘Venezuela free of sanctions’ address from the National Assembly; US Treasury has subsequently issued specific OFAC licenses for Banco de Venezuela, Banco del Tesoro and Banco Digital de los Trabajadores. The transition-track is now operational on the financial side. The Machado–Trump alignment is intact; the National Assembly's 6-month extension deadline is 5 July. Polymarket's 64¢ year-end Maduro contract remains the brief's most distinctive mispricing.",
        "photo_caption": "Miraflores Palace, Caracas — the seat of acting president Delcy Rodríguez since the 3 January US removal of Maduro. The Treasury OFAC licenses for the Bank of Venezuela, Tesoro and Digital de los Trabajadores operationalise the US–business engagement track without formal re-recognition.",
        "photo_credit": "PHOTO  ·  CARLOS E. PÉREZ / WIKIMEDIA COMMONS (CC BY-SA 2.0)",
    },
}

# ---------- Markdown -> ReportLab Paragraph helpers ----------
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^\*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^\*]+)\*(?!\*)")

PROB_MAP = [
    (r"almost certain(?:ly)?",                         "\u2248 95\u201399%"),
    (r"highly likely",                                 "\u2248 80\u201395%"),
    (r"very likely",                                   "\u2248 80\u201395%"),
    (r"likely",                                        "\u2248 60\u201380%"),
    (r"probable(?:ly)?",                               "\u2248 60\u201380%"),
    (r"roughly (?:an )?even (?:chance|odds)",          "\u2248 45\u201355%"),
    (r"(?:an )?even (?:chance|odds)",                  "\u2248 45\u201355%"),
    (r"highly unlikely",                               "\u2248 5\u201320%"),
    (r"very unlikely",                                 "\u2248 5\u201320%"),
    (r"unlikely",                                      "\u2248 20\u201340%"),
    (r"almost no chance",                              "\u2248 1\u20135%"),
    (r"high confidence",                               "\u2248 75\u201395%"),
    (r"moderate(?:-to-high)? confidence",              "\u2248 60\u201380%"),
    (r"low-to-moderate confidence",                    "\u2248 40\u201355%"),
    (r"moderate confidence",                           "\u2248 55\u201375%"),
    (r"low confidence",                                "\u2248 25\u201345%"),
]
PROB_RE = re.compile(
    r"\*\*(" + "|".join(p for p, _ in PROB_MAP) + r")\*\*",
    flags=re.IGNORECASE,
)
_PROB_LOOKUP = [(re.compile(r"^" + p + r"$", re.IGNORECASE), val) for p, val in PROB_MAP]


def _resolve_prob(phrase: str) -> str:
    for rx, val in _PROB_LOOKUP:
        if rx.match(phrase):
            return val
    return ""


_AUTHOR_PROB_FOLLOW = re.compile(r"^\s*\((\s*[\d>~<\u2265\u2264]+\s*[%\u2013\-\u2014]?\s*\d*\s*%?\s*)\)")


def inject_probabilities(text: str) -> str:
    out = []
    i = 0
    for m in PROB_RE.finditer(text):
        out.append(text[i:m.start()])
        phrase = m.group(1)
        end = m.end()
        tail = text[end:end+30]
        author = _AUTHOR_PROB_FOLLOW.match(tail)
        if author:
            author_text = author.group(1).strip()
            if not author_text.endswith("%"):
                author_text = author_text + "%"
            out.append(
                f"**{phrase}**"
                f' <font name="Mono" color="#9a916d" size="7.5">'
                f"[\u2248 {author_text}]</font>"
            )
            i = end + author.end()
        else:
            bracket = _resolve_prob(phrase)
            if bracket:
                out.append(
                    f"**{phrase}**"
                    f' <font name="Mono" color="#9a916d" size="7.5">'
                    f"[{bracket}]</font>"
                )
            else:
                out.append(m.group(0))
            i = end
    out.append(text[i:])
    return "".join(out)


def escape_amp(text: str) -> str:
    return re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", text)


def md_to_rl(text: str, footnote_map: dict, sources: list):
    """Convert markdown [name](url) to clickable inline link + numbered superscript."""
    def repl(m):
        name, url = m.group(1), m.group(2)
        existing = next((i for i, s in enumerate(sources) if s[1] == url), None)
        if existing is not None:
            n = existing + 1
        else:
            sources.append((name, url))
            n = len(sources)
        safe_name = escape_amp(name)
        return (f'<a href="{url}" color="#9a916d">{safe_name}</a>'
                f'<super><font size="6"><a href="{url}" color="#9a916d">'
                f'{n}</a></font></super>')
    text = LINK_RE.sub(repl, text)
    text = inject_probabilities(text)
    parts = re.split(r"(<[^>]+>)", text)
    for i, p in enumerate(parts):
        if not p.startswith("<"):
            parts[i] = escape_amp(p)
    text = "".join(parts)
    text = BOLD_RE.sub(r'<font color="#f4f4f4"><b>\1</b></font>', text)
    text = ITALIC_RE.sub(r"<i>\1</i>", text)
    return text


def parse_assessment(md_path: str):
    with open(md_path) as f:
        content = f.read()
    lines = content.splitlines()
    title = ""
    for ln in lines:
        if ln.startswith("# "):
            title = ln[2:].strip()
            break

    def grab(section_name):
        pattern = rf"## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\n---|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "title":       title,
        "bluf":        grab("Bottom Line Up Front"),
        "kjs":         grab("Key Judgments"),
        "discussion":  grab("Discussion"),
        "alt":         grab("Alternative Analysis"),
        "predictive":  grab("Predictive Judgments (Next 30–90 Days)") or grab("Predictive Judgments"),
        "indicators":  grab("Indicators to Watch"),
        "implications": grab("Implications"),
    }


def split_paragraphs(text: str):
    if not text:
        return []
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


_ESTIMATIVE_RE = re.compile(
    r"\*\*(" + "|".join(p for p, _ in PROB_MAP) + r")\*\*",
    flags=re.IGNORECASE,
)


def summarise_predictive(line: str, max_words: int = 22) -> tuple:
    m = _ESTIMATIVE_RE.search(line)
    if not m:
        return (line, "", "")
    term = m.group(1)
    prob = _resolve_prob(term)
    after = line[m.end():].strip()
    after = re.sub(r"^\(\s*[\d>~<\u2265\u2264]+\s*[%\u2013\-\u2014]?\s*\d*\s*%?\s*\)\s*", "", after)
    after = re.sub(r"^(that\s+|chance\s+that\s+|odds\s+that\s+)", "", after, flags=re.I)
    after = LINK_RE.sub(r"\1", after)
    after = re.sub(r"\*\*([^\*]+)\*\*", r"\1", after)
    after = re.sub(r"(?<!\*)\*([^\*]+)\*(?!\*)", r"\1", after)
    words = after.split()
    if len(words) > max_words:
        after = " ".join(words[:max_words]) + "\u2026"
    if after:
        after = after[0].upper() + after[1:]
    return (after, term, prob)


def summarise_indicator(line: str, max_words: int = 22) -> tuple:
    line = line.strip()
    m = re.match(r"\*\*([^\*]+)\*\*\s*:?\s*(.*)", line)
    if m:
        topic = m.group(1).strip()
        details = m.group(2).strip()
    else:
        topic = ""
        details = line
    details = LINK_RE.sub(r"\1", details)
    details = re.sub(r"\*\*([^\*]+)\*\*", r"\1", details)
    details = re.sub(r"(?<!\*)\*([^\*]+)\*(?!\*)", r"\1", details)
    words = details.split()
    if len(words) > max_words:
        details = " ".join(words[:max_words]) + "\u2026"
    return (topic, details)


# ---------- Page background fill (every non-cover page) ----------
def _draw_page_background(c):
    """Paint the full page warm-black BEFORE any content draws."""
    c.saveState()
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.restoreState()


def _draw_top_bar(c, page_n, kicker=""):
    c.saveState()
    # Hairline separator near top
    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.line(LM, PAGE_H - 0.55*inch, PAGE_W - RM, PAGE_H - 0.55*inch)
    # Mono masthead, very wide tracking simulated by Mono font + spaced text
    c.setFillColor(FG_3)
    c.setFont("Mono", 7.5)
    c.drawString(LM, PAGE_H - 0.42*inch,
                  "G L O B A L   S E C U R I T Y   /   I N T E L L I G E N C E   B R I E F")
    c.setFillColor(FG_3)
    c.setFont("Mono", 7.5)
    c.drawRightString(PAGE_W - RM, PAGE_H - 0.42*inch, "ISSUE 07  /  07 MAY 2026")
    # Section kicker (just below the rule)
    if kicker:
        c.setFillColor(ACCENT_LT)
        c.setFont("Mono", 7.5)
        c.drawString(LM, PAGE_H - 0.72*inch, kicker)
    c.restoreState()


def _draw_bottom_rule(c, page_n):
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.line(LM, 0.45*inch, PAGE_W - RM, 0.45*inch)
    c.setFillColor(FG_3)
    c.setFont("Mono", 7)
    c.drawString(LM, 0.30*inch, "TREVOR  /  STRATEGIC INTELLIGENCE")
    c.drawCentredString(PAGE_W/2, 0.30*inch, f"— {page_n:02d} —")
    c.drawRightString(PAGE_W - RM, 0.30*inch, "OPEN-SOURCE  /  CLASSIFIED: NONE")
    c.restoreState()


_KICKER_TRACK = {"current": ""}


def header_footer(canvas_obj, doc):
    _draw_page_background(canvas_obj)
    _draw_top_bar(canvas_obj, doc.page, _KICKER_TRACK.get("current", ""))
    _draw_bottom_rule(canvas_obj, doc.page)


def cover_only(canvas_obj, doc):
    """Cover: full-bleed dark image with overlay typography."""
    canvas_obj.saveState()
    # Pure black ground
    canvas_obj.setFillColor(BG_DEEP)
    canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Place full-bleed cover image (NASA Black Marble)
    cover_img_path = str(_IMAGES_DIR / f"{_TODAY}_cover.jpg")
    if os.path.exists(cover_img_path):
        from reportlab.lib.utils import ImageReader
        canvas_obj.drawImage(ImageReader(cover_img_path), 0, 0,
                              width=PAGE_W, height=PAGE_H, preserveAspectRatio=False, mask='auto')
    # Dark gradient overlay (top + bottom) — manual rectangles with translucent fill
    from reportlab.lib.colors import Color as RGBA
    canvas_obj.setFillColor(RGBA(0.086, 0.086, 0.086, alpha=0.55))
    canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Heavier overlay top (for masthead) + bottom (for colophon)
    canvas_obj.setFillColor(RGBA(0.012, 0.0, 0.0, alpha=0.80))
    canvas_obj.rect(0, PAGE_H - 1.3*inch, PAGE_W, 1.3*inch, fill=1, stroke=0)
    canvas_obj.rect(0, 0, PAGE_W, 1.4*inch, fill=1, stroke=0)
    # Top mono masthead
    canvas_obj.setFillColor(FG)
    canvas_obj.setFont("Mono", 9)
    canvas_obj.drawString(LM, PAGE_H - 0.45*inch,
                           "T R E V O R     /     S T R A T E G I C  I N T E L L I G E N C E")
    canvas_obj.setFillColor(FG_2)
    canvas_obj.drawRightString(PAGE_W - RM, PAGE_H - 0.45*inch, "ISSUE 07")
    # Hairline rule under masthead
    canvas_obj.setStrokeColor(BRAND_LT)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(LM, PAGE_H - 0.65*inch, PAGE_W - RM, PAGE_H - 0.65*inch)
    # Issue date in mono on top right
    canvas_obj.setFillColor(FG_2)
    canvas_obj.setFont("Mono", 8)
    canvas_obj.drawString(LM, PAGE_H - 0.85*inch, "07  MAY  2026")
    canvas_obj.drawRightString(PAGE_W - RM, PAGE_H - 0.85*inch, "OPEN-SOURCE ASSESSMENT")
    # Bottom: ThruDark-style chevron + colophon
    canvas_obj.setStrokeColor(BRAND_LT)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(LM, 1.0*inch, PAGE_W - RM, 1.0*inch)
    canvas_obj.setFillColor(FG_3)
    canvas_obj.setFont("Mono", 7.5)
    canvas_obj.drawString(LM, 0.35*inch, "AUTHOR  /  TREVOR ASSESSMENT")
    canvas_obj.drawRightString(PAGE_W - RM, 0.35*inch, "DISTRIBUTION: UNRESTRICTED ▷")
    canvas_obj.restoreState()


# ---------- Image helpers ----------
def fit_image(path, target_w, target_h=None, mode="contain"):
    from PIL import Image as PILImage
    pim = PILImage.open(path)
    iw, ih = pim.size
    if target_h is None:
        scale = target_w / iw
        return Image(path, width=target_w, height=ih*scale)
    target_ratio = target_w / target_h
    img_ratio = iw / ih
    if mode == "cover" and abs(img_ratio - target_ratio) > 0.02:
        if img_ratio > target_ratio:
            new_w = int(ih * target_ratio)
            x0 = (iw - new_w) // 2
            pim2 = pim.crop((x0, 0, x0 + new_w, ih))
        else:
            new_h = int(iw / target_ratio)
            y0 = (ih - new_h) // 2
            pim2 = pim.crop((0, y0, iw, y0 + new_h))
        out_path = f"/tmp/_crop_{os.path.basename(path)}"
        pim2.convert("RGB").save(out_path, "JPEG", quality=92)
        return Image(out_path, width=target_w, height=target_h)
    scale = min(target_w/iw, target_h/ih)
    return Image(path, width=iw*scale, height=ih*scale)


def make_bluf_panel(bluf_text: str, sources: list, width: float):
    """Build a properly self-contained BLUF block — label INSIDE the panel,
    drawn on the dark BRAND_DK box. No z-axis collision possible because
    the label and body are rendered as cells in a single Table."""
    label = Paragraph(
        '<font name="Mono" color="#7b7356" size="7.5">'
        '▷  BOTTOM LINE UP FRONT</font>',
        ParagraphStyle("BlufL", parent=BODY, spaceAfter=0,
                        textColor=ACCENT, fontName="Mono", fontSize=7.5))
    body_para = Paragraph(md_to_rl(bluf_text, {}, sources), BLUF_BODY)
    tbl = Table(
        [[label], [Spacer(1, 4)], [body_para]],
        colWidths=[width],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,-1), BRAND_DK),
        ("LEFTPADDING",    (0,0), (-1,-1), 14),
        ("RIGHTPADDING",   (0,0), (-1,-1), 14),
        ("TOPPADDING",     (0,0),  (0,0),  12),
        ("BOTTOMPADDING",  (0,0),  (0,0),  0),
        ("TOPPADDING",     (0,1),  (0,1),  0),
        ("BOTTOMPADDING",  (0,1),  (0,1),  0),
        ("TOPPADDING",     (0,2),  (0,2),  0),
        ("BOTTOMPADDING",  (0,2),  (0,2),  14),
        ("LINEABOVE",      (0,0), (-1,0),  1.0, ACCENT),
        ("VALIGN",         (0,0), (-1,-1), "TOP"),
    ]))
    return tbl


# ---------- Build ----------
def build():
    out_path = str(_BASE / f"security_brief_{_TODAY}.pdf")
    doc = BaseDocTemplate(
        out_path, pagesize=letter,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
        title="Global Security & Intelligence Brief — 7 May 2026",
        author="TREVOR (Threat Research and Evaluation Virtual Operations Resource)",
    )

    # Frames
    cover_frame = Frame(LM, BM, PAGE_W - LM - RM, PAGE_H - TM - BM,
                         id="cover", showBoundary=0,
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    single_frame = Frame(LM, BM, PAGE_W - LM - RM, PAGE_H - TM - BM,
                          id="single", showBoundary=0,
                          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    col_y = BM
    col_h = PAGE_H - TM - BM
    col1 = Frame(LM, col_y, COL_W, col_h, id="c1", showBoundary=0,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    col2 = Frame(LM + COL_W + GUTTER, col_y, COL_W, col_h, id="c2", showBoundary=0,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=cover_only),
        PageTemplate(id="Single", frames=[single_frame], onPage=header_footer),
        PageTemplate(id="TwoCol", frames=[col1, col2], onPage=header_footer),
        PageTemplate(id="Contents", frames=[single_frame], onPage=header_footer),
    ])

    story = []

    # ---------- COVER ----------
    # Cover layout uses cover_only canvas drawing; story content sits over the gradient.
    # Place the masthead block centered vertically on the page.
    story.append(Spacer(1, 1.4*inch))
    story.append(Paragraph(
        '<font name="Mono" color="#9a916d" size="9">▷  GLOBAL SECURITY  /  07 MAY 2026  /  SIX THEATRES</font>',
        ParagraphStyle("CoverLabel", parent=COVER_META, spaceAfter=14,
                        textColor=ACCENT_LT)))
    story.append(Paragraph("GLOBAL", H_MAST))
    story.append(Paragraph("SECURITY", H_MAST))
    story.append(Paragraph(
        '<font color="#7b7356">&amp;</font> INTELLIGENCE',
        H_MAST))
    story.append(Paragraph("BRIEF", H_MAST))
    story.append(Spacer(1, 0.18*inch))
    story.append(HRFlowable(width="35%", thickness=1.0, color=ACCENT,
                             spaceBefore=2, spaceAfter=12, hAlign="LEFT"))
    story.append(Paragraph(
        '<font color="#cfcfcf">A Sherman-Kent assessment across six theatres &mdash; the White House expects Iran to respond to a one-page MoU within 48 hours and Brent crashes &minus;8&percnt;; Russia ignores Zelensky&rsquo;s counter-truce while Moscow hardens into a fortress for the 9 May parade; the IAF marks the Sindoor anniversary with &lsquo;India Forgives Nothing&rsquo;; JNIM&rsquo;s late-April offensive is independently confirmed; the Sinaloa fallout settles; and US Treasury issues new specific licenses for Caracas&rsquo;s state banks.</font>',
        ParagraphStyle("CoverDek", parent=H_MAST_SUB,
                        fontName="Body", fontSize=11, leading=16,
                        textColor=FG_LITE, alignment=0,
                        leftIndent=0, rightIndent=2.5*inch)))

    # ---------- CONTENTS PAGE ----------
    story.append(NextPageTemplate("Contents"))
    story.append(PageBreak())
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("CONTENTS", H_HEADLINE))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_LT,
                             spaceBefore=4, spaceAfter=14))
    titles_short = {
        "europe":         ("EUROPE",         "Moscow fortress",               "RUSSIA / UKRAINE"),
        "africa":         ("AFRICA",         "JNIM offensive confirmed",      "SAHEL"),
        "asia":           ("SOUTH ASIA",     "India forgives nothing",        "INDIA / PAKISTAN"),
        "middle_east":    ("MIDDLE EAST",    "MoU inside 48 hours",           "IRAN"),
        "north_america":  ("NORTH AMERICA",  "Fallout settles",               "MEXICO"),
        "south_america":  ("SOUTH AMERICA",  "Treasury licenses",             "VENEZUELA"),
    }
    toc_num_st  = ParagraphStyle("Tn", parent=BODY, fontName="Mono", fontSize=11,
                                  textColor=ACCENT, leading=24)
    toc_eye_st  = ParagraphStyle("Teye", parent=BODY, fontName="Mono", fontSize=7.5,
                                  leading=10, textColor=FG_3, spaceAfter=4)
    toc_reg_st  = ParagraphStyle("Treg", parent=BODY, fontName="Display", fontSize=20,
                                  leading=22, textColor=FG)
    toc_head_st = ParagraphStyle("Tt", parent=BODY, fontName="Body", fontSize=11,
                                  leading=24, textColor=FG_LITE)
    toc_data = []
    for s in SECTIONS:
        region, headline, kicker = titles_short[s["key"]]
        toc_data.append([
            Paragraph(f'{s["n"]}', toc_num_st),
            [Paragraph(kicker, toc_eye_st), Paragraph(region, toc_reg_st)],
            Paragraph(headline, toc_head_st),
        ])
    # Add prediction markets row
    toc_data.append([
        Paragraph('07', toc_num_st),
        [Paragraph('MARKETS', toc_eye_st), Paragraph('PREDICTION MARKETS', toc_reg_st)],
        Paragraph('Ten high-conviction trades', toc_head_st),
    ])
    toc_data.append([
        Paragraph('08', toc_num_st),
        [Paragraph('METHOD', toc_eye_st), Paragraph('METHOD', toc_reg_st)],
        Paragraph('Estimative language and sourcing', toc_head_st),
    ])
    toc_table = Table(toc_data, colWidths=[0.45*inch, 2.4*inch, 4.25*inch])
    toc_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LINEBELOW", (0,0), (-1,-2), 0.4, BRAND_LT),
        ("LINEBELOW", (0,-1), (-1,-1), 0.4, BRAND_LT),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        '<font name="Mono" color="#787878" size="7.5">▷  EXFIL</font>',
        ParagraphStyle("Exfil", parent=COVER_META, textColor=ACCENT_LT)))

    # ---------- SECTIONS ----------
    for s in SECTIONS:
        key = s["key"]
        meta = parse_assessment(str(_ASSESS_DIR / f"{key}.md"))
        ed = EDITORIAL[key]
        sources = []

        story.append(_KickerSetter(ed["kicker"]))
        story.append(NextPageTemplate("Single"))
        story.append(PageBreak())

        # Big editorial photo at top (full content width)
        photo_w = PAGE_W - LM - RM
        photo_h = 3.4*inch
        if os.path.exists(PHOTO_FILES[key]):
            photo = fit_image(PHOTO_FILES[key], photo_w, photo_h, mode="cover")
            photo.hAlign = "CENTER"
            story.append(photo)
            story.append(Paragraph(ed["photo_caption"], CAPTION))
            story.append(Paragraph(ed["photo_credit"], CREDIT))

        # Section number + kicker (mono labels) — separated rule
        story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_LT,
                                 spaceBefore=4, spaceAfter=10))
        story.append(Paragraph(
            f'<font name="Mono" color="#7b7356" size="9">'
            f'  {s["n"]}    /    {ed["kicker"]}</font>', EYEBROW))
        # Headline (BIG display caps)
        story.append(Paragraph(ed["headline"], H_HEADLINE))
        # Dek
        story.append(Paragraph(ed["dek"], DEK))
        story.append(Spacer(1, 0.05*inch))

        # BLUF panel — self-contained Table on dark surface
        story.append(make_bluf_panel(meta["bluf"], sources, PAGE_W - LM - RM))

        # Switch to two-column for the body
        story.append(NextPageTemplate("TwoCol"))
        story.append(PageBreak())

        # Key Judgments
        story.append(Paragraph("KEY JUDGMENTS", H_SUB))
        story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                 spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
        for ln in meta["kjs"].splitlines():
            ln = ln.strip()
            if not ln or not ln.startswith("-"):
                continue
            txt = ln.lstrip("-").strip()
            txt = md_to_rl(txt, {}, sources)
            story.append(Paragraph(f'<font color="#7b7356">▷</font>  {txt}', KJ))

        # Discussion
        story.append(Paragraph("THE STORY", H_SUB))
        story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                 spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
        disc_paras = split_paragraphs(meta["discussion"])
        if disc_paras:
            first = md_to_rl(disc_paras[0], {}, sources)
            m_dc = re.match(r'((?:<[^>]+>)*)([A-Za-z\u00c0-\u017f])', first)
            if m_dc:
                pre, ch = m_dc.group(1), m_dc.group(2)
                rest = first[m_dc.end():]
                first_with_dc = (
                    f'{pre}<font name="Display" color="#7b7356" size="32">{ch}</font>'
                    f'{rest}'
                )
                story.append(Paragraph(first_with_dc, BODY_LEAD))
            else:
                story.append(Paragraph(first, BODY_LEAD))

        # Map inset
        if os.path.exists(MAP_FILES[key]):
            map_w = COL_W
            map_img = fit_image(MAP_FILES[key], map_w)
            kt = KeepTogether([
                map_img,
                Paragraph(
                    f'<font name="Mono" color="#7b7356" size="7">▷  MAP</font>  '
                    f'<font color="#cfcfcf">{ed["headline"].title()}</font> — '
                    f'territorial &amp; operational picture, 7 May 2026.',
                    CAPTION),
            ])
            story.append(kt)

        for para in disc_paras[1:]:
            txt = md_to_rl(para, {}, sources)
            story.append(Paragraph(txt, BODY))

        # Pull-quote
        pull_src = re.sub(r"\[[^\]]+\]\([^)]+\)", "", meta["bluf"])
        pull_src = re.sub(r"\*\*([^\*]+)\*\*", r"\1", pull_src)
        first_sentence = re.split(r"(?<=[.!?])\s+", pull_src.strip())[0]
        # Cap to 140 chars on word boundary so pull quote never gets clipped at column flow
        if len(first_sentence) > 140:
            cut = first_sentence[:140].rsplit(" ", 1)[0]
            first_sentence = cut + "\u2026"
        if first_sentence:
            story.append(Spacer(1, 0.05*inch))
            story.append(HRFlowable(width="60%", thickness=1.0, color=ACCENT,
                                     spaceBefore=4, spaceAfter=6, hAlign="LEFT"))
            story.append(Paragraph(
                f'<font color="#f4f4f4">{first_sentence.upper()}</font>',
                PULL))
            story.append(HRFlowable(width="60%", thickness=0.5, color=RULE_LT,
                                     spaceBefore=2, spaceAfter=8, hAlign="LEFT"))

        # Alternative analysis
        if meta["alt"]:
            story.append(Paragraph("ALTERNATIVE ANALYSIS", H_SUB))
            story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                     spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
            for para in split_paragraphs(meta["alt"]):
                txt = md_to_rl(para, {}, sources)
                story.append(Paragraph(txt, BODY))

        # Predictive Judgments — table
        if meta["predictive"]:
            story.append(Paragraph("PREDICTIVE JUDGMENTS \u2014 NEXT 30\u201390 DAYS", H_SUB))
            story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                     spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
            pred_rows = [[
                Paragraph('<font name="Mono" color="#7b7356" size="7">JUDGMENT</font>',
                           ParagraphStyle("h", parent=BODY)),
                Paragraph('<font name="Mono" color="#7b7356" size="7">PROBABILITY</font>',
                           ParagraphStyle("h", parent=BODY)),
            ]]
            for ln in meta["predictive"].splitlines():
                ln = ln.strip()
                if not ln.startswith("-"):
                    continue
                bullet = ln.lstrip("-").strip()
                summary, term, prob = summarise_predictive(bullet, max_words=22)
                if not term:
                    continue
                pred_rows.append([
                    Paragraph(escape_amp(summary), TABLE_BODY),
                    Paragraph(
                        f'<font name="Mono" color="#f4f4f4" size="8">'
                        f'{term.upper()}</font><br/>'
                        f'<font name="Mono" color="#9a916d" size="7.5">{prob}</font>',
                        TABLE_BODY),
                ])
            if len(pred_rows) > 1:
                pred_tbl = Table(pred_rows, colWidths=[COL_W*0.62, COL_W*0.38])
                pred_tbl.setStyle(TableStyle([
                    ("VALIGN",      (0,0), (-1,-1), "TOP"),
                    ("BACKGROUND",  (0,0), (-1,0),  BRAND_DK),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                    ("RIGHTPADDING",(0,0), (-1,-1), 6),
                    ("TOPPADDING",  (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                    ("LINEBELOW",   (0,0), (-1,-2), 0.3, RULE_LT),
                    ("LINEABOVE",   (0,0), (-1,0),  1.0, ACCENT),
                    ("LINEBELOW",   (0,-1),(-1,-1), 0.4, RULE_LT),
                ]))
                story.append(pred_tbl)
                story.append(Spacer(1, 0.08*inch))

        # Infographic inset
        if os.path.exists(INFO_FILES[key]):
            info_w = COL_W
            info_img = fit_image(INFO_FILES[key], info_w)
            kt = KeepTogether([
                info_img,
                Paragraph(
                    f'<font name="Mono" color="#7b7356" size="7">▷  BY THE NUMBERS</font>  '
                    f'<font color="#787878">Key data points underpinning this assessment.</font>',
                    CAPTION),
            ])
            story.append(kt)

        # Indicators table
        if meta["indicators"]:
            story.append(Paragraph("INDICATORS TO WATCH", H_SUB))
            story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                     spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
            ind_rows = [[
                Paragraph('<font name="Mono" color="#7b7356" size="7">INDICATOR</font>',
                           ParagraphStyle("h", parent=BODY)),
                Paragraph('<font name="Mono" color="#7b7356" size="7">WHAT TO LOOK FOR</font>',
                           ParagraphStyle("h", parent=BODY)),
            ]]
            for ln in meta["indicators"].splitlines():
                ln = ln.strip()
                if not ln.startswith("-"):
                    continue
                bullet = ln.lstrip("-").strip()
                topic, details = summarise_indicator(bullet, max_words=22)
                if not topic and not details:
                    continue
                ind_rows.append([
                    Paragraph(
                        f'<font name="Body-Bold" color="#f4f4f4" size="8.2">'
                        f'{escape_amp(topic) or "\u2014"}</font>',
                        TABLE_BODY),
                    Paragraph(escape_amp(details), TABLE_BODY),
                ])
            if len(ind_rows) > 1:
                ind_tbl = Table(ind_rows, colWidths=[COL_W*0.40, COL_W*0.60])
                ind_tbl.setStyle(TableStyle([
                    ("VALIGN",      (0,0), (-1,-1), "TOP"),
                    ("BACKGROUND",  (0,0), (-1,0),  BRAND_DK),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                    ("RIGHTPADDING",(0,0), (-1,-1), 6),
                    ("TOPPADDING",  (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                    ("LINEBELOW",   (0,0), (-1,-2), 0.3, RULE_LT),
                    ("LINEABOVE",   (0,0), (-1,0),  1.0, ACCENT),
                    ("LINEBELOW",   (0,-1),(-1,-1), 0.4, RULE_LT),
                ]))
                story.append(ind_tbl)

        # Implications
        if meta["implications"]:
            story.append(Paragraph("IMPLICATIONS", H_SUB))
            story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                                     spaceBefore=0, spaceAfter=8, hAlign="LEFT"))
            for ln in meta["implications"].splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("-"):
                    txt = md_to_rl(ln.lstrip("-").strip(), {}, sources)
                    story.append(Paragraph(f'<font color="#7b7356">▷</font>  {txt}', KJ))
                else:
                    txt = md_to_rl(ln, {}, sources)
                    story.append(Paragraph(txt, BODY))

        # Sources
        if sources:
            story.append(Spacer(1, 0.10*inch))
            story.append(HRFlowable(width="100%", thickness=0.4, color=BRAND_LT,
                                     spaceBefore=2, spaceAfter=6))
            story.append(Paragraph(
                '<font name="Mono" color="#7b7356" size="7.5">▷  SOURCES</font>',
                ParagraphStyle("SrcLabel", parent=BODY, spaceAfter=2)))
            for i, (name, url) in enumerate(sources, 1):
                safe_name = name.replace("&", "&amp;")
                safe_url = url.replace("&", "&amp;")
                story.append(Paragraph(
                    f'<font name="Mono" color="#7b7356">{i:02d}</font>  '
                    f'<font color="#97999b">{safe_name}.</font> '
                    f'<a href="{safe_url}" color="#9a916d">{safe_url}</a>',
                    FOOTNOTE))

    # ---------- PREDICTION MARKETS SECTION ----------
    story.append(_KickerSetter("PREDICTION MARKETS"))
    story.append(NextPageTemplate("Single"))
    story.append(PageBreak())
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        '<font name="Mono" color="#7b7356" size="9">'
        '  07    /    PREDICTION MARKETS</font>', EYEBROW))
    story.append(Paragraph("THE BOOK", H_HEADLINE))
    story.append(Paragraph(
        "Ten high-conviction trades on Polymarket and Kalshi as of market close, 7 May 2026. "
        "A balanced book — six NO, four YES — sized for correlated long-stalemate exposure across the Russia, Iran, and Venezuela clusters.",
        DEK))

    # Standfirst panel summarising methodology
    market_intro = ("These are the trades where our editorial assessment diverges meaningfully "
                    "from current market pricing, or where the market priced an outcome with such "
                    "high conviction that the EV is positive even at thin margins. "
                    "Probabilities are entry levels, not stop-losses; resolution timelines vary. "
                    "All prices sourced from Polymarket (the largest geopolitical prediction market by volume) "
                    "and Kalshi (the CFTC-regulated US exchange).")
    pm_sources = []
    story.append(make_bluf_panel(market_intro, pm_sources, PAGE_W - LM - RM))

    # Switch to two-column for the trades table
    story.append(NextPageTemplate("TwoCol"))
    story.append(PageBreak())

    # The 10 trades — each one a dense card
    story.append(Paragraph("HIGH-CONVICTION TRADES", H_SUB))
    story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                             spaceBefore=0, spaceAfter=10, hAlign="LEFT"))

    TRADES = [
        {"n":"01","theatre":"EUROPE","contract":"Russia × Ukraine ceasefire by end of 2026",
         "side":"BUY NO","price":"26¢","edge":"+62 pp",
         "thesis":"KJ-1 assesses Ukraine's drone campaign is producing structural rather than correctable damage to Russian war financing — Putin's incentive structure is to absorb pain, not settle. Ankara summit (May 21–22) is procedural.",
         "url":"https://polymarket.com/event/russia-x-ukraine-ceasefire-before-2027",
         "venue":"Polymarket"},
        {"n":"02","theatre":"EUROPE","contract":"Russia × Ukraine ceasefire by 30 Jun 2026",
         "side":"BUY NO","price":"9.5¢","edge":"thin / high conviction",
         "thesis":"Already priced 90.5% no-deal at six-week tenor. Tight margin but our confidence band is 95–99%. Position-sized small as near-term cash-flow generator.",
         "url":"https://polymarket.com/event/russia-x-ukraine-ceasefire-by-june-30-2026",
         "venue":"Polymarket"},
        {"n":"03","theatre":"EUROPE","contract":"Putin out as President of Russia by 31 Dec 2026",
         "side":"BUY NO","price":"12¢","edge":"+~10 pp",
         "thesis":"No elite-level coup signal from Perm, Orenburg or Ural governorships despite refinery destruction. Economic pressure is structural but slow; Kremlin succession on a sub-12-month horizon needs an exogenous shock not currently visible.",
         "url":"https://polymarket.com/event/putin-out-before-2027",
         "venue":"Polymarket"},
        {"n":"04","theatre":"SOUTH ASIA","contract":"India strike on Pakistan by 31 Dec 2026",
         "side":"BUY YES","price":"23¢","edge":"+22–32 pp / anniversary day-of",
         "thesis":"Holding at 23¢ on the day of the Sindoor anniversary. The IAF's 1:05 AM IST 7 May commemorative video ‘India Forgives Nothing’ is the most assertive public-messaging signal of the cycle. No LoC incident in the past 24h. Our through-year band (45–55%) implies the edge is intact. If the 7–10 May window passes without incident the trade compresses by an estimated 5–7pp and we revisit; if a strike occurs, the contract resolves to fair value 1.00.",
         "url":"https://polymarket.com/event/india-strike-on-pakistan-by",
         "venue":"Polymarket"},
        {"n":"05","theatre":"MIDDLE EAST","contract":"US–Iran nuclear deal by 31 May 2026",
         "side":"BUY NO","price":"28¢","edge":"compressed / second adverse leg",
         "thesis":"Second adverse leg: YES 19¢ → 28¢ (NO 81¢ → 72¢, −9pp on the NO side). Axios/Reuters/Turkiye Today report a one-page 14-point MoU framework with the White House expecting an Iranian response ‘within 48 hours’. Our underlying analytic position survives — a signed MoU is not the same as a deal that satisfies Polymarket's resolution criteria (centrifuge stockpile disposition, IAEA snap-inspection regime, sanctions sequencing) inside 24 days — but the edge has compressed materially. Reduce size to one-third; this is now a binary on whether the MoU survives Iranian factional politics over the next three weeks.",
         "url":"https://polymarket.com/event/us-iran-nuclear-deal-by-may-31-974",
         "venue":"Polymarket"},
        {"n":"06","theatre":"MIDDLE EAST","contract":"US–Iran nuclear deal by 30 Jun 2026",
         "side":"BUY NO","price":"25¢","edge":"partial retrace / supportive",
         "thesis":"Partial retrace from yesterday's blow-out: YES 32¢ → 25¢ (NO 68¢ → 75¢, +7pp supportive). Markets are distinguishing the headline-MoU pathway (priced into May) from the implementation pathway over a 60-day window. Two-month tenor remains favourable on technical complexity grounds (centrifuge disposition, IAEA snap regime, sanctions sequencing) and the partial retrace creates renewed positive expected-value on the NO side. Hold and reload incremental size.",
         "url":"https://polymarket.com/event/us-iran-nuclear-deal-by-june-30",
         "venue":"Polymarket"},
        {"n":"07","theatre":"MIDDLE EAST","contract":"Iranian regime falls before 2027",
         "side":"BUY NO","price":"17¢","edge":"+~10 pp / hold",
         "thesis":"Unchanged at 17¢ (83% survival) through the entire reversal cycle — markets correctly distinguish kinetic-cycle volatility from succession risk. Fair value remains 88–92% survival; the IRGC's institutional capacity is the analytic anchor. The MOU pathway, if real, actually re-legitimates the regime by re-engaging it diplomatically. Hold.",
         "url":"https://polymarket.com/event/will-the-iranian-regime-fall-by-the-end-of-2026",
         "venue":"Polymarket"},
        {"n":"08","theatre":"MIDDLE EAST","contract":"Strait of Hormuz traffic returns to normal by 30 Jun 2026",
         "side":"BUY NO","price":"33¢","edge":"largest two-day adverse / size cut",
         "thesis":"Largest two-day adverse move in the book: YES 10¢ → 18¢ → 33¢ (NO 90¢ → 82¢ → 67¢). Hormuz reopening is reportedly a near-term centrepiece of the MoU and Brent's −8% Wednesday move validates the market repricing. Resolution criteria require sustained ‘normalisation’ — Iran's domestic factional politics may yet derail the 30-day reopening sequence. Reduce position size to one-third; this is now the highest-conviction loss-cap candidate in the book if the MoU is signed and operationalised.",
         "url":"https://polymarket.com/event/strait-of-hormuz-traffic-returns-to-normal-by-end-of-june",
         "venue":"Polymarket"},
        {"n":"09","theatre":"NORTH AMERICA","contract":"US invades Mexico in 2026",
         "side":"BUY YES","price":"8¢","edge":"asymmetric tail",
         "thesis":"Tail-risk hedge. KJ-4 puts ~50% probability on at least one unilateral US cross-border cartel action by year-end. Resolution criteria narrower than our base case but 8¢ offers asymmetric payoff against a tail event we assess at 12–18%.",
         "url":"https://polymarket.com/event/will-the-us-invade-mexico-in-2026",
         "venue":"Polymarket"},
        {"n":"10","theatre":"SOUTH AMERICA","contract":"Maduro as Venezuela leader at end of 2026",
         "side":"SELL MADURO","price":"64¢","edge":"+~50 pp",
         "thesis":"Maduro was physically removed by US forces on 3 January. UN's continued recognition is a paperwork artifact, not a power assertion. Acting President Rodríguez governs on the ground. The market is pricing recognition lag, not control. Pair trade: buy Rodríguez at 22¢.",
         "url":"https://polymarket.com/event/venezuela-leader-end-of-2026",
         "venue":"Polymarket"},
    ]

    # Render trades as dense rows
    for t in TRADES:
        # Header bar: number, theatre, side, price (mono labels)
        header = Table([[
            Paragraph(f'<font name="Mono" color="#7b7356" size="11">{t["n"]}</font>',
                       ParagraphStyle("h", parent=BODY)),
            Paragraph(f'<font name="Mono" color="#787878" size="7.5">{t["theatre"]}</font>',
                       ParagraphStyle("h", parent=BODY)),
            Paragraph(f'<font name="Mono" color="#f4f4f4" size="9">{t["side"]} @ {t["price"]}</font>',
                       ParagraphStyle("h", parent=BODY, alignment=2)),
        ]], colWidths=[0.35*inch, COL_W - 1.55*inch, 1.20*inch])
        header.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        contract_para = Paragraph(
            f'<font name="Body-Bold" color="#f4f4f4" size="10">{escape_amp(t["contract"])}</font>',
            ParagraphStyle("c", parent=BODY, spaceBefore=0, spaceAfter=2))
        edge_para = Paragraph(
            f'<font name="Mono" color="#9a916d" size="7.5">EDGE  /  {t["edge"]}  </font>'
            f'<font name="Mono" color="#787878" size="7.5">·  {t["venue"]}</font>',
            ParagraphStyle("e", parent=BODY, spaceBefore=0, spaceAfter=4))
        thesis_para = Paragraph(
            f'<font color="#97999b">{escape_amp(t["thesis"])}</font>  '
            f'<a href="{t["url"]}" color="#9a916d">'
            f'<font name="Mono" size="7">▷  {t["venue"].upper()}</font></a>',
            ParagraphStyle("th", parent=BODY, spaceBefore=0, spaceAfter=0))

        kt = KeepTogether([
            HRFlowable(width="100%", thickness=0.6, color=ACCENT,
                        spaceBefore=4, spaceAfter=6),
            header,
            contract_para,
            edge_para,
            thesis_para,
            Spacer(1, 0.05*inch),
        ])
        story.append(kt)

    # Closing rule on the last trade
    story.append(HRFlowable(width="100%", thickness=0.6, color=ACCENT,
                             spaceBefore=4, spaceAfter=10))

    # Regional read-through
    story.append(Paragraph("REGIONAL READ-THROUGH", H_SUB))
    story.append(HRFlowable(width="40%", thickness=0.6, color=ACCENT,
                             spaceBefore=0, spaceAfter=8, hAlign="LEFT"))

    READ_THROUGH = [
        ("EUROPE",
         "Year-end ceasefire holds at 26¢; Putin-out at 12¢. Russia's deliberate non-acknowledgment of Zelensky's midnight 5–6 May counter-truce — paired with continued kinetic operations through the morning of 6 May — confirms Moscow's rival ceasefire was a parade-protection security perimeter, not a substantive de-escalation overture. The Mosfilm tower drone strike and the Moscow-as-fortress security posture (airport closures, mobile internet shutdowns, snipers) reset expectations on Russian air-defence credibility but do not move year-end resolution-criteria pricing. Positions hold; no edge in adding."),
        ("SAHEL",
         "The largest blind spot remains. The 25–26 April JNIM offensive — simultaneous strikes on Bamako airport, Kati military HQ, the Defence Minister's residence, and Mopti, Sevare and Gao — is the most consequential validation yet of the regime-fragility frame, and Polymarket still has no liquid contract on Mali junta survival, AES-bloc cohesion, JNIM territorial control, or ECOWAS standby activation. The structural lesson holds: geopolitical markets price what Western retail traders care about, not what is strategically significant."),
        ("SOUTH ASIA",
         "Trade #04 holds at 23¢ on the day of the Sindoor anniversary. The IAF's 1:05 AM IST 7 May commemorative video ‘India Forgives Nothing’ is the most assertive public-messaging signal of the cycle and a structural confirmation that the strike model is now institutionalised. No LoC incident in the past 24h. Through-year band 45–55%; edge 22–32pp. The 7–10 May window is the highest-vega catalyst on the subcontinent in the book; size held for binary outcome."),
        ("MIDDLE EAST",
         "Second adverse leg in the Iran cluster: May-31 deal YES 19¢ → 28¢ (+9pp); Hormuz-by-May-31 normalised YES 18¢ → 33¢ (+15pp); June-30 deal YES 32¢ → 25¢ (−7pp partial retrace, supportive). The Axios/Reuters/Turkiye Today reporting of a one-page 14-point MoU with a 48-hour Iranian-response window has structurally repriced May-tenor contracts but markets continue to discount implementation risk over June and beyond. Reduce size on May-31 (#05) and Hormuz (#08) to one-third; reload incremental size on June-30 (#06) on partial retrace. Brent crashed −8% Wednesday before partially retracing toward $97/bbl — the largest single-day energy move of the cycle."),
        ("NORTH AMERICA",
         "Cartel-war markets stable: US invasion 8¢, Sheinbaum-out 8¢. The Sinaloa political fallout has settled into the steady-state phase: governor and Mazatlán mayor have stepped down; the NYT's 1 May ‘We Have Always Known’ reframing depoliticises the indictment domestically while structurally locking in the kingpin-strategy logic. The unilateral-US-kinetic tail remains underpriced; our 8¢ buy stands."),
        ("SOUTH AMERICA",
         "The Maduro mispricing remains the single most distinctive trade in the book. Acting President Rodríguez's 14 April ‘Venezuela free of sanctions’ address and the subsequent US Treasury specific licenses for Banco de Venezuela, Banco del Tesoro and Banco Digital de los Trabajadores operationalise the US–business engagement track on the financial side without formal re-recognition. Year-end Maduro contract holds at 64¢; our valuation is sub-15¢. Pair trade: short Maduro at 64¢, long Rodríguez at 22¢."),
    ]
    for region, blurb in READ_THROUGH:
        story.append(Paragraph(
            f'<font name="Mono" color="#7b7356" size="8">{region}</font>',
            ParagraphStyle("rh", parent=BODY, spaceBefore=4, spaceAfter=2)))
        story.append(Paragraph(
            f'<font color="#97999b">{blurb}</font>',
            BODY))

    # Methodology footnote
    story.append(Spacer(1, 0.10*inch))
    story.append(HRFlowable(width="100%", thickness=0.4, color=BRAND_LT,
                             spaceBefore=2, spaceAfter=6))
    story.append(Paragraph(
        '<font name="Mono" color="#7b7356" size="7.5">▷  METHODOLOGY</font>',
        ParagraphStyle("MmL", parent=BODY, spaceAfter=2)))
    story.append(Paragraph(
        '<font color="#787878">Probabilities cited are real-time as of market close 7 May 2026; prices may have moved by publication. High-conviction trades require either a market price diverging from our assessment by ≥10 percentage points or near-certainty on the editorial side. Position sizing should reflect resolution timeline, market liquidity, and correlation across the book. Trades 01, 05, 06, 07, 08 are correlated long-stalemate exposure; size accordingly.</font>',
        FOOTNOTE))

    # ---------- METHOD NOTE ----------
    story.append(_KickerSetter("METHOD"))
    story.append(NextPageTemplate("Single"))
    story.append(PageBreak())

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        '<font name="Mono" color="#7b7356" size="9">'
        '  08    /    METHOD</font>', EYEBROW))
    story.append(Paragraph("ESTIMATIVE LANGUAGE &amp; SOURCING", H_HEADLINE))
    story.append(Paragraph(
        "All probability statements in this brief follow Sherman Kent's conventions for estimative intelligence. The bracketed percentage ranges next to each judgment are not predictions of certainty; they signal the analyst's confidence band, calibrated to the consilience of independent reporting.",
        DEK))
    method_data = [
        ["ALMOST CERTAINLY",            "≥ 95%"],
        ["VERY LIKELY / HIGHLY LIKELY", "80–95%"],
        ["LIKELY",                       "60–80%"],
        ["ROUGHLY EVEN ODDS",            "45–55%"],
        ["UNLIKELY",                     "20–40%"],
        ["VERY UNLIKELY",                "5–20%"],
        ["ALMOST NO CHANCE",             "≤ 5%"],
        ["HIGH CONFIDENCE",              "75–95%"],
        ["MODERATE CONFIDENCE",          "55–75%"],
        ["LOW CONFIDENCE",               "25–45%"],
    ]
    method_table = Table(method_data, colWidths=[3.2*inch, 1.6*inch])
    method_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Mono"),
        ("FONTNAME", (1,0), (1,-1), "Mono"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 0.3, RULE_LT),
        ("LINEABOVE", (0,0), (-1,0), 1.0, ACCENT),
        ("LINEBELOW", (0,-1),(-1,-1), 0.6, ACCENT),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (0,-1), FG),
        ("TEXTCOLOR", (1,0), (1,-1), ACCENT_LT),
        ("BACKGROUND", (0,0), (-1,-1), BG),
    ]))
    story.append(method_table)
    story.append(Spacer(1, 0.20 * inch))
    story.append(Paragraph(
        "Sources are open-source: ISW, Reuters, AP, BBC, Le Monde, Al Jazeera, Crisis Group, Carnegie Endowment, Chatham House, IAEA, ACLED, and primary government and IGO statements. Photographs are credited beneath each opening image. Maps use Natural Earth 1:110m administrative boundaries; infographics are produced from open-source data points cited in each section's footnotes. Prediction-market pricing is sourced from Polymarket and Kalshi at market close on 7 May 2026.",
        BODY))
    story.append(Paragraph(
        "This issue covers six theatres: Europe, Africa, South Asia, the Middle East, North America &amp; the Caribbean, and South America, plus a prediction-markets read-through. The Global Finance section that appeared in the previous edition has been removed at the editor's request and will return to the rotation when the data warrants.",
        BODY))

    doc.build(story)
    return out_path


# ---------- KickerSetter ----------
class _KickerSetter(Flowable):
    def __init__(self, kicker):
        super().__init__()
        self.kicker = kicker
    def wrap(self, *args):
        return (0, 0)
    def draw(self):
        _KICKER_TRACK["current"] = self.kicker


if __name__ == "__main__":
    out = build()
    print("PDF written to", out)
    print("Size:", os.path.getsize(out), "bytes")
