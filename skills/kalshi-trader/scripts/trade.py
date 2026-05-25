#!/usr/bin/env python3
"""
Kalshi Trade Planning & Execution

Usage:
  # Check status/portfolio
  python3 trade.py --status
  python3 trade.py --balance
  python3 trade.py --positions
  python3 trade.py --orders

  # Dry-run a trade plan
  python3 trade.py --dry-run --plan /tmp/kalshi-plan.json

  # Execute (requires explicit confirmation)
  python3 trade.py --execute --i-understand-risk --plan /tmp/kalshi-plan.json

  # Cancel orders
  python3 trade.py --cancel ORDER_ID
  python3 trade.py --cancel-all [--ticker TICKER]
"""

import sys
import json
import uuid
import argparse
from typing import Optional, Dict, Any
from client import KalshiClient, KalshiAuthError, KalshiAPIError


def format_cents(cents) -> str:
    """Format cents as dollars."""
    if cents is None or cents == "N/A":
        return "N/A"
    try:
        return f"${int(cents) / 100:.2f}"
    except (ValueError, TypeError):
        return str(cents)


def show_status(client: KalshiClient):
    """Display exchange status."""
    try:
        s = client.get_exchange_status()
        print("=== Kalshi Exchange Status ===")
        print(f"Exchange active:  {s.get('exchange_active')}")
        print(f"Trading active:   {s.get('trading_active')}")
        resume = s.get("exchange_estimated_resume_time")
        if resume:
            print(f"Est. resume:      {resume}")
        print()
    except KalshiAPIError as e:
        print(f"Error: {e}")


def show_balance(client: KalshiClient):
    """Display account balance."""
    try:
        b = client.get_balance()
        print("=== Account Balance ===")
        if "balance" in b:
            bal = b["balance"]
            print(f"Balance:          {format_cents(bal)}")
        if "available_balance" in b:
            print(f"Available:        {format_cents(b['available_balance'])}")
        if "portfolio_value" in b:
            print(f"Portfolio value:  {format_cents(b['portfolio_value'])}")
        if "total_value" in b:
            print(f"Total value:      {format_cents(b['total_value'])}")
        if "pending_withdrawal" in b:
            print(f"Pending withdraw: {format_cents(b['pending_withdrawal'])}")
        # Dump full response for any unexpected fields
        for k, v in b.items():
            if k not in ("balance", "available_balance", "portfolio_value",
                         "total_value", "pending_withdrawal"):
                print(f"{k}: {v}")
        print()
    except KalshiAPIError as e:
        print(f"Error: {e}")


def show_positions(client: KalshiClient):
    """Display open positions."""
    try:
        p = client.get_positions()
        positions = p.get("positions", [])
        print(f"=== Open Positions ({len(positions)}) ===")
        if not positions:
            print("No open positions.")
            return
        for pos in positions:
            ticker = pos.get("ticker", "?")
            side = pos.get("side", "?")
            count = pos.get("count", "?")
            yes_price = pos.get("average_yes_price", pos.get("avg_price", "N/A"))
            market_value = pos.get("market_value", "N/A")
            print(f"  {ticker:<45} {side:>3} ×{str(count):<5} "
                  f"avg:{format_cents(yes_price):>8}  mkt:{format_cents(market_value):>8}")
        print()
    except KalshiAPIError as e:
        print(f"Error: {e}")


def show_orders(client: KalshiClient, ticker: Optional[str] = None):
    """Display open orders."""
    try:
        o = client.get_orders(ticker=ticker)
        orders = o.get("orders", [])
        print(f"=== Open Orders ({len(orders)}) ===")
        if not orders:
            print("No open orders.")
            return
        for order in orders:
            oid = order.get("order_id", "?")
            tkr = order.get("ticker", "?")
            side = order.get("side", "?")
            action = order.get("action", "?")
            count = order.get("count", order.get("remaining_count", "?"))
            price = order.get("price", "N/A")
            status = order.get("status", "?")
            print(f"  [{oid[:16]}...] {tkr:<40} {action}/{side} ×{str(count):<5} "
                  f"@{format_cents(price):>8} [{status}]")
        print()
    except KalshiAPIError as e:
        print(f"Error: {e}")


