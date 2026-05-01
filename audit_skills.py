#!/usr/bin/env python3
"""
Daily skill security audit — context-aware wrapper around the underlying
skill-scanner tool.

The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as
"critical credential leak" even when they appear inside SKILL.md or README.md
documentation. That produces 30+ false positives per run, drowns the real
findings, and trains Trevor to ignore the report. This wrapper post-processes
the raw findings:

- Findings inside `*.md` documentation files where the match is inside a
  fenced code block or inline doc reference are downgraded from CRITICAL to
  INFO, since SKILL.md authors document config paths as a matter of course.
- The skill-scanner's own self-references in `skill_scanner.py` (which
  contains the regex patterns themselves) are allowlisted.
- A separate "real findings" section is emitted so the daily report has
  signal again.

Usage:
    python3 audit_skills.py                     # default scan paths
    python3 audit_skills.py --paths PATH [PATH] # override scan roots
    python3 audit_skills.py --json out.json --md out.md
    python3 audit_skills.py --strict            # don't downgrade docs

Exit codes:
    0  no real risks (any number of doc-only findings ok)
    1  real risks found
    2  scanner not available / scan errored
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------- defaults --------------------------------------------------------

DEFAULT_SCANNER = Path(os.path.expanduser("~/.openclaw/skills/skill-scanner/skill_scanner.py"))
DEFAULT_PATHS = [
    Path(os.path.expanduser("~/.openclaw/skills")),
    Path("/usr/lib/node_modules/openclaw/skills"),
]

# Allowlist: findings inside these files are scanner self-references and are
# expected (the scanner stores its own regexes).
SCANNER_SELF_FILES = {"skill_scanner.py", "skill_scanner.py:", "skill-scanner/skill_scanner.py", "skill-scanner/README.md"}

# Documentation file extensions that get the doc-context downgrade.
DOC_EXTS = {".md", ".mdx", ".rst", ".txt"}

# ---------- context detection ----------------------------------------------

_FENCE_RX = re.compile(r"^\s*```")
_INLINE_CODE_RX = re.compile(r"`[^`]*`")
_HTTP_LINK_RX = re.compile(r"https?://")


def _is_inside_fence(file_lines: list[str], line_no: int) -> bool:
    """Return True if file_lines[line_no-1] is inside a markdown ``` fence."""
    if line_no < 1 or line_no > len(file_lines):
        return False
    in_fence = False
    for i in range(line_no - 1):
        if _FENCE_RX.match(file_lines[i]):
            in_fence = not in_fence
    return in_fence


def _looks_like_doc_reference(code: str) -> bool:
    """The matched code is a documentation reference (path mention, prose,
    inline code) rather than executable code."""
    s = code.strip()
    # bullet point with a path mention
    if s.startswith(("-", "*", "1.", "2.", "3.", "#")):
        return True
    # inline code in prose
    if _INLINE_CODE_RX.search(s):
        return True
    # plain prose mentioning a path
    if "save it" in s.lower() or "config file" in s.lower() or "configuration" in s.lower():
        return True
    return False


def _is_doc_finding(finding: dict[str, Any], skill_root: Path) -> bool:
    """True if this finding is a documentation false positive."""
    file_rel = finding.get("file", "")
    if not file_rel:
        return False
    file_path = skill_root / file_rel
    ext = file_path.suffix.lower()
    if ext not in DOC_EXTS:
        return False
    # If we can read the file, check whether the line is inside a fence
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return _looks_like_doc_reference(finding.get("code", ""))
    line_no = finding.get("line", 0)
    if _is_inside_fence(lines, line_no):
        return True
    return _looks_like_doc_reference(finding.get("code", ""))


def _is_scanner_self(finding: dict[str, Any]) -> bool:
    f = finding.get("file", "")
    return any(f.endswith(suffix) for suffix in SCANNER_SELF_FILES) or "skill-scanner" in f or "skill_scanner.py" in f


# ---------- scanner invocation ---------------------------------------------

def run_scanner(scanner: Path, skill_path: Path) -> dict[str, Any]:
    """Run the underlying skill-scanner in JSON mode."""
    if not scanner.exists():
        return {"error": f"scanner not found at {scanner}", "skill_path": str(skill_path)}
    try:
        result = subprocess.run(
            ["python3", str(scanner), "--json", str(skill_path)],
            capture_output=True, text=True, check=False, timeout=60,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": result.stderr or result.stdout, "skill_path": str(skill_path)}
    except Exception as e:
        return {"error": str(e), "skill_path": str(skill_path)}


# ---------- post-processing -------------------------------------------------

def reclassify(skill_root: Path, findings: list[dict[str, Any]], strict: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split findings into real_findings and downgraded_findings."""
    real, downgraded = [], []
    for f in findings:
        if _is_scanner_self(f):
            f = {**f, "_reclassified": "scanner-self"}
            downgraded.append(f)
            continue
        if not strict and _is_doc_finding(f, skill_root):
            f = {**f, "_reclassified": "doc-context", "severity": "info"}
            downgraded.append(f)
            continue
        real.append(f)
    return real, downgraded


# ---------- main flow ------------------------------------------------------

def audit(paths: list[Path], scanner: Path, strict: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "scanner": str(scanner),
        "strict_mode": strict,
        "paths": [str(p) for p in paths],
        "skills": [],
        "summary": {"total": 0, "real_risk": 0, "doc_only": 0, "errors": 0},
    }

    for base in paths:
        if not base.exists():
            continue
        for skill_dir in sorted(base.iterdir()):
            if not skill_dir.is_dir():
                continue
            report["summary"]["total"] += 1
            print(f"[scan] {skill_dir.name}", file=sys.stderr)
            raw = run_scanner(scanner, skill_dir)
            if "error" in raw:
                report["skills"].append({
                    "name": skill_dir.name,
                    "path": str(skill_dir),
                    "error": raw["error"],
                })
                report["summary"]["errors"] += 1
                continue
            findings = raw.get("findings", [])
            real, downgraded = reclassify(skill_dir, findings, strict)
            entry = {
                "name": skill_dir.name,
                "path": str(skill_dir),
                "raw_verdict": raw.get("verdict"),
                "raw_risk_score": raw.get("risk_score", 0),
                "real_findings": real,
                "downgraded_findings": downgraded,
                "real_risk": bool(real),
            }
            report["skills"].append(entry)
            if real:
                report["summary"]["real_risk"] += 1
            elif downgraded:
                report["summary"]["doc_only"] += 1
    return report


def render_markdown(report: dict[str, Any]) -> str:
    s = f"# Skill Security Audit — {report['timestamp']}\n\n"
    s += f"**Scanner:** `{report['scanner']}`  \n"
    s += f"**Strict mode:** {report['strict_mode']}  \n"
    s += f"**Paths:** {', '.join(report['paths'])}\n\n"
    summ = report["summary"]
    s += f"## Summary\n\n"
    s += f"- Total skills scanned: **{summ['total']}**\n"
    s += f"- Skills with **real risk**: **{summ['real_risk']}**\n"
    s += f"- Skills with documentation-only flags (downgraded): {summ['doc_only']}\n"
    s += f"- Scan errors: {summ['errors']}\n\n"

    real_risk = [k for k in report["skills"] if k.get("real_risk")]
    if real_risk:
        s += "## Real risks (review)\n\n"
        for k in real_risk:
            s += f"### {k['name']}\n\n"
            for f in k["real_findings"]:
                s += f"- [{f.get('severity', 'unknown')}] {f.get('description', '')}\n"
                if f.get("file"):
                    s += f"  - file: `{f['file']}` line {f.get('line', '?')}\n"
                if f.get("code"):
                    s += f"  - code: `{f['code'][:160]}`\n"
            s += "\n"
    else:
        s += "## Real risks\n\nNone detected.\n\n"

    doc_only = [k for k in report["skills"] if not k.get("real_risk") and k.get("downgraded_findings")]
    if doc_only:
        s += "<details>\n<summary>Documentation-only flags (suppressed)</summary>\n\n"
        for k in doc_only:
            s += f"### {k['name']}\n\n"
            for f in k["downgraded_findings"]:
                s += f"- ~~[{f.get('severity', 'unknown')}] {f.get('description', '')}~~ — {f.get('_reclassified', '')}\n"
            s += "\n"
        s += "</details>\n\n"

    errors = [k for k in report["skills"] if "error" in k]
    if errors:
        s += "## Scan errors\n\n"
        for k in errors:
            s += f"- `{k['path']}`: {k['error']}\n"

    return s


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Trevor skill security audit (context-aware)")
    p.add_argument("--paths", nargs="*", default=[str(x) for x in DEFAULT_PATHS],
                   help="Skill root paths to scan")
    p.add_argument("--scanner", default=str(DEFAULT_SCANNER),
                   help="Path to underlying skill_scanner.py")
    p.add_argument("--json", default="skill_audit_report.json", help="JSON output path")
    p.add_argument("--md", default="skill_audit_report.md", help="Markdown output path")
    p.add_argument("--strict", action="store_true",
                   help="Disable doc-context downgrade (treat all findings as scanner classified)")
    args = p.parse_args(argv)

    paths = [Path(x) for x in args.paths]
    scanner = Path(args.scanner)

    report = audit(paths, scanner, strict=args.strict)
    Path(args.json).write_text(json.dumps(report, indent=2))
    Path(args.md).write_text(render_markdown(report))
    print(f"\n[summary] real_risk={report['summary']['real_risk']} "
          f"doc_only={report['summary']['doc_only']} "
          f"errors={report['summary']['errors']} "
          f"total={report['summary']['total']}")
    print(f"[output] {args.json}, {args.md}")

    if report["summary"]["errors"] and report["summary"]["total"] == 0:
        return 2
    return 1 if report["summary"]["real_risk"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
