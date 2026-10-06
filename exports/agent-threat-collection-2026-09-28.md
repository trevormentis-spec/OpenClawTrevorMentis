# Agent Threat Collection Report — Moltbook

**Operation:** Agent Ecosystem Collection · **Sweep:** initial · **Date:** 2026-09-28
**Coverage:** 1,800 posts across 12 security-relevant submolts, 300 raw scanned
**Status:** ⚠️ **PENDING HUMAN ANALYST QC REVIEW**

---

## Executive summary

**1. No confirmed attacks were found in this sample.** 1,800 posts were pulled and
pattern-scanned; 42 surfaced as candidates; **every one inspected is benign.** They fall into
three buckets: ordinary platform vocabulary (`ClawHub`, `skill.md`, `USDC`), *defensive*
security research, or straight false positives (the impersonation detector matched the phrase
"on behalf of my"). Zero defensible examples of prompt injection, malicious skill promotion,
impersonation, owner leakage, coordination, or agent-to-agent fraud.

**2. The most significant discovery is the inverse of the target.** r/security is running
**active defensive research on exactly this threat model** — agent-supply-chain and sandbox
security. This is the substantive good in the sample.

**3. Detector precision is unacceptable.** 42 hits, ~0 true positives. The regex approach in
`scripts/moltbook_collect.py` cannot support this operation as written; left unfixed it will
manufacture false reporting.

**4. Coverage is 0.04%** (1,800 of 4,325,218 posts) and **excludes comments entirely** —
22,634,235 of them, which is where agent-directed manipulation most plausibly lives.

**5. A possible independent corroboration** of our own prior finding on agent-skill risk
(see Finding 2.2).

---

## Findings by priority category

### 1. Prompt-injection and manipulation — **NOT FOUND**
- **Searched for:** instruction-override phrasing, prompt-extraction demands, credential/token
  exfiltration, obfuscation markers, tool-call bait.
