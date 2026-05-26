#!/usr/bin/env python3
"""
Kalshi WebSocket Listener
Real-time price updates, fill notifications, and orderbook tracking.

Connects to Kalshi WebSocket API v2 with RSA authentication.
Subscribes to:
  - ticker:    Live price updates for all markets
  - trade:     Trade executions on tracked markets
  - fill:      Your own order fills (private)
  - orderbook_delta: Orderbook changes on tracked markets

Usage:
  python3 ws_listener.py                        # Track all markets, log to console
  python3 ws_listener.py --markets TICKER1,TICKER2  # Track specific markets
  python3 ws_listener.py --daemon --log-file /path/to/log  # Background mode
  python3 ws_listener.py --exit-on-fill          # Exit process when your order fills

Integration:
  The listener publishes events to a local JSONL file that the monitor reads.
  Real-time → no polling lag on fills and price moves.
"""

import os
import sys
import json
import time
import signal
import base64
import asyncio
import logging
import datetime
import argparse
from pathlib import Path
from typing import Optional, Set, Dict, Any, List

import websockets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# ── Configuration ────────────────────────────────────────────────────

WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
WS_URL_DEMO = "wss://demo-api.kalshi.co/trade-api/ws/v2"
WS_SIGN_PATH = "/trade-api/ws/v2"

logger = logging.getLogger("kalshi-ws")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [ws] %(levelname)s %(message)s", datefmt="%H:%M:%S"
))
logger.addHandler(handler)


# ── Auth Helpers ─────────────────────────────────────────────────────

def load_private_key(path: str):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )


def sign_ws(private_key, timestamp_str: str) -> str:
    """Sign timestamp + GET + /trade-api/ws/v2."""
    message = f"{timestamp_str}GET{WS_SIGN_PATH}".encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def build_auth_headers(api_key: str, private_key) -> Dict[str, str]:
    """Build authentication headers for WebSocket connection."""
    ts = int(time.time() * 1000)
    sig = sign_ws(private_key, str(ts))
    return {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-TIMESTAMP": str(ts),
        "KALSHI-ACCESS-SIGNATURE": sig,
    }


# ── Event Bus ────────────────────────────────────────────────────────

