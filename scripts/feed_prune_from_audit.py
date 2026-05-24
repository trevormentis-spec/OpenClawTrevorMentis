#!/usr/bin/env python3
"""Prune dead feeds from collect.py using the last feed-health audit results.

Uses brain/memory/semantic/feed-health-latest.json to avoid re-scanning.
"""
import json, re, pathlib, sys, time

BRAIN_REPORT = pathlib.Path(__file__).resolve().parent.parent / "brain" / "memory" / "semantic" / "feed-health-latest.json"
COLLECT_PY = pathlib.Path(__file__).resolve().parent.parent / "skills" / "daily-intel-brief" / "scripts" / "collect.py"

report = json.loads(BRAIN_REPORT.read_text())
dead_list = report.get("dead_list", [])

if not dead_list:
    print("No dead feeds to prune.")
    sys.exit(0)

print(f"Pruning {len(dead_list)} dead feeds from collect.py...")
content = COLLECT_PY.read_text()
original_lines = content.count("\n")
removed = 0

for d in dead_list:
    name = d["name"]
    # Escape for regex
    escaped_name = re.escape(name)
    # Match the entire line containing this feed name
    pattern = re.compile(rf'^\s*\(\"{escaped_name}\",.*$', re.MULTILINE)
    new_content = pattern.sub("", content)
    if new_content != content:
        removed += 1
    content = new_content

# Clean up double blank lines
while "\n\n\n" in content:
    content = content.replace("\n\n\n", "\n\n")

COLLECT_PY.write_text(content)
new_lines = content.count("\n")
print(f"Removed {removed} dead feed entries.")
print(f"Lines: {original_lines} → {new_lines}")

# Save result state
prune_result = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "pruned_count": removed,
    "dead_from_audit": len(dead_list),
    "lines_before": original_lines,
    "lines_after": new_lines,
}
result_path = pathlib.Path(__file__).resolve().parent.parent / "brain" / "memory" / "semantic" / "feed-prune-latest.json"
result_path.write_text(json.dumps(prune_result, indent=2))
print(f"Prune result saved to {result_path}")
