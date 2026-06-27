# polypulse

[![PyPI](https://img.shields.io/pypi/v/polypulse.svg)](https://pypi.org/project/polypulse/)
[![CI](https://github.com/Gavr625/polypulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Gavr625/polypulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Real-time pulse of Polymarket — an order book feed that never freezes.**

`polypulse` keeps a live, in-memory Polymarket order book over WebSocket, so reading
the best bid/ask is instant — with no per-read network round-trip. REST `/book` polling
pays its latency on **every** read (≈185 ms from a typical host, ≈19 ms warm when
colocated); `polypulse` pays a one-time subscribe, then updates are pushed.
It adds the production reliability the official tooling lacks: heartbeat, a
PONG-aware watchdog that detects the silent WS freeze ([issue #292](https://github.com/Polymarket/py-clob-client/issues/292)),
exponential-backoff reconnect, and an optional REST fallback.

## Install

```bash
pip install polypulse
```

## Quickstart

```python
import asyncio
from polypulse import BookFeed

async def main():
    feed = BookFeed(["<token_id>"])
    asyncio.create_task(feed.run())   # connects, reconnects, self-heals
    await asyncio.sleep(2)
    print(feed.best_bid("<token_id>"), feed.mid("<token_id>"))  # 0 ms, in-memory
    feed.stop()

asyncio.run(main())
```

## Why

REST `/book` polling pays per-read latency and serves a book that is ~1 s stale.
Polymarket's WebSocket can also **silently freeze** — the connection stays open but
events stop. `polypulse` pushes updates as the book changes (no per-read latency) and
guarantees liveness with a watchdog that reconnects the moment the socket goes quiet.

## API

`BookFeed(token_ids, on_update=None, *, ping_interval=10, watchdog_timeout=30, rest_fallback=True, max_backoff=30, rest_poll_interval=1.0, logger=None)`

- `best_bid / best_ask / mid / spread (token_id)` — sync, no network
- `book(token_id)` — full-depth `OrderBook` snapshot
- `staleness(token_id)`, `source(token_id)` — freshness introspection
- `await run()` / `stop()`

### Behavior notes

- **Reads are synchronous and never hit the network** — they return whatever the
  background `run()` task has most recently applied.
- **`source(token_id)`** is `"ws"` when the latest update came from the live socket,
  or `"rest"` when it came from the REST fallback (used only while the WS is down).
  `staleness(token_id)` is seconds since that token last updated.
- **`on_update` fires on WebSocket events only.** While the socket is down, the REST
  fallback keeps the book fresh for readers (`best_bid` etc.) but does not invoke the
  callback; on reconnect you get a fresh `book` snapshot (which does fire it).
- **`stop()`** signals shutdown and closes the active connection so `run()` returns
  promptly.

## Benchmark

```bash
python -m polypulse benchmark
```

It picks a live market and compares REST `/book` time-to-first-byte against the
WebSocket feed. Example run (from a non-colocated host — your absolute numbers depend
on where you run it):

```
market: highest-temperature-in-karachi-on-june-29-2026  (11 tokens)
REST /book TTFB: median 184.5ms  min 124.4  max 238.3  (n=8)
WS subscribe → first book: 220.6ms
WS updates in 30s: 130 (4.3/s)

=== verdict ===
REST pays ~185ms EVERY read; WS pays 221ms ONCE, then updates are PUSHED (no per-read latency).
```

Absolute latency drops sharply when colocated (a eu-west-2 host measured ~19 ms warm
REST GETs), but the structural win holds everywhere: REST pays its round-trip on every
read; the WS feed pays once.

## Watch a live book

```bash
polypulse watch <token_id>
```

Prints top-of-book once a second — a quick sanity check that the feed is live:

```
3414098972...  bid=0.012  ask=0.024  mid=0.018  src=ws
3414098972...  bid=0.012  ask=0.024  mid=0.018  src=ws
```

Values tick as the market moves; `src` shows `ws` or `rest` (REST fallback). An
animated GIF reads even better here — record one to drop in.

## Honest note

`polypulse` was extracted from a live Polymarket trading bot. The trading edge didn't
pan out, but the low-latency feed is solid and battle-tested — so here it is. Out of
scope (for now): generic multi-CLOB support, book integrity hashing, indicators.

## License

MIT.
