#!/usr/bin/env python3
"""Build all remaining visual assets for the USMCA PDF."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pathlib, base64, datetime

OUT = pathlib.Path("memory/usmca-map")

# ============ (6) USDMXN Forecast Chart ============
dates = np.array([datetime.date(2026, 5, 18), datetime.date(2026, 6, 1), 
                   datetime.date(2026, 6, 15), datetime.date(2026, 7, 1),
                   datetime.date(2026, 7, 15), datetime.date(2026, 8, 1)])
x = mdates.date2num(dates)

# Scenario A: Extension 60-75% (most likely)
base_a = np.array([17.55, 17.60, 17.70, 17.80, 17.75, 17.65])
conf_a = np.array([0.30, 0.35, 0.40, 0.50, 0.40, 0.35])

# Scenario B: Selective tariffs 15-25%
base_b = np.array([17.55, 17.80, 18.20, 18.80, 19.00, 19.20])
conf_b = np.array([0.30, 0.50, 0.60, 0.70, 0.60, 0.50])

# Scenario C: Breakdown 5-15%
base_c = np.array([17.55, 18.00, 19.00, 20.50, 21.50, 22.00])
conf_c = np.array([0.30, 0.60, 0.80, 1.00, 1.00, 1.00])

fig, ax = plt.subplots(figsize=(7, 4))

colors = {'A': '#339933', 'B': '#cc9933', 'C': '#cc3333'}
labels = {'A': 'A: 90-day ext. (60-75%)', 'B': 'B: Select. tariffs (15-25%)', 'C': 'C: Breakdown (5-15%)'}

for k, base, conf in [('A', base_a, conf_a), ('B', base_b, conf_b), ('C', base_c, conf_c)]:
    ax.fill_between(x, base - conf, base + conf, alpha=0.15, color=colors[k])
    ax.plot(x, base, '-', color=colors[k], linewidth=2, label=labels[k])
    ax.plot(x[-1], base[-1], 'o', color=colors[k], markersize=6)

ax.axvline(x=mdates.date2num(datetime.date(2026, 7, 1)), color='#e94560', linestyle='--', linewidth=1, alpha=0.7)
ax.text(mdates.date2num(datetime.date(2026, 7, 5)), 22.5, 'July 1\nDeadline', fontsize=8, color='#e94560')

ax.set_title('USDMXN Forecast — Kent-Calibrated Scenario Bands', fontsize=12, fontweight='bold', color='#0f3460')
ax.set_ylabel('USDMXN Spot Rate', fontsize=9)
ax.set_xlabel('Date (2026)', fontsize=9)
ax.legend(fontsize=7, loc='upper left')
ax.set_ylim(16.5, 23.5)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.tick_params(labelsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT / 'usdmxn_forecast.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ USDMXN forecast chart saved")

# ============ (7) Mermaid Decision Tree ============
mermaid_dt = """graph TD
    A[USMCA Review<br/>July 1, 2026] --> B{Key Tipping Indicators}
    B --> C1[USTR requests<br/>more data]
    B --> C2[Trump tariff<br/> threat tweet]
    B --> C3[Ebrard<br/>concession offer]
    B --> C4[Sheinbaum<br/>hardline speech]
    C1 --> D[Extension Path<br/>60-75%]
    C2 --> E[Confrontation<br/>Path 15-25%]
    C3 --> D
    C4 --> E
    D --> F1[90-Day Extension]
    D --> F2[180-Day Extension]
    E --> G1[Selective<br/>Auto Tariffs 5-10%]
    E --> G2[Migration<br/>Sanctions]
    E --> G3[Energy Market<br/>Concessions]
    G1 --> H[Full Breakdown<br/>5-15%]
    G2 --> H
    G3 --> H
    
    style A fill:#0f3460,color:#fff,stroke:#0f3460
    style D fill:#339933,color:#fff,stroke:#339933
    style E fill:#cc9933,color:#fff,stroke:#cc9933
    style H fill:#cc3333,color:#fff,stroke:#cc3333
