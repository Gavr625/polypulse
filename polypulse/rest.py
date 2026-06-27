"""Tiny stdlib REST helper for Polymarket CLOB /book (fallback + benchmark)."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

REST_BOOK = "https://clob.polymarket.com/book?token_id="


def fetch_book(token_id: str, timeout: float = 10.0) -> dict[str, Any]:
    """Blocking GET of the order book for one token. Returns the parsed JSON
    (keys include ``bids`` and ``asks``, each a list of ``{"price","size"}``)."""
    req = urllib.request.Request(
        REST_BOOK + token_id,
        headers={"User-Agent": "polypulse"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted host)
        data: dict[str, Any] = json.load(resp)
    return data
