#!/usr/bin/env python3
"""
Kalshi Trading API Client
RSA PSS-signed requests to the Kalshi Trade API v2.

Authentication per Kalshi docs:
  Headers: KALSHI-ACCESS-KEY, KALSHI-ACCESS-TIMESTAMP, KALSHI-ACCESS-SIGNATURE
  Signature = base64(RSA-PSS-SHA256(timestamp + method + path_without_query))

Usage:
  from client import KalshiClient
  kc = KalshiClient()
  status = kc.get_exchange_status()
  balance = kc.get_balance()
"""

import os
import sys
import json
import time
import base64
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("kalshi")
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(levelname)s [kalshi] %(message)s"))
logger.addHandler(ch)


class KalshiAuthError(Exception):
    """Authentication or signing failure."""


class KalshiAPIError(Exception):
    """API returned an error response."""


class KalshiClient:
    """Authenticated Kalshi Trade API v2 client."""

    BASE_URL_DEFAULT = "https://api.elections.kalshi.com"
    BASE_URL_DEMO = "https://demo-api.kalshi.co"
    API_PREFIX = "/trade-api/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rsa_key_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Args:
            api_key: Kalshi API key UUID (env: KALSHI_API_KEY)
            rsa_key_path: Path to RSA private key PEM (env: KALSHI_RSA_KEY_PATH)
            base_url: API base URL (env: KALSHI_BASE_URL)
        """
        self.api_key = api_key or os.environ.get("KALSHI_API_KEY")
        self.rsa_key_path = rsa_key_path or os.environ.get("KALSHI_RSA_KEY_PATH")
        raw_url = (
            base_url
            or os.environ.get("KALSHI_BASE_URL")
            or self.BASE_URL_DEFAULT
        )
        # Strip trailing slash and /trade-api/v2 suffix — we'll prefix paths ourselves
        raw_url = raw_url.rstrip("/")
        if raw_url.endswith("/trade-api/v2"):
            raw_url = raw_url[:-len("/trade-api/v2")]
        self.base_url = raw_url

        if not self.api_key:
            raise KalshiAuthError(
                "KALSHI_API_KEY not set. Provide it or set env var."
            )
        if not self.rsa_key_path:
            raise KalshiAuthError(
                "KALSHI_RSA_KEY_PATH not set. Provide it or set env var."
            )

        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    @property
    def private_key(self) -> rsa.RSAPrivateKey:
        if self._private_key is None:
            try:
                with open(self.rsa_key_path, "rb") as f:
                    self._private_key = serialization.load_pem_private_key(
                        f.read(), password=None, backend=default_backend()
                    )
            except FileNotFoundError:
                raise KalshiAuthError(
                    f"RSA key file not found: {self.rsa_key_path}"
                )
            except Exception as e:
                raise KalshiAuthError(f"Failed to load RSA key: {e}")
        return self._private_key

    def _sign(self, timestamp_str: str, method: str, path: str) -> str:
        """Sign timestamp + method + path with RSA PSS SHA-256."""
        message = f"{timestamp_str}{method}{path}"
        try:
            signature = self.private_key.sign(
                message.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )
            return base64.b64encode(signature).decode("utf-8")
        except Exception as e:
            raise KalshiAuthError(f"RSA signing failed: {e}")

    def _auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """Build Kalshi authentication headers."""
        ts = int(time.time() * 1000)
        ts_str = str(ts)
        # Strip query params from path for signing; include API prefix
        full_path = f"{self.API_PREFIX}{path}"
        path_no_query = full_path.split("?")[0]
        sig = self._sign(ts_str, method, path_no_query)
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-TIMESTAMP": ts_str,
            "KALSHI-ACCESS-SIGNATURE": sig,
        }

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Send an authenticated request to the Kalshi API."""
        # Build full URL: base_url + API_PREFIX + path
        url = f"{self.base_url}{self.API_PREFIX}{path}"
        headers = self._auth_headers(method, path)

        logger.debug("→ %s %s", method, url)
        if data:
            logger.debug("  body: %s", json.dumps(data))

        resp = self._session.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=30,
        )

        logger.debug("← %s %s", resp.status_code, resp.text[:500])
        return resp

    def _handle_response(
        self, resp: requests.Response, ok_codes: tuple = (200, 201)
    ) -> Dict[str, Any]:
        """Parse response, raising on error status."""
        if resp.status_code in ok_codes:
            return resp.json()
        # Try to extract error detail
        try:
            body = resp.json()
            detail = body.get("error", body.get("message", str(body)))
        except Exception:
            detail = resp.text[:500]
        raise KalshiAPIError(
            f"{resp.status_code} {resp.reason}: {detail}"
        )

    # ── Exchange ────────────────────────────────────────────────────

    def get_exchange_status(self) -> Dict[str, Any]:
        """GET /exchange/status — check if exchange is active."""
        return self._handle_response(self._request("GET", "/exchange/status"))

    # ── Markets ─────────────────────────────────────────────────────

    def get_markets(
        self,
        status: Optional[str] = None,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
        with_nested_markets: bool = False,
    ) -> Dict[str, Any]:
        """GET /markets — list/filter markets."""
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor
        if with_nested_markets:
            params["with_nested_markets"] = "true"
        return self._handle_response(self._request("GET", "/markets", params=params))

    def get_market(self, ticker: str) -> Dict[str, Any]:
        """GET /markets/{ticker} — single market detail."""
        return self._handle_response(
            self._request("GET", f"/markets/{ticker}")
        )

    def get_orderbook(self, ticker: str, depth: int = 25) -> Dict[str, Any]:
        """GET /markets/{ticker}/orderbook — order book depth."""
        return self._handle_response(
            self._request(
                "GET", f"/markets/{ticker}/orderbook", params={"depth": depth}
            )
        )

    # ── Portfolio ───────────────────────────────────────────────────

    def get_balance(self) -> Dict[str, Any]:
        """GET /portfolio/balance — account balance."""
        return self._handle_response(
            self._request("GET", "/portfolio/balance")
        )

    def get_positions(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        settlement_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /portfolio/positions — open positions."""
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if settlement_status:
            params["settlement_status"] = settlement_status
        return self._handle_response(
            self._request("GET", "/portfolio/positions", params=params)
        )

    def get_orders(
        self,
        ticker: Optional[str] = None,
        status: str = "open",
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /portfolio/orders — list orders."""
        params: Dict[str, Any] = {"limit": limit, "status": status}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor
        return self._handle_response(
            self._request("GET", "/portfolio/orders", params=params)
        )

    def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        buy_max_cost: Optional[int] = None,
        client_order_id: Optional[str] = None,
        time_in_force: str = "good_till_canceled",
        post_only: bool = False,
        reduce_only: bool = False,
        expiration_ts: Optional[int] = None,
        self_trade_prevention_type: Optional[str] = None,
        cancel_order_on_pause: bool = False,
    ) -> Dict[str, Any]:
        """POST /portfolio/orders — submit an order.

        Args:
            ticker: Market ticker (e.g., KXTARIFFRATEPRC-25JUL01)
            side: "yes" or "no"
            action: "buy" or "sell"
            count: Number of contracts (integer, >= 1)
            yes_price: Limit price in cents for YES (1-99)
            no_price: Limit price in cents for NO (1-99)
            buy_max_cost: Max cost in cents for market orders (forces FoK)
            client_order_id: Optional client reference ID
            time_in_force: "fill_or_kill", "good_till_canceled", "immediate_or_cancel"
            post_only: Only add liquidity
            reduce_only: Only reduce position
            expiration_ts: Unix seconds for GTC expiration
            self_trade_prevention_type: "taker_at_cross" or "maker"
            cancel_order_on_pause: Cancel if exchange pauses
        """
        body: Dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "time_in_force": time_in_force,
        }

        if yes_price is not None:
            body["yes_price"] = yes_price
        if no_price is not None:
            body["no_price"] = no_price
        if buy_max_cost is not None:
            body["buy_max_cost"] = buy_max_cost
        if client_order_id:
            body["client_order_id"] = client_order_id
        if post_only:
            body["post_only"] = True
        if reduce_only:
            body["reduce_only"] = True
        if expiration_ts:
            body["expiration_ts"] = expiration_ts
        if self_trade_prevention_type:
            body["self_trade_prevention_type"] = self_trade_prevention_type
        if cancel_order_on_pause:
            body["cancel_order_on_pause"] = True

        return self._handle_response(
            self._request("POST", "/portfolio/orders", data=body), ok_codes=(201,)
        )

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """DELETE /portfolio/orders/{order_id} — cancel an order."""
        return self._handle_response(
            self._request("DELETE", f"/portfolio/orders/{order_id}")
        )

    def cancel_all_orders(
        self, ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """DELETE /portfolio/orders — cancel all open orders, optionally for a ticker."""
        params = {}
        if ticker:
            params["ticker"] = ticker
        return self._handle_response(
            self._request("DELETE", "/portfolio/orders", params=params)
        )

    def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /portfolio/trades — trade history."""
        params: Dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor
        return self._handle_response(
            self._request("GET", "/portfolio/trades", params=params)
        )

    def get_settlements(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /portfolio/settlements — settlement history."""
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._handle_response(
            self._request("GET", "/portfolio/settlements", params=params)
        )


# ── CLI: quick status/balance/positions queries ────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kalshi API Quick Query")
    parser.add_argument("--status", action="store_true", help="Exchange status")
    parser.add_argument("--balance", action="store_true", help="Account balance")
    parser.add_argument("--positions", action="store_true", help="Open positions")
    parser.add_argument("--orders", action="store_true", help="Open orders")
    parser.add_argument("--ticker", type=str, help="Filter by ticker")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        kc = KalshiClient()

        if args.status:
            status = kc.get_exchange_status()
            print(json.dumps(status, indent=2))

        if args.balance:
            balance = kc.get_balance()
            print(json.dumps(balance, indent=2))

        if args.positions:
            positions = kc.get_positions()
            print(json.dumps(positions, indent=2))

        if args.orders:
            orders = kc.get_orders(ticker=args.ticker)
            print(json.dumps(orders, indent=2))

        if not any([args.status, args.balance, args.positions, args.orders]):
            # Default: show status + balance
            print("=== Exchange Status ===")
            print(json.dumps(kc.get_exchange_status(), indent=2))
            print("\n=== Balance ===")
            print(json.dumps(kc.get_balance(), indent=2))

    except (KalshiAuthError, KalshiAPIError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