"""

(OUT / 'decision_tree_full.mermaid').write_text(mermaid_dt)
print("✅ Full decision tree saved")

# Try to render mermaid to SVG
import subprocess, shutil
mermaid_cmd = shutil.which('npx') or shutil.which('mmdc')
if mermaid_cmd:
    try:
        subprocess.run(['npx', '@mermaid-js/mermaid-cli', '-i', str(OUT/'decision_tree_full.mermaid'),
                       '-o', str(OUT/'decision_tree_full.png'), '--backgroundColor', 'white'],
                      capture_output=True, timeout=30)
        print("✅ Decision tree rendered to PNG")
    except:
        print("⚠️  Mermaid render failed — will embed as text")

# ============ (8) Watch Indicator Dashboard ============
fig, ax = plt.subplots(figsize=(7, 3))
ax.axis('tight')
ax.axis('off')

watch_data = [
    ['🔴 Kalshi >9% strike price', '$0.13 (13%)', '<$0.08 = bullish', '>$0.20 = tariff risk', 'Weekly'],
    ['🟡 State mfg PMI data', 'April: 51.2', '<50 contraction', '>52 expansion', 'Monthly'],
    ['🟢 Ebrard US visit', 'Mid-June', 'No meeting = bearish', 'Joint statement = bullish', 'Ongoing'],
    ['🟡 Trump tariff tweet', 'Daily monitor', 'No mention in 30d = bullish', 'New threat = bearish', 'Daily'],
    ['🔴 USMCA review deadline', 'July 1, 2026', 'Extension filed = bullish', 'No action = bearish', 'Imminent'],
]

table = ax.table(cellText=watch_data,
                 colLabels=['Indicator', 'Current', 'Upgrade', 'Downgrade', 'Cadence'],
                 cellLoc='left', loc='center', fontsize=7)
table.auto_set_font_size(False)
table.set_fontsize(7)
table.scale(1, 1.3)

for key, cell in table.get_celld().items():
    if key[0] == 0:
        cell.set_facecolor('#0f3460')
        cell.set_text_props(color='white', fontweight='bold', fontsize=7)
    elif key[0] % 2 == 1:
        cell.set_facecolor('#f5f5f5')

plt.tight_layout()
plt.savefig(OUT / 'watch_dashboard.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ Watch dashboard saved")

# ============ (10) Calendar Visualization ============
calendar_events = [
    ('May 18', 'Assessment produced', 'baseline'),
    ('May 20', 'Banxico minutes release', 'important'),
    ('Jun 1', 'USTR preliminary report', 'important'),
    ('Jun 15', 'Ebrard expected US visit', 'critical'),
    ('Jun 20', 'Banxico rate decision', 'important'),
    ('Jun 25', 'Last USMCA working group', 'critical'),
    ('Jul 1', 'USMCA REVIEW DEADLINE', 'deadline'),
]

fig, ax = plt.subplots(figsize=(7, 3.5))

y_pos = range(len(calendar_events))
colors_cal = {'baseline': '#999999', 'important': '#cc9933', 'critical': '#cc6633', 'deadline': '#cc3333'}
markers = {'baseline': 'o', 'important': 's', 'critical': 'D', 'deadline': '*'}

for i, (date, event, cat) in enumerate(calendar_events):
    ax.plot(0, i, marker=markers[cat], color=colors_cal[cat], markersize=10, 
            markeredgecolor='white', markeredgewidth=1)
    ax.text(1.5, i, f'{date} — {event}', va='center', fontsize=9, color=colors_cal[cat],
            fontweight='bold' if cat in ('critical', 'deadline') else 'normal')

ax.set_xlim(-1, 12)
ax.set_ylim(-0.5, len(calendar_events) - 0.5)
ax.set_title('USMCA Review — Calendar to July 1 Deadline', fontsize=12, fontweight='bold', color='#0f3460')
ax.axis('off')

legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#999999', label='Baseline'),
    plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#cc9933', label='Important'),
    plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='#cc6633', label='Critical'),
    plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#cc3333', label='Deadline', markersize=10),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=7, ncol=4)

plt.tight_layout()
plt.savefig(OUT / 'calendar_viz.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ Calendar visualization saved")

print("\n=== All USMCA visual assets complete ===")
for f in sorted(OUT.iterdir()):
    size = f.stat().st_size if f.is_file() else 0
    print(f"  {f.name:35s} {size:>8,} bytes")
