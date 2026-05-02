# Recommended OpenClaw Memory Configuration

This note captures the recommended runtime memory settings for Trevor's MyClaw/OpenClaw instance. The repository-level `brain/` runtime remains the file-backed fast path, while OpenClaw's built-in memory search can provide a stronger hybrid retrieval layer when configured in `~/.openclaw/openclaw.json`.

## Recommended block

```jsonc
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "provider": "openai",
        "query": {
          "hybrid": {
            "enabled": true,
            "vectorWeight": 0.65,
            "textWeight": 0.35,
            "candidateMultiplier": 4,
            "mmr": {
              "enabled": true,
              "lambda": 0.7
            },
            "temporalDecay": {
              "enabled": true,
              "halfLifeDays": 45
            }
          }
        },
        "cache": {
          "enabled": true,
          "maxEntries": 25000
        },
        "store": {
          "vector": {
            "enabled": true
          }
        },
        "experimental": {
          "sessionMemory": false
        },
        "sources": ["memory"]
      }
    }
  }
}
```

## Notes

- Keep `sessionMemory` disabled unless transcript recall is explicitly needed.
- Keep the file-backed `brain/` runtime as the cheap fast path.
- Use OpenClaw hybrid retrieval for semantically fuzzy or long-context memory queries.
- If local embedding support is added later, replace `provider` with the local provider and keep the same query/cache/store shape.
