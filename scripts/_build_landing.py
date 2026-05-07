#!/usr/bin/env python3
"""Build the landing page HTML from templates and dynamic data.

Usage: 
  python3 _build_landing.py --index <path> --summaries <json> --date <str> --issue <str>
"""
import json, os, re, argparse
from pathlib import Path

def load_kalshi_table(kalshi_path):
    """Parse Kalshi scan markdown into HTML table rows."""
    if not kalshi_path or not os.path.exists(kalshi_path):
        return ""
    content = Path(kalshi_path).read_text()
    rows = []
    for line in content.split('\n'):
        if line.startswith('KX'):
            parts = line.split()
            if len(parts) >= 7:
                series = parts[0]
                yes_bid = parts[1]
                vol = parts[6]
                rows.append(f'''<tr><td>{series}</td><td>{yes_bid}</td><td>{vol}</td></tr>''')
    return '\n'.join(rows[:8])


def build_theatre_grid(summaries):
    """Build theatre cards HTML from summaries JSON."""
    if not summaries:
        return ""
    cards = []
    for s in summaries:
        bluf = s.get('bluf', '')[:300]
        icon = s.get('icon', '🌍')
        label = s.get('label', s.get('theatre', ''))
        cards.append(f'''
<div class="theatre-card">
    <div class="theatre-header">
        <span class="theatre-icon">{icon}</span>
        <h3>{label}</h3>
        <span class="theatre-status">✓</span>
    </div>
    <p>{bluf}</p>
</div>''')
    return '\n'.join(cards)


def inject_after(html, marker, content):
    """Insert content after the first occurrence of marker."""
    idx = html.find(marker)
    if idx < 0:
        return html
    return html[:idx + len(marker)] + '\n' + content + html[idx + len(marker):]


def replace_between(html, start_marker, end_marker, new_content):
    """Replace content between start and end markers inclusive."""
    s = html.find(start_marker)
    e = html.find(end_marker)
    if s < 0 or e < 0 or e <= s:
        return html
    return html[:s] + new_content + html[e + len(end_marker):]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', required=True)
    parser.add_argument('--summaries', default='')
    parser.add_argument('--kalshi', default='')
    parser.add_argument('--date', default='')
    parser.add_argument('--issue', default='')
    parser.add_argument('--pdf', default='')
    parser.add_argument('--pdf-size', default='')
    args = parser.parse_args()

    html = Path(args.index).read_text()
    summaries = []
    if args.summaries and os.path.exists(args.summaries):
        summaries = json.loads(Path(args.summaries).read_text())
    
    date_pt = args.date
    issue = args.issue
    pdf_file = args.pdf
    pdf_size = args.pdf_size or '?'

    # 1. Update hero badge with current issue
    html = re.sub(
        r'<div class="hero-badge">[^<]+</div>',
        f'<div class="hero-badge">Issue #{issue} — {date_pt}</div>',
        html
    )

    # 2. Build the theatre grid
    theatre_html = build_theatre_grid(summaries)
    if theatre_html:
        html = replace_between(
            html,
            '<div class="theatre-grid">',
            '</div><!-- end theatres -->',
            f'<div class="theatre-grid">\n{theatre_html}\n        </div><!-- end theatres -->'
        )

    # 3. Add "Latest Brief" CTA section before pricing
    cta = ""
    if pdf_file:
        cta = f'''        <div style="text-align:center; padding: 60px 24px; background: var(--bg-secondary); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 12px;">📄 Latest Brief Available</h2>
            <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto 24px;">Issue #{issue} — {date_pt}. Full PDF with structured analysis, calibrated probability judgments, and prediction market integration across six theatres.</p>
            <a href="{pdf_file}" class="btn-hero" style="display:inline-block; padding: 14px 36px; background: var(--accent-gold); color: #0d0d0d; font-weight: 600; border-radius: 4px; text-transform: uppercase; letter-spacing: 1px;">Download Today\'s Brief ({pdf_size})</a>
        </div>'''

    pricing_marker = '<div class="pricing-grid">'
    if cta and pricing_marker in html:
        html = inject_after(html, '</div><!-- end theatres -->', cta)

    # 4. Add market data section before pricing
    kalshi_rows = load_kalshi_table(args.kalshi)
    if kalshi_rows:
        market_section = f'''    <!-- Market Data -->
    <section style="padding: 60px 24px; background: var(--bg-secondary); border-top: 1px solid var(--border);">
        <div class="container">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 8px;">📊 Prediction Market Snapshot</h2>
            <p style="color: var(--text-secondary); margin-bottom: 24px;">Live pricing from Kalshi — updated daily after the brief is published.</p>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <th style="text-align: left; padding: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Market</th>
                            <th style="text-align: left; padding: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Yes Bid</th>
                            <th style="text-align: left; padding: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        {kalshi_rows}
                    </tbody>
                </table>
            </div>
            <p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 12px;">Data from Kalshi. Refreshed {date_pt}. Not financial advice. TREVOR may hold positions.</p>
        </div>
    </section>'''

        if pricing_marker in html:
            html = html.replace(pricing_marker, market_section + '\n' + pricing_marker, 1)

    # 5. Update last-modified timestamp
    html = re.sub(
        r'Last updated: [^<]+',
        f'Last updated: {date_pt}',
        html
    )

    # 6. Write
    Path(args.index).write_text(html)
    print(f"Landing page updated — issue #{issue}, {date_pt}")
    print(f"  Theatres: {len(summaries)}")
    print(f"  Kalshi rows: {len(kalshi_rows.split(chr(10))) if kalshi_rows else 0}")
    if pdf_file:
        print(f"  PDF: {pdf_file}")


if __name__ == '__main__':
    main()
