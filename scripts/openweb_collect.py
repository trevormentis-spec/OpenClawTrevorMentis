#!/usr/bin/env python3
"""
OpenWeb Collection Wrapper — TREVOR HYDRA integration.

Routes collection requests through openweb when the target site is supported.
Falls back to reverse-api-engineer for spec generation on unsupported sites,
then to standard HTTP scraping.

Usage:
    python3 scripts/openweb_collect.py --site reuters --query "Mexico CJNG"
    python3 scripts/openweb_collect.py --site wikipedia --params '{"title":"Mexico"}'
    python3 scripts/openweb_collect.py --discover --url "https://example.com"
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OPENWEB_CLI = "openweb"  # installed globally or via npx
OPENWEB_HOME = os.environ.get("OPENWEB_HOME", str(pathlib.Path.home() / ".openweb"))
RAE_DIR = REPO_ROOT / "skills" / "collection" / "reverse-api-engineer"
SPECS_DIR = REPO_ROOT / "skills" / "collection" / "_specs"


def log(msg: str) -> None:
    print(f"[openweb-collect] {msg}", file=sys.stderr, flush=True)


def get_available_sites() -> list[str]:
    """Return list of sites available via openweb CLI."""
    try:
        result = subprocess.run(
            [OPENWEB_CLI, "sites"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "OPENWEB_HOME": OPENWEB_HOME}
        )
        return [s.strip() for s in result.stdout.strip().split("\n") if s.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        log(f"openweb CLI unavailable: {e}")
        return []


def collect_via_openweb(site: str, operation: str, params: dict | None = None) -> dict:
    """Collect data from a site using openweb CLI."""
    site = site.lower().strip()

    # Check custom specs first
    spec_path = SPECS_DIR / f"{site}.json"
    if spec_path.exists():
        log(f"Using custom spec: {spec_path}")
        # Custom specs may need different handling — return the spec info
        return {"source": site, "method": "custom_spec", "spec": str(spec_path)}

    # Use openweb CLI
    cmd = [OPENWEB_CLI, site, operation]
    if params:
        cmd.append(json.dumps(params))

    log(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            env={**os.environ, "OPENWEB_HOME": OPENWEB_HOME}
        )
        if result.returncode == 0:
            return {"source": site, "method": "openweb", "data": result.stdout}
        else:
            log(f"openweb error: {result.stderr[:200]}")
            return {"source": site, "method": "openweb", "error": result.stderr[:500]}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        log(f"openweb failed: {e}")
        return {"source": site, "method": "openweb", "error": str(e)}


def discover_via_rae(url: str) -> dict:
    """Use reverse-api-engineer to discover API endpoints for a URL."""
    log(f"Running reverse-api-engineer discovery on: {url}")
    try:
        result = subprocess.run(
            ["uv", "run", "reverse-api-engineer", "agent", "--url", url, "--no-interactive"],
            capture_output=True, text=True, timeout=120,
            cwd=str(RAE_DIR),
            env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")}
        )
        return {"url": url, "method": "rae", "output": result.stdout[-1000:]}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        log(f"RAE discovery failed: {e}")
        return {"url": url, "method": "rae", "error": str(e)}


def list_supported_sites() -> list[str]:
    """List all sites we can collect from."""
    builtin = get_available_sites()
    custom = [f.stem for f in SPECS_DIR.glob("*.json")]
    return sorted(set(builtin + custom))


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenWeb collection wrapper for TREVOR HYDRA")
    parser.add_argument("--site", help="Target site name")
    parser.add_argument("--operation", default="search", help="Site operation to call")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--params", help="JSON parameters for the operation")
    parser.add_argument("--discover", action="store_true", help="Use RAE to discover API for a URL")
    parser.add_argument("--url", help="URL for discovery mode")
    parser.add_argument("--list-sites", action="store_true", help="List all supported sites")
    args = parser.parse_args()

    if args.list_sites:
        sites = list_supported_sites()
        print(f"Supported sites ({len(sites)}):")
        for s in sites:
            print(f"  {s}")
        return 0

    if args.discover:
        if not args.url:
            print("ERROR: --discover requires --url", file=sys.stderr)
            return 1
        result = discover_via_rae(args.url)
        print(json.dumps(result, indent=2))
        return 0

    if not args.site:
        parser.print_help()
        return 1

    # Build params
    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            params = {"q": args.params}
    elif args.query:
        params = {"q": args.query}

    result = collect_via_openweb(args.site, args.operation, params)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Emit BigQuery pipeline record
    if "error" not in result:
        nato_source = "B" if result.get("method") == "openweb" else "C"
        nato_info = "2" if result.get("method") == "openweb" else "3"
        record = {
            "source": args.site,
            "site_spec_version": "openweb-0.1.6",
            "method": result.get("method", "unknown"),
            "nato_admiralty_source_rating": nato_source,
            "nato_admiralty_info_rating": nato_info,
            "collected_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "payload": {"query": args.query or args.params, "result_length": len(str(result.get("data", ""))), "qc_status": "PENDING_HUMAN_ANALYST_QC_REVIEW"},
        }
        # Try to write record; non-blocking
        try:
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "append_collection_record.py"),
                 "--record", json.dumps(record)],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
