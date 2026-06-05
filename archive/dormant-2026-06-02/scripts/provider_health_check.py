#!/usr/bin/env python3
# GATE_EXEMPT: provider endpoints are hardcoded API URLs, not secrets
"""Provider health check — pre-flight probe for all three API providers.

Tests:
1. OpenRouter: lightweight model list query
2. Anthropic Direct: short prompt completion
3. DeepSeek Direct: short prompt completion

Output: JSON to stdout with provider status and latency.
Exit code: 0 if at least one provider works, 1 if all fail.

Environment variables:
  OPENROUTER_API_KEY   — OpenRouter API key
  ANTHROPIC_API_KEY    — Anthropic Direct API key
  DEEPSEEK_API_KEY     — DeepSeek Direct API key

Usage:
  python3 scripts/provider_health_check.py
  python3 scripts/provider_health_check.py --json  # machine-readable
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error


def probe_openrouter():
    """Probe OpenRouter by fetching model list (lightweight)."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return {
            "provider": "openrouter",
            "status": "failed",
            "reason": "no API key configured",
            "latency_ms": -1,
            "model_tested": "N/A",
            "billing_issue": False,
        }

    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency = int((time.time() - start) * 1000)
            status_code = resp.getcode()
            if status_code == 200:
                return {
                    "provider": "openrouter",
                    "status": "ok",
                    "latency_ms": latency,
                    "model_tested": "models.list (lightweight probe)",
                    "billing_issue": False,
                }
            else:
                return {
                    "provider": "openrouter",
                    "status": "degraded",
                    "latency_ms": latency,
                    "model_tested": "N/A",
                    "reason": f"HTTP {status_code}",
                    "billing_issue": status_code in (401, 402, 403),
                    "billing_message": f"HTTP {status_code} — check API key or billing status"
                    if status_code in (401, 402, 403)
                    else None,
                }
    except urllib.error.HTTPError as e:
        latency = int((time.time() - start) * 1000)
        result = {
            "provider": "openrouter",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"HTTP {e.code}: {str(e)[:200]}",
        }
        if e.code in (401, 402, 403):
            result["billing_issue"] = True
            result["billing_message"] = f"HTTP {e.code} — check API key or billing status"
        else:
            result["billing_issue"] = False
        return result
    except urllib.error.URLError as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "openrouter",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"URLError: {str(e.reason)[:200] if hasattr(e, 'reason') else str(e)[:200]}",
            "billing_issue": False,
        }
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "openrouter",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"Exception: {str(e)[:200]}",
            "billing_issue": False,
        }


def probe_anthropic():
    """Probe Anthropic Direct with a short prompt completion."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "provider": "anthropic_direct",
            "status": "failed",
            "reason": "no API key configured",
            "latency_ms": -1,
            "model_tested": "N/A",
            "billing_issue": False,
        }

    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Reply with just the word OK."}],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("Content-Type", "application/json")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            latency = int((time.time() - start) * 1000)
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            model_used = data.get("model", "claude-sonnet-4-20250514")
            return {
                "provider": "anthropic_direct",
                "status": "ok",
                "latency_ms": latency,
                "model_tested": model_used,
                "billing_issue": False,
            }
    except urllib.error.HTTPError as e:
        latency = int((time.time() - start) * 1000)
        try:
            body = e.read().decode("utf-8")
            detail = json.loads(body).get("error", {}).get("message", str(e))[:200]
        except Exception:
            detail = str(e)[:200]
        result = {
            "provider": "anthropic_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"HTTP {e.code}: {detail}",
        }
        if e.code in (401, 402, 403):
            result["billing_issue"] = True
            result["billing_message"] = f"HTTP {e.code} — check API key or billing status"
        else:
            result["billing_issue"] = False
        return result
    except urllib.error.URLError as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "anthropic_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"URLError: {str(e.reason)[:200] if hasattr(e, 'reason') else str(e)[:200]}",
            "billing_issue": False,
        }
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "anthropic_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"Exception: {str(e)[:200]}",
            "billing_issue": False,
        }


def probe_deepseek():
    """Probe DeepSeek Direct with a short prompt completion."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return {
            "provider": "deepseek_direct",
            "status": "failed",
            "reason": "no API key configured",
            "latency_ms": -1,
            "model_tested": "N/A",
            "billing_issue": False,
        }

    url = "https://api.deepseek.com/chat/completions"
    payload = json.dumps({
        "model": "deepseek-chat",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Reply with just the word OK."}],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            latency = int((time.time() - start) * 1000)
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            model_used = data.get("model", "deepseek-chat")
            return {
                "provider": "deepseek_direct",
                "status": "ok",
                "latency_ms": latency,
                "model_tested": model_used,
                "billing_issue": False,
            }
    except urllib.error.HTTPError as e:
        latency = int((time.time() - start) * 1000)
        try:
            body = e.read().decode("utf-8")
            detail = json.loads(body).get("error", {}).get("message", str(e))[:200]
        except Exception:
            detail = str(e)[:200]
        result = {
            "provider": "deepseek_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"HTTP {e.code}: {detail}",
        }
        if e.code in (401, 402, 403):
            result["billing_issue"] = True
            result["billing_message"] = f"HTTP {e.code} — check API key or billing status"
        else:
            result["billing_issue"] = False
        return result
    except urllib.error.URLError as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "deepseek_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"URLError: {str(e.reason)[:200] if hasattr(e, 'reason') else str(e)[:200]}",
            "billing_issue": False,
        }
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {
            "provider": "deepseek_direct",
            "status": "failed",
            "latency_ms": latency,
            "model_tested": "N/A",
            "reason": f"Exception: {str(e)[:200]}",
            "billing_issue": False,
        }


def main():
    results = []
    results.append(probe_openrouter())
    results.append(probe_anthropic())
    results.append(probe_deepseek())

    # Determine overall exit code
    any_ok = any(r.get("status") == "ok" for r in results)
    exit_code = 0 if any_ok else 1

    # Build output
    output = {"providers": results, "exit_code": exit_code}

    if "--json" in sys.argv:
        print(json.dumps(output, indent=2))
    else:
        print(f"Provider Health Check — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
        print(f"Exit code: {exit_code} ({'At least one provider OK' if any_ok else 'ALL PROVIDERS FAILED'})")
        print()
        for r in results:
            icon = {"ok": "✅", "degraded": "⚠️", "failed": "❌"}.get(r["status"], "❓")
            bill = " [BILLING ISSUE]" if r.get("billing_issue") else ""
            lat = f"{r['latency_ms']}ms" if r["latency_ms"] >= 0 else "N/A"
            print(f"  {icon} {r['provider']}: {r['status']}{bill} ({lat})")
            if r.get("reason"):
                print(f"     Reason: {r['reason']}")
            if r.get("billing_message"):
                print(f"     Billing: {r['billing_message']}")
        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
