---
name: collection
description: |
  Collection Capability Expansion — programmatic API access for TREVOR's HYDRA OSINT pipeline.
  Combines openweb (94 pre-built site specs for JSON API access) with reverse-api-engineer
  (HAR-based site spec generation for unsupported sites). Preferred over DOM scraping.
metadata:
  version: "1.0.0"
  openclaw:
    requires:
      bins: [openweb, node, python3]
      env: [ANTHROPIC_API_KEY, OPENWEB_HOME]
    install:
      - kind: node
        package: "@openweb-org/openweb"
        bins: [openweb]
---

# Collection Capability Expansion — OpenWeb + Reverse-API-Engineer

## Architecture

TREVOR now has two complementary web collection layers:

1. **openweb** — npm package providing typed JSON API access to 94 pre-built sites
2. **reverse-api-engineer** — Python tool generating openweb-compatible site specs by capturing HAR traffic

The preference order for web collection:
```
openweb (if site supported) → reverse-api-engineer (generate spec) → DOM scraping (fallback)
```

## Quick Start

### openweb — Using existing site specs

List available sites:
```bash
openweb sites
```

Call a site operation:
```bash
openweb <site> <operation>
openweb wikipedia getPageSummary '{"title":"Mexico"}'
openweb reuters search '{"q":"Mexico CJNG"}'
```

See details for a specific site:
```bash
openweb <site>
```

### reverse-api-engineer — Generating new site specs

Record HAR traffic and generate an openweb-compatible spec:
```bash
cd skills/collection/reverse-api-engineer
uv run reverse-api-engineer agent  # Interactive browser session
uv run reverse-api-engineer engineer --run <run-id>  # Generate spec
```

Promote a generated spec to openweb format:
```bash
cp <output-spec> ../_specs/<sitename>.json
```

## Integration with HYDRA Pipeline

### Prefer API collection over scraping
When `collect.py` is about to use DOM/HTTP scraping for a source, first check:
1. Is the site in `openweb sites`? If yes, use `openweb <site>` instead.
2. Is there a custom spec in `skills/collection/_specs/`? If yes, use that.

### Campaign integration
`scripts/collection_campaign.py` can use openweb for high-value sources:
```python
# Example: collect via openweb instead of RSS/HTTP
subprocess.run(["openweb", "reuters", "search", json.dumps({"q": query})], capture_output=True)
```

## Site Spec Storage

- **Pre-built:** `/home/ubuntu/.openweb/sites/` (94 sites)
- **Custom specs:** `skills/collection/_specs/` (reverse-engineered, promoted here)
- **New openweb site packages:** `skills/collection/openweb-projects/` (for site package development)

## Adding a New Site

1. Use reverse-api-engineer to capture HAR traffic:
   ```bash
   cd skills/collection/reverse-api-engineer
   uv run reverse-api-engineer agent --url <target-url>
   uv run reverse-api-engineer engineer --run <run-id>
   ```
2. Review and test the generated spec
3. Promote to `skills/collection/_specs/<site>.json`
4. If the spec is high quality and generalizable, consider contributing as an openweb package

## Dependencies

| Tool | Location | Dependencies |
|---|---|---|
| openweb | `skills/collection/openweb/` | Node.js >=20, npm |
| reverse-api-engineer | `skills/collection/reverse-api-engineer/` | Python >=3.11, uv, Playwright chromium, ANTHROPIC_API_KEY |
| Spec registry | `skills/collection/_specs/` | None (JSON files) |

## License Notes

Both openweb (MIT) and reverse-api-engineer (MIT) are compatible with internal commercial use.
See `skills/collection/LICENSES.md` for attribution requirements.
