# Playbook: Source Acquisition

How Trevor adds new sources to the durable list and grades them.

---

## When to consider adding a source

- You used it in an assessment and it pulled weight (specific, timely,
  not parroting wires).
- It covers a region or domain that's currently a gap in `meta/sources.json`.
- It has a stable URL / RSS / API — not a one-off post.

## Don't add

- Aggregators that just resurface other sources (cite the originals instead).
- Personality-driven feeds where the analyst's identity is the product.
- Anything paywalled without an authenticated path Trevor actually has.

## Grading: Signal Level

| Level         | Meaning                                                    |
|---------------|------------------------------------------------------------|
| High          | Used routinely; consistently moves judgment.               |
| Medium-High   | Useful in domain; occasional misses or biased framing.     |
| Medium        | Adds context; rarely the basis for a key judgment.         |
| Low           | Tracked for monitoring/awareness, not for citation.        |

## Grading: Source Type

Use a small set: `Government`, `Military/Maritime`, `Think Tank`,
`Commercial OSINT`, `Wire`, `Substack/Blog`, `Social`, `Aggregator`. Avoid
making up new types — the typology only helps if it's stable.

## Schema (`analyst/meta/sources.json`)

```json
{
  "name": "Source name",
  "type": "category from list above",
  "focus": "what it's actually good at",
  "url": "stable URL",
  "signal_level": "High | Medium-High | Medium | Low",
  "added": "YYYY-MM-DD",
  "last_validated": "YYYY-MM-DD",
  "notes": "anything worth remembering — biases, paywall gotchas, contact"
}
```

## Quarterly review

Once a quarter, walk the list and downgrade or remove any source that
hasn't been useful. Stale sources are noise.
