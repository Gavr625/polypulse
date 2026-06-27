# Launch checklist — polypulse

## Pre-flight (must all be true before announcing)
- [ ] `pip install polypulse` works from a clean venv
- [ ] README hook shows REAL benchmark numbers from `python -m polypulse benchmark`
- [ ] A short GIF/asciinema of `polypulse watch <token>` is embedded in the README
- [ ] CI is green on 3.10/3.11/3.12
- [ ] Published to PyPI (version 0.1.0)
- [ ] GitHub repo description + topics set:
      polymarket, prediction-markets, orderbook, websocket, clob, low-latency, asyncio, trading, python

## Announce (in order of signal)
- [ ] Polymarket Discord — builders/dev channel
- [ ] X/Twitter thread (draft below)
- [ ] Show HN (draft below) — post a weekday morning US time
- [ ] Reddit: r/algotrading, r/Polymarket, r/Python (show-and-tell)
- [ ] PRs to awesome lists: awesome-quant, awesome-asyncio, awesome-polymarket (if it exists)

## After
- [ ] Respond to every issue/PR within ~24h for the first 2 weeks
- [ ] Pin 1-2 "good first issue"s
- [ ] Optional: dev.to/Medium write-up of the latency findings, linked from README

---

## Show HN draft
**Title:** Show HN: polypulse - a never-freezing real-time order book for Polymarket

I built this for a Polymarket trading bot. The trading edge didn't survive contact
with reality, but the infrastructure did: a low-latency in-memory order book over
WebSocket that reconnects itself when Polymarket's socket silently freezes (a real,
documented failure mode). Reads are 0 ms (in-memory) vs ~19-80 ms per REST poll.
MIT, pip-installable, tested. Happy to answer questions about the latency work.

## X/Twitter thread draft
1/ I open-sourced polypulse - a real-time Polymarket order book that never freezes.
   pip install polypulse. Here's why it exists.
2/ Reading the book via REST /book costs ~19-80 ms per call and is ~1 s stale.
   Over WebSocket you get pushes ~sub-2 ms from the matching engine.
3/ But Polymarket's WS can silently freeze - open connection, no events. polypulse
   ships a PONG-aware watchdog + auto-reconnect + REST fallback so the book stays live.
4/ Built it for a trading bot; the edge didn't pan out, the infra did. Take it.
   MIT, typed, tested, CI. Star it: github.com/Gavr625/polypulse
