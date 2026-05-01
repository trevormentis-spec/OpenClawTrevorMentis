# ACH Matrix — {Question}

**Date:** {YYYY-MM-DD}
**Question:** {one sentence}

Analysis of Competing Hypotheses (Heuer). Score each hypothesis against each
piece of evidence:

- `++` strongly consistent
- `+`  consistent
- `0`  irrelevant / can't tell
- `-`  inconsistent
- `--` strongly inconsistent

The hypothesis with the **fewest disconfirming items** wins, not the one with
the most confirming items. (Confirmation is cheap; disconfirmation is what
breaks tied evidence.)

---

## Hypotheses

- **H1:** {statement}
- **H2:** {statement}
- **H3:** {statement}
- **H4 (alt / wildcard):** {statement}

---

## Evidence

| #   | Evidence item                                      | Source rating | H1 | H2 | H3 | H4 |
|-----|----------------------------------------------------|---------------|----|----|----|----|
| E1  | _…_                                                | A1            |    |    |    |    |
| E2  | _…_                                                | B2            |    |    |    |    |
| E3  | _…_                                                | C3            |    |    |    |    |
| E4  | _…_                                                | B2            |    |    |    |    |
| E5  | _…_                                                | A2            |    |    |    |    |
|     | **Disconfirming totals (count of `-` and `--`)**   |               |    |    |    |    |

---

## Result

- **Strongest hypothesis:** H{n} ({fewest disconfirms})
- **Probability band:** {Sherman Kent}
- **Sensitivity:** which evidence items, if revised, would flip the result?
- **What we'd want to collect to break the tie / strengthen the call:**
  _bullet_

---

## Notes

- Beware diagnosticity = 0 evidence. If every hypothesis scores `+` on it,
  the item is decorative — drop it from the matrix.
- Re-run the matrix when **two new high-rated** evidence items arrive.
