# Methodology

ProseBench treats prose assessment as a constrained evidence task rather than a free-form impression.

## Separate judgments

The broader framework distinguishes four questions:

1. **Prose quality:** rhetorical and craft performance in the finished text.
2. **Epistemic and source integrity:** whether factual claims, quotations, and sources are trustworthy or need checking.
3. **Authorial agency and process:** evidence of judgment and revision when a task assesses process.
4. **AI-use transparency and policy compliance:** whether tool use fits announced rules.

The MVP implements the first two and stores assignment context without collapsing everything into a “human” score.

## Evidence before arithmetic

The evaluator returns a structured object with criterion ratings, paragraph-located evidence, rationales, revision actions, integrity status, and confidence. Application code then:

- verifies that all criterion IDs appear exactly once;
- rejects missing or unknown criteria;
- attaches checked-in weights;
- calculates weighted points and totals;
- records model, profile version, context, metrics, and warnings.

## Revision hierarchy

The coach ranks criteria by weighted gap: `(4 - rating) × weight`. This is a pragmatic ordering heuristic. Global questions of purpose, claim, development, support, and sequence normally precede local polishing.

## Claim lock

The revision pipeline compares numbers, URLs, citation tokens, and direct quotations between source and candidate. Added, removed, or changed tokens are surfaced. This catches consequential drift but does not replace semantic fact checking.

## Offline diagnostics

The local provider inspects only visible proxies: document shape, support markers, connective language, repeated paragraph openings, sentence metrics, and a narrow set of verbose wrappers. It deliberately avoids authorship inference and labels all judgments low confidence.

## Calibration roadmap

A mature release should be calibrated against blinded, multiply scored prose across genres, proficiency levels, dialects, multilingual backgrounds, disciplines, and AI-use conditions. Validation should test criterion-level agreement, fairness, generalization, usefulness for later revision, and resistance to superficial gaming.
