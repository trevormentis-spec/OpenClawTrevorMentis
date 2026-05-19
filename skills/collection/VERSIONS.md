# Collection Skills — Version Pins

| Skill | Pinned Commit SHA | Date Pulled | Repo URL |
|---|---|---|---|
| openweb | `02154abb04244c4952fa66ea9a3bcc58003e2f5e` | 2026-05-19 | https://github.com/openweb-org/openweb |
| reverse-api-engineer | `fd560f0f0eb786a219cc04cbd04b5f79f87ce6a5` | 2026-05-19 | https://github.com/kalil0321/reverse-api-engineer |

To reproduce:
```bash
cd skills/collection/openweb && git checkout 02154abb04244c4952fa66ea9a3bcc58003e2f5e && npm install
cd skills/collection/reverse-api-engineer && git checkout fd560f0f0eb786a219cc04cbd04b5f79f87ce6a5 && uv sync && uv run playwright install chromium
```

Both projects are MIT-licensed and compatible with internal commercial use.
