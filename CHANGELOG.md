# Changelog

## 0.1.0 — 2026-06-27
- Initial release: `BookFeed` real-time Polymarket order book over WebSocket.
- Heartbeat, PONG-aware watchdog, exponential-backoff reconnect, REST fallback.
- `OrderBook` model with best bid/ask, mid, spread, depth.
- Market discovery: `list_markets` / `tokens_for_slug`.
- CLI: `polypulse benchmark`, `polypulse watch`, `polypulse markets`.
