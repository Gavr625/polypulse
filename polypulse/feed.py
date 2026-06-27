"""Real-time Polymarket order-book feed over WebSocket."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from collections.abc import Callable
from typing import Any

import websockets

from .orderbook import OrderBook

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

UpdateCallback = Callable[[str, dict[str, Any]], Any]


class BookFeed:
    """Maintains a live in-memory order book for a fixed set of token ids.

    Reads (:meth:`best_bid`, :meth:`mid`, …) are synchronous and never touch
    the network. Call :meth:`run` (a coroutine) to keep the book fresh.
    """

    def __init__(
        self,
        token_ids: list[str],
        on_update: UpdateCallback | None = None,
        *,
        ping_interval: float = 10.0,
        watchdog_timeout: float = 30.0,
        rest_fallback: bool = True,
        max_backoff: float = 30.0,
        rest_poll_interval: float = 1.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.token_ids = [str(t) for t in token_ids]
        self.on_update = on_update
        self.ping_interval = ping_interval
        self.watchdog_timeout = watchdog_timeout
        self.rest_fallback = rest_fallback
        self.max_backoff = max_backoff
        self.rest_poll_interval = rest_poll_interval
        self.logger = logger or logging.getLogger("polypulse")

        self.books: dict[str, OrderBook] = {}
        self._stop = False
        self._connected = False
        self._last_frame_ts = 0.0
        self._pending: set[asyncio.Task[Any]] = set()

    # ----- reads (sync, no network) -----

    def _ob(self, token_id: str) -> OrderBook | None:
        return self.books.get(str(token_id))

    def best_bid(self, token_id: str) -> float | None:
        ob = self._ob(token_id)
        return ob.best_bid() if ob else None

    def best_ask(self, token_id: str) -> float | None:
        ob = self._ob(token_id)
        return ob.best_ask() if ob else None

    def mid(self, token_id: str) -> float | None:
        ob = self._ob(token_id)
        return ob.mid() if ob else None

    def spread(self, token_id: str) -> float | None:
        ob = self._ob(token_id)
        return ob.spread() if ob else None

    def book(self, token_id: str) -> OrderBook | None:
        ob = self._ob(token_id)
        return ob.snapshot() if ob else None

    def staleness(self, token_id: str) -> float | None:
        ob = self._ob(token_id)
        return (time.time() - ob.ts) if ob else None

    def source(self, token_id: str) -> str | None:
        ob = self._ob(token_id)
        return ob.source if ob else None

    # ----- event handling -----

    def _handle(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            self.logger.debug("polypulse: dropped unparseable frame")
            return
        events = data if isinstance(data, list) else [data]
        now = time.time()
        for ev in events:
            if not isinstance(ev, dict):
                continue
            try:
                et = ev.get("event_type")
                if et == "book":
                    aid = ev.get("asset_id")
                    if not aid:
                        continue
                    ob = self.books.get(aid)
                    if ob is None:
                        ob = OrderBook()
                    ob.apply_snapshot(ev.get("bids"), ev.get("asks"), now, "ws")
                    self.books[aid] = ob
                    self._fire(aid, ev)
                elif et == "price_change":
                    for pc in ev.get("price_changes") or []:
                        aid = pc.get("asset_id")
                        ob = self.books.get(aid) if aid else None
                        if ob is None:
                            continue
                        ob.apply_change(
                            pc.get("side", ""), pc.get("price", ""),
                            float(pc.get("size", 0)), now, "ws",
                        )
                        self._fire(aid, ev)
                else:
                    aid = ev.get("asset_id")
                    if aid:
                        self._fire(aid, ev)
            except (ValueError, TypeError, KeyError):
                self.logger.debug("polypulse: dropped malformed event")
                continue

    def _fire(self, token_id: str, event: dict[str, Any]) -> None:
        if self.on_update is None:
            return
        try:
            result = self.on_update(token_id, event)
        except Exception:
            self.logger.exception("polypulse: on_update callback raised")
            return
        if inspect.isawaitable(result):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop (sync caller): run to completion in a fresh loop.
                try:
                    asyncio.run(self._await_cb(result))
                except Exception:
                    self.logger.exception("polypulse: async on_update callback raised")
                return
            task = loop.create_task(self._await_cb(result))
            self._pending.add(task)
            task.add_done_callback(self._pending.discard)

    async def _await_cb(self, awaitable: Any) -> None:
        try:
            await awaitable
        except Exception:
            self.logger.exception("polypulse: async on_update callback raised")

    # ----- connection loop -----

    def stop(self) -> None:
        self._stop = True

    def _subscribe_msg(self) -> str:
        return json.dumps({
            "assets_ids": self.token_ids,
            "type": "market",
            "custom_feature_enabled": True,
        })

    async def run(self) -> None:
        """Maintain the connection forever (until :meth:`stop`), reconnecting
        with exponential backoff and resubscribing each time."""
        backoff = 0.5
        while not self._stop:
            try:
                async with websockets.connect(
                    WS_URL, ping_interval=None, open_timeout=10, close_timeout=5
                ) as ws:
                    await ws.send(self._subscribe_msg())
                    self._connected = True
                    self._last_frame_ts = time.time()
                    backoff = 0.5
                    try:
                        async for raw in ws:
                            self._last_frame_ts = time.time()
                            msg = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
                            if msg == "PONG":
                                continue
                            self._handle(msg)
                    finally:
                        self._connected = False
            except Exception as exc:
                self.logger.debug("polypulse: ws error, will reconnect: %s", exc)
            if self._stop:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self.max_backoff)
