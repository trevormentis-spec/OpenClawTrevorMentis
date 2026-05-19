# TOS_REVIEW — Sites Flagged for Programmatic Access Restrictions

This file tracks sites whose Terms of Service explicitly prohibit programmatic access,
automated scraping, or API use outside published developer APIs. If a target site is
listed here, halt collection and do not proceed without Roderick's explicit review.

## Flagged Sites

| Site | TOS Clause | Date Flagged | Status |
|---|---|---|---|
| (none yet) | | | |

## Review Protocol

1. Before adding a site to `_specs/`, check its `robots.txt` and Terms of Service
2. If TOS explicitly prohibits automated access (not just "don't overload our servers"):
   - Do NOT proceed with collection
   - Add the site to this table
   - Flag for Roderick's review with the relevant TOS language
3. If TOS allows API access but requires attribution or rate limiting:
   - Implement attribution/rate limiting in the spec
   - Document the requirement in the spec metadata

## Known Safe Categories

These site categories are generally safe for programmatic access, but always verify:

- **Open/public APIs** (Wikipedia, HackerNews, arXiv, etc.) — explicitly designed for API access
- **News sites with RSS feeds** (Reuters, BBC, Al Jazeera) — RSS is an implicit API
- **Government/public data portals** — public domain or open data licensed
- **Sites with published developer APIs** — use the published API

## Known Restricted Categories

These site categories frequently prohibit automated access. Flag for review:

- **Social media platforms** (LinkedIn, Facebook, Instagram) — aggressive anti-scraping + login walls
- **Job boards** (LinkedIn Jobs, Indeed) — commercial data protection
- **E-commerce** (Amazon product data, price aggregation) — protected by TOS
- **Password-managed subscription content** — the access itself is a legal issue beyond automation
