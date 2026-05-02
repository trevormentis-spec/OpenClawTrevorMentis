"""Generate Bloomberg/Financial Times style maps for the TREVOR assessment."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"

# FT/Bloomberg style colors
FT_BG = '#F5F3EF'       # Warm off-white
FT_TEXT = '#1A1A1A'      # Near-black
FT_MUTED = '#6B6B6B'     # Grey for secondary text
FT_GOLD = '#C5A572'      # FT gold accent
FT_RED = '#C0392B'       # Bloomberg red
FT_BLUE = '#1B4F72'      # Deep blue
FT_LIGHT_BLUE = '#5DADE2'
FT_GREEN = '#27AE60'
FT_ORANGE = '#E67E22'
FT_GREY = '#95A5A6'
FT_GRID = '#D5D0C8'      # Subtle grid

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8,
    'axes.titlesize': 11,
    'axes.labelsize': 8,
})


def hormuz_blockade_map():
    """Strait of Hormuz blockade zone map — FT style."""
    fig = plt.figure(figsize=(12, 9), facecolor=FT_BG)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_facecolor(FT_BG)
    ax.set_extent([42, 62, 22, 30], crs=ccrs.PlateCarree())

    # Base geography
    ax.add_feature(cfeature.LAND, facecolor='#E8E4DB', edgecolor='#D5D0C8', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='#DEE5EB')
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_MUTED, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, edgecolor='#B8B0A0', linewidth=0.6, linestyle=':')
    ax.add_feature(cfeature.LAKES, facecolor='#DEE5EB', edgecolor='#B8B0A0', linewidth=0.3)

    # Gridlines - FT style (subtle)
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color=FT_GRID, alpha=0.5, linestyle='-')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 7, 'color': FT_MUTED}
    gl.ylabel_style = {'size': 7, 'color': FT_MUTED}

    # Country labels
    labels = [
        (46.5, 26.0, 'SAUDI\nARABIA', FT_TEXT),
        (51.5, 27.0, 'BAHRAIN', FT_MUTED),
        (51.2, 25.3, 'QATAR', FT_MUTED),
        (55.5, 24.0, 'UAE', FT_MUTED),
        (57.5, 23.0, 'OMAN', FT_MUTED),
        (44.5, 25.0, 'IRAQ', FT_MUTED),
        (48.0, 28.5, 'KUWAIT', FT_MUTED),
        (59.0, 27.5, 'IRAN', FT_TEXT),
    ]
    for lon, lat, name, color in labels:
        ax.text(lon, lat, name, transform=ccrs.PlateCarree(),
               fontsize=8, fontweight='bold' if color == FT_TEXT else 'normal',
               color=color, ha='center', va='center')

    # Strait of Hormuz annotation
    hormuz_lon, hormuz_lat = 56.0, 26.5
    ax.plot(hormuz_lon, hormuz_lat, 's', color=FT_RED, markersize=6, 
            transform=ccrs.PlateCarree(), markeredgecolor='white', markeredgewidth=1.5, zorder=10)
    ax.annotate('Strait of\nHormuz', xy=(56.0, 26.5), xytext=(57.0, 27.8),
               transform=ccrs.PlateCarree(),
               fontsize=9, fontweight='bold', color=FT_RED,
               ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_RED, lw=1.5))

    # Blockade enforcement zone (shaded area)
    from shapely.geometry import Polygon
    blockade_pts = [(52, 24), (58, 24), (60, 28), (54, 29), (52, 24)]
    blockade_poly = Polygon(blockade_pts)
    ax.add_geometries([blockade_poly], crs=ccrs.PlateCarree(),
                     facecolor=FT_RED, alpha=0.08, edgecolor=FT_RED, linewidth=1.5, linestyle='--')

    # Blockade label
    ax.text(55.0, 28.0, 'BLOCKADE ENFORCEMENT ZONE\n200 aircraft · 25 ships', 
           transform=ccrs.PlateCarree(), fontsize=7, color=FT_RED, 
           ha='center', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=FT_RED, alpha=0.85))

    # Vessel turn-back markers
    vessel_positions = [
        (56.8, 26.0, '42 vessels\nturned back'),
        (54.5, 25.5, 'Insurance\nwithdrawn'),
        (58.2, 27.0, 'AIS jamming\nactive'),
    ]
    for lon, lat, label in vessel_positions:
        ax.plot(lon, lat, 'v', color=FT_ORANGE, markersize=8, 
               transform=ccrs.PlateCarree(), markeredgecolor='white', markeredgewidth=1, zorder=10)
        ax.text(lon - 0.3, lat - 0.5, label, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_ORANGE, fontweight='bold', ha='right', va='top')

    # Key ports
    ports = [
        (56.3, 27.2, 'Bandar Abbas', 'Iranian naval\nbase'),
        (54.4, 24.5, 'Khalifa Port', 'UAE hub'),
        (56.0, 23.5, 'Fujairah', 'Key bunkering\nport'),
    ]
    for lon, lat, name, note in ports:
        ax.plot(lon, lat, 'o', color=FT_BLUE, markersize=4, 
               transform=ccrs.PlateCarree(), zorder=10)
        ax.text(lon, lat, f' {name}', transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_BLUE, fontweight='bold', ha='left', va='bottom')

    # Oil field markers
    oil_fields = [
        (49.5, 28.5, '🛢'),
        (51.0, 26.0, '🛢'),
        (53.0, 25.5, '🛢'),
    ]
    for lon, lat, marker in oil_fields:
        ax.text(lon, lat, marker, transform=ccrs.PlateCarree(), fontsize=10, ha='center', va='center')

    # Title block — FT style
    ax.text(42, 30.5, 'Strait of Hormuz — Blockade Enforcement Zone', 
           transform=ccrs.PlateCarree(), fontsize=13, fontweight='bold', color=FT_TEXT, ha='left')
    ax.text(42, 29.8, 'Operation Epic Fury · 1 May 2026 · 200+ aircraft · 25 vessels deployed', 
           transform=ccrs.PlateCarree(), fontsize=8, color=FT_MUTED, ha='left')

    # Key metrics sidebar
    metrics_text = (
        "KEY METRICS\n"
        "━━━━━━━━━\n"
        "Vessels turned back: 42\n"
        "Brent crude: $124.67/bbl\n"
        "Militia strikes: 400+\n"
        "Aircraft deployed: 200\n"
        "Naval vessels: 25\n"
        "Affected countries: 6"
    )
    ax.text(60.5, 30.0, metrics_text, transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_TEXT, ha='left', va='top',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=FT_GRID, alpha=0.9),
           fontfamily='monospace')

    # Scale bar
    ax.plot([42, 47], [22.2, 22.2], color=FT_MUTED, linewidth=2, transform=ccrs.PlateCarree())
    ax.plot([42, 42], [22.0, 22.4], color=FT_MUTED, linewidth=1.5, transform=ccrs.PlateCarree())
    ax.plot([47, 47], [22.0, 22.4], color=FT_MUTED, linewidth=1.5, transform=ccrs.PlateCarree())
    ax.text(44.5, 21.9, '~500 km', transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_MUTED, ha='center')

    # Source
    ax.text(42, 22.0, 'Sources: JMIC, UKMTO, Windward, US Navy CENTCOM · TREVOR Assessment',
           transform=ccrs.PlateCarree(), fontsize=6, color=FT_MUTED, ha='left', style='italic')

    plt.savefig(f"{OUTPUT}/map-hormuz-blockade.png", dpi=250, bbox_inches='tight', facecolor=FT_BG)
    plt.close()
    print("  ✅ map-hormuz-blockade.png")


def militia_strike_map():
    """Regional militia strike activity map — FT/Bloomberg style."""
    fig = plt.figure(figsize=(12, 8), facecolor=FT_BG)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_facecolor(FT_BG)
    ax.set_extent([32, 62, 20, 38], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND, facecolor='#E8E4DB', edgecolor='#D5D0C8', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='#DEE5EB')
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_MUTED, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, edgecolor='#B8B0A0', linewidth=0.6, linestyle=':')
    ax.add_feature(cfeature.LAKES, facecolor='#DEE5EB', edgecolor='#B8B0A0', linewidth=0.3)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color=FT_GRID, alpha=0.5, linestyle='-')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 7, 'color': FT_MUTED}
    gl.ylabel_style = {'size': 7, 'color': FT_MUTED}

    # Country labels
    country_pos = {
        'IRAQ': (44.0, 33.5), 'IRAN': (55.0, 34.0), 'SAUDI\nARABIA': (45.0, 24.5),
        'KUWAIT': (47.8, 29.5), 'BAHRAIN': (50.5, 26.0), 'QATAR': (51.2, 25.3),
        'UAE': (54.5, 24.0), 'OMAN': (57.0, 22.5), 'JORDAN': (36.5, 31.0),
        'ISRAEL': (34.8, 31.5), 'SYRIA': (38.5, 35.0),
    }
    for name, (lon, lat) in country_pos.items():
        ax.text(lon, lat, name, transform=ccrs.PlateCarree(),
               fontsize=7, fontweight='bold', color=FT_MUTED, ha='center', va='center', alpha=0.7)

    # Strike data by country
    strikes = [
        ('Iraq', 44.0, 33.5, 120, FT_RED),
        ('Saudi Arabia', 46.0, 26.0, 85, FT_ORANGE),
        ('Kuwait', 47.8, 29.5, 55, FT_ORANGE),
        ('UAE', 54.5, 24.0, 60, FT_ORANGE),
        ('Qatar', 51.2, 25.3, 40, FT_GOLD),
        ('Bahrain', 50.5, 26.0, 25, FT_GOLD),
        ('Jordan', 36.5, 31.0, 15, FT_GREY),
    ]
    
    for name, lon, lat, count, color in strikes:
        size = count * 2 + 10
        ax.scatter(lon, lat, s=size, c=color, alpha=0.7, 
                  edgecolors='white', linewidth=1.5, transform=ccrs.PlateCarree(), zorder=8)
        ax.text(lon + 0.8, lat + 0.5, f'{count}', transform=ccrs.PlateCarree(),
               fontsize=8, fontweight='bold', color=color)

    # Militia base locations (Iraq)
    militia_bases = [
        (44.3, 33.2, 'Popular\nMobilization\nForces'),
        (44.0, 31.5, 'Kata\'ib\nHezbollah'),
        (44.5, 30.3, 'Asa\'ib\nAhl al-Haq'),
    ]
    for lon, lat, name in militia_bases:
        ax.plot(lon, lat, '^', color=FT_RED, markersize=6, 
               transform=ccrs.PlateCarree(), markeredgecolor='white', markeredgewidth=1, zorder=10)
        ax.text(lon - 0.5, lat, name, transform=ccrs.PlateCarree(),
               fontsize=6, color=FT_RED, ha='right', va='center', fontweight='bold')

    # Israeli defensive weapons delivery to UAE
    ax.annotate('Israel → UAE\nAdvanced defensive\nweaponry delivery',
               xy=(54.5, 24.0), xytext=(49.0, 28.0),
               transform=ccrs.PlateCarree(),
               fontsize=7, color=FT_BLUE, fontweight='bold', ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_BLUE, lw=1.5, connectionstyle='arc3,rad=0.3'))

    # Islamic Resistance in Iraq label
    ax.text(44.0, 37.0, '"Islamic Resistance in Iraq"\nCoalition · 400+ combined strikes',
           transform=ccrs.PlateCarree(), fontsize=8, color=FT_RED, fontweight='bold', ha='center',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=FT_RED, alpha=0.85))

    # Title
    ax.text(32, 38.5, 'Iran-Aligned Militia Strikes — Regional Impact', 
           transform=ccrs.PlateCarree(), fontsize=13, fontweight='bold', color=FT_TEXT, ha='left')
    ax.text(32, 37.8, '"Islamic Resistance in Iraq" coalition · 400+ strikes across 6 countries · 1 May 2026', 
           transform=ccrs.PlateCarree(), fontsize=8, color=FT_MUTED, ha='left')

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=FT_RED, alpha=0.7, label='>100 strikes'),
        mpatches.Patch(facecolor=FT_ORANGE, alpha=0.7, label='40-85 strikes'),
        mpatches.Patch(facecolor=FT_GOLD, alpha=0.7, label='15-40 strikes'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor=FT_RED, markersize=8, label='Militia HQ'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=7,
             framealpha=0.9, edgecolor=FT_GRID, facecolor='white')

    # Source
    ax.text(32, 20.5, 'Sources: Institute for the Study of War, FDD, open-source reporting · TREVOR Assessment',
           transform=ccrs.PlateCarree(), fontsize=6, color=FT_MUTED, ha='left', style='italic')

    plt.savefig(f"{OUTPUT}/map-militia-strikes.png", dpi=250, bbox_inches='tight', facecolor=FT_BG)
    plt.close()
    print("  ✅ map-militia-strikes.png")


def global_impact_map():
    """Global impact map showing oil flows, affected routes — FT style."""
    fig = plt.figure(figsize=(14, 8), facecolor=FT_BG)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson(central_longitude=20))
    ax.set_facecolor(FT_BG)
    ax.set_global()

    ax.add_feature(cfeature.LAND, facecolor='#E8E4DB', edgecolor='#D5D0C8', linewidth=0.3)
    ax.add_feature(cfeature.OCEAN, facecolor='#DEE5EB')
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_MUTED, linewidth=0.3)
    ax.add_feature(cfeature.BORDERS, edgecolor='#B8B0A0', linewidth=0.3, linestyle=':')
    ax.add_feature(cfeature.LAKES, facecolor='#DEE5EB', edgecolor='#B8B0A0', linewidth=0.3)
    ax.stock_img()

    # Gridlines
    gl = ax.gridlines(linewidth=0.2, color=FT_GRID, alpha=0.5, linestyle='-', draw_labels=False)

    # Major oil shipping routes from Hormuz
    routes = [
        ([56, 54, 50, 45, 38, 30, 20, 10, 0], [26, 26, 27, 28, 28, 28, 28, 28, 28], 'Europe', '#1B4F72'),
        ([56, 58, 62, 66, 70, 75, 80, 85, 90, 100, 110, 120], [26, 26, 25, 24, 22, 20, 18, 16, 14, 10, 6, 2], 'Asia-Pacific', '#27AE60'),
        ([56, 54, 52, 50, 48, 46, 44, 42, 40, 38, 36], [26, 26, 25, 24, 23, 22, 20, 18, 16, 14, 12], 'Africa (Cape)', '#E67E22'),
    ]
    
    for route_lons, route_lats, label, color in routes:
        ax.plot(route_lons, route_lats, color=color, linewidth=2.5, alpha=0.5, 
               transform=ccrs.PlateCarree(), linestyle='--')
        ax.plot(route_lons, route_lats, color=color, linewidth=1, alpha=0.7,
               transform=ccrs.PlateCarree(), linestyle=':', zorder=5)
        ax.text(route_lons[-1], route_lats[-1], label, transform=ccrs.PlateCarree(),
               fontsize=7, color=color, fontweight='bold', ha='left')

    # Hormuz chokepoint highlight
    ax.scatter(56, 26.5, s=200, c=FT_RED, alpha=0.6, edgecolors='white', linewidth=2, 
              transform=ccrs.PlateCarree(), zorder=10)
    ax.annotate('STRAIT OF HORMUZ\n~20 mb/d throughput\nBLOCKADED', 
               xy=(56, 26.5), xytext=(50, 32),
               transform=ccrs.PlateCarree(),
               fontsize=8, color=FT_RED, fontweight='bold', ha='center',
               arrowprops=dict(arrowstyle='->', color=FT_RED, lw=2))

    # Other chokepoints
    chokepoints = [
        (44, 12.5, 'Bab el-Mandeb\n(Houthi risk)'),
        (36, 35, 'Turkish Straits'),
        (4.5, 51.5, 'English Channel'),
        (103, 1.5, 'Malacca Strait'),
    ]
    for lon, lat, label in chokepoints:
        ax.scatter(lon, lat, s=60, c=FT_ORANGE, alpha=0.5, edgecolors='white', linewidth=1,
                  transform=ccrs.PlateCarree(), zorder=9)
        ax.text(lon, lat - 3, label, transform=ccrs.PlateCarree(),
               fontsize=6, color=FT_ORANGE, ha='center', fontweight='bold')

    # Impact annotations
    impacts = [
        (-10, 52, 'EUROPE\nGas +70%\nRecession risk\n↑'),
        (120, 35, 'JAPAN/KOREA\nLNG prices +45%\nStrategic reserves\nactivated'),
        (80, 5, 'S. ASIA\nFuel crisis\nSri Lanka, Pakistan\nworst hit'),
        (-80, 25, 'AMERICAS\n$124.67/bbl\nInflation pressure\n↑'),
    ]
    for lon, lat, text in impacts:
        ax.text(lon, lat, text, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_TEXT, ha='center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=FT_GRID, alpha=0.85))

    # Title
    ax.text(-170, 20, 'Global Energy Disruption — Chokepoint Cascade', 
           transform=ccrs.PlateCarree(), fontsize=13, fontweight='bold', color=FT_TEXT, ha='left')
    ax.text(-170, 14, 'Hormuz blockade cascading through global supply chains · 1 May 2026', 
           transform=ccrs.PlateCarree(), fontsize=8, color=FT_MUTED, ha='left')

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], color='#1B4F72', linewidth=2, linestyle='--', label='Europe-bound oil'),
        plt.Line2D([0], [0], color='#27AE60', linewidth=2, linestyle='--', label='Asia-Pacific oil'),
        plt.Line2D([0], [0], color='#E67E22', linewidth=2, linestyle='--', label='Africa/Cape route'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=FT_RED, markersize=8, label='Blockaded chokepoint'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=FT_ORANGE, markersize=6, label='At-risk chokepoint'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=6,
             framealpha=0.9, edgecolor=FT_GRID, facecolor='white')

    plt.savefig(f"{OUTPUT}/map-global-impact.png", dpi=250, bbox_inches='tight', facecolor=FT_BG)
    plt.close()
    print("  ✅ map-global-impact.png")


def ukraine_adaptation_map():
    """Ukraine-Gulf security partnerships map."""
    fig = plt.figure(figsize=(10, 7), facecolor=FT_BG)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_facecolor(FT_BG)
    ax.set_extent([20, 60, 20, 55], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND, facecolor='#E8E4DB', edgecolor='#D5D0C8', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='#DEE5EB')
    ax.add_feature(cfeature.COASTLINE, edgecolor=FT_MUTED, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, edgecolor='#B8B0A0', linewidth=0.6, linestyle=':')
    ax.add_feature(cfeature.LAKES, facecolor='#DEE5EB', edgecolor='#B8B0A0', linewidth=0.3)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color=FT_GRID, alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 7, 'color': FT_MUTED}
    gl.ylabel_style = {'size': 7, 'color': FT_MUTED}

    # Ukraine
    ax.scatter(31, 49, s=150, c=FT_BLUE, alpha=0.8, edgecolors='white', linewidth=2, 
              transform=ccrs.PlateCarree(), zorder=10)
    ax.text(31, 50.5, 'UKRAINE', transform=ccrs.PlateCarree(),
           fontsize=9, fontweight='bold', color=FT_BLUE, ha='center')
    ax.text(31, 48.5, 'Anti-drone specialists\ndeployed to 5 Gulf states', 
           transform=ccrs.PlateCarree(), fontsize=6.5, color=FT_MUTED, ha='center')

    # Gulf states
    gulf_states = [
        (46.7, 24.7, 'Saudi Arabia', 'Security pact\nsigned ✅'),
        (51.5, 25.3, 'Qatar', 'Security pact\nsigned ✅'),
        (54.4, 24.0, 'UAE', 'Anti-drone\ndeployment active'),
    ]
    for lon, lat, name, note in gulf_states:
        ax.scatter(lon, lat, s=120, c=FT_GOLD, alpha=0.8, edgecolors='white', linewidth=2,
                  transform=ccrs.PlateCarree(), zorder=10)
        ax.text(lon, lat + 1.5, name, transform=ccrs.PlateCarree(),
               fontsize=7, fontweight='bold', color=FT_TEXT, ha='center')
        ax.text(lon, lat - 1.5, note, transform=ccrs.PlateCarree(),
               fontsize=6.5, color=FT_MUTED, ha='center')

    # Connection lines
    connections = [(46.7, 24.7), (51.5, 25.3), (54.4, 24.0)]
    for lon, lat in connections:
        ax.plot([31, lon], [48, lat], color=FT_BLUE, linewidth=1, alpha=0.4,
               transform=ccrs.PlateCarree(), linestyle='-', zorder=1)

    # Russia
    ax.scatter(37, 55, s=100, c=FT_RED, alpha=0.4, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=8)
    ax.text(37, 56, 'RUSSIA', transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_RED, ha='center')
    ax.text(37, 54.5, 'Grain theft\nstolen cargo', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_MUTED, ha='center')

    # Israel
    ax.scatter(34.8, 31.5, s=80, c=FT_BLUE, alpha=0.6, edgecolors='white', linewidth=1,
              transform=ccrs.PlateCarree(), zorder=8)
    ax.text(34.8, 32.5, 'ISRAEL', transform=ccrs.PlateCarree(),
           fontsize=7, color=FT_BLUE, ha='center')
    ax.text(34.8, 30.5, 'Ukraine requests\nstolen grain seizure', transform=ccrs.PlateCarree(),
           fontsize=6, color=FT_MUTED, ha='center')

    # Title
    ax.text(20, 55.5, 'Ukraine Strategic Adaptation — Gulf Partnerships', 
           transform=ccrs.PlateCarree(), fontsize=13, fontweight='bold', color=FT_TEXT, ha='left')
    ax.text(20, 54.8, 'Military-technical cooperation · 1 May 2026', 
           transform=ccrs.PlateCarree(), fontsize=8, color=FT_MUTED, ha='left')

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=FT_BLUE, markersize=8, label='Security partner'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=FT_GOLD, markersize=8, label='Gulf signatory'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=7,
             framealpha=0.9, edgecolor=FT_GRID, facecolor='white')

    plt.savefig(f"{OUTPUT}/map-ukraine-gulf.png", dpi=250, bbox_inches='tight', facecolor=FT_BG)
    plt.close()
    print("  ✅ map-ukraine-gulf.png")


if __name__ == "__main__":
    os.makedirs(OUTPUT, exist_ok=True)
    print("Generating FT/Bloomberg-style maps...")
    hormuz_blockade_map()
    militia_strike_map()
    global_impact_map()
    ukraine_adaptation_map()
    print(f"\nAll maps saved to {OUTPUT}/")