def validate_plan(plan: Dict[str, Any]):
    """Validate a trade plan against required schema."""
    errors = []

    if "thesis" not in plan:
        errors.append("Missing 'thesis'")

    if "max_total_cents" not in plan:
        errors.append("Missing 'max_total_cents' (max risk in cents)")
    elif not isinstance(plan["max_total_cents"], (int, float)) or plan["max_total_cents"] <= 0:
        errors.append("'max_total_cents' must be a positive number")

    if "orders" not in plan or not isinstance(plan["orders"], list) or len(plan["orders"]) == 0:
        errors.append("Missing or empty 'orders' array")
    else:
        for i, order in enumerate(plan["orders"]):
            for field in ["ticker", "action", "side", "count"]:
                if field not in order:
                    errors.append(f"Order[{i}]: missing '{field}'")
            # Validate price fields
            has_limit = "yes_price" in order or "no_price" in order
            has_market = "buy_max_cost" in order
            if not has_limit and not has_market:
                errors.append(
                    f"Order[{i}]: need 'yes_price'/'no_price' (limit) or 'buy_max_cost' (market)"
                )
            if order.get("action") not in ("buy", "sell"):
                errors.append(f"Order[{i}]: action must be 'buy' or 'sell'")
            if order.get("side") not in ("yes", "no"):
                errors.append(f"Order[{i}]: side must be 'yes' or 'no'")
            if not isinstance(order.get("count"), int) or order["count"] < 1:
                errors.append(f"Order[{i}]: count must be integer >= 1")

    if "invalidation" not in plan:
        errors.append("Missing 'invalidation' condition")

    if errors:
        print("❌ Plan validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("✅ Plan validation PASSED")
    return True


def dry_run(client: KalshiClient, plan: Dict[str, Any]):
    """Dry-run: validate and preview what would be sent."""
    if not validate_plan(plan):
        return False

    print(f"\n=== DRY RUN ===\n")
    print(f"Thesis: {plan['thesis']}")
    print(f"Max risk: {format_cents(plan['max_total_cents'])}")
    print(f"Invalidation: {plan.get('invalidation', 'N/A')}")
    print(f"Exit: {plan.get('exit_criteria', 'N/A')}")
    print()

    # Fetch current market prices
    total_est_cost = 0
    for i, order in enumerate(plan["orders"]):
        ticker = order["ticker"]
        print(f"Order {i+1}: {ticker}")
        print(f"  Action: {order['action']} {order['side']} × {order['count']}")

        if "yes_price" in order or "no_price" in order:
            price = order.get("yes_price", order.get("no_price"))
            est_cost = order["count"] * price  # in cents
            print(f"  Limit price: {price}¢ → est. cost: {format_cents(est_cost)}")
        elif "buy_max_cost" in order:
            est_cost = order["buy_max_cost"]
            print(f"  Market order: max cost {format_cents(est_cost)}")

        total_est_cost += est_cost

        # Try to get live market data
        try:
            m = client.get_market(ticker)
            market = m.get("market", m)
            print(f"  Current: bid {market.get('yes_bid_dollars', market.get('yes_bid', '?'))} / ask {market.get('yes_ask_dollars', market.get('yes_ask', '?'))}")
            print(f"  Last price: {market.get('last_price_dollars', market.get('last_price', '?'))}")
            print(f"  24h Volume: {market.get('volume_24h_fp', market.get('volume', '?'))}")
            print(f"  Status: {market.get('status', '?')}")
        except KalshiAPIError:
            print(f"  [Could not fetch live market data]")

        print(f"  Rationale: {order.get('rationale', 'N/A')}")
        print()

    print(f"Total estimated cost: {format_cents(total_est_cost)}")
    print(f"Max risk allowed:     {format_cents(plan['max_total_cents'])}")

    if total_est_cost > plan["max_total_cents"]:
        print(f"❌ Estimated cost {format_cents(total_est_cost)} exceeds max risk {format_cents(plan['max_total_cents'])}!")
        return False
    else:
        print(f"✅ Within risk limits")
        return True


def execute_plan(client: KalshiClient, plan: Dict[str, Any], i_understand_risk: bool = False):
    """Execute a validated trade plan."""
    if not i_understand_risk:
        print("ERROR: --i-understand-risk flag is required for execution.")
        print("Run with --dry-run first to preview.")
        return False

    if not validate_plan(plan):
        return False

    print(f"\n=== EXECUTING ===\n")
    print(f"Thesis: {plan['thesis']}")

    results = []
    total_cost = 0

    for i, order in enumerate(plan["orders"]):
        print(f"\n▶ Order {i+1}/{len(plan['orders'])}: {order['action'].upper()} {order['side'].upper()} ×{order['count']} {order['ticker']}")

        try:
            kwargs = {
                "ticker": order["ticker"],
                "side": order["side"],
                "action": order["action"],
                "count": order["count"],
                "time_in_force": order.get("time_in_force", "good_till_canceled"),
            }
            if "yes_price" in order:
                kwargs["yes_price"] = order["yes_price"]
            if "no_price" in order:
                kwargs["no_price"] = order["no_price"]
            if "buy_max_cost" in order:
                kwargs["buy_max_cost"] = order["buy_max_cost"]
            if "client_order_id" in order:
                kwargs["client_order_id"] = order["client_order_id"]
            if order.get("post_only"):
                kwargs["post_only"] = True
            if order.get("reduce_only"):
                kwargs["reduce_only"] = True
            if order.get("cancel_order_on_pause"):
                kwargs["cancel_order_on_pause"] = True

            resp = client.create_order(**kwargs)
            created = resp.get("order", resp)
            order_id = created.get("order_id", "UNKNOWN")
            status = created.get("status", "?")
            price = created.get("price", created.get("average_price", "N/A"))

            print(f"  ✅ Created order {order_id}")
            print(f"     Status: {status}")
            print(f"     Price: {format_cents(price)}")

            results.append({"order_id": order_id, "status": status, "price": price})
            if price and price != "N/A":
                total_cost += order["count"] * int(price)

        except KalshiAPIError as e:
            print(f"  ❌ Failed: {e}")
            results.append({"error": str(e)})
            continue

    print(f"\n{'='*60}")
    print(f"Execution complete. {len([r for r in results if 'order_id' in r])}/{len(plan['orders'])} placed.")
    print(f"Estimated total cost: {format_cents(total_cost)}")

    return True


def cancel_order(client: KalshiClient, order_id: str):
    """Cancel a specific order."""
    try:
        resp = client.cancel_order(order_id)
        print(f"✅ Order {order_id} cancelled.")
        print(json.dumps(resp, indent=2))
    except KalshiAPIError as e:
        print(f"Error: {e}")


def cancel_all(client: KalshiClient, ticker: Optional[str] = None):
    """Cancel all open orders, optionally filtered by ticker."""
    try:
        resp = client.cancel_all_orders(ticker=ticker)
        msg = f"all orders" if not ticker else f"orders for {ticker}"
        print(f"✅ Cancelled {msg}.")
        print(json.dumps(resp, indent=2))
    except KalshiAPIError as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Kalshi Trade Planning & Execution"
    )

    # Query commands (no trade)
    parser.add_argument("--status", action="store_true", help="Exchange status")
    parser.add_argument("--balance", action="store_true", help="Account balance")
    parser.add_argument("--positions", action="store_true", help="Open positions")
    parser.add_argument("--orders", action="store_true", help="Open orders")
    parser.add_argument("--ticker", type=str, help="Filter by ticker")

    # Trade commands
    parser.add_argument("--plan", type=str, help="Path to trade plan JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview plan")
    parser.add_argument("--execute", action="store_true", help="Execute the plan")
    parser.add_argument("--i-understand-risk", action="store_true",
                        help="Acknowledge trading risk (required for --execute)")

    # Cancel commands
    parser.add_argument("--cancel", type=str, help="Cancel order by ID")
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all open orders")

    args = parser.parse_args()

    try:
        client = KalshiClient()

        # Query commands
        if args.status:
            show_status(client)
        if args.balance:
            show_balance(client)
        if args.positions:
            show_positions(client)
        if args.orders:
            show_orders(client, args.ticker)

        # Cancel commands
        if args.cancel:
            cancel_order(client, args.cancel)
        if args.cancel_all:
            cancel_all(client, args.ticker)

        # Trade commands
        if args.dry_run or args.execute:
            if not args.plan:
                print("ERROR: --plan is required for --dry-run or --execute", file=sys.stderr)
                sys.exit(1)

            with open(args.plan) as f:
                plan = json.load(f)

            if args.dry_run:
                dry_run(client, plan)
            elif args.execute:
                if not args.i_understand_risk:
                    print("ERROR: --i-understand-risk flag required for execution.",
                          file=sys.stderr)
                    sys.exit(1)
                execute_plan(client, plan, i_understand_risk=True)

    except (KalshiAuthError, KalshiAPIError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in plan file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
