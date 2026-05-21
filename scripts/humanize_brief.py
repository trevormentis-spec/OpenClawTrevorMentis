#!/usr/bin/env python3
"""
Humanize brief text — remove AI writing patterns from daily brief output.

Applies rules from the humanizer skill (Wikipedia-based AI writing detection).
Runs as a post-processing step on the assembled brief before Gmail delivery.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ============================================================
# AI vocabulary — words that flag AI-generated text
# ============================================================
AI_VOCAB = {
    "additionally": None,
    "align with": None,
    "crucial": "important",
    "delve": "go into",
    "emphasizing": None,  # handled by -ing rule
    "enduring": None,
    "enhance": "improve",
    "enhancing": "improving",
    "fostering": "building",
    "foster": "build",
    "garner": "get",
    "highlighting": None,
    "interplay": "interaction",
    "intricate": "complex",
    "intricacies": "complexities",
    "pivotal": "key",
    "showcase": "show",
    "showcasing": "showing",
    "tapestry": None,  # remove
    "testament": None,  # remove
    "underscore": "show",
    "underscoring": None,  # -ing + vocab
    "vibrant": "lively",
    "groundbreaking": "important",
    "boasts": "has",
    "indelible": None,
    "monumental": "big",
    "transformative": "significant",
}

# ============================================================
# Inflated symbolism patterns
# ============================================================
SYMBOLISM_PATTERNS = [
    (r"(?i)\b(serves?|stands?)\s+as\s+a\s+(testament|reminder|symbol|milestone)\b", None),
    (r"(?i)\b(marks|represents)\s+a\s+(pivotal|significant|key|critical|monumental)\s+(moment|shift|turning point|milestone)\b", None),
    (r"(?i)\bbroader\s+(movement|context|trend|landscape)\b", None),
    (r"(?i)\bevolving\s+landscape\b", None),
    (r"(?i)\bdeeply\s+rooted\b", None),
    (r"(?i)\bsetting\s+the\s+stage\b", None),
    (r"(?i)\b(indelible|lasting)\s+mark\b", None),
    (r"(?i)\bfocal\s+point\b", None),
]

# ============================================================
# -ing suffix analysis patterns
# ============================================================
ING_PATTERNS = [
    r"(?i),?\s+highlighting\s+",
    r"(?i),?\s+underscoring\s+",
    r"(?i),?\s+emphasizing\s+",
    r"(?i),?\s+reflecting\s+",
    r"(?i),?\s+symbolizing\s+",
    r"(?i),?\s+showcasing\s+",
    r"(?i),?\s+fostering\s+",
    r"(?i),?\s+encompassing\s+",
    r"(?i),?\s+cultivating\s+",
    r"(?i),?\s+ensuring\s+",
]

# ============================================================
# Vague attribution patterns
# ============================================================
VAGUE_PATTERNS = [
    (r"(?i)\b(industry\s+reports?|observers\s+(have\s+)?cited?|experts?\s+(believe|argue|say|suggest)\b)", "sources indicate"),
    (r"(?i)\bsome\s+(critics?|argue|observers?)\b", None),
    (r"(?i)\baccording\s+to\s+(several|some|various)\s+sources\b", None),
    (r"(?i)\b(proponents?|detractors?)\s+(argue|claim|point\s+out)\b", None),
]

# ============================================================
# Negative parallelisms
# ============================================================
NEG_PARALLEL = [
    (r"(?i)\bit's?\s+not\s+(just\s+)?(about|merely)\s+\w+,\s+it'[ns]\s+", None),
    (r"(?i)\bnot\s+only\s+\w+\s+(but\s+)?(also\s+)?,\s+but\s+", None),
    (r"(?i)\bnot\s+merely\s+\w+,\s+but\s+", None),
]

# ============================================================
# Copula avoidance patterns
# ============================================================
COPULA_AVOID = [
    (r"(?i)\bserves?\s+as\s+", "is "),
    (r"(?i)\bstands?\s+as\s+", "is "),
    (r"(?i)\bboasts?\s+", "has "),
    (r"(?i)\bfeatures?\s+", "has "),
]

# ============================================================
# Filler phrases
# ============================================================
FILLERS = [
    (r"(?i)\bin\s+order\s+to\b", "to"),
    (r"(?i)\bdue\s+to\s+the\s+fact\s+that\b", "because"),
    (r"(?i)\bat\s+this\s+point\s+in\s+time\b", "now"),
    (r"(?i)\bin\s+the\s+event\s+that\b", "if"),
    (r"(?i)\bhas\s+the\s+ability\s+to\b", "can"),
    (r"(?i)\bit\s+is\s+important\s+to\s+note\s+that\b", ""),
    (r"(?i)\bit\s+is\s+worth\s+noting\s+that\b", ""),
    (r"(?i)\bin\s+a\s+manner\s+that\b", "so that"),
    (r"(?i)\bon\s+a\s+\w+\s+basis\b", None),  # "on a daily basis" → "daily"
]

# ============================================================
# Rule of three — detect comma-separated groups
# ============================================================
THREE_PATTERN = re.compile(r"(\w+[,\s]+){2}(and|or)\s+\w+")


def log(msg):
    print(f"[humanizer] {msg}", file=sys.stderr, flush=True)


def humanize(text: str) -> str:
    """Apply all humanizer rules to text."""
    original = text
    changes = []

    # 1. Remove AI vocabulary words
    for word, replacement in AI_VOCAB.items():
        pattern = r"(?i)\b" + re.escape(word) + r"\b"
        if replacement is None:
            # Flag for review — but in automated mode, let compound rules handle it
            continue
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, replacement, text)
            if count > 0:
                changes.append(f"  Replaced '{word}' x{count} → '{replacement}'")

    # 2. Remove inflated symbolism
    for pattern, _ in SYMBOLISM_PATTERNS:
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, "", text)
            changes.append(f"  Removed symbolism pattern x{count}")

    # 3. Remove -ing analysis constructions
    for pattern in ING_PATTERNS:
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, ". ", text)
            changes.append(f"  Removed -ing analysis x{count}")

    # 4. Remove vague attributions
    for pattern, repl in VAGUE_PATTERNS:
        count = len(re.findall(pattern, text))
        if count > 0:
            if repl:
                text = re.sub(pattern, repl, text)
            else:
                text = re.sub(pattern, "", text)
            changes.append(f"  Removed vague attribution x{count}")

    # 5. Remove negative parallelisms
    for pattern, _ in NEG_PARALLEL:
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, "", text)
            changes.append(f"  Removed negative parallelism x{count}")

    # 6. Replace copula avoidance
    for pattern, repl in COPULA_AVOID:
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, repl, text)
            changes.append(f"  Fixed copula avoidance x{count} ('{pattern}' → '{repl}')")

    # 7. Replace filler phrases
    for pattern, repl in FILLERS:
        count = len(re.findall(pattern, text))
        if count > 0:
            if repl:
                text = re.sub(pattern, repl, text)
            else:
                text = re.sub(pattern, "", text)
            changes.append(f"  Removed filler x{count}")

    # 8. Condense double spaces from removals
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\.\s+\.", ". ", text)
    text = re.sub(r",\s*,", ", ", text)

    # 9. Replace em dashes with commas where excessive
    em_count = text.count("—")
    if em_count > 3:
        # Replace all but first with commas
        parts = text.split("—")
        if len(parts) > 2:
            text = parts[0] + "—" + " —".join(parts[1:3]) + ",".join(parts[3:])
            changes.append(f"  Condensed em dashes ({em_count}→2)")

    # 10. Remove "Moreover" and "Furthermore" at sentence starts
    text = re.sub(r"(?i)\bMoreover,\s*", "", text)
    text = re.sub(r"(?i)\bFurthermore,\s*", "", text)
    text = re.sub(r"(?i)\bAdditionally,\s*", "", text)

    # 11. Clean up orphaned punctuation from removals
    text = re.sub(r",\s*\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\.\.,", ".", text)
    text = re.sub(r"\s+\.", ".", text)

    # 12. Replace curly quotes with straight
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    total_changes = len(changes)
    if total_changes > 0:
        log(f"Applied {total_changes} humanizer changes:")
        for c in changes:
            log(c)
    else:
        log("No AI patterns detected — text looks natural")

    return text


def main():
    parser = argparse.ArgumentParser(description="Humanize brief text")
    parser.add_argument("--file", help="Path to brief text file to humanize")
    parser.add_argument("--in-place", action="store_true", help="Modify file in place")
    args = parser.parse_args()

    if args.file:
        path = pathlib.Path(args.file)
        if not path.exists():
            log(f"ERROR: File not found: {path}")
            sys.exit(1)

        text = path.read_text()
        log(f"Read {len(text)} chars from {path}")

        humanized = humanize(text)
        log(f"Humanized: {len(humanized)} chars")

        if args.in_place:
            path.write_text(humanized)
            log(f"Written back to {path}")
        else:
            print(humanized)
    else:
        # Read from stdin
        text = sys.stdin.read()
        print(humanize(text))


if __name__ == "__main__":
    main()
