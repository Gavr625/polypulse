# Changelog

## 0.1.0 (unreleased)
- Initial release: `BookFeed` real-time Polymarket order book over WebSocket.
- Heartbeat, PONG-aware watchdog, exponential-backoff reconnect, REST fallback.
- `OrderBook` model with best bid/ask, mid, spread, depth.
- CLI: `polypulse benchmark`, `polypulse watch`.
