# ProseBench instructions for Codex

## Purpose

ProseBench assesses and revises prose through transparent, versioned rubrics. It is not an AI detector or a detector-evasion tool.

## Product rules

1. Never infer authorship from prose style.
2. Never add a “human score,” detector score, or detector-avoidance workflow.
3. Keep prose quality and epistemic integrity as separate judgments.
4. Every scored criterion must cite evidence from the submitted document.
5. Application code, not the model, calculates weighted totals.
6. Rewrites must not invent facts, sources, quotations, names, dates, numbers, examples, or personal experience.
7. Never overwrite a source document.
8. Offline diagnostics must remain explicitly low confidence.
9. Do not make punctuation, vocabulary rarity, sentence length, dialect, or formality automatic quality penalties.
10. Add or update tests whenever the rubric, report schema, scoring pipeline, or claim lock changes.

## Architecture

- `prosebench/document.py`: parsing, paragraph locations, and descriptive metrics.
- `prosebench/rubric.py`: loading and validating versioned YAML profiles.
- `prosebench/providers/`: deterministic local diagnostics and OpenAI Structured Outputs.
- `prosebench/pipeline.py`: evidence validation, deterministic arithmetic, coaching, revision, and comparison.
- `prosebench/reports.py`: Markdown, HTML, JSON, and diff output.
- `prosebench/cli.py`: Typer commands.
- `prosebench/rubric_data/`: stable criterion IDs and genre-specific weights.

## Validation commands

```bash
pytest
prosebench profiles
prosebench assess examples/sample_essay.md --provider local
prosebench coach examples/sample_essay.md --provider local
prosebench revise examples/sample_essay.md --provider local --focus diction,sentence_craft
```

## Change discipline

- Keep Pydantic models backwards compatible where practical.
- Bump rubric versions when definitions or weights change.
- Preserve paragraph-location evidence in every criterion report.
- Document methodological changes in `docs/methodology.md`.
- Never expose API keys or hidden reasoning in report output.
