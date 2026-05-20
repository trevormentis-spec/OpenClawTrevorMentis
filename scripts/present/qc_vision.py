#!/usr/bin/env python3
"""Vision QC via Opus 4.7 through analyst/llm_clients/."""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import subprocess
import sys
import tempfile

from analyst.llm_clients.openrouter_client import OpenRouterClient

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
QC_SPEC = '{"pass": bool, "issues": [str], "fixes": [str]}'


def self_test() -> list[str]:
    failures = []
    client = OpenRouterClient()
    if not client.is_available():
        failures.append("OPENROUTER_API_KEY not configured")
        return failures
    result = client.complete(model="anthropic/claude-opus-4.7",
        messages=[{"role": "user", "content": "OK"}], max_tokens=10)
    if not result.get("content"):
        failures.append("Opus 4.7 returned empty")
    return failures


def get_mime(path: str) -> str:
    header = pathlib.Path(path).read_bytes()[:4]
    if header[:3] == b"\xff\xd8\xff": return "image/jpeg"
    if header[:4] == b"\x89PNG": return "image/png"
    return "application/octet-stream"


def qc_check(file_path: str, spec: str) -> dict:
    client = OpenRouterClient()
    if not client.is_available():
        return {"pass": False, "issues": ["Key not configured"], "fixes": []}

    b64 = base64.b64encode(pathlib.Path(file_path).read_bytes()).decode("ascii")
    mime = get_mime(file_path)

    instruction = f"QC check. SPEC: {spec}. Answer in JSON: {QC_SPEC}"

    if mime.startswith("image/"):
        msg = [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            {"type": "text", "text": instruction},
        ]}]
    elif pathlib.Path(file_path).suffix == ".mp4":
        msg = [{"role": "user", "content": f"QC video: {instruction}"}]
    else:
        msg = [{"role": "user", "content": instruction}]

    try:
        result = client.complete(model="anthropic/claude-opus-4.7", messages=msg, max_tokens=1000)
        text = result.get("content", "")
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        return {"pass": False, "issues": ["No JSON in response"], "fixes": []}
    except Exception as exc:
        return {"pass": False, "issues": [f"Error: {exc}"], "fixes": []}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to file")
    parser.add_argument("--spec", help="QC spec")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        failures = self_test()
        for f in failures or ["QC READY"]: print(f"  {f}")
        return
    if not args.file or not args.spec:
        parser.error("--file and --spec required")
    print(json.dumps(qc_check(args.file, args.spec), indent=2))

if __name__ == "__main__":
    main()
