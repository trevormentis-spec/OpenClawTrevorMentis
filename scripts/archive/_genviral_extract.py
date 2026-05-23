#!/usr/bin/env python3
"""Extract structured content from brief source for GenViral social posts.

Reads a brief source file and extracts BLUF, sections, and key judgments.
Handles all orchestrator output formats:
  - exec_summary.json (top-level bluf + five_judgments)
  - Theatre analysis JSONs (region + narrative + key_judgments[])
  - Markdown / plain text (legacy)

Usage: _genviral_extract.py <input_file> <output_file>
"""
import json, re, sys, os
from pathlib import Path


def extract(source_text: str, source_name: str = "") -> dict:
    result = {
        "bluf": "",
        "sections": [],
        "judgments": []
    }
    
    # Try JSON parsing
    try:
        data = json.loads(source_text)
        return extract_from_json(data, source_name)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Markdown / plain text
    return extract_from_text(source_text)


def extract_from_json(data: dict, source_name: str) -> dict:
    result = {"bluf": "", "sections": [], "judgments": []}
    
    # Check if this is a theatre analysis (has "region" key)
    if "region" in data and "narrative" in data:
        region_name = data["region"].replace("_", " ").title()
        result["bluf"] = data.get("narrative", "")[:500]
        kjs = data.get("key_judgments", [])
        for kj in kjs:
            statement = kj.get("statement", "")
            band = kj.get("sherman_kent_band", "")
            pct = kj.get("prediction_pct", "")
            if statement:
                result["judgments"].append(
                    f"[{region_name}] {statement} ({band}; {pct}% / 7d)"
                )
        return result
    
    # Exec summary format
    if "bluf" in data:
        result["bluf"] = data.get("bluf", "")
    
    # Get sections from theatre analysis keys
    for key in sorted(data.keys()):
        if key.endswith("_analysis") and isinstance(data[key], dict):
            region = data[key].get("region", key.replace("_analysis", "").replace("_", " ").title())
            result["sections"].append(region.replace("_", " ").title())
            # Pull key judgment from this theatre
            kjs = data[key].get("key_judgments", [])
            for kj in kjs[:1]:
                statement = kj.get("statement", "")
                band = kj.get("sherman_kent_band", "")
                pct = kj.get("prediction_pct", "")
                if statement:
                    result["judgments"].append(
                        f"[{region}] {statement} ({band}; {pct}% / 7d)"
                    )
    
    # Also grab five_judgments from exec summary level
    if "five_judgments" in data:
        for kj in data["five_judgments"]:
            statement = kj.get("statement", "")
            band = kj.get("sherman_kent_band", "")
            pct = kj.get("prediction_pct", "")
            region = kj.get("drawn_from_region", "Global")
            if statement:
                jt = f"[{region}] {statement} ({band}; {pct}% / 7d)"
                if jt not in result["judgments"]:
                    result["judgments"].append(jt)
    
    return result


def extract_from_text(text: str) -> dict:
    result = {"bluf": "", "sections": [], "judgments": []}
    lines = text.split("\n")
    
    # BLUF
    bluf_match = re.search(
        r'(?:BLUF|BOTTOM LINE|EXECUTIVE SUMMARY)\s*\n(.+?)(?:\n\n|\n---|\n##|$)',
        text, re.DOTALL | re.IGNORECASE
    )
    if bluf_match:
        result["bluf"] = bluf_match.group(1).strip()
    if not result["bluf"] or len(result["bluf"]) < 20:
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 40:
                result["bluf"] = line[:500]
                break
    
    # Section headings
    for match in re.finditer(r'##\s+\d*\.?\s*(.+?)(?:\n|$)', text):
        heading = match.group(1).strip()
        if heading and len(heading) > 3:
            clean = re.sub(
                r'^[🔴🟠🟡🟢🔵🟣⚪\U0001f300-\U0001f9ff]+', '', heading
            ).strip()
            result["sections"].append(clean if clean else heading)
    
    # Key judgments
    for match in re.finditer(
        r'(?:###\s*)?Key Judgment\s*\n(.+?)(?:\n\n|\n###|\n---|$)',
        text, re.DOTALL
    ):
        j = match.group(1).strip()
        if j:
            result["judgments"].append(j[:300])
    
    return result


def find_brief_files(brief_dir: str) -> str:
    """Try to build a merged JSON from the orchestrator output directory."""
    brief_path = Path(brief_dir)
    exec_summary = brief_path / "analysis" / "exec_summary.json"
    
    if exec_summary.exists():
        with open(exec_summary) as f:
            data = json.load(f)
        
        # Merge in theatre analyses for sections
        analysis_dir = brief_path / "analysis"
        if analysis_dir.exists():
            for fpath in sorted(analysis_dir.glob("*.json")):
                if fpath.name == "exec_summary.json":
                    continue
                with open(fpath) as f:
                    try:
                        td = json.load(f)
                    except json.JSONDecodeError:
                        continue
                region = td.get("region", fpath.stem)
                data[f"{region}_analysis"] = td
        
        return json.dumps(data)
    
    return ""


def main():
    if len(sys.argv) < 3:
        print("Usage: _genviral_extract.py <input_file> <output_file> [--brief-dir <dir>]", file=sys.stderr)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Optional --brief-dir argument
    brief_dir = None
    if "--brief-dir" in sys.argv:
        idx = sys.argv.index("--brief-dir")
        if idx + 1 < len(sys.argv):
            brief_dir = sys.argv[idx + 1]
    
    # Read the input
    with open(input_path, "r", errors="replace") as f:
        source_text = f.read()
    
    # Try to merge orchestrator directory data
    if brief_dir and os.path.isdir(brief_dir):
        merged = find_brief_files(brief_dir)
        if merged:
            source_text = merged
    else:
        # Try auto-detect from input path
        merged = find_brief_files(os.path.dirname(os.path.dirname(input_path)))
        if merged:
            source_text = merged
    
    result = extract(source_text, os.path.basename(input_path))
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"  BLUF: {len(result['bluf'])} chars")
    print(f"  Sections: {len(result['sections'])}")
    print(f"  Judgments: {len(result['judgments'])}")


if __name__ == "__main__":
    main()
