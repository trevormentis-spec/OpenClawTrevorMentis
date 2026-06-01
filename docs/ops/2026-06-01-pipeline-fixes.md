# Pipeline Fixes Applied — 2026-06-01

## Issues Found

### 1. Invalid `--provider anthropic` in daily-text-brief.sh
The orchestrator's `--provider` argument only accepts `deepseek` or `openrouter` (choices defined in argparse). The script was passing `--provider anthropic` which caused `argparse` to exit with error.

**Fix:** Changed to `--provider openrouter` (for the primary config, Claude Opus exec summary via OpenRouter). Eventually switched to all-DeepSeek-Direct after OpenRouter issues.

### 2. DeepSeek V4 Pro via OpenRouter hangs
OpenRouter's routing of `deepseek/deepseek-v4-pro` was unreliable — API calls would hang for 10+ minutes with no response. The health check showed 92ms latency for OpenRouter, but the actual model calls didn't complete.

**Fix:** Use `--tier2-provider deepseek` for region analysis (DeepSeek Direct API at api.deepseek.com). Health check showed 556ms latency.

### 3. OpenAI Python SDK hangs on API calls
The `openai` Python SDK was making `client.chat.completions.create(**kwargs)` calls that would block indefinitely even with `"timeout": 120` in kwargs. The SDK's connection handling would hang at the socket poll level (`do_poll.constprop.0` kernel state) for 15+ minutes without respect to the configured timeout.

**Fixes tried (in order):**
- Changed to `urllib.request.urlopen()` directly (same hang)
- Added SIGALRM-based hard timeout (handler used generator `.throw()` which doesn't propagate exceptions from signal handlers)
- Fixed to proper `def _timeout_handler(): raise TimeoutError` pattern (still hung — SIGALRM can't interrupt all blocking C calls)
- Changed to `ThreadPoolExecutor` with `future.result(timeout=240)` (hung because `with ThreadPoolExecutor()` calls `shutdown(wait=True)` which waits for worker thread to complete even after timeout)
- **Final fix:** Created `scripts/_api_call.py` — standalone subprocess script called via `subprocess.run(['python3', '_api_call.py', ...], timeout=240)`. This provides OS-level process killing.

### 4. Claude Opus model name rejected by OpenRouter (400 Bad Request)
The model `claude-4-opus-20250514` isn't recognized by OpenRouter. Got HTTP 400 Bad Request when trying to call exec summary.

**Fix:** Use DeepSeek V4 Pro for all tiers (exec summary + regions + red team) via DeepSeek Direct API.

## Key Architectural Change
`scripts/_api_call.py` — A standalone Python script that:
- Receives model, system prompt, user content, and provider via command-line args
- Makes the API call using `urllib.request` with proper timeout
- Returns JSON result to stdout
- Called via `subprocess.run(timeout=N)` which provides reliable OS-level process timeout

## Pipeline Config (as of final fix)
```
--model deepseek/deepseek-v4-pro
--tier2-model deepseek/deepseek-v4-pro  
--provider deepseek
--tier2-provider deepseek
--redteam-model deepseek/deepseek-v4-pro
--redteam-provider deepseek
```

## Status
Pipeline is running in background as of ~13:50 UTC. Previous run (with OpenRouter Claude for exec) completed 14/14 regions but failed on exec summary. Current run should complete fully with DeepSeek Direct for everything.
