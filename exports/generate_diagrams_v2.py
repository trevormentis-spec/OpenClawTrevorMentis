"""Financial Times-style diagrams for TREVOR assessment."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"

# FT Color Palette
FT_CREAM = '#F5F3EF'
FT_RED = '#C0392B'
FT_BLUE = '#1B3A5C'
FT_GOLD = '#B8860B'
FT_GREEN = '#2E7D32'
FT_ORANGE = '#E67E22'
FT_GREY = '#6B6B6B'
FT_LIGHT_GREY = '#999999'
FT_TEXT = '#222222'
FT_GRID = '#E0DCD4'
FT_BORDER = '#D5CCC0'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7,
    'figure.facecolor': FT_CREAM,
    'axes.facecolor': FT_CREAM,
    'axes.edgecolor': FT_BORDER,
    'axes.linewidth': 0.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'savefig.facecolor': FT_CREAM,
    'savefig.dpi': 300,
})


def add_title(ax, title, subtitle='', source=''):
    """FT-style title block."""
    ax.text(0, 1.08, title, transform=ax.transAxes, fontsize=11, fontweight='bold',
            color=FT_TEXT, ha='left', va='bottom')
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=7,
                color=FT_LIGHT_GREY, ha='left', va='bottom')
    if source:
        ax.text(0, -0.12, source, transform=ax.transAxes, fontsize=5.5,
                fontstyle='italic', color=FT_LIGHT_GREY, ha='left', va='top')


def diagram_timeline():
    """Clean timeline — FT style."""
    fig, ax = plt.subplots(figsize=(10, 3.5))
    add_title(ax, 'Operation Epic Fury — Event Timeline', 'February — May 2026')

    events = [
        ('Feb 2026', 'US-Israeli strikes begin\nBushehr nuclear plant shut'),
        ('Mar 2026', 'Senate resolution defeated\nHormuz closure begins'),
        ('Apr 2026', 'Ceasefire declared\nMaritime blockade formalized'),
        ('1 May 2026', 'Trump briefed on options\nBrent crude $124.67'),
        ('Next 48h', 'Ceasefire decision\npoint'),
        ('Next 7d', 'Beijing summit\nMaritime coalition push'),
    ]

    colors = [FT_BLUE, FT_ORANGE, FT_GOLD, FT_RED, '#8E44AD', FT_BLUE]
    y = 0

    for i, (date, desc) in enumerate(events):
        x = i * 1.6
        # Timeline node
        ax.scatter(x, y, s=60, c=colors[i], edgecolors='white', linewidth=1.5, zorder=5)
        # Label above
        ax.text(x, y + 0.25, date, ha='center', va='bottom', fontsize=7,
               fontweight='bold', color=colors[i])
        # Description below
        ax.text(x, y - 0.25, desc, ha='center', va='top', fontsize=6.5,
               color=FT_GREY)
        # Connecting line
        if i < len(events) - 1:
            ax.plot([x + 0.2, x + 1.3], [y, y], color=FT_BORDER, linewidth=1.5, zorder=1)

    ax.set_ylim(-1.2, 0.8)
    ax.set_xlim(-0.5, len(events) * 1.6 - 0.5)
    ax.axis('off')
    plt.subplots_adjust(left=0.05, right=0.95, top=0.8, bottom=0.1)
    plt.savefig(f"{OUTPUT}/timeline.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ timeline.png")


def diagram_iw_dashboard():
    """I&W dashboard — FT style bar charts."""
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.5))

    categories = [
        ('Escalation Track', [
            ('IRGC Leadership Signals', 0.92, FT_RED),
            ('Militia Strike Frequency', 0.87, FT_RED),
            ('Naval Activity Hormuz', 0.58, FT_ORANGE),
            ('Diplomatic Channel Status', 0.22, FT_GREEN),
        ]),
        ('De-escalation Track', [
            ('Direct Negotiations', 0.05, FT_GREEN),
            ('Oil Price Decline\n(7-day trend)', 0.08, FT_RED),
            ('Blockade Relaxation\nSignals', 0.03, FT_GREEN),
            ('Iran Moderation\nSignals', 0.06, FT_GREEN),
        ]),
        ('Instability Track', [
            ('Iraqi Political\nFracture', 0.82, FT_RED),
            ('Houthi Red Sea\nActivation Risk', 0.42, FT_ORANGE),
            ('Cyber Attack\nFrequency (MENA)', 0.78, FT_RED),
            ('Gulf State\nAlignment Shifts', 0.48, FT_ORANGE),
        ]),
    ]

    for idx, (title, indicators) in enumerate(categories):
        ax = axes[idx]
        names = [i[0] for i in indicators]
        values = [i[1] for i in indicators]
        colors = [i[2] for i in indicators]

        bars = ax.barh(names, values, color=colors, alpha=0.8, height=0.55, edgecolor='white', linewidth=0.5)
        ax.set_xlim(0, 1)
        ax.set_title(title, fontsize=9, fontweight='bold', color=FT_TEXT, pad=8)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(['None', 'Low', 'Moderate', 'High', 'Critical'], fontsize=6)
        ax.tick_params(axis='y', labelsize=6.5, colors=FT_GREY)
        ax.tick_params(axis='x', labelsize=5.5, colors=FT_LIGHT_GREY)
        ax.spines['bottom'].set_color(FT_BORDER)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_color(FT_BORDER)
        ax.spines['left'].set_linewidth(0.5)
        ax.yaxis.set_tick_params(length=0)
        ax.xaxis.set_tick_params(length=2)

        for bar, val in zip(bars, values):
            if val > 0.3:
                ax.text(val - 0.02, bar.get_y() + bar.get_height()/2,
                       f'{val:.0%}', ha='right', va='center', fontsize=6, fontweight='bold', color='white')
            else:
                ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                       f'{val:.0%}', ha='left', va='center', fontsize=6, color=FT_GREY)

    plt.suptitle('Indicators & Warnings Dashboard — 1 May 2026', fontsize=11, fontweight='bold',
                 color=FT_TEXT, y=1.02, ha='center')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT}/iw-dashboard.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ iw-dashboard.png")


def diagram_oil_price():
    """Oil price chart — FT style."""
    fig, ax = plt.subplots(figsize=(7, 4))
    add_title(ax, 'Brent Crude Oil Price — Trajectory',
             'Monthly average · July 2025 — May 2026',
             'Sources: EIA, S&P Global Platts')

    months = ['Jul\n25', 'Sep', 'Nov', 'Jan\n26', 'Mar', 'May']
    prices = [72, 75, 78, 82, 98, 124.67]
    bar_colors = ['#1B3A5C'] * 2 + ['#E67E22'] * 2 + ['#C0392B'] * 2

    bars = ax.bar(range(len(months)), prices, color=bar_colors, alpha=0.85,
                  width=0.6, edgecolor='white', linewidth=1)

    for i, (bar, price) in enumerate(zip(bars, prices)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'${price:.1f}', ha='center', va='bottom', fontsize=7,
               fontweight='bold', color=bar_colors[i])

    # Event markers
    events = [(2.5, 'Strikes\nbegin', '#E67E22'), (4.5, 'Hormuz\nclosure', '#C0392B')]
    for x, label, color in events:
        ax.axvline(x=x, color=color, linewidth=0.8, linestyle='--', alpha=0.5)
        ax.text(x, 115, label, ha='center', va='bottom', fontsize=6,
               color=color, fontweight='bold')

    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, fontsize=6.5, color=FT_GREY)
    ax.set_ylabel('$/barrel', fontsize=7, color=FT_GREY)
    ax.tick_params(axis='y', labelsize=6.5, colors=FT_GREY)
    ax.spines['bottom'].set_color(FT_BORDER)
    ax.spines['left'].set_color(FT_BORDER)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.spines['left'].set_linewidth(0.5)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.15)
    plt.savefig(f"{OUTPUT}/oil-price-chart.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ oil-price-chart.png")


def diagram_scenario():
    """Scenario flowchart — FT minimal style."""
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Title at top
    ax.text(5, 6.8, 'Operation Epic Fury — Scenario Pathways', fontsize=11, fontweight='bold',
           color=FT_TEXT, ha='center', va='center')

    # Decision tree - clean, compact
    nodes = [
        (5, 6.0, 'Current Posture\nCeasefire + Blockade', '#1B3A5C'),
        (5, 4.8, 'Trump Decision\nPoint', '#C0392B'),
        (2, 3.4, 'Option A:\nRenewed Strikes', '#E67E22'),
        (5, 3.4, 'Option B:\nSustained Blockade', '#B8860B'),
        (8, 3.4, 'Option C:\nDiplomatic Off-Ramp', '#2E7D32'),
        (0.5, 2.0, 'Escalation\nIran Retaliation', '#C0392B'),
        (5, 2.0, 'Protracted\nStandoff', '#E67E22'),
        (8, 2.0, 'Coalition\nBuilding', '#1B3A5C'),
        (1.5, 0.8, 'Regional Crisis\nRisk: HIGH', '#C0392B'),
        (5, 0.8, 'Extended Pressure\nRisk: MODERATE', '#B8860B'),
        (8, 0.8, 'De-escalation\nRisk: LOW', '#2E7D32'),
    ]

    for x, y, label, color in nodes:
        ax.text(x, y, label, ha='center', va='center', fontsize=6.5,
               color='white', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.35', facecolor=color, edgecolor='white', linewidth=0.5))

    # Connecting lines
    edges = [(5, 5.75, 5, 5.15), (5, 4.45, 2, 3.7), (5, 4.45, 5, 3.7),
             (5, 4.45, 8, 3.7), (2, 3.05, 0.5, 2.3), (2, 3.05, 5, 2.3),
             (5, 3.05, 5, 2.3), (8, 3.05, 8, 2.3),
             (0.5, 1.65, 1.5, 1.1), (5, 1.65, 5, 1.1), (8, 1.65, 8, 1.1)]
    for x1, y1, x2, y2 in edges:
        ax.plot([x1, x2], [y1, y2], color=FT_BORDER, linewidth=1, zorder=1)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.savefig(f"{OUTPUT}/scenario-flow.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ scenario-flow.png")


def diagram_threat_quadrant():
    """Threat quadrant — FT clean style."""
    fig, ax = plt.subplots(figsize=(8.5, 7.5))
    add_title(ax, 'Threat Actor Assessment — Intent × Capability',
             'Bubble size = relative threat weight · 1 May 2026')

    # Quadrant lines
    ax.axhline(y=0.5, color=FT_GRID, linewidth=0.5)
    ax.axvline(x=0.5, color=FT_GRID, linewidth=0.5)

    # Quadrant labels
    for x, y, label, color in [(0.25, 0.95, 'Watch List', FT_RED),
                                 (0.75, 0.95, 'High Priority', '#E67E22'),
                                 (0.25, 0.05, 'Low Priority', FT_GREEN),
                                 (0.75, 0.05, 'Capable Adversaries', FT_BLUE)]:
        ax.text(x, y, label, ha='center', fontsize=8, fontweight='bold', color=color, alpha=0.5)

    # Actors
    actors = [
        ('Iran', 0.88, 0.92, FT_RED, 250),
        ('Hezbollah', 0.65, 0.82, '#E67E22', 180),
        ('Iraqi Militias', 0.58, 0.88, '#D35400', 200),
        ('Houthis', 0.48, 0.72, '#B8860B', 140),
        ('China (SCS)', 0.92, 0.52, FT_BLUE, 220),
        ('Russia', 0.82, 0.42, '#8E44AD', 190),
        ('Cyber APTs', 0.78, 0.62, '#1ABC9C', 170),
        ('ISIS-K', 0.32, 0.68, FT_GREY, 110),
    ]

    for name, x, y, color, size in actors:
        ax.scatter(x, y, s=size, c=color, alpha=0.8, edgecolors='white', linewidth=1.5, zorder=5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 10),
                   ha='center', fontsize=7, fontweight='bold', color=FT_TEXT)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Capability →', fontsize=8, color=FT_GREY, labelpad=6)
    ax.set_ylabel('Intent →', fontsize=8, color=FT_GREY, labelpad=6)
    ax.tick_params(colors=FT_LIGHT_GREY, labelsize=6.5)
    ax.spines['bottom'].set_color(FT_BORDER)
    ax.spines['left'].set_color(FT_BORDER)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.spines['left'].set_linewidth(0.5)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

    plt.subplots_adjust(left=0.1, right=0.95, top=0.88, bottom=0.08)
    plt.savefig(f"{OUTPUT}/threat-quadrant.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ threat-quadrant.png")


if __name__ == "__main__":
    os.makedirs(OUTPUT, exist_ok=True)
    print("Generating FT-style diagrams v2...")
    diagram_timeline()
    diagram_iw_dashboard()
    diagram_oil_price()
    diagram_scenario()
    diagram_threat_quadrant()
    print(f"\nAll diagrams saved to {OUTPUT}/")
