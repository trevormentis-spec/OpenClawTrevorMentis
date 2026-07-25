# ProseBench

ProseBench is a local-first, rubric-driven prose assessment and revision toolkit. It evaluates writing against transparent criteria, cites evidence for its judgments, proposes controlled revisions, and produces auditable reports.

It does **not** detect AI authorship and does not treat surface “human-like” features as writing quality.

## What the MVP includes

- Assessment of Markdown and plain-text prose against versioned YAML rubrics.
- Twelve criterion ratings with weighted points, quotations, rationales, confidence, and revision actions.
- Separate epistemic-integrity status rather than hiding integrity problems inside a style score.
- A revision coach that ranks global changes before sentence polishing.
- Controlled candidate rewrites under a strict no-new-facts rule.
- Automatic audits of numbers, URLs, citation tokens, and quotations before and after revision.
- Before-and-after draft comparison with descriptive metrics, a unified diff, and optional score deltas.
- Markdown, HTML, and JSON reports.
- OpenAI Structured Outputs plus a low-confidence offline diagnostic mode.
- `AGENTS.md` and tests for continued development with Codex.

## Install

```bash
cd prosebench
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -e ".[openai,dev]"
cp .env.example .env
```

For offline-only use, install without the OpenAI extra:

```bash
pip install -e ".[dev]"
```

For full assessment and revision, place an API key in `.env`:

```env
OPENAI_API_KEY=your_key_here
PROSEBENCH_MODEL=gpt-5.6
```

Keys are read from the environment and never written to reports.

## Quick start

```bash
# Show the bundled profiles
prosebench profiles

# Full assessment. `auto` uses OpenAI when a key is available.
prosebench assess examples/sample_essay.md \
  --profile academic_argument \
  --audience "municipal policy staff" \
  --purpose "recommend a risk-tiered oversight policy"

# Explicit offline diagnostics
prosebench assess examples/sample_essay.md --provider local

# Prioritized revision plan without changing the prose
prosebench coach examples/sample_essay.md --profile academic_argument

# Fact-locked candidate revision; the source file is never overwritten
prosebench revise examples/sample_essay.md \
  --focus development,macrostructure,diction \
  --fact-lock strict

# Compare drafts
prosebench compare draft-v1.md draft-v2.md

# Compare and reassess both drafts
prosebench compare draft-v1.md draft-v2.md --assess --provider openai
```

Reports go to `prosebench-reports/` unless `--output-dir` is supplied. A representative offline report is checked in at [`examples/sample_assessment.md`](examples/sample_assessment.md).

## The twelve dimensions

1. Rhetorical fit
2. Motive, problem, or stakes
3. Controlling idea, claim, or tension
4. Development, reasoning, or narrative movement
5. Support, evidence, and concrete particulars
6. Complexity, qualification, and counterpressure
7. Macrostructure and sequence
8. Paragraph and section cohesion
9. Sentence clarity, emphasis, and rhythm
10. Diction, precision, and economy
11. Voice, ethos, and originality of perception
12. Conventions, accessibility, and presentation

The provider returns evidence and 0–4 ratings. ProseBench validates the criterion IDs and calculates the total from checked-in weights, so the evaluator cannot silently alter the rubric or arithmetic.

## Bundled profiles

- `academic_argument`
- `professional_prose`
- `narrative_nonfiction`

Profiles share stable criteria and change only genre-sensitive weights. Every profile must total exactly 100 points.

## Providers

### OpenAI

Uses the Responses API with Pydantic Structured Outputs. The model is recorded in every report and can be changed through `PROSEBENCH_MODEL` or `--model`.

### Local

Uses deterministic surface diagnostics with no network request. It is useful for installation checks and basic mechanical signals, but every result is marked low confidence. It cannot reliably judge deep reasoning, originality, or literary quality.

### Auto

Uses OpenAI when `OPENAI_API_KEY` is available and otherwise falls back to local diagnostics.

## Revision safeguards

Revision is deliberately separated from assessment. The pipeline:

1. assesses the original;
2. chooses the highest-impact weaknesses or user-selected criteria;
3. requests a bounded candidate rewrite;
4. prohibits invented facts, citations, quotations, numbers, dates, names, examples, and personal experiences;
5. audits locked tokens;
6. saves the candidate and diff separately.

No command overwrites the original file.

## Responsible use

Model judgments remain fallible. ProseBench is a structured second reader, not the sole authority for a high-stakes grade. A score does not establish authorship, originality, factual accuracy, or policy compliance.

See [`docs/methodology.md`](docs/methodology.md) and [`docs/limitations.md`](docs/limitations.md).

## Develop with Codex

The repository includes [`AGENTS.md`](AGENTS.md). A suitable Codex task is:

> Add a legal-analysis rubric profile without changing the core criterion IDs. Make the weights total 100, add tests, and document how the profile differs from academic argument.

Run before committing:

```bash
pytest
prosebench assess examples/sample_essay.md --provider local
```

## License

MIT