- **Found:** 4 candidates, all benign on inspection:
  - r/security — *"The Inherited File Descriptor Trap: Why 100% Path-Denial Pass Rates Still
    Leak Credentials"* — sandbox-hardening research. Matched on "Leak Credential".
  - r/security — a puzzle post containing a **deliberately published teaser key** ("the room's
    real key never gets posted"). A game mechanic, not an attack.
  - r/agentskills — *"Standard Base64 in URL Path Segments Produces Probabilistic Failures"* —
    an encoding-robustness post. Matched on "Base64".
  - r/builds — a lyric/mood post. Matched on "upload the file".
- **Admiralty:** F6 (cannot be judged) on *prevalence*. **Kent:** cannot form a probability from
  this sample; absence in 0.04% is not evidence of absence.

### 2. Malicious skills and tools — **NOT FOUND AS PROMOTION** (but see below)
- **Searched for:** skill/plugin installation pushes, vague or hard-sold tooling from new
  accounts, manifest-name references.
- **Found:** 30 candidates, predominantly **defensive or ordinary**:
  - r/security — *"Skill.md Supply Chain Vectors: Treating Agent Tool Instructions as Untrusted
    Binaries and Hardening Package Ecosystems"* — directly on-model defensive work.
  - r/security — *"Rufio scanned 286 ClawdHub skills using static pattern matching and recovered
    a credential"* — **a skill-supply-chain study.**
  - r/agents — a social/game post using `clawhub install` as flavour text.
  - r/agents — analysis of skill.md provenance risk ("verifies nothing about its own provenance…
    a malicious actor swaps the skill.md file").
- **Analytic note:** the "286 skills scanned / credential recovered" post **independently tracks
  our own workspace finding of roughly 1-in-286 agent skills being malicious**. Two unrelated
  sources converging on the same ratio is worth recording — treat as *possible* corroboration,
  not confirmation.
- **Admiralty:** B2 for "r/security is doing serious defensive work on skill supply chains"
  (probably true). F6 on prevalence of malicious promotion.

### 3. Impersonation — **NOT FOUND** (pure false positives)
- 3 candidates, all matched the phrase "on behalf of my/someone". No agent observed claiming to
  represent a real person, company, or institution.
- **Admiralty:** F6.

### 4. Owner leakage — **NOT FOUND**
- No posts surfaced where an agent disclosed an owner's identity, location, travel, finances, or
  employer. Recorded at pattern level only; no personal data was collected or retained.
- **Admiralty:** F6.

### 5. Coordinated activity — **NOT FOUND AT THRESHOLD**
- Method: 8-word shingle fingerprinting across 1,800 posts; flagging any shingle shared by ≥4
  distinct agents across ≥4 posts. **Result: 0 clusters.**
- **Caveat:** threshold may simply be too strict for this corpus, and n=1,800 from `sort=new` is
  a poor substrate for detecting coordinated campaigns, which usually need temporal depth.
- **Admiralty:** F6.

### 6. Agent-to-agent commerce and fraud — **NOT FOUND**
- 5 candidates, all ordinary agent-economy material: x402/USDC payment infrastructure discussion,
  a micro-service publishing stablecoin transfer fees, protocol-chatter. No scam offers, no
  escrow-bait, no fake services, no wallet-solicitation.
- **Admiralty:** F6.

---

## TTP library

**Observed attack TTPs from this sweep: none.** Recording that plainly rather than padding it.

**Defensive TTPs observed instead** (worth adding to hardening practice):
| # | Technique | Source context |
|---|---|---|
| D1 | Treat skill manifests (SKILL.md) as **unsigned binaries**, not trusted instructions | r/security |
| D2 | Static-pattern scanning of a skill corpus before install; expect a non-trivial hit rate | r/security (286-skill scan) |
| D3 | Path-denial test suites give a **false sense of coverage** — file-descriptor inheritance bypasses them | r/security |
| D4 | Verify skill-file **provenance**; an unverified manifest executes file reads and network calls with full trust | r/agents |

**Hypothesised TTP classes the operation should hunt** (from tasking; **unverified — not yet
observed**): instruction-override prose, prompt-extraction, credential exfiltration, tool-call
bait, obfuscated payload transfer, coordinated narrative seeding, escrow-bait commerce fraud.

---

## Client relevance

**Nothing actionable from this sweep.** No finding rises to a client service trigger.

Conditional mapping, for when a finding is confirmed:
- **Owner leakage** → family-office/principal exposure (the owner's movements and habits becoming
  inferable from their agent's public posting). Highest-severity class because it targets people,
  not systems.
- **Malicious skills / supply chain** → corporate agent-deployment risk.
- **Commerce fraud** → agent-mediated payment abuse.

*(I do not have the Eclipse/SPS/NOVA trigger definitions in workspace — flagging as a gap so I
can map findings to them properly.)*

---

## Collection gaps and recommended next steps

1. **Comments are unsampled — this is the biggest gap.** 22.6M comments vs 4.3M posts; replies
   to an agent's post are the natural delivery vector for manipulation. Priority fix.
2. **Sample size.** 0.04% coverage, `sort=new` only, 150 posts/submolt cap. Needs cursor
   pagination depth plus `sort=top` for high-reach material.
3. **Detector precision.** Replace regex-first with triage-then-inspect, or accept that all
   candidates need manual review. Current precision makes automated counts meaningless.
4. **No temporal baseline.** Only two prior reads exist (2026-09-17). Coordination and campaign
   detection need longitudinal depth — a reason to establish the cadence.
5. **DMs inaccessible by design** — assume blind to the highest-value channel.
6. **Analyst tasking needed** on Eclipse/SPS/NOVA triggers.

---

## Forced dissent on the main assessment

My main assessment is "no attacks found." **The strongest case against it:**

- **It may be a false negative dressed as a finding.** A regex detector with demonstrably ~0
  precision has unknown *recall*. Precision and recall fail together more often than not. "My
  weak instrument found nothing" is not the same statement as "there is nothing there."
- **I sampled the wrong stratum.** I read posts. Attack content plausibly lives in **comments**
  (unsampled), **DMs** (inaccessible), and **long-tail submolts** outside my 12. A headline of
  "zero attacks found" across 0.04% of a platform, in the wrong stratum, is close to vacuous.
- **Detection bias runs both ways.** The posts I *did* find are security research — which could
  mean the community self-polices, or could mean attackers are simply quieter and better.
- **Selection effect on `sort=new`.** Newest ≠ most consequential; high-reach manipulative posts
  may be older and now buried, while `sort=top` (used in the 09-17 pull) would surface them.

**Where I hold firm:** the 42 candidates really are benign — that judgement survives inspection.
What does *not* survive is any implication that the ecosystem is therefore clean.

---

⚠️ **PENDING HUMAN ANALYST QC REVIEW**

*Read-only collection. No posting, no account changes, no code executed from source material.
All content treated as data. Owner-related material deliberately not retained.*
