---
name: daily-4-briefings
description: Compose and email 4 daily briefings (UK, Trump, Markets, Sports) at 8am PT
version: 1.0.0
author: Trevor
created: 2026-05-11
tags: [publishing, email, briefings, cron]
---

# Daily 4 Briefings

## When to Use
Every day at 8am PT via cron ID `9ee44803-223c-45cc-ad59-f404919bd5f9`.

## Sources
- Web search for latest news in 4 categories
- Existing brief analysis data for UK/Trump/Markets sections
- Polymarket/Kalshi for prediction market odds
- ESPN/Fox Sports/Soccerbase for sports

## Format
Plain text email, 4 sections separated by ═══ dividers:
1. UK News Update — politics, economy, international
2. Trump Leadership Analysis — what he might do this week
3. Financial Market Review — equities, oil, data calendar, bets
4. Global Sports Review — leagues, playoffs, tournaments, bets

## Delivery
- To: roderick.jones@gmail.com
- From: trevor.mentis@gmail.com
- Via: Maton Gmail API
- Subject: "Your 4 Daily Briefings — <today date>"

## Pitfalls
- Cross-section repetition (Trump Polymarket numbers appear in both §2 and §3)
- Sports odds math verification needed
- Oil price consistency (Brent vs WTI) must reconcile
- Add "Top 3 Today" summary at the top for busy executive scan
