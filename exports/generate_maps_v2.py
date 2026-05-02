"""Financial Times-style maps for TREVOR assessment. Clean, minimal, professional."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"

# FT Color Palette
FT_CREAM = '#F5F3EF'
FT_OCEAN = '#E8E2D8'
FT_LAND = '#F0ECE3'
FT_BORDER = '#D5CCC0'
FT_COAST = '#B8AFA0'
FT_RED = '#C0392B'
FT_BLUE = '#1B3A5C' 
FT_GOLD = '#B8860B'
FT_GREY = '#6B6B6B'
FT_LIGHT_GREY = '#999999'
FT_TEXT = '#222222'
FT_GRID = '#E0DCD4'

# Default figure style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7,
    'axes.titlesize': 0,
    'axes.labelsize': 0,
    'figure.facecolor': FT_CREAM,
    'axes.facecolor': FT_CREAM,
    'savefig.facecolor': FT_CREAM,
    'savefig.dpi': 300,
})


def add_ft_title(ax, title, subtitle="", source=""):
    """Add FT-style title block to axis."""
    ax.text(0, 1.04, title, transform=ax.transAxes,
            fontsize=11, fontweight='bold', color=FT_TEXT, ha='left', va='bottom',
            fontfamily='sans-serif')
    if subtitle:
        ax.text(0, 1.005, subtitle, transform=ax.transAxes,
                fontsize=7, color=FT_LIGHT_GREY, ha='left', va='bottom')
    if source:
        ax.text(0, -0.045, source, transform=ax.transAxes,
                fontsize=5.5, fontstyle='italic', color=FT_LIGHT_GREY, ha='left', va='top')


def add_scale_bar(ax, x_start, y, length_deg, label):
    """Add thin FT-style scale bar."""
    ax.plot([x_start, x_start + length_deg], [y, y],
            color=FT_GREY, linewidth=1.5, transform=ccrs.PlateCarree())
    ax.plot([x_start, x_start], [y-0.15, y+0.15],
            color=FT_GREY, linewidth=1, transform=ccrs.PlateCarree())
    ax.plot([x_start + length_deg, x_start + length_deg], [y-0.15, y+0.15],
            color=FT_GREY, linewidth=1, transform=ccrs.PlateCarree())
    ax.text(x_start + length_deg/2, y - 0.3, label,
            transform=ccrs.PlateCarree(), fontsize=6, color=FT_GREY, ha='center')


def setup_map(ax, extent, show_grid=False):
    """Apply FT base styling to map axis."""
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor=FT_LAND, edgecolor='none')
    ax.add_feature(cfeature.OCEAN, facecolor=FT_OCEAN)
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_COAST, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, edgecolor=FT_BORDER, linewidth=0.4, linestyle='-')
    ax.add_feature(cfeature.LAKES, facecolor=FT_OCEAN, edgecolor=FT_COAST, linewidth=0.3)
    if show_grid:
        gl = ax.gridlines(draw_labels=True, linewidth=0.2, color=FT_GRID, alpha=0.5, linestyle='-')
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 6, 'color': FT_LIGHT_GREY}
        gl.ylabel_style = {'size': 6, 'color': FT_LIGHT_GREY}
    else:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)


def map1_hormuz():
    """Strait of Hormuz — FT style."""
    fig = plt.figure(figsize=(10.5, 8), facecolor=FT_CREAM)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    setup_map(ax, [42, 62, 22, 30])
    add_ft_title(ax,
        'Strait of Hormuz — Blockade Enforcement Zone',
        'Operation Epic Fury · 1 May 2026 · 200+ aircraft · 25 naval vessels deployed',
        'Sources: JMIC, UKMTO, Windward Maritime, US NAVCENT · TREVOR Assessment')

    # Blockade zone — subtle hashed polygon
    from shapely.geometry import Polygon
    bx = [52, 58, 60, 56, 52]
    by = [24, 24, 28, 29, 24]
    ax.add_geometries([Polygon(list(zip(bx, by)))], crs=ccrs.PlateCarree(),
                     facecolor=FT_RED, alpha=0.06, edgecolor=FT_RED, linewidth=1.2, linestyle='--')

    # Vessel turn-back dots (randomized positions near strait)
    np.random.seed(42)
    for _ in range(42):
        lon = 55 + np.random.rand() * 3
        lat = 25.5 + np.random.rand() * 1.5
        ax.scatter(lon, lat, s=4, c=FT_RED, alpha=0.4, transform=ccrs.PlateCarree(), zorder=3)

    # Strait marker
    ax.scatter(56.2, 26.5, s=80, marker='s', c=FT_RED, edgecolors='white', linewidth=1.5,
              transform=ccrs.PlateCarree(), zorder=10)
    ax.annotate('Strait of Hormuz\n~20 mb/d throughput', xy=(56.2, 26.5), xytext=(57.5, 27.8),
               transform=ccrs.PlateCarree(), fontsize=7, fontweight='bold', color=FT_RED, ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_RED, lw=1, connectionstyle='arc3,rad=0.2'))

    # Ports
    ports = [(56.3, 27.2, 'Bandar Abbas'), (54.4, 24.5, 'Khalifa Port'),
             (56.0, 23.5, 'Fujairah'), (48.0, 29.3, 'Kuwait')]
    for lon, lat, name in ports:
        ax.scatter(lon, lat, s=12, c=FT_BLUE, edgecolors='white', linewidth=0.5,
                  transform=ccrs.PlateCarree(), zorder=8)
        ax.text(lon + 0.4, lat, name, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_BLUE, fontweight='bold', va='center')

    # Country labels
    clabels = [(46.5, 26.5, 'SAUDI\nARABIA'), (51.2, 25.3, 'QATAR'), (54.5, 23.5, 'UAE'),
               (57.5, 22.5, 'OMAN'), (44.5, 25.0, 'IRAQ'), (59.0, 28.0, 'IRAN')]
    for lon, lat, name in clabels:
        ax.text(lon, lat, name, transform=ccrs.PlateCarree(),
               fontsize=7, color=FT_GREY, ha='center', va='center', fontweight='bold', alpha=0.6)

    # Blockade annotation
    ax.text(53.5, 28.8, 'BLOCKADE ENFORCEMENT ZONE\n42 vessels turned back · AIS jamming active',
           transform=ccrs.PlateCarree(), fontsize=6.5, color=FT_RED, ha='center', fontweight='bold')

    # Metrics sidebar
    metrics = (
        "KEY METRICS\n"
        "━━━━━━━━━━━\n"
        "Turned back:    42 vessels\n"
        "Aircraft:      200+\n"
        "Naval vessels:   25\n"
        "Brent crude:  $124.67\n"
        "Insurance:   WITHDRAWN"
    )
    ax.text(60.5, 30.0, metrics, transform=ccrs.PlateCarree(),
           fontsize=6.5, color=FT_TEXT, ha='left', va='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=FT_BORDER, linewidth=0.5),
           fontfamily='monospace')

    add_scale_bar(ax, 42.5, 22.2, 4.5, '~500 km')
    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.04)
    plt.savefig(f"{OUTPUT}/map-hormuz-blockade.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ map-hormuz-blockade.png")


def map2_militia():
    """Iran-aligned militia strikes — FT style."""
    fig = plt.figure(figsize=(10.5, 8), facecolor=FT_CREAM)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    setup_map(ax, [32, 62, 20, 38])
    add_ft_title(ax,
        'Iran-Aligned Militia Strikes — Regional Impact',
        '"Islamic Resistance in Iraq" coalition · 400+ strikes across 6 countries',
        'Sources: Institute for the Study of War, FDD · TREVOR Assessment')

    # Proportional strike circles
    strikes = [
        (44.0, 33.5, 120, 'Iraq'),
        (46.0, 26.0, 85, 'Saudi Arabia'),
        (47.8, 29.5, 55, 'Kuwait'),
        (54.5, 24.0, 60, 'UAE'),
        (51.2, 25.3, 40, 'Qatar'),
        (50.5, 26.0, 25, 'Bahrain'),
        (36.5, 31.0, 15, 'Jordan'),
    ]
    for lon, lat, count, name in strikes:
        radius = np.sqrt(count) * 2.5
        circle = plt.Circle((lon, lat), radius, facecolor=FT_RED, edgecolor='white',
                           linewidth=1, alpha=0.45, transform=ccrs.PlateCarree(), zorder=5)
        ax.add_patch(circle)
        ax.text(lon, lat - radius - 0.3, f'{name}\n{count}', transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_RED, ha='center', va='top', fontweight='bold')

    # Militia HQ markers
    hqs = [(44.3, 33.2, 'PMF'), (44.0, 31.5, 'Kata\'ib\nHezbollah'), (44.5, 30.3, 'Asa\'ib\nAhl al-Haq')]
    for lon, lat, name in hqs:
        ax.scatter(lon, lat, s=60, marker='^', c=FT_RED, edgecolors='white', linewidth=1,
                  transform=ccrs.PlateCarree(), zorder=8)
        ax.text(lon - 0.8, lat, name, transform=ccrs.PlateCarree(),
               fontsize=6, color=FT_RED, ha='right', va='center', fontweight='bold')

    # Israel → UAE arrow
    ax.annotate('Israel → UAE: Advanced\ndefensive weaponry delivery',
               xy=(54.5, 24.0), xytext=(48.0, 27.5),
               transform=ccrs.PlateCarree(), fontsize=6.5, color=FT_BLUE, fontweight='bold', ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_BLUE, lw=1.2, connectionstyle='arc3,rad=0.25'))

    # Country labels
    for lon, lat, name in [(44.0, 36.5, 'IRAQ'), (55.0, 34.5, 'IRAN'), (34.8, 32.0, 'ISRAEL'),
                           (38.5, 35.5, 'SYRIA'), (36.0, 24.5, 'EGYPT')]:
        ax.text(lon, lat, name, transform=ccrs.PlateCarree(),
               fontsize=7, color=FT_GREY, ha='center', va='center', fontweight='bold', alpha=0.5)

    # Legend
    legend_data = [(100, '100+ strikes'), (60, '60 strikes'), (25, '25 strikes')]
    x0, y0 = 33, 20.5
    for count, label in legend_data:
        r = np.sqrt(count) * 2.5
        circle = plt.Circle((x0 + r, y0 + r), r, facecolor=FT_RED, edgecolor='white',
                           linewidth=0.8, alpha=0.45, transform=ccrs.PlateCarree(), zorder=5)
        ax.add_patch(circle)
        ax.text(x0 + r*2 + 0.3, y0 + r, label, transform=ccrs.PlateCarree(),
               fontsize=6, color=FT_TEXT, va='center')
    ax.text(x0, y0 + 0.2, 'Strike count:', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_GREY, va='bottom', fontweight='bold')

    plt.subplots_adjust(left=0.03, right=0.98, top=0.92, bottom=0.04)
    plt.savefig(f"{OUTPUT}/map-militia-strikes.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ map-militia-strikes.png")


def map3_global():
    """Global energy disruption — FT style Robinson projection."""
    fig = plt.figure(figsize=(14, 8.5), facecolor=FT_CREAM)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson(central_longitude=20))
    ax.set_facecolor(FT_CREAM)
    ax.set_global()

    ax.add_feature(cfeature.LAND, facecolor=FT_LAND, edgecolor='none')
    ax.add_feature(cfeature.OCEAN, facecolor=FT_OCEAN)
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_COAST, linewidth=0.3)
    ax.add_feature(cfeature.BORDERS, edgecolor=FT_BORDER, linewidth=0.2, linestyle='-')
    ax.set_frame_on(False)

    add_ft_title(ax,
        'Global Energy Disruption — Chokepoint Cascade',
        'Hormuz blockade cascading through global supply chains · 1 May 2026',
        'Sources: EIA, IEA, S&P Global, Windward · TREVOR Assessment')

    # Oil routes from Hormuz
    routes = [
        ([56, 50, 40, 30, 20, 10, 0, -5], [26, 28, 30, 30, 30, 30, 30, 30], '#1B4F72', 'Europe / Mediterranean'),
        ([56, 60, 70, 80, 90, 100, 110, 120, 130, 140], [26, 26, 24, 22, 20, 18, 16, 14, 12, 10], '#1B5E20', 'Asia-Pacific'),
        ([56, 55, 50, 45, 40, 35], [26, 24, 22, 20, 18, 15], '#B8860B', 'Africa / Cape of Good Hope'),
    ]
    for lons, lats, color, label in routes:
        ax.plot(lons, lats, color=color, linewidth=1.5, alpha=0.35,
               transform=ccrs.PlateCarree(), linestyle='-', zorder=3)
        ax.plot(lons, lats, color=color, linewidth=0.5, alpha=0.6,
               transform=ccrs.PlateCarree(), linestyle=':', zorder=4)
        ax.text(lons[-1]+2, lats[-1], label, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=color, fontweight='bold', va='center')

    # Chokepoints
    chokepoints = [
        (56, 26.5, 'Strait of Hormuz\nBLOCKADED', FT_RED, 120),
        (44, 13, 'Bab el-Mandeb\n(Houthi risk)', '#E67E22', 40),
        (36, 41, 'Turkish\nStraits', '#E67E22', 30),
        (103, 1.5, 'Malacca\nStrait', '#E67E22', 30),
        (-80, 25, 'Panama\nCanal', '#E67E22', 25),
    ]
    for lon, lat, label, color, size in chokepoints:
        ax.scatter(lon, lat, s=size, c=color, alpha=0.7, edgecolors='white', linewidth=1.5,
                  transform=ccrs.PlateCarree(), zorder=8)
        ax.text(lon, lat-4, label, transform=ccrs.PlateCarree(),
               fontsize=6, color=color, ha='center', fontweight='bold')

    # Impact annotations
    impacts = [
        (-10, 55, 'EUROPE\nGas +70%\nRecession risk'),
        (140, 40, 'JAPAN / KOREA\nLNG +45%\nStrategic reserves'),
        (80, 5, 'SOUTH ASIA\nFuel crisis\nPakistan, Sri Lanka'),
        (-80, 10, 'AMERICAS\n$124.67/bbl\nInflation pressure'),
    ]
    for lon, lat, text in impacts:
        ax.text(lon, lat, text, transform=ccrs.PlateCarree(),
               fontsize=6, color=FT_TEXT, ha='center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=FT_BORDER, linewidth=0.5, alpha=0.85))

    plt.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)
    plt.savefig(f"{OUTPUT}/map-global-impact.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ map-global-impact.png")


def map4_ukraine():
    """Ukraine-Gulf partnerships — FT style."""
    fig = plt.figure(figsize=(10, 7.5), facecolor=FT_CREAM)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    setup_map(ax, [20, 60, 20, 55])
    add_ft_title(ax,
        'Ukraine Strategic Adaptation — Gulf Security Partnerships',
        'Military-technical cooperation · Anti-drone deployments · 1 May 2026',
        'Sources: Atlantic Council, official government statements · TREVOR Assessment')

    # Ukraine
    ax.scatter(31, 49, s=150, c=FT_BLUE, edgecolors='white', linewidth=2,
              transform=ccrs.PlateCarree(), zorder=10)
    ax.text(31, 47, 'UKRAINE', transform=ccrs.PlateCarree(),
           fontsize=9, fontweight='bold', color=FT_BLUE, ha='center')
    ax.annotate('Anti-drone specialists\ndeployed to 5 Gulf states',
               xy=(31, 49), xytext=(31, 44),
               transform=ccrs.PlateCarree(), fontsize=6.5, color=FT_GREY, ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_GREY, lw=0.8, connectionstyle='arc3,rad=0'))

    # Gulf states
    gulf = [
        (46.7, 24.7, 'Saudi Arabia', 'Security pact', FT_GOLD),
        (51.5, 25.3, 'Qatar', 'Security pact', FT_GOLD),
        (54.4, 24.0, 'UAE', 'Anti-drone active', FT_GOLD),
    ]
    for lon, lat, name, note, color in gulf:
        ax.scatter(lon, lat, s=120, c=color, edgecolors='white', linewidth=2,
                  transform=ccrs.PlateCarree(), zorder=10)
        ax.text(lon, lat + 1.8, name, transform=ccrs.PlateCarree(),
               fontsize=7, fontweight='bold', color=FT_TEXT, ha='center')
        ax.text(lon, lat - 1.8, note, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_GREY, ha='center')
        # Connection line
        ax.plot([31, lon], [48, lat], color=FT_BLUE, linewidth=0.8, alpha=0.3,
               transform=ccrs.PlateCarree(), linestyle='-', zorder=1)

    # Russia
    ax.scatter(37, 55, s=60, c=FT_RED, alpha=0.4, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=8)
    ax.text(37, 56, 'RUSSIA', transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_RED, ha='center', fontweight='bold')
    ax.text(37, 54, 'Grain theft\ndispute', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_GREY, ha='center')

    # Israel
    ax.scatter(34.8, 31.5, s=60, c=FT_BLUE, alpha=0.5, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=8)
    ax.text(34.8, 32.8, 'ISRAEL', transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_BLUE, ha='center', fontweight='bold')
    ax.annotate('Ukraine requests\nstolen grain seizure',
               xy=(34.8, 31.5), xytext=(37, 29),
               transform=ccrs.PlateCarree(), fontsize=6, color=FT_GREY, ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_GREY, lw=0.8, connectionstyle='arc3,rad=0.2'))

    # Status legend
    legend_y = 21
    ax.text(22, legend_y, 'PARTNERSHIP STATUS:', transform=ccrs.PlateCarree(),
           fontsize=6.5, color=FT_GREY, fontweight='bold', va='top')
    ax.scatter(22, legend_y-1.2, s=40, c=FT_GOLD, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=10)
    ax.text(22.8, legend_y-1.2, 'Signed security partnership', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_TEXT, va='center')
    ax.scatter(22, legend_y-2.2, s=40, c=FT_BLUE, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=10)
    ax.text(22.8, legend_y-2.2, 'Diplomatic engagement', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_TEXT, va='center')

    plt.subplots_adjust(left=0.03, right=0.98, top=0.92, bottom=0.04)
    plt.savefig(f"{OUTPUT}/map-ukraine-gulf.png", dpi=300, bbox_inches='tight', facecolor=FT_CREAM)
    plt.close()
    print("  ✅ map-ukraine-gulf.png")


if __name__ == "__main__":
    os.makedirs(OUTPUT, exist_ok=True)
    print("Generating FT-style maps v2...")
    map1_hormuz()
    map2_militia()
    map3_global()
    map4_ukraine()
    print(f"\nAll maps saved to {OUTPUT}/")
