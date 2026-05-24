#!/usr/bin/env python3
"""
Trevor A2A Server — exposes Trevor as an A2A-compatible agent.
Run as a sidecar: python3 skills/a2a/server.py [--port 9999]

Agent Card available at: http://host:port/.well-known/agent-card.json
JSON-RPC endpoint at: http://host:port/
"""

import argparse
import os
import sys
from pathlib import Path

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Add parent to path for agent_executor import
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills" / "a2a"))

from agent_executor import TrevorAgentExecutor

# ── Trevor's Agent Card ──────────────────────────────────────────

TREVOR_SKILLS = [
    AgentSkill(
        id="daily_brief",
        name="Daily Geopolitical Intelligence Brief",
        description=(
            "Produces a calibrated daily intelligence brief covering 10 global regions. "
            "Includes BLUF, key judgments with Sherman Kent confidence bands, "
            "forced dissent, and source attribution per NATO Admiralty ratings. "
            "Regions: Europe, North America, Central America/Caribbean, South America, "
            "Africa, Middle East, Central Asia, Southeast Asia, East Asia, South Asia, "
            "Oceania, and Prediction Markets."
        ),
        input_modes=["text/plain"],
        output_modes=["text/plain", "application/json"],
        tags=["intelligence", "geopolitics", "daily-brief", "osint"],
        examples=[
            "Give me today's South America brief",
            "What's the BLUF for Middle East today?",
            "Show me the five key judgments from today's brief",
        ],
    ),
    AgentSkill(
        id="market_scan",
        name="Prediction Market Scanner",
        description=(
            "Scans Kalshi and Polymarket (via Simmer) for geopolitically-relevant "
            "prediction markets. Returns probabilities, volumes, and signal strength "
            "for conflict, sanction, election, and economic event markets."
        ),
        input_modes=["text/plain"],
        output_modes=["text/plain", "application/json"],
        tags=["markets", "prediction", "kalshi", "polymarket", "finance"],
        examples=[
            "Scan for Iran-related markets",
            "What are the top geopolitical prediction markets right now?",
            "Show me ceasefire probability markets",
        ],
    ),
    AgentSkill(
        id="osint_query",
        name="OSINT Research Query",
        description=(
            "Researches a specific geopolitical topic, region, or event using "
            "Trevor's 286-validated-source OSINT collection pipeline. Returns "
            "sourced analysis with Admiralty ratings."
        ),
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["osint", "research", "analysis", "sources"],
        examples=[
            "What's happening with Russia-Ukraine right now?",
            "Analyze the Iran nuclear deal negotiations",
            "Brief me on South China Sea tensions",
        ],
    ),
    AgentSkill(
        id="source_discovery",
        name="OSINT Source Discovery",
        description=(
            "Discovers and validates new OSINT sources for a given region or topic. "
            "Trevor maintains 286 working RSS feeds across 10 regions and can find "
            "additional sources via web search and RSS pattern detection."
        ),
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["osint", "sources", "discovery", "rss"],
        examples=[
            "Find new sources for West Africa security",
            "What RSS feeds cover Southeast Asia maritime disputes?",
            "Validate these 5 RSS feeds for me",
        ],
    ),
]

PUBLIC_AGENT_CARD = AgentCard(
    name="Trevor — Threat Research and Evaluation Virtual Operations Resource",
    description=(
        "Autonomous intelligence analyst producing calibrated geopolitical briefs, "
        "OSINT research, and prediction market analysis. Trevor processes 286 validated "
        "RSS sources across 10 global regions with DeepSeek V4 Pro analysis, Sherman Kent "
        "calibration, NATO Admiralty source ratings, and forced dissent methodology. "
        "Operates on a daily 05:00 PT pipeline with AgentMail delivery."
    ),
    version="2.0.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain", "application/json"],
    capabilities=AgentCapabilities(
        streaming=False,
        push_notifications=False,
        extended_agent_card=True,
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://0.0.0.0:9999",
        ),
    ],
    skills=TREVOR_SKILLS,
)


def build_app(port: int = 9999) -> Starlette:
    """Build the A2A Starlette application."""
    # Update interface URL with actual port
    PUBLIC_AGENT_CARD.supported_interfaces[0].url = f"http://0.0.0.0:{port}"

    request_handler = DefaultRequestHandler(
        agent_executor=TrevorAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=PUBLIC_AGENT_CARD,
    )

    # Build routes list (as shown in helloworld example)
    routes = []
    routes.extend(create_agent_card_routes(PUBLIC_AGENT_CARD))
    routes.extend(create_jsonrpc_routes(request_handler, rpc_url="/"))

    app = Starlette(routes=routes)
    return app, request_handler


def main():
    parser = argparse.ArgumentParser(description="Trevor A2A Agent Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("A2A_PORT", "9999")),
                        help="Port to listen on (default: 9999, env: A2A_PORT)")
    parser.add_argument("--host", default=os.environ.get("A2A_HOST", "0.0.0.0"),
                        help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    app, _ = build_app(port=args.port)

    print(f"🦞 Trevor A2A Server starting on http://{args.host}:{args.port}")
    print(f"   Agent Card: http://{args.host}:{args.port}/.well-known/agent-card.json")
    print(f"   JSON-RPC:   http://{args.host}:{args.port}/")
    print(f"   Skills: {len(TREVOR_SKILLS)} registered")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