class EventBus:
    """Simple pub/sub for WebSocket events. Writes to JSONL log for monitor integration."""

    def __init__(self, log_path: Optional[str] = None):
        self._handlers: Dict[str, List] = {}
        self._log_path = log_path
        self._prices: Dict[str, Dict[str, Any]] = {}  # ticker → latest price data
        self._fills: List[Dict] = []
        self._last_fill_time: Optional[float] = None

    def on(self, event_type: str):
        """Decorator to register a handler."""
        def decorator(func):
            self._handlers.setdefault(event_type, []).append(func)
            return func
        return decorator

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered handlers."""
        # Persist to JSONL
        if self._log_path:
            try:
                record = {
                    "ts": datetime.datetime.now(datetime.UTC).isoformat(),
                    "type": event_type,
                    **data,
                }
                with open(self._log_path, "a") as f:
                    f.write(json.dumps(record, default=str) + "\n")
            except Exception:
                pass

        # Dispatch to handlers
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Handler error [{event_type}]: {e}")

    def get_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        return self._prices.get(ticker)

    def get_all_prices(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._prices)


# ── WebSocket Client ─────────────────────────────────────────────────

class KalshiWebSocket:
    """Authenticated Kalshi WebSocket client with auto-reconnect."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rsa_key_path: Optional[str] = None,
        demo: bool = False,
        log_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ["KALSHI_API_KEY"]
        self.rsa_key_path = rsa_key_path or os.environ["KALSHI_RSA_KEY_PATH"]
        self.ws_url = WS_URL_DEMO if demo else WS_URL
        self.bus = EventBus(log_path=log_path)

        self._private_key = load_private_key(self.rsa_key_path)
        self._ws = None
        self._running = True
        self._reconnect_delay = 1  # seconds, exponential backoff
        self._max_reconnect_delay = 60
        self._message_id = 0
        self._subscribed_markets: Set[str] = set()

    async def connect(self):
        """Establish WebSocket connection with authentication."""
        headers = build_auth_headers(self.api_key, self._private_key)
        logger.info(f"Connecting to {self.ws_url}...")

        try:
            self._ws = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            logger.info("✅ Connected to Kalshi WebSocket")
            self._reconnect_delay = 1  # Reset on successful connection
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def subscribe(self, channels: List[str], markets: Optional[List[str]] = None):
        """Subscribe to channels, optionally scoped to specific markets."""
        self._message_id += 1
        sub = {
            "id": self._message_id,
            "cmd": "subscribe",
            "params": {"channels": channels},
        }
        if markets:
            sub["params"]["market_tickers"] = markets
            self._subscribed_markets.update(markets)

        await self._ws.send(json.dumps(sub))
        logger.info(f"Subscribed: {channels}" + (f" ({len(markets)} markets)" if markets else ""))

    async def update_subscription(self, markets: List[str]):
        """Add markets to existing subscriptions."""
        new_markets = set(markets) - self._subscribed_markets
        if not new_markets:
            return

        self._message_id += 1
        sub = {
            "id": self._message_id,
            "cmd": "update_subscription",
            "params": {
                "action": "add_markets",
                "market_tickers": list(new_markets),
            },
        }
        await self._ws.send(json.dumps(sub))
        self._subscribed_markets.update(new_markets)
        logger.info(f"Added {len(new_markets)} markets to subscription")

    async def listen(self):
        """Main message processing loop with reconnect."""
        while self._running:
            if not self._ws:
                connected = await self.connect()
                if not connected:
                    delay = min(self._reconnect_delay, self._max_reconnect_delay)
                    logger.warning(f"Reconnecting in {delay}s...")
                    await asyncio.sleep(delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                    continue

                # Subscribe to base channels on (re)connect
                try:
                    await self.subscribe(["fill"])     # Your own fills (private, no market filter needed)
                    if self._subscribed_markets:
                        await self.subscribe(
                            ["ticker", "trade", "orderbook_delta"],
                            list(self._subscribed_markets),
                        )
                except Exception as e:
                    logger.error(f"Subscribe error: {e}")
                    await self._ws.close()
                    continue

            try:
                async for message in self._ws:
                    await self._process_message(message)
            except websockets.ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
            except Exception as e:
                logger.error(f"Listen error: {e}")

            # Reconnect with backoff
            self._ws = None
            delay = min(self._reconnect_delay, self._max_reconnect_delay)
            logger.warning(f"Reconnecting in {delay}s...")
            await asyncio.sleep(delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _process_message(self, raw: str):
        """Parse and route incoming WebSocket messages."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON message: {raw[:100]}")
            return

        msg_type = data.get("type", "unknown")
        msg = data.get("msg", {})

        if msg_type == "ticker":
            ticker = msg.get("market_ticker", "?")
            self.bus._prices[ticker] = {
                "yes_bid": msg.get("yes_bid_dollars"),
                "yes_ask": msg.get("yes_ask_dollars"),
                "last_price": msg.get("last_price_dollars"),
                "volume_24h": msg.get("volume_24h_fp"),
                "ts": msg.get("ts"),
            }
            await self.bus.emit("ticker", {"ticker": ticker, "data": self.bus._prices[ticker]})

        elif msg_type == "trade":
            ticker = msg.get("market_ticker", "?")
            trade_data = {
                "ticker": ticker,
                "price": msg.get("price_dollars"),
                "size": msg.get("size_fp"),
                "side": msg.get("side"),
                "ts": msg.get("ts"),
            }
            await self.bus.emit("trade", trade_data)

        elif msg_type == "fill":
            fill_data = {
                "order_id": msg.get("order_id"),
                "ticker": msg.get("ticker"),
                "side": msg.get("side"),
                "action": msg.get("action"),
                "count": msg.get("count"),
                "price": msg.get("price_dollars"),
                "fee": msg.get("fee_dollars"),
            }
            self.bus._fills.append(fill_data)
            self.bus._last_fill_time = time.time()
            await self.bus.emit("fill", fill_data)

        elif msg_type == "orderbook_snapshot":
            ticker = msg.get("market_ticker", "?")
            await self.bus.emit("orderbook_snapshot", {
                "ticker": ticker,
                "yes_bids": msg.get("yes_bids", [])[:5],
                "no_bids": msg.get("no_bids", [])[:5],
            })

        elif msg_type == "orderbook_delta":
            ticker = msg.get("market_ticker", "?")
            changes = msg.get("changes", [])
            await self.bus.emit("orderbook_delta", {
                "ticker": ticker,
                "changes": changes,
                "our_order": "client_order_id" in msg,
            })

        elif msg_type == "market_lifecycle_v2":
            ticker = msg.get("market_ticker", "?")
            await self.bus.emit("market_lifecycle", {
                "ticker": ticker,
                "status": msg.get("status"),
                "close_time": msg.get("close_time"),
            })

        elif msg_type == "subscribed":
            # Confirmation of subscription — no action needed
            pass

        elif msg_type == "error":
            logger.error(f"WS Error: {msg.get('code')} — {msg.get('msg')}")

        elif msg_type == "subscription_status":
            status = msg.get("status")
            channels = msg.get("channels", [])
            logger.info(f"Subscription {status}: {channels}")

        else:
            # Log unknown types at debug level
            logger.debug(f"Unknown message type: {msg_type}")

    async def close(self):
        """Graceful shutdown."""
        self._running = False
        if self._ws:
            try:
                await self._ws.close()
                logger.info("WebSocket closed")
            except Exception:
                pass


# ── Monitor Integration ──────────────────────────────────────────────

async def price_guard_handler(ws_client: KalshiWebSocket, guard, exit_event):
    """
    Example monitor integration handler.
    Checks prices against guardrails on every ticker update.
    """
    positions = ["KXUSAIRANAGREEMENT-27-26JUN", "KXUSAIRANAGREEMENT-27-26JUL"]

    async def check_price(data):
        ticker = data.get("ticker")
        if ticker not in positions:
            return

        price = data["data"]
        last = price.get("last_price")
        if last is None:
            return

        last_cents = int(float(last) * 100)

        # Log significant price moves
        logger.info(f"  📊 {ticker}: {last}")

    ws_client.bus._handlers.setdefault("ticker", []).append(check_price)


# ── Main ─────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Kalshi WebSocket Listener")
    parser.add_argument("--demo", action="store_true", help="Use demo environment")
    parser.add_argument("--markets", type=str, help="Comma-separated tickers to track")
    parser.add_argument("--log-file", type=str, default="logs/kalshi/ws-events.jsonl",
                        help="JSONL log path for monitor integration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    if args.log_file:
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)

    ws = KalshiWebSocket(
        demo=args.demo,
        log_path=args.log_file,
    )

    # Graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(ws.close()))
        except NotImplementedError:
            # Signal handlers not supported on all platforms
            pass

    # Subscribe to specific markets if requested
    if args.markets:
        target_markets = [m.strip() for m in args.markets.split(",") if m.strip()]
        ws._subscribed_markets = set(target_markets)

    try:
        await ws.listen()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        await ws.close()

    logger.info("Listener stopped")


if __name__ == "__main__":
    asyncio.run(main())
