---
name: a2a
description: Google A2A (Agent-to-Agent) Protocol — lets Trevor discover, communicate with, and be discovered by other AI agents. JSON-RPC 2.0 over HTTP. Linux Foundation project, Apache 2.0.
metadata:
  author: "Google / Linux Foundation"
  version: "1.0.3"
  displayName: A2A Protocol
  difficulty: intermediate
---

# A2A — Agent-to-Agent Protocol

Trevor speaks A2A. Other agents can discover and task Trevor. Trevor can discover and task other agents.

## Architecture

```
Agent A ──discover──► Agent Card (/.well-known/agent-card.json)
Agent A ──task──────► JSON-RPC endpoint (/)
Agent A ◄──result─── JSON-RPC response
```

## Trevor's Agent Card

- **Name:** Trevor — Threat Research and Evaluation Virtual Operations Resource
- **Version:** 2.0.0
- **Skills:** daily_brief, market_scan, osint_query, source_discovery
- **Protocol:** JSON-RPC 2.0 over HTTP

## Server

Start the A2A server (exposes Trevor to other agents):

```bash
python3 skills/a2a/server.py --port 9999
```

Agent card available at `http://host:9999/.well-known/agent-card.json`

## Client

Discover and task other agents:

```bash
# Discover an agent
python3 skills/a2a/client.py discover http://other-agent:9999 --save --label "ResearchBot"

# Send a task
python3 skills/a2a/client.py task http://other-agent:9999 "Analyze Iran deal probability" --skill osint_query

# List known agents
python3 skills/a2a/client.py list
```

## Known Agents Registry

Stored in `config/a2a/known_agents.json`. Trevor automatically uses known agents for:
- Cross-referencing intelligence with specialist agents
- Delegating compute-heavy tasks
- Discovering new data sources

## Protocol Spec

- **Spec:** https://a2a-protocol.org/latest/specification/
- **SDK:** https://github.com/a2aproject/a2a-python
- **Samples:** https://github.com/a2aproject/a2a-samples
- **Inspector:** https://github.com/a2aproject/a2a-inspector
