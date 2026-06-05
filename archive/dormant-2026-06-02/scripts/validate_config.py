#!/usr/bin/env python3
"""
Config validation safeguard — validates OpenClaw config before any edit.

Called BEFORE any OpenClaw config modification. Prevents the type of
invalid config entries I introduced earlier today (cron.jobs).

Usage:
    python3 scripts/validate_config.py                          # Validate current config
    python3 scripts/validate_config.py --proposed proposed.json  # Validate a proposed change
    python3 scripts/validate_config.py --check-field cron.jobs   # Check if a field is valid

Exit code: 0 = valid, 1 = invalid
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

CONFIG_FILE = pathlib.Path.home() / ".openclaw" / "openclaw.json"

# Known valid top-level keys in openclaw.json
VALID_TOP_KEYS = {
    "update", "gateway", "agents", "models", "channels",
    "skills", "plugins", "session", "tools", "auth",
    "wizard", "meta",
}

# Known valid fields within skills.entries
VALID_SKILL_FIELDS = {"enabled", "env", "apiKey", "location"}

# Known env vars that skills may declare
KNOWN_SKILL_ENV_KEYS = {
    "AGENTMAIL_API_KEY", "GENVIRAL_API_KEY", "STRIPE_SECRET_KEY",
    "BUTTONDOWN_API_KEY", "MATON_API_KEY", "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY", "MOLTBOOK_API_KEY",
}


def log(msg: str) -> None:
    print(f"[validate] {msg}", file=sys.stderr, flush=True)


def validate_config(data: dict, path: str = "") -> list[str]:
    """Validate openclaw.json structure. Returns list of errors."""
    errors = []

    if not path:
        # Top-level keys
        for key in data:
            if key not in VALID_TOP_KEYS:
                errors.append(f"Unrecognized top-level key: '{key}'")

        # Check specific sections
        if "skills" in data:
            errors.extend(validate_skills(data["skills"], "skills"))
        if "cron" in data:
            errors.append("'cron' is not a valid top-level key in openclaw.json")
        if "plugins" in data:
            errors.extend(validate_plugins(data["plugins"], "plugins"))

    return errors


def validate_skills(skills: dict, path: str) -> list[str]:
    """Validate the skills section."""
    errors = []
    if not isinstance(skills, dict):
        return [f"{path}: expected dict"]

    entries = skills.get("entries", {})
    if not isinstance(entries, dict):
        errors.append(f"{path}.entries: expected dict")
        return errors

    for name, entry in entries.items():
        if not isinstance(entry, dict):
            errors.append(f"{path}.entries.{name}: expected dict")
            continue
        for field in entry:
            if field not in VALID_SKILL_FIELDS:
                errors.append(
                    f"{path}.entries.{name}: unrecognized field '{field}'"
                )
        # Validate env sub-object
        env = entry.get("env", {})
        if isinstance(env, dict):
            for key in env:
                if key not in KNOWN_SKILL_ENV_KEYS:
                    # Warn but don't fail — new keys can be added
                    pass

    return errors


def validate_plugins(plugins: dict, path: str) -> list[str]:
    """Validate plugins section."""
    errors = []
    if not isinstance(plugins, dict):
        return [f"{path}: expected dict"]

    entries = plugins.get("entries", {})
    if isinstance(entries, dict):
        for name, entry in entries.items():
            if not isinstance(entry, dict):
                errors.append(f"{path}.entries.{name}: expected dict")
                continue

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposed", default="",
                        help="Validate a proposed config file instead of current")
    parser.add_argument("--check-field", default="",
                        help="Check if a dot-notation field path is valid")
    args = parser.parse_args()

    if args.check_field:
        parts = args.check_field.split(".")
        if parts[0] not in VALID_TOP_KEYS:
            print(f"INVALID: '{parts[0]}' is not a known top-level key")
            print(f"Valid keys: {', '.join(sorted(VALID_TOP_KEYS))}")
            return 1
        print(f"VALID: '{parts[0]}' is a known top-level key")
        return 0

    if args.proposed:
        try:
            with open(args.proposed) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            log(f"Failed to load proposed config: {exc}")
            return 1
    else:
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            log(f"Failed to load config: {exc}")
            return 1

    errors = validate_config(data)
    if errors:
        log(f"Validation FAILED — {len(errors)} error(s):")
        for e in errors:
            log(f"  ❌ {e}")
        return 1
    else:
        log("Config validation PASSED ✅")
        return 0


if __name__ == "__main__":
    sys.exit(main())
