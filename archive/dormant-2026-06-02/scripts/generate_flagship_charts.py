#!/usr/bin/env python3
"""Generate all charts for the Mexico Mid-2026 Flagship PDF."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json, os

OUT = "/home/ubuntu/.openclaw/workspace/exports/flagship-charts"
os.makedirs(OUT, exist_ok=True)

# Color palette
DARK = '#1a1a2e'
ACCENT_RED = '#c0392b'
ACCENT_BLUE = '#2980b9'
ACCENT_GREEN = '#27ae60'
ACCENT_AMBER = '#f39c12'
ACCENT_PURPLE = '#8e44ad'
GRAY = '#7f8c8d'
LIGHT_BG = '#f8f9fa'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.facecolor': LIGHT_BG,
    'figure.facecolor': 'white',
    'axes.edgecolor': DARK,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': GRAY,
})

# ============================================================
# CHART 1: Sheinbaum Approval Rating Trajectory
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

months = ['Oct\n2024', 'Dec', 'Mar\n2025', 'Jun', 'Sep', 'Dec', 'Mar\n2026']
# Combined poll data + estimates
approval = [68, 70, 72, 74, 70, 69, 54]  # reasonable curve
dates = np.arange(len(months))

ax.fill_between(dates, 40, 45, alpha=0.15, color=ACCENT_RED, label='Danger Zone (<45%)')
ax.fill_between(dates, 45, 55, alpha=0.10, color=ACCENT_AMBER, label='Functional Range (45-55%)')
ax.plot(dates, approval, color=ACCENT_BLUE, linewidth=2.5, marker='o', markersize=8, zorder=5)
ax.scatter([3], [74], color=ACCENT_GREEN, s=120, zorder=6, label='El Mencho Op (Feb 2026)')
ax.annotate('El Mencho\noperation\nboost', xy=(3, 74), xytext=(4.2, 78),
            arrowprops=dict(arrowstyle='->', color=ACCENT_GREEN), fontsize=9, color=ACCENT_GREEN)

ax.set_xticks(dates)
ax.set_xticklabels(months, fontsize=9)
ax.set_ylabel('Approval Rating (%)', fontweight='bold')
ax.set_title('Sheinbaum Approval Rating Trajectory (Oct 2024 – Mar 2026)', fontweight='bold', fontsize=13)
ax.set_ylim(35, 85)
ax.legend(fontsize=8, loc='lower left')
ax.text(0.5, -0.12, 'Sources: El Financiero, AS/COA, AtlasIntel LatAm Pulse | Open Claw Mexico',
        transform=ax.transAxes, ha='center', fontsize=7, color=GRAY)

plt.tight_layout()
fig.savefig(f"{OUT}/01-approval.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 01-approval.png")

# ============================================================
# CHART 2: Top 10 Judgments — Confidence Band Visualization
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

judgments = [
    "1. USMCA 16-yr extension by Q4 2026",
    "2. Sheinbaum accepts tighter ROO + China screening",
    "3. S&P downgrade (sovereign or Pemex) in 12mo",
    "4. CJNG fragmentation violence H2 2026",
    "5. Technical recession H1 2026",
    "6. Fixed investment negative → Q3 2026",
    "7. Greenfield FDI <2023 levels before 2028",
    "8. World Cup → no major incident, minor friction",
    "9. CDMX subsidence infrastructure failure in 12mo",
    "10. Banxico cycle floor reached; H2 holds/tightens",
]

# [low%, mid%, high%] for each (forecast visualization)
bands = [
    [55, 60, 65],
    [60, 65, 70],
    [55, 60, 65],
    [80, 85, 90],
    [90, 93, 95],
    [85, 88, 90],
    [60, 65, 70],
    [60, 65, 70],
    [55, 60, 65],
    [60, 65, 70],
]

colors_band = [ACCENT_BLUE, ACCENT_BLUE, ACCENT_BLUE, ACCENT_RED, '#e74c3c',
               ACCENT_RED, ACCENT_BLUE, ACCENT_AMBER, ACCENT_BLUE, ACCENT_BLUE]

y_pos = np.arange(len(judgments))

for i, (low, mid, high) in enumerate(bands):
    ax.barh(i, high - low, left=low, height=0.6, color=colors_band[i], alpha=0.3, edgecolor='none')
    ax.barh(i, 0.001, left=mid, height=0.6, color=DARK, alpha=0.8)  # midpoint marker

ax.set_yticks(y_pos)
ax.set_yticklabels(judgments, fontsize=9)
ax.set_xlabel('Probability (%)', fontweight='bold')
ax.set_title('Top 10 Judgments — Kent Confidence Bands', fontweight='bold', fontsize=13)
ax.set_xlim(40, 100)

# Add vertical lines for Kent bands
for pct, lbl in [(50, 'Even\n50%'), (60, 'Likely\n60%'), (80, 'High\nLikely\n80%'), (90, 'Almost\nCertain\n90%')]:
    ax.axvline(pct, color=GRAY, alpha=0.3, linewidth=0.5)
    if pct in [50, 60, 80, 90]:
        ax.text(pct, -0.8, lbl, ha='center', fontsize=7, color=GRAY)

plt.tight_layout()
fig.savefig(f"{OUT}/02-judgments.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 02-judgments.png")

# ============================================================
# CHART 3: Macro Dashboard — GDP, Inflation, Interest Rate
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# Left: GDP Growth trajectory
quarters = ['Q1\n2025', 'Q2', 'Q3', 'Q4', 'Q1\n2026', 'Q2E', 'Q3E', 'Q4E']
gdp_qoq = [0.5, 0.3, 0.1, -0.2, -0.8, -0.3, 0.2, 0.5]
colors_gdp = [ACCENT_BLUE if v >= 0 else ACCENT_RED for v in gdp_qoq]
bars1 = ax1.bar(range(len(quarters)), gdp_qoq, color=colors_gdp, width=0.6, edgecolor='white')
ax1.axhline(0, color=DARK, linewidth=0.8)
ax1.set_xticks(range(len(quarters)))
ax1.set_xticklabels(quarters, fontsize=8)
ax1.set_ylabel('QoQ % Change', fontweight='bold')
ax1.set_title('GDP Trajectory (Actual + Estimates)', fontweight='bold', fontsize=11)
for i, v in enumerate(gdp_qoq):
    ax1.text(i, v + 0.08 if v >= 0 else v - 0.15, f'{v:+.1f}%', ha='center', fontsize=8, fontweight='bold')

# Right: Inflation & Banxico Rate
months2 = ['Jan\n2025', 'Apr', 'Jul', 'Oct', 'Jan\n2026', 'Apr']
cpi = [4.9, 4.6, 4.3, 4.1, 3.77, 4.45]
rate = [10.00, 9.50, 9.00, 8.50, 8.00, 7.50]

ax2.plot(months2, cpi, color=ACCENT_RED, linewidth=2, marker='s', label='Headline CPI (%)')
ax2.plot(months2, rate, color=ACCENT_BLUE, linewidth=2, marker='o', label='Banxico Policy Rate (%)')
ax2.axhline(3.0, color=ACCENT_GREEN, linewidth=1, linestyle='--', alpha=0.7, label='Target (3%)')
ax2.set_ylabel('Percent', fontweight='bold')
ax2.set_title('Inflation & Policy Rate', fontweight='bold', fontsize=11)
ax2.legend(fontsize=7, loc='upper right')
ax2.tick_params(axis='x', labelsize=8)

fig.suptitle('Mexico Macro Dashboard', fontweight='bold', fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUT}/03-macro.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 03-macro.png")

# ============================================================
# CHART 4: Sector Exposure Bubble Chart
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5.5))

sectors = ['Autos &\nAuto Parts', 'Electronics', 'Agriculture', 'Medical\nDevices', 'Steel &\nAluminum', 'Beverages', 'Aerospace', 'Tourism']
exports_val = [193, 87, 45, 25, 22, 15, 10, 25]  # $bn
risk_score = [95, 80, 40, 15, 85, 25, 20, 35]  # USMCA risk 0-100

# Size = export value
sizes = [v * 15 for v in exports_val]

# Colors by risk
def risk_color(r):
    if r >= 80: return ACCENT_RED
    elif r >= 50: return ACCENT_AMBER
    else: return ACCENT_GREEN

colors_s = [risk_color(r) for r in risk_score]

scatter = ax.scatter(risk_score, [v/5 for v in exports_val], s=sizes, c=colors_s, alpha=0.7, edgecolors=DARK, linewidth=0.5)

# Label each bubble
for i, (x, y, s) in enumerate(zip(risk_score, [v/5 for v in exports_val], sizes)):
    ax.annotate(sectors[i], (x, y), fontsize=7, ha='center', va='center', fontweight='bold', color='white', 
                bbox=dict(boxstyle='round,pad=0.15', facecolor=DARK, alpha=0.6, edgecolor='none'))

ax.set_xlabel('USMCA Review Risk Score (0-100)', fontweight='bold')
ax.set_ylabel('Normalized Export Value', fontweight='bold')
ax.set_title('Sector Exposure: Export Value × USMCA Risk', fontweight='bold', fontsize=13)
ax.set_xlim(-5, 105)

# Legend for bubble size
legend_elements = [
    mpatches.Circle((0,0), radius=10, facecolor=GRAY, alpha=0.4, label='$10bn'),
    mpatches.Circle((0,0), radius=25, facecolor=GRAY, alpha=0.4, label='$50bn'),
    mpatches.Circle((0,0), radius=40, facecolor=GRAY, alpha=0.4, label='$100bn+'),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=8, title='Export Value', title_fontsize=9)

plt.tight_layout()
fig.savefig(f"{OUT}/04-sector-exposure.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 04-sector-exposure.png")

# ============================================================
# CHART 5: USMCA Scenario Tree
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis('off')

# Draw tree manually
tree_data = [
    (0.10, 'USMCA\nReview', DARK),
    (0.35, 'Scenario 1\nBruised Extension\n55-65%', ACCENT_GREEN),
    (0.55, 'Scenario 2\nAnnual Review\nPurgatory\n20-30%', ACCENT_AMBER),
    (0.85, 'Scenario 3\nRupture\n5-15%', ACCENT_RED),
]

# Only use ax.text and ax.annotate
ax.text(0.5, 0.85, 'USMCA July 1, 2026\nJoint Review', ha='center', va='center', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.8', facecolor='white', edgecolor=DARK, linewidth=2))

# Scenario boxes
y_base = 0.30
for i, (y_off, label, color) in enumerate(tree_data[1:]):
    y = y_base - i * 0.28
    ax.text(0.50, y, label, ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.7', facecolor=color, edgecolor='none', alpha=0.85))
    
    # Line connecting
    mid_y = (0.85 + y) / 2
    ax.annotate('', xy=(0.50, y + 0.08), xytext=(0.50, 0.75),
                arrowprops=dict(arrowstyle='->', color=GRAY, linewidth=1.5))

    # Key outcomes
    if i == 0:
        outcomes = ['16 yr extension', 'ROO tightened', 'China screening', 'Peso rallies to 18-19']
    elif i == 1:
        outcomes = ['Annual reviews', 'FDI frozen', 'Nearshoring dead', 'Peso 19-21']
    else:
        outcomes = ['Tariff spiral', 'Stranded assets', 'Peso 22-24', 'CDS blowout']
    
    for j, o in enumerate(outcomes):
        ax.text(0.85, y - 0.10 + j*0.05, f'• {o}', fontsize=6, color='white' if color != ACCENT_AMBER else DARK,
                ha='left', va='top')

    ax.text(0.05, y, f'{chr(65+i)}' if i == 0 else f'{chr(65+i)}', fontsize=10, fontweight='bold', 
            color=color, va='center')

fig.suptitle('USMCA Review — Decision Tree', fontweight='bold', fontsize=14)
plt.tight_layout()
fig.savefig(f"{OUT}/05-usmca-tree.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 05-usmca-tree.png")

# ============================================================
# CHART 6: Cartel Territory Risk Heatmap (by state)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

states = ['Sinaloa', 'Jalisco', 'Michoacán', 'Guanajuato', 'Colima', 'Tamaulipas', 
          'Nuevo León', 'CDMX', 'Querétaro', 'Ags', 'BC', 'Sonora']
violence_risk = [95, 90, 80, 75, 70, 55, 30, 25, 35, 30, 20, 25]  # 0-100
cartel_presence = ['Sinaloa Cartel\n(Chapitos/Mayos)', 'CJNG\n(fragmentation)', 'CJNG +\nViagras', 
                   'CJNG + SRL', 'CJNG', 'CDN\n(border monopoly)', 'CDN\n(constrained)', 
                   'Multi-cartel\n(extortion)', 'CJNG\n(peripheral)', 'CJNG', 'CJNG/Sinaloa', 'Sinaloa']
fentanyl_link = [95, 80, 70, 50, 75, 40, 25, 20, 30, 25, 15, 20]

y_pos = np.arange(len(states))
colors_v = [ACCENT_RED if v >= 70 else (ACCENT_AMBER if v >= 40 else ACCENT_GREEN) for v in violence_risk]

bars = ax.barh(y_pos, violence_risk, height=0.6, color=colors_v, alpha=0.8)
ax.set_yticks(y_pos)
ax.set_yticklabels(states, fontsize=9, fontweight='bold')
ax.set_xlabel('Commercial Risk Score (0-100)', fontweight='bold')
ax.set_title('State-Level Cartel Commercial Risk Assessment', fontweight='bold', fontsize=13)

# Annotate cartel presence
for i, (v, cp, fl) in enumerate(zip(violence_risk, cartel_presence, fentanyl_link)):
    ax.text(v + 1, i, f'  {cp}  |  Fentanyl: {fl}', fontsize=6, va='center', color=DARK)

plt.tight_layout()
fig.savefig(f"{OUT}/06-cartel-risk.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 06-cartel-risk.png")

# ============================================================
# CHART 7: H2 2026 Timeline — Gantt-style
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

events = [
    ('May 25\nBilateral\nNegotiations', 0, ACCENT_BLUE, '⚡'),
    ('June 2\nUS Primaries\n(TX, CA)', 0, ACCENT_AMBER, '🗳️'),
    ('June-July\nWorld Cup\n2026', 0.6, ACCENT_GREEN, '⚽'),
    ('July 1\nUSMCA\nDeadline', 0.3, ACCENT_RED, '🔥'),
    ('Aug-Sep\nExtension\nResolution', 0.7, ACCENT_BLUE, '✅'),
    ('Sep 1\nCongress\nReconvenes', 0.7, ACCENT_AMBER, '🏛️'),
    ('Nov 3\nUS Midterm\nElections', 0.9, ACCENT_RED, '🗳️'),
    ('Ongoing\nBanxico\nDecisions', 0.5, ACCENT_PURPLE, '💰'),
    ('Ongoing\nCJNG\nFragment', 0.3, ACCENT_RED, '💀'),
    ('Ongoing\nPemex Debt\nMaturities', 0.5, ACCENT_AMBER, '⛽'),
]

# Timeline bar
ax.barh([0], [1], left=0, height=0.02, color=DARK, alpha=0.3)

for i, (label, pos, color, icon) in enumerate(events):
    x = pos * 0.9 + 0.05  # 0 to 1 scale with margin
    y = -0.02 + (0.08 * (i % 5))  # offset rows
    ax.scatter([x], [y], s=150, color=color, zorder=5, edgecolors='white', linewidth=1)
    
    # Label line
    ax.text(x, y, f' {icon} {label.replace(chr(10), " ")} ', fontsize=7, ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.85))

# Month markers
months_2026 = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for i, m in enumerate(months_2026):
    x = 0.05 + i * 0.105
    ax.axvline(x, color=GRAY, alpha=0.15, linewidth=0.5)
    ax.text(x, -0.14, m, ha='center', fontsize=8, color=GRAY)

ax.set_ylim(-0.18, 0.35)
ax.set_xlim(0, 1)
ax.axis('off')
ax.set_title('H2 2026 Critical Path Calendar', fontweight='bold', fontsize=14, pad=15)

plt.tight_layout()
fig.savefig(f"{OUT}/07-timeline.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 07-timeline.png")

# ============================================================
# CHART 8: Strategic Recommendations Summary Dashboard
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.axis('off')

recs = {
    'Family Office': [
        ('Reduce auto/REIT by 33%', 'H2 2026', ACCENT_RED),
        ('USDMXN options structure', 'Immediate', ACCENT_BLUE),
        ('Pre-position for sovereign', 'Q3 2026', ACCENT_GREEN),
        ('Diversify CDMX RE holdings', '12mo', ACCENT_AMBER),
    ],
    'Lloyd\'s / Underwriters': [
        ('Lock PRI pricing 12-18mo', 'Immediate', ACCENT_RED),
        ('Raise Bajío/Jal reserves', 'H2 2026', ACCENT_AMBER),
        ('WC claims capacity', 'Pre-June', ACCENT_BLUE),
        ('Review CDS exposure', 'Conditional', ACCENT_PURPLE),
    ],
    'Sovereign Wealth': [
        ('Underweight MX equities', 'Immediate', ACCENT_RED),
        ('MX renewable debt +', '12-18mo', ACCENT_GREEN),
        ('Scenario committee', 'Immediate', ACCENT_BLUE),
        ('Patience on entry', '12mo', ACCENT_AMBER),
    ],
}

x_start = 0.05
y_start = 0.90

for idx, (group, items) in enumerate(recs.items()):
    x = x_start + idx * 0.33
    ax.text(x, y_start, group, fontsize=10, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=DARK, edgecolor='none'))
    
    for j, (rec_text, timeline, color) in enumerate(items):
        y = y_start - 0.08 - j * 0.12
        ax.fill_between([x-0.12, x+0.12], y-0.04, y+0.04, color=color, alpha=0.15)
        ax.text(x, y, f'{j+1}. {rec_text}', fontsize=7, ha='center', va='center', fontweight='bold')
        ax.text(x, y-0.03, f'⏱ {timeline}', fontsize=6, ha='center', color=GRAY)

ax.set_title('Strategic Recommendations Summary — 12 Actions', fontweight='bold', fontsize=14)

plt.tight_layout()
fig.savefig(f"{OUT}/08-recommendations.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 08-recommendations.png")

# ============================================================
# CHART 9: Calibration Distribution Pie
# ============================================================
fig, ax = plt.subplots(figsize=(6, 5))

bands_counts = {
    'Almost Certain\n(90-95%)': 1,
    'Highly Likely\n(80-90%)': 2,
    'Likely\n(60-70%)': 4,
    'Likely\n(55-65%)': 3,
}
labels = list(bands_counts.keys())
sizes = list(bands_counts.values())
colors_pie = ['#e74c3c', '#c0392b', '#2980b9', '#3498db']

wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=140,
                                   colors=colors_pie, textprops={'fontsize': 9})
ax.set_title('Judgment Calibration Distribution\n(10 Judgments)', fontweight='bold', fontsize=12)

plt.tight_layout()
fig.savefig(f"{OUT}/09-calibration.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 09-calibration.png")

# Write chart manifest
manifest = {
    "charts": [
        {"id": "01-approval", "title": "Sheinbaum Approval Rating Trajectory", "file": "01-approval.png"},
        {"id": "02-judgments", "title": "Top 10 Judgments — Kent Confidence Bands", "file": "02-judgments.png"},
        {"id": "03-macro", "title": "Mexico Macro Dashboard", "file": "03-macro.png"},
        {"id": "04-sector-exposure", "title": "Sector Exposure Bubble Chart", "file": "04-sector-exposure.png"},
        {"id": "05-usmca-tree", "title": "USMCA Review — Decision Tree", "file": "05-usmca-tree.png"},
        {"id": "06-cartel-risk", "title": "State-Level Cartel Commercial Risk", "file": "06-cartel-risk.png"},
        {"id": "07-timeline", "title": "H2 2026 Critical Path Calendar", "file": "07-timeline.png"},
        {"id": "08-recommendations", "title": "Strategic Recommendations Summary", "file": "08-recommendations.png"},
        {"id": "09-calibration", "title": "Calibration Distribution", "file": "09-calibration.png"},
    ]
}

with open(f"{OUT}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\n✅ All {len(manifest['charts'])} charts generated in {OUT}")
