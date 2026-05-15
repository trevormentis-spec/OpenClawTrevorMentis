# Mexico Desk — Week 1 Status

**Date:** 2026-05-15
**Pivot Day:** 1 (pivot activated today, Friday)
**Note:** This is a partial week — the pivot directive was received and executed within a single day. Week 2 will be the first full week.

---

## Sources Added / Promoted / Demoted

### Added this week (62 total in new sources-mexico.json)

| Category | Count | Examples |
|----------|-------|---------|
| Spanish-language news | 10 | Reforma, El Universal, Milenio, Animal Politico, Proceso, El Financiero, Aristegui, La Jornada, El País México, El Economista |
| Specialist desks | 8 | Riodoce (Sinaloa), Pie de Página, Borderland Beat, InSight Crime Mexico, Quinto Elemento, A dónde van los desaparecidos, El Blog del Narco, Lantia Intelligence |
| Mexican government | 15 | DOF, SEDENA, SEMAR, FGR, SAT/Aduanas, Banxico, Pemex IR, CFE, CRE, CNH, INEGI, SESNSP, SECODAM, ASF, SE |
| US government | 10 | CBP, DEA, OFAC, USTR, State Dept Mexico, FBI Houston/El Paso, DHS, FinCEN, USMCA/CBP Trade |
| Think tanks | 8 | Wilson Center Mexico, Brookings LAI, RAND, ICG, Atlantic Council LAC, CSIS Americas, WOLA, MCCI |
| Individual analysts | 6 | Falko Ernst, Mike Vigil, Vanda Felbab-Brown, Cecilia Farfán-Méndez, Eduardo Guerrero, GZERO Latin America |
| Prediction markets | 2 | Kalshi Mexico, Polymarket Mexico |
| Financial/ratings | 3 | Fitch/Moody's/S&P Mexico, INEGI trade data, Houston Chronicle |

### Promoted (n/a — first week)

### Demoted (n/a — first week)

### Archived
- 95+ global sources from previous sources.json → `sources.archived.2026-05-15-1510.json`
- These remain accessible for context when non-Mexico stories impact Mexico

### Collection quality assessment
- **High confidence:** US government sources (CBP stats, OFAC designations, State Dept reports), Banxico data, INEGI statistics — authoritative and machine-readable
- **Medium confidence:** Spanish-language news (some paywall issues, variable accessibility), think tank reports
- **Low confidence:** Local specialist sources — some are intermittent, some behind paywalls, some have uncertain update cadence
- **Gap:** I have not yet tested the actual fetchability of all 62 sources. Paywall may be more restrictive than expected for Reforma, El Financiero, and some think tanks. This is a collection triage priority for week 2.

---

## Knowledge Architecture: Entities Deepened

### LDAP-7 Profiles Created
- **Sheinbaum, Claudia** — Full 7-dimension profile with master variable (AMLO-faction balance), decision-cycle diagnosis, CPCA ALL GREEN, 4 scenario forecasts. Stored at `brain/memory/semantic/ldap7-profiles/sheinbaum-claudia.md`

### Actors (seeded)
| Entity | Type | Completeness |
|--------|------|-------------|
| Sheinbaum | Political leader | Full LDAP-7 |
| CJNG / El Mencho | Cartel | Working profile in framework |
| (Chapitos, Mayos, CDN, CU covered in cartel framework but not yet individual actor files) | | |

### Geography (seeded)
| Region | File | Completeness |
|--------|------|-------------|
| Sinaloa | `geography/sinaloa.md` | Working — covers economy, politics, criminal dynamics, watch items |

### Frameworks Created
| Framework | File | Notes |
|-----------|------|-------|
| Cartel Factional Dynamics | `frameworks/cartel-factional-dynamics.md` | 6-axis, tested against 3 fronts |
| Huachicoleo | `frameworks/huachicoleo.md` | 4-layer intersection (corruption × cartel × infra × politics) |

### Chronologies Created
| Chronology | File | Notes |
|------------|------|-------|
| USMCA 2026 Review | `chronologies/usmca-2026.md` | Key dates, watch items, confidence assessment |

**Target for week 4: 30+ entity files.** Currently at ~8. On track but will need 2+ entities per day starting week 2.

---

## Calibration: Postdiction Results

### Status
- **Total judgments tracked:** 55 (from pre-pivot global analysis, May 8-14)
- **Correct:** 5
- **Incorrect:** 0
- **Unresolved:** 30 (time horizon hasn't elapsed)
- **Stale/expired (no postdiction run):** 20

### Honest assessment
The 5/5 correct with 0 incorrect is **suspicious and likely an artifact of the postdiction mechanism** — it appears to only resolve judgments where confirming evidence is available rather than honestly scoring all expired judgments. This is a calibration framework gap I'm flagging before any Mexico-specific predictions compound the problem.

### Mexico-specific calibration
- Zero Mexico-specific predictions have been made yet. The first set will accompany the first Mexico daily brief.
- I will not make a prediction I cannot postdict. The postdiction mechanism needs to be fixed first (see framework reflection memo).

### Key finding
The calibration-tracking data schema stores `by_region` with the old 6 global regions. This needs to change to `by_theme` (the 6 Mexico themes) for meaningful postdiction. Framework adaptation required.

---

## Creative Angles Generated

**None yet** — the creative angle generation loop requires sustained depth that doesn't exist on day 1 of a pivot. First batch will be produced by end of week 2.

---

## Skill Patches Proposed

**None yet** — no skills have been stress-tested against Mexico use cases. Expected pain points I anticipate:
1. `executive_protection_assessment` — assumes Western corporate context, not Mexican-billionaire-in-Sinaloa context
2. `social_post` — assumes English-only output; may need bilingual capability
3. Source ingest scripts — need Spanish-language interface for Reforma, Milenio, Animal Politico
4. Postdiction script — needs Mexico-theme schema update

---

## Open Mexico Questions I Cannot Answer (Day 1)

1. **What is the actual current state of the Sinaloa intra-CDS war?** I have general patterns but no ground truth from this week's Riodoce or InSight Crime reporting.
2. **What is Sheinbaum's private relationship with the AMLO faction?** Public reporting shows the split on Rocha, but I cannot assess whether this is a managed performance or genuine tension.
3. **How effective is the current SEDENA anti-huachicoleo campaign?** I have Pemex historical data but not May 2026 operational stats.
4. **What is El Mencho's actual health status?** Persistent rumors but no credible sourcing.
5. **Which Kalshi/Polymarket Mexico contracts exist?** Have not yet scanned. This is a week-2 priority.
6. **How much does the Rocha indictment reveal about Chapitos vs Mayos alignment?** The US charged 10 officials — I do not have the full list of names to assess factional targeting.

---

## Week 2 Priorities

1. Spanish-language source ingest — test fetchability of all 62 sources, build daily scan
2. Postdiction mechanism repair — fix script to handle expired judgment resolution
3. Actor files — deepen Chapitos, Mayos, El Mencho, Harfuch, Ebrard, Rocha
4. Kalshi/Polymarket Mexico contract scan
5. First Mexico daily brief (6 themes)
6. First Mexico-specific predictions for postdiction tracking

---

*Prepared by Open Claw Mexico*
*2026-05-15*
