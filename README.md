# polypulse

[![PyPI](https://img.shields.io/pypi/v/polypulse.svg)](https://pypi.org/project/polypulse/)
[![CI](https://github.com/gavriil/polypulse/actions/workflows/ci.yml/badge.svg)](https://github.com/gavriil/polypulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Real-time pulse of Polymarket — an order book feed that never freezes.**

`polypulse` keeps a live, in-memory Polymarket order book over WebSocket, so reading
the best bid/ask is instant instead of paying ~19–80 ms on every REST `/book` poll.
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
events stop. `polypulse` pushes updates (~sub-2 ms from the matching engine) and
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

Prints REST `/book` TTFB vs WebSocket time-to-first-book and update cadence on a live
market — the empirical case for the WS feed. Replace the figures above with your own
run's output.

## Honest note

`polypulse` was extracted from a live Polymarket trading bot. The trading edge didn't
pan out, but the low-latency feed is solid and battle-tested — so here it is. Out of
scope (for now): generic multi-CLOB support, book integrity hashing, indicators.

## License

MIT.
