"""Latency benchmark: WebSocket push vs REST /book TTFB on a live market."""

from __future__ import annotations

import asyncio
import json
import statistics
import time
from typing import Any

import websockets

from .feed import WS_URL
from .rest import fetch_book, get_json

GAMMA = (
    "https://gamma-api.polymarket.com/events"
    "?tag_slug=weather&limit=80&order=createdAt&ascending=false"
)
GAMMA_FALLBACK = (
    "https://gamma-api.polymarket.com/events"
    "?limit=80&order=createdAt&ascending=false"
)


def pick_active_market(
    events: list[dict[str, Any]], min_tokens: int = 4
) -> tuple[str, list[str]] | None:
    """From Gamma events, return (slug, [first token per market]) for the first
    event exposing at least ``min_tokens`` open markets."""
    for ev in events:
        slug = ev.get("slug", "")
        tokens: list[str] = []
        for m in ev.get("markets", []):
            if m.get("closed") or m.get("active") is False:
                continue
            cti = m.get("clobTokenIds")
            if isinstance(cti, str):
                try:
                    cti = json.loads(cti)
                except Exception:
                    continue
            if cti:
                tokens.append(str(cti[0]))
        if len(tokens) >= min_tokens:
            return slug, tokens
    return None


async def run_benchmark() -> None:
    print("=== Polymarket CLOB: WebSocket push vs REST poll latency ===\n")
    picked = pick_active_market(get_json(GAMMA))
    if not picked:
        picked = pick_active_market(get_json(GAMMA_FALLBACK))
    if not picked:
        print("no active market found")
        return
    slug, tokens = picked
    one = tokens[0]
    print(f"market: {slug}  ({len(tokens)} tokens)\n")

    rest_ms: list[float] = []
    for _ in range(8):
        t0 = time.time()
        try:
            fetch_book(one)
            rest_ms.append((time.time() - t0) * 1000)
        except Exception as exc:
            print(f"  REST err: {exc}")
        await asyncio.sleep(0.3)
    if rest_ms:
        print(f"REST /book TTFB: median {statistics.median(rest_ms):.1f}ms  "
              f"min {min(rest_ms):.1f}  max {max(rest_ms):.1f}  (n={len(rest_ms)})")

    first_book_ms: float | None = None
    update_count = 0
    async with websockets.connect(WS_URL, ping_interval=None, open_timeout=10) as ws:
        sub_msg = json.dumps(
            {"assets_ids": tokens, "type": "market", "custom_feature_enabled": True}
        )
        await ws.send(sub_msg)
        t_sub = time.time()
        deadline = t_sub + 30
        while time.time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, deadline - time.time()))
            except asyncio.TimeoutError:
                break
            if raw == "PONG":
                continue
            data = json.loads(raw)
            for ev in (data if isinstance(data, list) else [data]):
                et = ev.get("event_type")
                if et == "book" and first_book_ms is None:
                    first_book_ms = (time.time() - t_sub) * 1000
                if et in ("book", "price_change"):
                    update_count += 1

    elapsed = time.time() - t_sub
    if first_book_ms is not None:
        print(f"\nWS subscribe → first book: {first_book_ms:.1f}ms")
    rate = update_count / elapsed if elapsed > 0 else 0.0
    print(f"WS updates in {elapsed:.0f}s: {update_count} ({rate:.1f}/s)")
    if rest_ms and first_book_ms is not None:
        print("\n=== verdict ===")
        print(f"REST pays ~{statistics.median(rest_ms):.0f}ms EVERY read; "
              f"WS pays {first_book_ms:.0f}ms ONCE, then updates are PUSHED (no per-read latency).")
