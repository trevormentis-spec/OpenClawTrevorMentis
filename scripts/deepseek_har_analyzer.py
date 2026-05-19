#!/usr/bin/env python3
"""
DeepSeek HAR Analyzer — replaces reverse-api-engineer's Claude agent.

Takes a captured HAR file, sends the relevant API call patterns to DeepSeek V4 Pro,
and generates an openweb-compatible site spec + runnable API client.

Usage:
    python3 scripts/deepseek_har_analyzer.py --har /tmp/elfinanciero.har --site elfinanciero
    python3 scripts/deepseek_har_analyzer.py --har /tmp/elfinanciero.har --site elfinanciero --prompt "search for 'Mexico' on elfinanciero.com.mx"
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import datetime as dt

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Pro

# Try both possible env var names and fallback chain
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY_V4", "")


def log(msg: str) -> None:
    print(f"[ds-har] {msg}", file=sys.stderr, flush=True)


def call_deepseek(prompt: str, system_prompt: str = "") -> str:
    """Call DeepSeek V4 Pro with the given prompt. Returns content string."""
    import urllib.request
    import urllib.error

    url = "https://api.deepseek.com/v1/chat/completions"
    # Try OpenRouter as fallback
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,  # Low temp for deterministic spec generation
    }

    data = json.dumps(payload).encode("utf-8")
    
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content
                return json.dumps(result)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            log(f"DeepSeek API error (attempt {attempt+1}): {e.code} {err_body[:200]}")
            if attempt == 0 and openrouter_key and "401" in str(e.code):
                # Fallback to OpenRouter
                log("Falling back to OpenRouter...")
                headers["Authorization"] = f"Bearer {openrouter_key}"
                url = "https://openrouter.ai/api/v1/chat/completions"
                payload["model"] = "deepseek/deepseek-v4-pro"
                data = json.dumps(payload).encode("utf-8")
                continue
            return f"ERROR: {e.code} {err_body[:200]}"
        except Exception as e:
            log(f"Request failed: {e}")
            return f"ERROR: {e}"


def summarize_har(har_path: str, max_entries: int = 50) -> str:
    """Extract a summary of API-relevant entries from a HAR file."""
    with open(har_path) as f:
        har = json.load(f)
    
    entries = har.get("log", {}).get("entries", [])
    
    # Find API-like calls (JSON, XHR, fetch, graphql, etc.)
    api_calls = []
    for e in entries:
        url = e["request"]["url"]
        # Only include responses with JSON-like content
        ct = e["response"]["content"].get("mimeType", "")
        if "json" in ct or "text" in ct:
            api_calls.append(e)
    
    # If few JSON responses, include XHR/Fetch calls
    if len(api_calls) < 5:
        api_calls = [e for e in entries if e["request"]["url"] != "data:" and 
                     not any(e["request"]["url"].endswith(ext) for ext in 
                     [".png", ".jpg", ".gif", ".svg", ".woff", ".woff2", ".css", ".ico", ".mp4", ".webm"])]
    
    summary_parts = []
    site_url = har.get("log", {}).get("pages", [{}])[0].get("title", har_path) if har.get("log", {}).get("pages") else har_path
    
    summary_parts.append(f"Site: {site_url}")
    summary_parts.append(f"Total HAR entries: {len(entries)}")
    summary_parts.append(f"Entries in analysis set: {len(api_calls)}")
    summary_parts.append("")
    
    # Group by domain
    domains = {}
    for e in api_calls[:max_entries]:
        from urllib.parse import urlparse
        parsed = urlparse(e["request"]["url"])
        domain = parsed.netloc
        path = parsed.path
        qs = parsed.query
        status = e["response"]["status"]
        method = e["request"]["method"]
        
        if domain not in domains:
            domains[domain] = []
        domains[domain].append({
            "path": path,
            "method": method,
            "status": status,
            "query": qs[:200],
            "request_headers": {h["name"]: h["value"][:100] for h in e["request"]["headers"][:10] 
                               if h["name"].lower() not in ("cookie", "authorization")},
            "response_size": e["response"]["content"].get("size", 0),
            "response_type": e["response"]["content"].get("mimeType", "unknown"),
            "response_body": e["response"]["content"].get("text", "")[:500]
        } if status != 404 else None)
    
    for domain, calls in sorted(domains.items()):
        valid_calls = [c for c in calls if c is not None]
        if not valid_calls:
            continue
        summary_parts.append(f"Domain: {domain} ({len(valid_calls)} calls)")
        for c in valid_calls[:8]:
            resp_sample = c["response_body"][:300] if c["response_body"] else "(no body)"
            summary_parts.append(f"  [{c['status']}] {c['method']} {c['path']}")
            if c["query"]:
                summary_parts.append(f"    Query: {c['query'][:150]}")
            summary_parts.append(f"    Type: {c['response_type']}")
            if "json" in c["response_type"]:
                summary_parts.append(f"    Sample: {resp_sample[:300]}")
        summary_parts.append("")
    
    return "\n".join(summary_parts)


def generate_openweb_spec(har_summary: str, site_name: str, prompt: str = "") -> dict:
    """Ask DeepSeek to analyze HAR and generate an openweb-compatible spec."""
    system = f"""You are a web API reverse-engineering specialist. You analyze HAR (HTTP Archive) 
