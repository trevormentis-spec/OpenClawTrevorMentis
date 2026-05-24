#!/usr/bin/env python3
"""
Trevor A2A Client — discovers and communicates with other A2A agents.
Uses direct HTTP/JSON-RPC calls (pragmatic approach — the A2A SDK v1.0 
protobuf types are still maturing).

Usage:
    python3 skills/a2a/client.py discover http://other-agent:9999
    python3 skills/a2a/client.py task http://other-agent:9999 "query"
    python3 skills/a2a/client.py list
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
KNOWN_AGENTS_PATH = REPO / "config" / "a2a" / "known_agents.json"


async def discover_agent(url: str) -> dict:
    """Fetch an agent's card from its well-known endpoint."""
    card_url = url.rstrip("/") + "/.well-known/agent-card.json"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(card_url)
            resp.raise_for_status()
            card = resp.json()
            return {
                "name": card.get("name", "?"),
                "description": card.get("description", "")[:300],
                "version": card.get("version", "?"),
                "url": url,
                "skills": [
                    {"id": s["id"], "name": s["name"], "description": s.get("description", "")[:200]}
                    for s in card.get("skills", [])
                ],
                "interfaces": card.get("supportedInterfaces", []),
            }
        except Exception as e:
            return {"error": str(e), "url": url}


async def send_task(url: str, message: str, skill_id: str | None = None) -> dict:
    """Send a task to an A2A agent via JSON-RPC."""
    rpc_url = url.rstrip("/") + "/"
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "params": {
            "message": {
                "message_id": f"trevor-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "role": "ROLE_USER",
                "parts": [{"text": message}],
            },
            "configuration": {
                "returnImmediately": False,
            },
            "metadata": {"skill_id": skill_id} if skill_id else {},
        },
        "id": 1,
    }
    headers = {
        "Content-Type": "application/json",
        "A2A-Version": "1.0",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(rpc_url, json=payload, headers=headers)
        return resp.json()


def load_known_agents() -> dict:
    """Load the known agents registry."""
    KNOWN_AGENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KNOWN_AGENTS_PATH.exists():
        return json.loads(KNOWN_AGENTS_PATH.read_text())
    return {"agents": {}, "updated_at": ""}


def save_known_agents(registry: dict) -> None:
    """Persist the known agents registry."""
    registry["updated_at"] = datetime.now(timezone.utc).isoformat()
    KNOWN_AGENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    KNOWN_AGENTS_PATH.write_text(json.dumps(registry, indent=2))


async def add_known_agent(url: str, label: str | None = None) -> dict:
    """Discover an agent and add it to the known registry."""
    info = await discover_agent(url)
    if "error" in info:
        return info
    registry = load_known_agents()
    registry["agents"][url] = {
        **info,
        "label": label or info["name"],
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    save_known_agents(registry)
    return info


def list_known_agents() -> list[dict]:
    """List all known A2A agents."""
    registry = load_known_agents()
    return [
        {"url": url, "label": info.get("label", info.get("name", "?")),
         "skills": len(info.get("skills", [])), "added": info.get("added_at", "?")[:10]}
        for url, info in registry.get("agents", {}).items()
    ]


async def main_async():
    parser = argparse.ArgumentParser(description="Trevor A2A Client")
    sub = parser.add_subparsers(dest="command")

    discover_p = sub.add_parser("discover", help="Discover an A2A agent")
    discover_p.add_argument("url")
    discover_p.add_argument("--save", action="store_true")
    discover_p.add_argument("--label")

    task_p = sub.add_parser("task", help="Send a task to an A2A agent")
    task_p.add_argument("url")
    task_p.add_argument("message")
    task_p.add_argument("--skill")

    sub.add_parser("list", help="List known A2A agents")

    args = parser.parse_args()

    if args.command == "discover":
        if args.save:
            result = await add_known_agent(args.url, args.label)
        else:
            result = await discover_agent(args.url)
        print(json.dumps(result, indent=2))

    elif args.command == "task":
        result = await send_task(args.url, args.message, args.skill)
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        agents = list_known_agents()
        if not agents:
            print("No known A2A agents. Use 'discover <url> --save' to add one.")
        else:
            print(f"Known agents ({len(agents)}):")
            for a in agents:
                print(f"  {a['label']} — {a['url']} ({a['skills']} skills, added {a['added']})")

    else:
        parser.print_help()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
