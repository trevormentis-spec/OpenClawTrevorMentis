#!/usr/bin/env python3
"""Validate or execute a human-approved Polymarket trade plan.

Dry-run is default. Execution requires:
  --execute --i-understand-risk
plus wallet environment variables.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

HOST = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rstrip("/")
CHAIN_ID = int(os.environ.get("POLYMARKET_CHAIN_ID", "137"))

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"GTC", "FOK", "FAK"}


def get_json(url: str, timeout: int = 15) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Trevor-polymarket-trader/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_geoblock() -> dict[str, Any]:
    for path in ("/auth/access-status", "/access-status"):
        try:
            payload = get_json(HOST + path)
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return {"unknown": True, "warning": "Could not confirm Polymarket access status from CLOB host."}


def dec(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{field} must be numeric, got {value!r}") from exc


def load_plan(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if "trade_plan" in payload and isinstance(payload["trade_plan"], dict):
        payload = payload["trade_plan"]
    if not isinstance(payload, dict):
        raise ValueError("plan must be a JSON object")
    return payload


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not plan.get("thesis"):
        errors.append("missing thesis")
    max_total = dec(plan.get("max_total_usdc", 0), "max_total_usdc")
    if max_total <= 0:
        errors.append("max_total_usdc must be > 0")
    orders = plan.get("orders")
    if not isinstance(orders, list) or not orders:
        errors.append("orders must be a non-empty list")
        return errors
    total = Decimal("0")
    for i, order in enumerate(orders):
        prefix = f"orders[{i}]"
        if not isinstance(order, dict):
            errors.append(f"{prefix} must be object")
            continue
        if not order.get("token_id"):
            errors.append(f"{prefix}.token_id missing")
        side = str(order.get("side", "")).upper()
        if side not in VALID_SIDES:
            errors.append(f"{prefix}.side must be one of {sorted(VALID_SIDES)}")
        order_type = str(order.get("order_type", "GTC")).upper()
        if order_type not in VALID_ORDER_TYPES:
            errors.append(f"{prefix}.order_type must be one of {sorted(VALID_ORDER_TYPES)}")
        has_amount = order.get("amount") is not None
        has_limit = order.get("price") is not None and order.get("size") is not None
        if has_amount and has_limit:
            errors.append(f"{prefix} must use either amount OR price+size, not both")
        elif has_amount:
            amount = dec(order.get("amount"), f"{prefix}.amount")
            if amount <= 0:
                errors.append(f"{prefix}.amount must be > 0")
            total += amount
        elif has_limit:
            price = dec(order.get("price"), f"{prefix}.price")
            size = dec(order.get("size"), f"{prefix}.size")
            if price <= 0 or price >= 1:
                errors.append(f"{prefix}.price must be between 0 and 1")
            if size <= 0:
                errors.append(f"{prefix}.size must be > 0")
            total += price * size
        else:
            errors.append(f"{prefix} must include amount OR price+size")
        if not order.get("rationale"):
            errors.append(f"{prefix}.rationale missing")
        if not order.get("invalidation"):
            errors.append(f"{prefix}.invalidation missing")
    if max_total > 0 and total > max_total:
        errors.append(f"estimated total risk {total} exceeds max_total_usdc {max_total}")
    return errors


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required env var: {name}")
    return value


def build_client():
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds
    except ImportError as exc:
        raise RuntimeError("Install py-clob-client-v2 before execution: pip install py-clob-client-v2") from exc

    private_key = require_env("POLYMARKET_PRIVATE_KEY")
    signature_type = int(os.environ.get("POLYMARKET_SIGNATURE_TYPE", "2"))
    funder = os.environ.get("POLYMARKET_FUNDER")
    kwargs: dict[str, Any] = {"host": HOST, "key": private_key, "chain_id": CHAIN_ID, "signature_type": signature_type}
    if funder:
        kwargs["funder"] = funder
    client = ClobClient(**kwargs)

    api_key = os.environ.get("POLYMARKET_CLOB_API_KEY")
    secret = os.environ.get("POLYMARKET_CLOB_SECRET")
    passphrase = os.environ.get("POLYMARKET_CLOB_PASS_PHRASE")
    if api_key and secret and passphrase:
        client.set_api_creds(ApiCreds(api_key=api_key, api_secret=secret, api_passphrase=passphrase))
    else:
        client.set_api_creds(client.create_or_derive_api_creds())
    return client


def execute_order(client: Any, order: dict[str, Any]) -> Any:
    try:
        from py_clob_client.clob_types import MarketOrderArgs, OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY, SELL
    except ImportError as exc:
        raise RuntimeError("py-clob-client-v2 imports failed") from exc

    side = BUY if str(order["side"]).upper() == "BUY" else SELL
    order_type = getattr(OrderType, str(order.get("order_type", "GTC")).upper())
    token_id = str(order["token_id"])
    if order.get("amount") is not None:
        args = MarketOrderArgs(token_id=token_id, amount=float(order["amount"]), side=side)
        signed = client.create_market_order(args)
    else:
        args = OrderArgs(price=float(order["price"]), size=float(order["size"]), side=side, token_id=token_id)
        signed = client.create_order(args)
    return client.post_order(signed, order_type)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate or execute Polymarket trade plan")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--execute", action="store_true", help="Actually submit orders")
    parser.add_argument("--i-understand-risk", action="store_true", help="Required with --execute")
    parser.add_argument("--skip-geoblock-check", action="store_true", help="Dry-run only; ignored during execution")
    args = parser.parse_args(argv)

    plan = load_plan(args.plan)
    errors = validate_plan(plan)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 2

    orders = plan["orders"]
    summary = {"ok": True, "mode": "execute" if args.execute else "dry_run", "orders": orders, "max_total_usdc": plan.get("max_total_usdc")}

    if not args.execute:
        if not args.skip_geoblock_check:
            summary["access_status"] = check_geoblock()
        print(json.dumps(summary, indent=2))
        return 0

    if not args.i_understand_risk:
        print("Refusing execution: --i-understand-risk is required with --execute", file=sys.stderr)
        return 2

    access = check_geoblock()
    if access.get("blocked") or access.get("geoBlocked") or access.get("restricted"):
        print(json.dumps({"ok": False, "error": "Polymarket access appears blocked/restricted", "access_status": access}, indent=2), file=sys.stderr)
        return 3

    client = build_client()
    results: list[Any] = []
    for order in orders:
        results.append(execute_order(client, order))
    print(json.dumps({"ok": True, "submitted": len(results), "results": results}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
