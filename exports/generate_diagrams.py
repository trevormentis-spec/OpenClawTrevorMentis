"""Generate analytical diagrams for TREVOR assessment using matplotlib."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"

def scenario_flow():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('#1a1a2e')

    nodes = [
        (7, 9.0, "Operation Epic Fury\nCurrent Posture", '#3498db'),
        (7, 7.0, "Trump Decision Point\n(Next 48h)", '#e74c3c'),
        (3, 5.0, "Option A: Renewed\nKinetic Operations", '#e67e22'),
        (7, 5.0, "Option B: Sustained\nBlockade Only", '#f39c12'),
        (11, 5.0, "Option C: Diplomatic\nOff-Ramp", '#27ae60'),
        (1, 3.0, "Ground Intervention\n/ Iran Retaliation", '#c0392b'),
        (7, 3.0, "Protracted\nRegional Standoff", '#e67e22'),
        (11, 3.0, "Maritime Freedom\nConstruct Coalition", '#2980b9'),
        (2, 1.0, "Regional Escalation\n400+ Militia Strikes", '#e74c3c'),
        (10, 1.0, "Partial Stabilization\nOil $90-100/bbl", '#27ae60'),
    ]

    for x, y, label, color in nodes:
        box = FancyBboxPatch((x-1.5, y-0.35), 3.0, 0.7,
                             facecolor=color, edgecolor='white', linewidth=2, alpha=0.85,
                             boxstyle="round,pad=0.1")
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    edges = [
        (7, 8.6, 7, 7.4), (7, 6.6, 3, 5.4), (7, 6.6, 7, 5.4),
        (7, 6.6, 11, 5.4), (3, 4.6, 1, 3.4), (3, 4.6, 7, 3.4),
        (3, 4.6, 2, 1.4), (7, 4.6, 7, 3.4), (11, 4.6, 11, 3.4),
        (10, 2.6, 10, 1.4),
    ]
    for x1, y1, x2, y2 in edges:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2, alpha=0.7))

    ax.set_title("Operation Epic Fury — Scenario Decision Tree", fontsize=14, fontweight='bold', color='white', pad=20)
    plt.savefig(f"{OUTPUT}/scenario-flow.png", dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print("  ✅ scenario-flow.png")


def threat_quadrant():
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.3)
    ax.fill_between([0, 0.5], 0.5, 1, alpha=0.08, color='#e74c3c')
    ax.fill_between([0.5, 1], 0.5, 1, alpha=0.08, color='#e67e22')
    ax.fill_between([0, 0.5], 0, 0.5, alpha=0.08, color='#27ae60')
    ax.fill_between([0.5, 1], 0, 0.5, alpha=0.08, color='#3498db')

    ax.text(0.25, 0.95, "Watch List", ha='center', fontsize=11, fontweight='bold', color='#e74c3c', alpha=0.6)
    ax.text(0.75, 0.95, "High Priority", ha='center', fontsize=11, fontweight='bold', color='#e67e22', alpha=0.6)
    ax.text(0.25, 0.05, "Low Priority", ha='center', fontsize=11, fontweight='bold', color='#27ae60', alpha=0.6)
    ax.text(0.75, 0.05, "Capable Adversaries", ha='center', fontsize=11, fontweight='bold', color='#3498db', alpha=0.6)

    actors = [
        ('Iran', 0.88, 0.92, '#e74c3c', 220),
        ('Hezbollah', 0.65, 0.82, '#c0392b', 160),
        ('Iraqi Militias', 0.58, 0.88, '#e67e22', 180),
        ('Houthis', 0.48, 0.72, '#f39c12', 140),
        ('China (SCS)', 0.92, 0.52, '#3498db', 200),
        ('Russia', 0.82, 0.42, '#8e44ad', 180),
        ('Cyber APTs', 0.78, 0.62, '#1abc9c', 160),
        ('ISIS-K', 0.32, 0.68, '#95a5a6', 120),
    ]
    for name, x, y, color, size in actors:
        ax.scatter(x, y, s=size, c=color, alpha=0.8, edgecolors='white', linewidth=2, zorder=5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 12),
                   ha='center', fontsize=9, fontweight='bold', color='white')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Capability →", fontsize=12, fontweight='bold', color='white')
    ax.set_ylabel("Intent →", fontsize=12, fontweight='bold', color='white')
    ax.set_title("Threat Actor Assessment — Intent × Capability", fontsize=14, fontweight='bold', color='white')
    ax.tick_params(colors='white')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color('white')

    plt.savefig(f"{OUTPUT}/threat-quadrant.png", dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print("  ✅ threat-quadrant.png")


def timeline_chart():
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    events = [
        ("Feb 2026", "Initial US-Israeli strikes begin", '#3498db'),
        ("Mar 2026", "Bushehr shut down / Hormuz closure", '#e67e22'),
        ("Apr 2026", "Ceasefire / Blockade formalized", '#f39c12'),
        ("1 May 2026", "Trump briefed / Brent $124.67", '#e74c3c'),
        ("Next 48h", "Ceasefire decision point", '#c0392b'),
        ("Next 7d", "Beijing summit / Coalition push", '#2980b9'),
        ("Next 30d", "Protracted standoff risk phase", '#8e44ad'),
    ]

    for i, (date, desc, color) in enumerate(events):
        ax.barh(i, 1, left=i, height=0.5, color=color, alpha=0.8, edgecolor='white', linewidth=1)
        ax.text(i + 0.5, i + 0.15, f"  {date}", ha='left', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(i + 0.5, i - 0.15, f"  {desc}", ha='left', va='top', fontsize=7.5, color='#bdc3c7')

    ax.set_ylim(-0.5, len(events) - 0.5)
    ax.invert_yaxis()
    ax.set_title("Operation Epic Fury — Event Timeline", fontsize=14, fontweight='bold', color='white')
    ax.axis('off')
    plt.savefig(f"{OUTPUT}/timeline.png", dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print("  ✅ timeline.png")


def iw_dashboard():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.patch.set_facecolor('#1a1a2e')

    categories = [
        ("Escalation Track", [
            ("IRGC Leadership\nSignals", 0.9, '#e74c3c'),
            ("Militia Strike\nFrequency", 0.85, '#e74c3c'),
            ("Naval Movement\nHormuz", 0.55, '#f39c12'),
            ("Diplomatic\nStatus", 0.25, '#e67e22'),
        ]),
        ("De-escalation Track", [
            ("Direct\nNegotiations", 0.05, '#27ae60'),
            ("Oil Price\nTrend", 0.1, '#c0392b'),
            ("Blockade\nRelaxation", 0.05, '#27ae60'),
            ("Iran Moderation\nSignals", 0.08, '#27ae60'),
        ]),
        ("Instability Track", [
            ("Iraqi Political\nFracture", 0.8, '#e74c3c'),
            ("Red Sea Houthi\nActivation", 0.45, '#f39c12'),
            ("Cyber Attack\nFrequency", 0.75, '#e74c3c'),
            ("Gulf Alignment\nShifts", 0.5, '#f39c12'),
        ]),
    ]

    for idx, (title, indicators) in enumerate(categories):
        ax = axes[idx]
        ax.set_facecolor('#1a1a2e')
        names = [i[0] for i in indicators]
        values = [i[1] for i in indicators]
        colors = [i[2] for i in indicators]

        bars = ax.barh(names, values, color=colors, alpha=0.85, edgecolor='white', linewidth=1, height=0.6)
        ax.set_xlim(0, 1)
        ax.set_title(title, fontsize=11, fontweight='bold', color='white', pad=10)
        ax.tick_params(colors='white', labelsize=8)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('white')
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(['None', 'Low', 'Moderate', 'High', 'Critical'], fontsize=7)
        ax.axvline(x=0.33, color='#27ae60', linestyle='--', alpha=0.3, linewidth=1)
        ax.axvline(x=0.66, color='#f39c12', linestyle='--', alpha=0.3, linewidth=1)

        for bar, val in zip(bars, values):
            x_pos = val - 0.05 if val > 0.3 else val + 0.02
            ha = 'right' if val > 0.3 else 'left'
            ax.text(x_pos, bar.get_y() + bar.get_height()/2,
                   f'{val:.0%}', ha=ha, va='center', fontsize=8, fontweight='bold',
                   color='white' if val > 0.3 else '#bdc3c7')

    plt.suptitle("Indicators & Warnings Dashboard — 1 May 2026", fontsize=14, fontweight='bold', color='white', y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/iw-dashboard.png", dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print("  ✅ iw-dashboard.png")


def oil_price_chart():
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    prices = [76, 82, 98, 112, 124.67]
    colors = ['#3498db', '#3498db', '#e67e22', '#e74c3c', '#c0392b']

    bars = ax.bar(months, prices, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5, width=0.5)
    for bar, price in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'${price:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='white')

    ax.set_ylabel('Brent Crude ($/bbl)', fontsize=10, fontweight='bold', color='white')
    ax.set_title('Oil Price Trajectory — 2025-2026 Crisis', fontsize=12, fontweight='bold', color='white')
    ax.tick_params(colors='white')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color('white')
    ax.spines['bottom'].set_color('#2c3e50')
    ax.spines['left'].set_color('#2c3e50')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.annotate('Strikes Begin', xy=(1, 82), xytext=(0.3, 90),
               arrowprops=dict(arrowstyle='->', color='#e67e22', lw=2, alpha=0.8),
               fontsize=8, color='#e67e22', fontweight='bold')
    ax.annotate('Hormuz Closure', xy=(3, 112), xytext=(3.5, 118),
               arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2, alpha=0.8),
               fontsize=8, color='#e74c3c', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/oil-price-chart.png", dpi=200, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print("  ✅ oil-price-chart.png")


if __name__ == "__main__":
    os.makedirs(OUTPUT, exist_ok=True)
    scenario_flow()
    threat_quadrant()
    timeline_chart()
    iw_dashboard()
    oil_price_chart()
    print(f"\nAll diagrams saved to {OUTPUT}/")
