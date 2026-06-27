"""Market discovery via the Polymarket Gamma API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from .rest import get_json

GAMMA_EVENTS = "https://gamma-api.polymarket.com/events"


@dataclass
class Market:
    slug: str
    question: str
    condition_id: str
    token_ids: list[str]
    outcomes: list[str]
    end_date: str | None = None
    volume_24h: float | None = None


def _as_list(value: Any) -> list[Any]:
    """Gamma sometimes returns list-ish fields as JSON-encoded strings."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return []
    return value if isinstance(value, list) else []


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def list_markets(
    tag: str | None = None,
    *,
    closed: bool = False,
    limit: int = 100,
    timeout: float = 20.0,
) -> list[Market]:
    """Fetch markets from the Polymarket Gamma events API.

    Args:
        tag: optional Gamma ``tag_slug`` filter (e.g. ``"weather"``).
        closed: include closed/inactive markets too (default: only open).
        limit: max events to request.

    Returns a flat list of :class:`Market`. Markets without parseable token ids are
    skipped. Raises ``urllib.error.URLError`` on network failure.
    """
    url = f"{GAMMA_EVENTS}?limit={int(limit)}&order=createdAt&ascending=false"
    if tag:
        url += f"&tag_slug={quote(tag, safe='')}"
    events = get_json(url, timeout=timeout)
    out: list[Market] = []
    for ev in events if isinstance(events, list) else []:
        if not isinstance(ev, dict):
            continue
        ev_slug = str(ev.get("slug", ""))
        for m in ev.get("markets") or []:
            if not isinstance(m, dict):
                continue
            if not closed and (m.get("closed") or m.get("active") is False):
                continue
            token_ids = [str(t) for t in _as_list(m.get("clobTokenIds"))]
            if not token_ids:
                continue
            ed = m.get("endDate") or ev.get("endDate")
            out.append(
                Market(
                    slug=str(m.get("slug") or ev_slug),
                    question=str(m.get("question") or ev.get("title") or ""),
                    condition_id=str(m.get("conditionId") or ""),
                    token_ids=token_ids,
                    outcomes=[str(o) for o in _as_list(m.get("outcomes"))],
                    end_date=str(ed) if ed is not None else None,
                    volume_24h=_to_float(m.get("volume24hr")),
                )
            )
    return out


def tokens_for_slug(markets: list[Market], slug: str) -> list[str]:
    """Return the token ids of the first market whose slug equals ``slug`` (else [])."""
    for m in markets:
        if m.slug == slug:
            return list(m.token_ids)
    return []
