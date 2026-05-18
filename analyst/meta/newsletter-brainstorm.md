# Newsletter Sources — Initial Brainstorm

**Generated:** 2026-05-18
**Model:** Anthropic Claude Opus 4.7
**Purpose:** Initial discovery for AgentMail newsletter subscription pipeline

---

## Priority 1 — Daily/Weekly Security & Cartel Sources

| Source | Category | Priority | Subscription | Est. Signal |
|--------|----------|----------|-------------|-------------|
| Insight Crime Mexico | Security | Critical | Free weekly | Very High |
| Wilson Center Mexico Institute | Policy | Critical | Free weekly | Very High |
| RANE/Stratfor Mexico | Security | High | Paid ($) | High |
| Borderland Beat | Cartel | Critical | Free/RSS | Very High |
| Justice in Mexico (USD) | Security | High | Free monthly | High |
| Los Angeles Times Mexico Coverage | General | Medium | Free | Medium |
| NYT Mexico Coverage | General | Medium | Free/paywall | Medium |
| Crisis24 Mexico Alerts | Security | High | Paid ($) | High |

## Priority 2 — Business & Economic

| Source | Category | Priority | Subscription | Est. Signal |
|--------|----------|----------|-------------|-------------|
| Mexico Business News | Business | Critical | Free weekly | Very High |
| LatinFinance | Finance | High | Paid ($) | High |
| El Financiero English | Finance | High | Free newsletter | Very High |
| Refinitiv Mexico | Markets | Medium | Terminal | Medium |
| Bloomberg Latam | Finance | Medium | Terminal | Medium |
| S&P Global Mexico | Markets | Medium | Paid | Medium |
| Moody's Mexico Reports | Credit | Medium | Paid | Low-Med |

## Priority 3 — Think Tank & Policy

| Source | Category | Priority | Subscription | Est. Signal |
|--------|----------|----------|-------------|-------------|
| AS/COA (Americas Quarterly) | Policy | High | Free weekly | High |
| CSIS Americas | Policy | High | Free | High |
| CFR Mexico | Policy | Medium | Free | Medium |
| Atlantic Council Latin America | Policy | Medium | Free | Medium |
| Baker Institute Mexico | Policy | Medium | Free | Medium |

## Priority 4 — Independent & Substack

| Source | Category | Priority | Type | Notes |
|--------|----------|----------|------|-------|
| Mexico Risk Monitor | Independent | High | Substack | Security analysis |
| The Mexico Report | Independent | Medium | Substack | Business/political hybrid |
| Border Security Report | Independent | High | Substack | US-MX border coverage |

## Priority 5 — Data & Statistics

| Source | Type | Cadence | Access |
|--------|------|---------|-------:|
| INEGI data releases | Government | Monthly/Quarterly | Free API |
| Banxico economic calendar | Central bank | Daily | Free |
| SIE (Banxico) | Central bank | Daily/Weekly | Free API |
| CBP monthly operations | US Government | Monthly | Free |
| US CBP trade statistics | US Government | Monthly | Free |

---

## First Subscription Wave (Top 10)

1. Insight Crime Mexico (free weekly)
2. Wilson Center Mexico Institute (free weekly)
3. Mexico Business News (free weekly)
4. Borderland Beat (free/RSS)
5. AS/COA Americas (free weekly)
6. CSIS Americas (free)
7. El Financiero newsletter (free)
8. Mexico Risk Monitor (Substack)
9. Justice in Mexico (free monthly)
10. RANE/Stratfor Mexico (paid)

---

## AgentMail Configuration

| Field | Value |
|-------|-------|
| AgentMail address | trevor_mentis@agentmail.to (existing) |
| Send method | AgentMail API (bearer token) |
| Receive method | AgentMail API / Gmail API (gmail_reader.py) |
| Inbox polling | Every 30 min via heartbeat |
| Newsletter folder | Separate from operational mail |
| Auto-process | Unsubscribe non-performing after 30 days |
