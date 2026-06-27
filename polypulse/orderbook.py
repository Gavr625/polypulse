"""Pure in-memory order-book model. No IO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrderBook:
    """One market's order book. Prices are kept as strings (exchange-native),
    sizes as floats. Best bid/ask are cached on mutation for O(1) reads."""

    bids: dict[str, float] = field(default_factory=dict)
    asks: dict[str, float] = field(default_factory=dict)
    ts: float = 0.0
    source: str = "ws"  # "ws" | "rest"
    _best_bid: float | None = field(default=None, init=False, repr=False)
    _best_ask: float | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._recompute()

    def apply_snapshot(
        self,
        bids: list[dict[str, Any]] | None,
        asks: list[dict[str, Any]] | None,
        ts: float,
        source: str = "ws",
    ) -> None:
        self.bids = {
            lvl["price"]: float(lvl["size"]) for lvl in (bids or []) if float(lvl["size"]) > 0
        }
        self.asks = {
            lvl["price"]: float(lvl["size"]) for lvl in (asks or []) if float(lvl["size"]) > 0
        }
        self.ts = ts
        self.source = source
        self._recompute()

    def apply_change(
        self, side: str, price: str, size: float, ts: float, source: str = "ws"
    ) -> None:
        book = self.bids if side == "BUY" else self.asks
        if size <= 0:
            book.pop(price, None)
        else:
            book[price] = size
        self.ts = ts
        self.source = source
        self._recompute()

    def _recompute(self) -> None:
        self._best_bid = max((float(p) for p in self.bids), default=None)
        self._best_ask = min((float(p) for p in self.asks), default=None)

    def best_bid(self) -> float | None:
        return self._best_bid

    def best_ask(self) -> float | None:
        return self._best_ask

    def mid(self) -> float | None:
        if self._best_bid is None or self._best_ask is None:
            return None
        return round((self._best_bid + self._best_ask) / 2, 10)

    def spread(self) -> float | None:
        if self._best_bid is None or self._best_ask is None:
            return None
        return self._best_ask - self._best_bid

    def bid_levels(self) -> list[tuple[float, float]]:
        return sorted(((float(p), s) for p, s in self.bids.items()), reverse=True)

    def ask_levels(self) -> list[tuple[float, float]]:
        return sorted((float(p), s) for p, s in self.asks.items())

    def snapshot(self) -> OrderBook:
        return OrderBook(bids=dict(self.bids), asks=dict(self.asks), ts=self.ts, source=self.source)