files and produce openweb-compatible site specifications.

An openweb site spec defines:
1. A `site.json` manifest with site metadata, operations, and parameter schemas
2. A transport adapter (HTTP or browser-backed fetch)
3. Operation handlers that map user intent to API calls

Rules:
- Always identify the actual API endpoints from the HAR, not the rendered DOM
- Look for JSON response patterns — those are the API targets
- Pagination (cursor/offset) patterns should be extracted
- Authentication type (none, cookie, JWT, API key) should be identified
- Output a spec_stub JSON that can be registered as an openweb site

Return ONLY valid JSON. The JSON must have this structure:
{{
  "site": "<site_name>",
  "version": "1.0.0",
  "transport": "http",
  "base_url": "<detected_base_url>",
  "auth_type": "none|cookie|jwt|api_key",
  "operations": [
    {{
      "name": "<operation_name>",
      "description": "<what it does>",
      "method": "GET|POST",
      "endpoint": "<relative_path>",
      "params": [{{"name": "<param>", "type": "string|int|boolean", "required": true|false, "description": "..."}}],
      "response_selector": "<JSONPath or key to extract>",
      "pagination": {{
        "type": "cursor|offset|none",
        "param": "<param_name>",
        "response_key": "<key_with_next_cursor>"
      }}
    }}
  ],
  "client_code": "<python code snippet that calls the API>"
}}"""

    prompt_text = f"""Analyze this HAR capture from {site_name} and produce an openweb-compatible site spec.

Additional context from the user: {prompt if prompt else 'Extract the core news/article API'}

{har_summary}

Return the spec JSON only. No explanation."""
    
    log(f"Sending to DeepSeek {DEEPSEEK_MODEL}...")
    result = call_deepseek(prompt_text, system)
    
    # Try to parse JSON from the response
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in result:
            json_str = result.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        else:
            log(f"Could not parse JSON from response. Raw response length: {len(result)}")
            return {"raw_response": result, "parse_error": "JSON extraction failed"}


def save_spec(spec: dict, site_name: str) -> str:
    """Save the generated spec to the _specs directory."""
    spec_dir = REPO_ROOT / "skills" / "collection" / "_specs" / site_name
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Save spec
    spec_path = spec_dir / "spec.json"
    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    # Save client code separately if present
    client_code = spec.pop("client_code", None)
    if client_code:
        client_path = spec_dir / "client.py"
        with open(client_path, "w") as f:
            f.write(client_code)
        spec_path = spec_dir / "spec.json"
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
    
    return str(spec_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek HAR Analyzer")
    parser.add_argument("--har", required=True, help="Path to HAR file")
    parser.add_argument("--site", required=True, help="Site name for output spec")
    parser.add_argument("--prompt", help="Additional context for analysis", default="")
    parser.add_argument("--max-entries", type=int, default=50, help="Max HAR entries to analyze")
    args = parser.parse_args()

    if not os.path.exists(args.har):
        log(f"HAR file not found: {args.har}")
        return 1

    if not DEEPSEEK_API_KEY:
        log("DEEPSEEK_API_KEY not set in environment")
        return 1

    # Step 1: Summarize HAR
    log(f"Analyzing HAR: {args.har}")
    summary = summarize_har(args.har, args.max_entries)
    
    summary_path = REPO_ROOT / "tmp" / f"{args.site}_har_summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary)
    log(f"HAR summary written to {summary_path}")

    # Step 2: Generate spec via DeepSeek
    log("Generating openweb spec via DeepSeek V4 Pro...")
    spec = generate_openweb_spec(summary, args.site, args.prompt)
    
    if "parse_error" in spec:
        log(f"Spec generation failed: {spec['parse_error']}")
        log(f"Raw response saved to tmp/{args.site}_raw_response.txt")
        (summary_path.parent / f"{args.site}_raw_response.txt").write_text(
            spec.get("raw_response", "No response")
        )
        return 1

    # Step 3: Save spec
    spec_dir = save_spec(spec, args.site)
    log(f"✅ Spec saved to {spec_dir}")

    # Step 4: Write collection record
    record = {
        "source": args.site,
        "site_spec_version": f"ds-har-v1-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}",
        "method": "reverse_engineered",
        "nato_admiralty_source_rating": "C",
        "nato_admiralty_info_rating": "3",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": {"har_entries": len(summary.split("\n"))}
    }
    subprocess_run = __import__("subprocess").run
    try:
        subprocess_run(
            [sys.executable, str(REPO_ROOT / "scripts" / "append_collection_record.py"),
             "--record", json.dumps(record)],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

    print(json.dumps(spec, indent=2, ensure_ascii=False))
    log(f"Spec generated: {len(json.dumps(spec))} bytes, {len(spec.get('operations', []))} operations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
