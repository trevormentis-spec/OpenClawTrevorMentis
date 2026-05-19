#!/usr/bin/env python3
"""Generate all 8 visualizations for the Brazil Fiscal Trajectory flagship brief."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch
import os

OUTPUT_DIR = "/home/ubuntu/.openclaw/workspace/memory/2026-05-v2-validation/brazil-flagship"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color palette
DARK_NAVY = '#0C2D48'
TEAL = '#145DA0'
BLUE = '#0E86D4'
LIGHT_BLUE = '#B1D4E0'
ORANGE = '#FF6B35'
RED = '#C1292E'
GREEN = '#17B978'
GREY = '#6C757D'
GOLD = '#F7C548'
PURPLE = '#7B2D8E'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

# ─── Chart 1: Cover Page ───────────────────────────────────────────────────
def make_cover():
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 11)
    ax.axis('off')

    # Background gradient
    rect = FancyBboxPatch((0, 0), 8.5, 11,
                          boxstyle="round,pad=0",
                          facecolor=DARK_NAVY, edgecolor='none', zorder=0)
    ax.add_patch(rect)

    # Decorative header bar
    ax.add_patch(plt.Rectangle((0, 8.5), 8.5, 0.08, color=GOLD, alpha=0.9, zorder=1))

    # Title
    ax.text(4.25, 7.5, 'Brazil Fiscal Trajectory',
            ha='center', va='center', fontsize=28, fontweight='bold',
            color='white', zorder=2)
    ax.text(4.25, 6.7, 'H2 2026 + 2027 Outlook',
            ha='center', va='center', fontsize=18,
            color=GOLD, zorder=2)

    # Subtitle
    ax.text(4.25, 5.5, 'A Multi-Scenario Assessment for\nFamily Office EM Exposure ($200M–$2B)',
            ha='center', va='center', fontsize=12,
            color=LIGHT_BLUE, zorder=2)

    # Decorative line
    ax.plot([2.5, 6.0], [4.8, 4.8], color=GOLD, linewidth=1.5, zorder=2)

    # Classification
    ax.text(4.25, 4.2, 'CLIENT CONFIDENTIAL',
            ha='center', va='center', fontsize=10, fontweight='bold',
            color=RED, zorder=2)
    ax.text(4.25, 3.7, 'Prepared by Trevor Intelligence — May 19, 2026',
            ha='center', va='center', fontsize=9, color=LIGHT_BLUE, zorder=2)

    # Bottom metadata
    ax.add_patch(plt.Rectangle((0, 0.8), 8.5, 0.04, color=GOLD, alpha=0.5, zorder=1))
    ax.text(4.25, 0.4, 'TREVOR v2 Validation | Phase 2 Flagship Deliverable',
            ha='center', va='center', fontsize=8, color='grey', zorder=2)

    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-cover.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 1: Cover page generated.")

# ─── Chart 2: Calibration Distribution Pie ─────────────────────────────────
def make_calibration_pie():
    labels = ['Very High\n(85-99%)', 'High\n(70-85%)', 'Moderate\n(50-70%)', 'Low-Moderate\n(30-50%)',
              'Low\n(15-30%)', 'Very Low\n(1-15%)', 'Nearly Impossible\n(0-1%)', 'No Judgment']
    sizes = [8, 22, 25, 18, 12, 8, 2, 5]
    colors = ['#1B4F72', '#2E86C1', '#85C1E9', '#F7DC6F', '#F5B041', '#E67E22', '#C0392B', '#95A5A6']
    explode = (0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.05, 0.05)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        explode=explode, colors=colors, startangle=140,
        textprops={'fontsize': 7.5}, pctdistance=0.75
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_fontweight('bold')
    ax.set_title('Sherman Kent Calibration Distribution Across Judgments', fontsize=12, fontweight='bold', pad=15)
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-calibration.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 2: Calibration pie generated.")

# ─── Chart 3: USD/BRL Forecast Bands ──────────────────────────────────────
def make_usdbrl_bands():
    months = ['Jan\n2026', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Jan\n2027', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Dec\n2027']
    x = np.arange(len(months))
    
    # Central forecast
    central = [5.10, 5.16, 5.04, 5.10, 5.05, 4.95, 4.90, 4.85, 4.95, 5.05, 5.10, 5.07, 5.07]
    
    # Upper band (85th percentile)
    upper = [5.30, 5.40, 5.25, 5.35, 5.30, 5.25, 5.20, 5.20, 5.30, 5.40, 5.45, 5.45, 5.45]
    
    # Lower band (15th percentile)
    lower = [4.90, 4.85, 4.80, 4.70, 4.65, 4.55, 4.50, 4.40, 4.45, 4.50, 4.55, 4.55, 4.55]
    
    # Upper-lower further bands
    upper_wide = [5.50, 5.60, 5.50, 5.60, 5.60, 5.55, 5.55, 5.60, 5.70, 5.80, 5.85, 5.85, 5.85]
    lower_wide = [4.70, 4.65, 4.55, 4.40, 4.30, 4.20, 4.10, 4.00, 4.00, 4.10, 4.15, 4.15, 4.15]

    fig, ax = plt.subplots(figsize=(9, 5))
    
    ax.fill_between(x, lower_wide, upper_wide, alpha=0.15, color=BLUE, label='90% Confidence')
    ax.fill_between(x, lower, upper, alpha=0.30, color=BLUE, label='70% Confidence')
    ax.plot(x, central, color=DARK_NAVY, linewidth=2.5, marker='o', markersize=4, label='Central Forecast')
    
    # Current spot
    ax.axhline(y=5.037, color=RED, linestyle='--', linewidth=1, alpha=0.7, label='Spot (19 May 2026: 5.037)')
    
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=7.5)
    ax.set_ylabel('USD/BRL')
    ax.set_title('USD/BRL Exchange Rate Forecast with Confidence Bands', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(3.8, 6.0)
    
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-usdbrl.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 3: USD/BRL bands generated.")

# ─── Chart 4: Fiscal Trajectory ────────────────────────────────────────────
def make_fiscal_trajectory():
    years = ['2023', '2024', '2025e', '2026f', '2027f', '2028f', '2029f', '2030f', '2031f']
    
    # Gross debt % GDP (IMF methodology)
    debt_imf = [85.6, 89.2, 92.8, 96.5, 99.0, 101.2, 103.0, 104.5, 106.5]
    
    # Gross debt % GDP (Domestic methodology)
    debt_dom = [74.3, 79.2, 82.0, 84.8, 87.0, 89.0, 90.0, 91.0, 92.0]
    
    # Primary balance % GDP (IMF, negative = deficit)
    primary = [2.1, -0.3, -0.6, -0.5, -0.1, 0.1, 0.3, 0.5, 0.6]
    
    # Nominal deficit % GDP
    nominal = [-4.5, -6.3, -7.2, -7.7, -7.0, -6.5, -6.2, -6.0, -6.1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # Left: Debt trajectory
    ax1.plot(years, debt_imf, color=RED, marker='o', linewidth=2.2, label='IMF Methodology')
    ax1.plot(years, debt_dom, color=BLUE, marker='s', linewidth=2.2, label='Domestic Methodology')
    ax1.axhline(y=100, color=RED, linestyle=':', alpha=0.5, linewidth=1)
    ax1.text(8, 100.5, '100% threshold', fontsize=7, color=RED, alpha=0.6)
    ax1.axhline(y=78.9, color=GREEN, linestyle=':', alpha=0.5, linewidth=1)
    ax1.text(0, 79.5, 'EM avg (78.9%)', fontsize=7, color=GREEN, alpha=0.6)
    ax1.set_ylabel('Gross Debt (% of GDP)')
    ax1.set_title('Public Debt Trajectory', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Right: Fiscal balances
    x = np.arange(len(years))
    width = 0.35
    bars1 = ax2.bar(x - width/2, primary, width, color=BLUE, label='Primary Balance', alpha=0.85)
    bars2 = ax2.bar(x + width/2, nominal, width, color=RED, label='Nominal Balance', alpha=0.85)
    ax2.axhline(y=0, color='black', linewidth=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(years, fontsize=7.5, rotation=45)
    ax2.set_ylabel('% of GDP')
    ax2.set_title('Fiscal Balance Trajectory', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Color bars by positive/negative
    for bar in bars1:
        if bar.get_height() < 0:
            bar.set_color(RED)
    for bar in bars2:
        if bar.get_height() >= 0:
            bar.set_color(GREEN)
    
    fig.suptitle('Brazil Fiscal Trajectory: Debt and Balance Dynamics', fontsize=13, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-fiscal.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 4: Fiscal trajectory generated.")

# ─── Chart 5: Selic Path Forecast ─────────────────────────────────────────
def make_selic_path():
    months = ['Jan\n2026', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Jan\n2027', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Dec\n2027']
    x = np.arange(len(months))
    
    # Base case
    base = [14.75, 14.75, 14.50, 14.25, 14.00, 13.75, 13.50, 13.25, 13.00, 12.50, 12.00, 11.50, 11.25]
    
    # Bull case (faster easing)
    bull = [14.75, 14.75, 14.50, 14.00, 13.50, 13.00, 12.50, 12.00, 11.50, 11.00, 10.50, 10.25, 10.00]
    
    # Bear case (slower/higher)
    bear = [14.75, 14.75, 14.50, 14.50, 14.25, 14.00, 14.00, 13.75, 13.75, 13.50, 13.25, 13.00, 12.75]
    
    # Upper/lower bands for base
    base_upper = [14.75, 14.75, 14.50, 14.25, 14.00, 13.75, 13.50, 13.25, 13.00, 12.50, 12.00, 11.50, 11.25]
    # Add some spread over base
    base_upper_wide = [14.75, 14.75, 14.50, 14.50, 14.25, 14.00, 14.00, 13.75, 13.75, 13.50, 13.25, 13.00, 12.75]
    base_lower_wide = [14.75, 14.75, 14.50, 14.00, 13.50, 13.00, 12.50, 12.00, 11.50, 11.00, 10.50, 10.25, 10.00]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    
    ax.fill_between(x, base_lower_wide, base_upper_wide, alpha=0.12, color=TEAL, label='Possible Range')
    ax.plot(x, base, color=DARK_NAVY, linewidth=2.5, marker='o', markersize=5, label='Base Case (Focus Survey Consensus)')
    ax.plot(x, bull, color=GREEN, linewidth=1.8, linestyle='--', marker='^', markersize=4, label='Bull: Faster Easing')
    ax.plot(x, bear, color=RED, linewidth=1.8, linestyle='--', marker='v', markersize=4, label='Bear: Sticky Inflation')
    
    # Key announcements
    ax.axvline(x=2, color=GREY, linestyle=':', alpha=0.5, linewidth=0.8)  # May 2026
    ax.axvline(x=7, color=GREY, linestyle=':', alpha=0.5, linewidth=0.8)  # Jan 2027
    
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=7.5)
    ax.set_ylabel('Selic Rate (%)')
    ax.set_title('Selic Policy Rate Path: Base, Bull, and Bear Scenarios', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(9.0, 15.5)
    
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-selic.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 5: Selic path generated.")

# ─── Chart 6: Scenario Tree ────────────────────────────────────────────────
def make_scenario_tree():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')

    def draw_box(x, y, w, h, text, color=DARK_NAVY, text_color='white', fontsize=10):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                              boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', linewidth=2, zorder=3)
        ax.add_patch(rect)
        lines = text.split('\n')
        line_h = 0.25
        start_y = y + (len(lines)-1) * line_h / 2
        for i, line in enumerate(lines):
            ax.text(x, start_y - i * line_h, line, ha='center', va='center',
                    fontsize=fontsize, color=text_color, fontweight='bold' if i == 0 else 'normal', zorder=4)

    def draw_line(x1, y1, x2, y2, color='grey', lw=1.5):
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, zorder=2)

    def draw_label(x, y, label, color='grey'):
        mid_x = (x[0] + x[1]) / 2
        mid_y = (y[0] + y[1]) / 2
        ax.text(mid_x, mid_y, label, ha='center', va='center',
                fontsize=8, color=color, style='italic', zorder=5,
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=2))

    # Root
    draw_box(6, 9.2, 3.5, 0.6, 'BRAZIL FISCAL\nTRAJECTORY OUTLOOK', DARK_NAVY, 'white', 9)
    
    # Key assumptions row
    draw_box(6, 7.8, 4.5, 0.5, 'KEY NODES', DARK_NAVY, GOLD, 8)
    
    # Assumptions
    assumptions = [
        (1.5, 6.6, 'ELECTION\nOUTCOME'),
        (4.0, 6.6, 'FISCAL\nFRAMEWORK'),
        (6.5, 6.6, 'GLOBAL\nENVIRONMENT'),
        (9.0, 6.6, 'MONETARY\nPOLICY'),
        (11.0, 6.6, 'COMMODITY\nPRICES'),
    ]
    for x, y, text in assumptions:
        draw_box(x, y, 1.5, 0.5, text, TEAL, 'white', 7)
        draw_line(6, 7.3, x, 6.9, GREY, 0.8)

    # Scenarios
    # Draw lines from assumptions to scenarios
    draw_line(1.5, 6.35, 1.5, 5.8, GREY, 1)  # Left
    draw_line(4.0, 6.35, 3.0, 5.8, GREY, 1)  # Center-left
    draw_line(6.5, 6.35, 6.5, 5.8, GREY, 1)  # Center
    draw_line(9.0, 6.35, 9.8, 5.8, GREY, 1)  # Center-right
    draw_line(11.0, 6.35, 10.5, 5.8, GREY, 1)  # Right

    # 4 scenarios
    scenarios = [
        (1.5, 5.2, 'UPSIDE\n(15%)', GREEN, 'Fiscal consolidation\nachieves surplus\nSelic below 10%\nGrowth recovers'),
        (4.5, 5.2, 'BASE\n(45%)', BLUE, 'Slow grind lower\nDeficit narrows\ngradually\nSelic 11-12%\nGrowth ~1.8-2.0%'),
        (7.8, 5.2, 'DOWNSIDE\n(30%)', ORANGE, 'Fiscal drift continues\nDeficit ~0.5%\nSelic 12-13%\nGrowth <1.5%'),
        (10.8, 5.2, 'TAIL\n(10%)', RED, 'Fiscal crisis\nDebt >100%\nSelic above 14%\nRating downgrade\nCapital flight'),
    ]
    for x, y, title, color, desc in scenarios:
        draw_box(x, y, 2.2, 0.5, title, color, 'white' if color != GOLD else DARK_NAVY, 8)
        draw_box(x, y - 1.3, 2.2, 1.6, desc, 'white', DARK_NAVY, 7)
        
        # Connect scenario to assumptions
        draw_line(x, y + 0.3, x, y + 0.6, GREY, 0.8)

    # Probability label
    draw_box(6, 1.8, 3, 0.4, 'Probability-weighted central case:', DARK_NAVY, 'white', 8)
    draw_box(6, 1.0, 5, 0.5, 'Debt trajectory: rising | Selic: gradual easing | Growth: below potential', GREY, 'white', 8)

    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-scenario-tree.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 6: Scenario tree generated.")

# ─── Chart 7: Sectoral Exposure Matrix ─────────────────────────────────────
def make_sectoral_matrix():
    sectors = ['Banks &\nFinancials', 'Commodities\n& Mining', 'Oil & Gas\n(Petrobras)', 'Utilities\n& Energy', 
               'Consumer\nDiscretionary', 'Consumer\nStaples', 'Real Estate\n& Construction', 'Technology\n& Telecom',
               'Healthcare', 'Transport\n& Logistics']
    
    # Risk scores (0-100) for each scenario
    upside_risk = [55, 65, 70, 60, 75, 60, 65, 70, 55, 60]
    base_risk = [45, 55, 60, 50, 45, 50, 40, 55, 45, 45]
    downside_risk = [35, 40, 50, 35, 25, 40, 20, 35, 35, 30]
    tail_risk = [20, 30, 35, 20, 10, 25, 10, 20, 20, 15]

    fig, ax = plt.subplots(figsize=(12, 6))
    
    y = np.arange(len(sectors))
    height = 0.2
    
    ax.barh(y - 1.5*height, upside_risk, height, color=GREEN, alpha=0.75, label='Upside Scenario')
    ax.barh(y - 0.5*height, base_risk, height, color=BLUE, alpha=0.75, label='Base Scenario')
    ax.barh(y + 0.5*height, downside_risk, height, color=ORANGE, alpha=0.75, label='Downside Scenario')
    ax.barh(y + 1.5*height, tail_risk, height, color=RED, alpha=0.75, label='Tail Scenario')
    
    ax.set_yticks(y)
    ax.set_yticklabels(sectors, fontsize=8)
    ax.set_xlabel('Sector Resilience Score (0 = Weak / 100 = Strong)', fontsize=10)
    ax.set_title('Sectoral Exposure Matrix: Resilience Across Scenarios', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, 100)
    
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-sectoral-matrix.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 7: Sectoral matrix generated.")

# ─── Chart 8: Watch Calendar (Gantt-style) ────────────────────────────────
def make_watch_calendar():
    events = [
        ('Jun 2026', 'May 2026\n− Mid-Year Budget Review', 0.0, 1.0),
        ('Jun 2026\nIPCA-15 print', 0.0, 1.0),
        ('Jun 2026\nCopom meeting (Selic decision)', 0.0, 1.0),
        ('Jun 2026', 'Jun 2026\nBCB Focus Survey weekly', 1.0, 1.0),
        ('Jun 2026\nIMF Article IV for Brazil', 1.0, 1.0),
        ('Jul 2026', 'Jul 2026\nQ2 GDP flash estimate', 2.0, 1.0),
        ('Jul 2026\nCopom meeting', 2.0, 1.0),
        ('Jul 2026\nBiannual budget report', 2.0, 1.0),
        ('Aug 2026', 'Aug 2026\nElectoral campaign intensifies', 3.0, 1.0),
        ('Aug 2026\nPrimary surplus target mid-check', 3.0, 1.0),
        ('Aug 2026\nCopom minutes released', 3.0, 1.0),
        ('Sep 2026', 'Sep 2026\nPre-election spending peak', 4.0, 1.0),
        ('Sep 2026\nCopom meeting', 4.0, 1.0),
        ('Sep 2026\nLast Focus Survey pre-election', 4.0, 1.0),
        ('Oct 2026', 'Oct 4: FIRST ROUND ELECTION', 5.0, 1.0),
        ('Oct 2026\nPossible run-off (Oct 25)', 5.0, 1.0),
        ('Oct 2026\nCopom meeting', 5.0, 1.0),
        ('Nov 2026', 'Nov 2026\nTransition planning begins', 6.0, 1.0),
        ('Nov 2026\nQ3 GDP release', 6.0, 1.0),
        ('Nov 2026\nFocus Survey - 2027 outlook', 6.0, 1.0),
        ('Dec 2026', 'Dec 2026\nYear-end fiscal balance update', 7.0, 1.0),
        ('Dec 2026\nCopom meeting - last of year', 7.0, 1.0),
        ('Dec 2026\n2027 Budget Law approved', 7.0, 1.0),
        ('Jan 2027', 'Jan 2027\nNew administration takes office', 8.0, 1.0),
        ('Jan 2027\nLula or opposition agenda details', 8.0, 1.0),
        ('Jan 2027\nFirst Copom of 2027', 8.0, 1.0),
        ('Feb 2027', 'Feb 2027\nFirst monthly fiscal result', 9.0, 1.0),
        ('Feb 2027\nPost-election policy signals', 9.0, 1.0),
        ('Feb 2027\nCredit rating review', 9.0, 1.0),
        ('Mar 2027+', 'Mar-May 2027\nFiscal consolidation assessment', 10.0, 1.0),
        ('Mar-May 2027\nInflation trajectory confirmation', 10.0, 1.0),
        ('H2 2027', 'Jun-Dec 2027\nSustained fiscal adjustment?', 11.0, 1.0),
        ('Jun-Dec 2027\nRating action window', 11.0, 1.0),
        ('Jun-Dec 2027\nSelir at/near terminal rate', 11.0, 1.0),
        ('Jun-Dec 2027\nGrowth trajectory re-assessment', 11.0, 1.0),
    ]

    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Time periods
    period_labels = ['May-Jun\n2026', 'Jul-Aug\n2026', 'Sep-Oct\n2026\n(ELECTION)', 'Nov-Dec\n2026', 'Jan-Feb\n2027', 'Mar-May\n2027', 'Jun-Dec\n2027']
    
    # Assign events to periods and colors
    periods = [0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6]
    
    # Shorten events list to manageable
    events_short = [
        ('May-Jun 2026', 'Mid-Year Budget Review', 0, 1, TEAL),
        ('', 'June Copom (Selic decision)', 0, 1, TEAL),
        ('', 'IMF Article IV Report', 0, 1, TEAL),
        ('', 'BCB Focus Survey weekly', 0, 0.5, LIGHT_BLUE),
        ('Jul-Aug 2026', 'Q2 GDP Flash Estimate', 1, 1, TEAL),
        ('', 'July Copom meeting', 1, 1, TEAL),
        ('', 'Electoral Campaign Intensifies', 1, 1, ORANGE),
        ('', 'Biannual Budget Report', 1, 0.5, LIGHT_BLUE),
        ('Sep-Oct 2026', 'Pre-election spending peaks', 2, 1, ORANGE),
        ('ELECTION PERIOD', 'Oct 4: FIRST ROUND', 2, 1, RED),
        ('', 'Oct 25: Possible Run-off', 2, 1, RED),
        ('', 'September Copom meeting', 2, 0.5, TEAL),
        ('Nov-Dec 2026', 'Transition planning begins', 3, 1, ORANGE),
        ('', 'Q3 GDP Release', 3, 1, TEAL),
        ('', 'Year-end Fiscal Balance Update', 3, 0.5, LIGHT_BLUE),
        ('', 'Dec Copom - last of year', 3, 0.5, TEAL),
        ('Jan-Feb 2027', 'New administration takes office', 4, 1, ORANGE),
        ('', 'Policy Agenda & First Budget Signals', 4, 1, RED),
        ('', 'First Copom of 2027', 4, 0.5, TEAL),
        ('', 'Credit Rating Review Window', 4, 0.5, PURPLE),
        ('Mar-May 2027', 'Fiscal consolidation assessment', 5, 1, DARK_NAVY),
        ('', 'Inflation trajectory confirmation', 5, 0.5, TEAL),
        ('', 'First monthly fiscal results', 5, 0.5, LIGHT_BLUE),
        ('Jun-Dec 2027', 'Sustained fiscal adjustment path', 6, 1, DARK_NAVY),
        ('', 'Rating action window', 6, 1, PURPLE),
        ('', 'Selic near terminal rate', 6, 0.5, TEAL),
        ('', 'Growth trajectory re-assessment', 6, 0.5, LIGHT_BLUE),
    ]

    y_positions = list(range(len(events_short) - 1, -1, -1))
    
    for i, (period, event, period_idx, duration, color) in enumerate(events_short):
        y = y_positions[i]
        
        if period:
            # Period label on the left
            ax.text(-0.5, y, period, ha='right', va='center', fontsize=8, fontweight='bold', color=DARK_NAVY)
        
        # Event bar
        bar_start = period_idx * 1.0
        bar_width = duration * 1.0
        ax.barh(y, bar_width, left=bar_start, height=0.6, color=color, alpha=0.7, edgecolor='white')
        
        # Event label inside/next to bar
        ax.text(bar_start + 0.05, y, event, ha='left', va='center', fontsize=7, color='white' if color in [DARK_NAVY, RED, PURPLE] else DARK_NAVY)

    # Period header labels
    for i, label in enumerate(period_labels):
        ax.text(i + 0.5, max(y_positions) + 1.5, label, ha='center', va='center', fontsize=8, fontweight='bold', color=DARK_NAVY)
        ax.axvline(x=i, color=GREY, linestyle=':', alpha=0.3)

    ax.set_ylim(-1, max(y_positions) + 2.5)
    ax.set_xlim(0, 7)
    ax.set_title('Watch Calendar: Key Milestones through Dec 2027', fontsize=13, fontweight='bold')
    ax.axis('off')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=TEAL, alpha=0.7, label='Monetary/Fiscal Events'),
        mpatches.Patch(facecolor=ORANGE, alpha=0.7, label='Political/Election Events'),
        mpatches.Patch(facecolor=RED, alpha=0.7, label='High-Impact Events'),
        mpatches.Patch(facecolor=PURPLE, alpha=0.7, label='Rating/External Events'),
        mpatches.Patch(facecolor=DARK_NAVY, alpha=0.7, label='Assessment/Decision Points'),
    ]
    ax.legend(handles=legend_elements, fontsize=8, loc='lower right', ncol=3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'chart-watch-calendar.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Chart 8: Watch calendar generated.")


if __name__ == '__main__':
    make_cover()
    make_calibration_pie()
    make_usdbrl_bands()
    make_fiscal_trajectory()
    make_selic_path()
    make_scenario_tree()
    make_sectoral_matrix()
    make_watch_calendar()
    print("\n✓ All 8 charts generated successfully.")
