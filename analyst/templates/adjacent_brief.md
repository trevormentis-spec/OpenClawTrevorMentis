# Adjacent Brief Template — Open Claw Mexico

**Use case:** The user asked about a non-Mexico topic that touches Mexico
through specific transmission vectors. This template replaces the standard
analyst prompt when scope_status == "adjacent".

**Do NOT use:** for in-scope topics (standard analyst prompt) or
out-of-scope topics (decline template).

## Prose Brief Structure (for chat responses)

Every adjacent brief follows this structure, in order:

### BLUF
One sentence on what this topic means for Mexico-exposed subscribers.

### Vector sections (3-5)
Each section is one transmission vector. Structure each:

**{Vector name} — {one-line impact judgment}**
- **Development:** What happened globally (1-2 sentences)
- **Mechanism to Mexico:** How this reaches Mexican assets, institutions,
  or interests (1-2 sentences)
- **Magnitude / Timing:** How big, how fast. Quantify where possible
  (e.g., "a $5/b Brent move swings Pemex revenue ~$2B/yr"; "Banxico
  next meets June 20")
- **Subscriber action line:** What a Mexico-exposed subscriber does with
  this information (e.g., "hedge MXN if Brent-MXN correlation breaks
  0.6"; "watch Pemex bond spread vs. EMHY"; "reduce peso duration
  before Banxico meeting")

### Calibration
Sherman Kent band on the directional thesis (e.g., "likely (65%) —
vector 1 is structural, vectors 2-3 amplify").

### Watch items
3-5 forward-looking indicators, each with a specific observable trigger
and a "what it means" signal.

## JSON Prompt Template (for pipeline)

```
ADJACENCY BRIEF MODE — The user's request is NOT directly about Mexico
but reaches it through specific transmission vectors. The output must
be a Mexico-first adjacent brief.

Structure the brief as:
- BLUF: one sentence on what this topic means for Mexico-exposed subscribers
- 3-5 sections, each a transmission vector:
  - Development (global context, 1-2 sentences)
  - Mechanism to Mexico (how it reaches MX assets/institutions)
  - Magnitude / Timing (quantified where possible)
  - Subscriber action line (what to do with the information)
- Calibration: Sherman Kent band on directional thesis
- Watch items: 3-5 forward-looking indicators with triggers and signals

Use NATO Admiralty source ratings. Use Sherman Kent confidence bands.

{adjacency_preamble_from_scope_check}

Output as valid JSON:
{
  "brief_type": "adjacent",
  "as_of_utc": "{date_utc}",
  "original_topic": "{user_topic}",
  "bluf": "...",
  "vectors": [
    {
      "name": "...",
      "development": "...",
      "mechanism_to_mexico": "...",
      "magnitude_timing": "...",
      "subscriber_action": "..."
    }
  ],
  "calibration": "{sherman kent band}",
  "watch_items": [
    {"indicator": "...", "trigger": "...", "signal": "..."}
  ]
}
```

## Quality discipline
- Every quantitative claim must be sourced. If you do not have a specific
  number from a named source, describe the direction and magnitude without
  inventing precision. "Corresponds to an ~X% increase" without a source
  is a fabrication, not analysis.
- Plausible directional theses are valuable without invented specific
  correlations. "This typically hardens enforcement posture in past
  episodes" is honest. "Every $0.25/gal corresponds to a 15% increase
  in X" without sourcing is a subscriber-trust failure.
- **Hard rule:** no unsourced specific percentages, correlations, or
  statistical claims. Direction + magnitude from a named source is fine.
  Specific numbers without a source are never fine.

## Do NOT
- Produce a generic global brief with Mexico paragraphs appended
- Use the decline template for adjacent topics
- Structure by geography rather than by vector
- Include standard regional analyses
- Invent specific correlations or percentages without a named source
