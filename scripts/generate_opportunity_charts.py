#!/usr/bin/env python3
"""Generate charts for the Mexico Opportunity Landscape report."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json, os

OUT = "/home/ubuntu/.openclaw/workspace/exports/opportunity-charts"
os.makedirs(OUT, exist_ok=True)

DARK = '#1a1a2e'
RED = '#c0392b'
BLUE = '#2980b9'
GREEN = '#27ae60'
AMBER = '#f39c12'
PURPLE = '#8e44ad'
GRAY = '#7f8c8d'
LIGHT = '#f8f9fa'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.facecolor': LIGHT,
    'figure.facecolor': 'white',
    'axes.edgecolor': DARK,
    'axes.grid': True,
    'grid.alpha': 0.3,
})

# ============================================================
# CHART 1: Market Opportunity Sizing (Investment)
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5))

sectors = ['Energy\nInfra', 'Industrial\nReal Estate', 'C&I Solar\nPPAs', 'Sovereign\nDuration', 'Medical\nDevices', 'Aerospace\nCluster']
usd_size = [20, 12, 4.75, 8, 25, 3]  # $bn total addressable
risk_score = [25, 45, 20, 50, 15, 20]  # USMCA/execution risk 0-100
time_horizon = [24, 18, 12, 6, 24, 36]  # months to realize

# Bubble: size = addressable market, color = risk
sizes = [min(v * 8, 120) for v in usd_size]

colors_s = []
for r in risk_score:
    if r >= 40: colors_s.append(AMBER)
    elif r >= 25: colors_s.append(GREEN)
    else: colors_s.append(GREEN)

ax.scatter(risk_score, time_horizon, s=sizes, c=colors_s, alpha=0.7, edgecolors=DARK, linewidth=0.8)

for i, (x, y, s, label) in enumerate(zip(risk_score, time_horizon, sizes, sectors)):
    offset_x = 2 if i % 2 == 0 else -2
    ax.annotate(label, (x, y), fontsize=8, ha='center', va='center', fontweight='bold',
                color='white', bbox=dict(boxstyle='round,pad=0.2', facecolor=DARK, alpha=0.6))

# Legend for size
legend_vals = [
    mpatches.Circle((0,0), 8, facecolor=GRAY, alpha=0.4, label='<$5bn'),
    mpatches.Circle((0,0), 20, facecolor=GRAY, alpha=0.4, label='$5-15bn'),
    mpatches.Circle((0,0), 35, facecolor=GRAY, alpha=0.4, label='>$15bn'),
]
ax.legend(handles=legend_vals, loc='upper right', fontsize=7, title='Market Size', title_fontsize=8)

ax.set_xlabel('Execution / USMCA Risk (0-100)', fontweight='bold')
ax.set_ylabel('Time Horizon (months)', fontweight='bold')
ax.set_title('Investment Opportunity Map — Size × Risk × Timing', fontweight='bold', fontsize=13)
ax.set_xlim(-5, 65)
ax.set_ylim(0, 45)

plt.tight_layout()
fig.savefig(f"{OUT}/01-investment-map.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 01-investment-map.png")

# ============================================================
# CHART 2: Security Company Opportunity Sizing
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

verticals = ['Cargo &\nLogistics\nSecurity', 'Cybersecurity\nServices', 'Industrial\nFacility\nSecurity', 'Executive\nProtection', 'C&I Solar\nSecurity', 'Border/Freight\nTech']
est_mkt = [350, 3900, 500, 150, 80, 200]  # $M current
growth_rate = [14, 8.9, 10, 12, 15, 25]  # CAGR %
supply_gap = [40, 25, 60, 35, 50, 45]  # undersupply estimate %

x = np.arange(len(verticals))
width = 0.35

bars1 = ax.bar(x - width/2, est_mkt, width, color=BLUE, alpha=0.8, label='Est. Current Market ($M)')
ax2 = ax.twinx()
bars2 = ax2.bar(x + width/2, growth_rate, width, color=RED, alpha=0.7, label='Growth Rate (CAGR %)')

ax.set_xticks(x)
ax.set_xticklabels(verticals, fontsize=8)
ax.set_ylabel('Market Size ($M USD)', fontweight='bold', color=BLUE)
ax2.set_ylabel('CAGR (%)', fontweight='bold', color=RED)

ax.legend(loc='upper left', fontsize=8)
ax2.legend(loc='upper right', fontsize=8)
ax.set_title('Security Company Opportunity — Market Size × Growth Rate', fontweight='bold', fontsize=13)

# Annotate supply gap
for i, gap in enumerate(supply_gap):
    ax.annotate(f'Supply gap:\n~{gap}%', (x[i], est_mkt[i] + 50), fontsize=6, ha='center', color=DARK,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

plt.tight_layout()
fig.savefig(f"{OUT}/02-security-opportunity.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 02-security-opportunity.png")

# ============================================================
# CHART 3: Cybersecurity Sub-Segment Breakdown
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5))

sub_segments = ['Zero-Trust\nArchitecture', 'OT/ICS\nSecurity', 'Supply Chain\nAudits', 'Managed\nDetection (MDR)', 'Identity &\nAccess Mgmt']
sub_growth = [9.5, 8.5, 7.2, 10.1, 8.2]  # CAGR %
sub_size = [850, 450, 320, 600, 520]  # $M projected 2027

ax.barh(range(len(sub_segments)), sub_size, color=[BLUE, PURPLE, GREEN, AMBER, RED], alpha=0.8)
ax.set_yticks(range(len(sub_segments)))
ax.set_yticklabels(sub_segments, fontsize=9, fontweight='bold')
ax.set_xlabel('Projected 2027 Market Size ($M)', fontweight='bold')
ax.set_title('Mexico Cybersecurity Sub-Segments: Opportunity Sizing', fontweight='bold', fontsize=12)

for i, (v, g) in enumerate(zip(sub_size, sub_growth)):
    ax.text(v + 15, i, f'CAGR {g:.1f}%', fontsize=8, va='center', color=DARK)

plt.tight_layout()
fig.savefig(f"{OUT}/03-cybersecurity-breakdown.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 03-cybersecurity-breakdown.png")

# ============================================================
# CHART 4: Portfolio Action Timeline
# ============================================================
fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('off')

actions = {
    'Investors': [
        ('Conditional MBONO entry', 'Q2-Q3\n2026', '6mo', BLUE),
        ('Bajío/ML build-to-suit', 'H2\n2026', '18mo', BLUE),
        ('C&I solar PPA portfolio', '12mo\nbuild', '24mo+', GREEN),
        ('MIP co-investment relationship', 'Q3\n2026', '36mo', PURPLE),
        ('Medical devices overweight', 'Now', '36mo', GREEN),
    ],
    'Security Firms': [
        ('Zero-Trust / OT practice', 'Immediate', '36mo+', RED),
        ('Cargo security division', 'H2\n2026', '24mo', RED),
        ('Industrial park security', '12mo\nbuild', '36mo', AMBER),
        ('USMCA compliance-as-service', '18mo\nbuild', '36mo+', PURPLE),
        ('World Cup security capacity', 'Pre-June\n2026', '2mo', AMBER),
    ],
}

y = 0.75
for label, items in actions.items():
    ax.text(0.02, y, label, fontsize=11, fontweight='bold', va='center',
            bbox=dict(boxstyle='round', facecolor=DARK, edgecolor='none'))
    
    for i, (action, start, duration, color) in enumerate(items):
        x_start = 0.20 + i * 0.16
        ax.barh(y, 0.12, left=x_start, height=0.10, color=color, alpha=0.8)
        ax.text(x_start + 0.06, y, action, fontsize=6, ha='center', va='center', color='white', fontweight='bold')
        ax.text(x_start + 0.06, y - 0.06, f'{start}', fontsize=5, ha='center', color=GRAY)
    
    y -= 0.20

# Time axis
for i, m in enumerate(['Now', 'H2 2026', '2027', '2028+']):
    x = 0.20 + i * 0.20
    ax.text(x, 0.90, m, fontsize=8, ha='center', color=DARK, fontweight='bold')

ax.set_xlim(0, 1)
ax.set_ylim(0, 0.95)
ax.set_title('Portfolio Action Timeline — Recommended Sequencing', fontweight='bold', fontsize=13, pad=5)

plt.tight_layout()
fig.savefig(f"{OUT}/04-timeline-actions.png", dpi=200, bbox_inches='tight')
plt.close()
print("✅ 04-timeline-actions.png")

# Write manifest
manifest = {"charts": [
    {"id": "01-investment-map", "title": "Investment Opportunity Map", "file": "01-investment-map.png"},
    {"id": "02-security-opportunity", "title": "Security Company Opportunity", "file": "02-security-opportunity.png"},
    {"id": "03-cybersecurity-breakdown", "title": "Cybersecurity Sub-Segments", "file": "03-cybersecurity-breakdown.png"},
    {"id": "04-timeline-actions", "title": "Portfolio Action Timeline", "file": "04-timeline-actions.png"},
]}
with open(f"{OUT}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\n✅ {len(manifest['charts'])} charts generated")
