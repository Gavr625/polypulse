import json

from polypulse.feed import BookFeed
from polypulse.orderbook import OrderBook


def _book_msg(token: str) -> str:
    return json.dumps({
        "event_type": "book",
        "asset_id": token,
        "bids": [{"price": "0.40", "size": "100"}],
        "asks": [{"price": "0.42", "size": "80"}],
    })


def test_handle_book_populates_accessors():
    feed = BookFeed(["T1"])
    feed._handle(_book_msg("T1"))
    assert feed.best_bid("T1") == 0.40
    assert feed.best_ask("T1") == 0.42
    assert feed.mid("T1") == 0.41
    assert round(feed.spread("T1"), 10) == 0.02
    assert isinstance(feed.book("T1"), OrderBook)
    assert feed.source("T1") == "ws"


def test_handle_price_change_updates_book():
    feed = BookFeed(["T1"])
    feed._handle(_book_msg("T1"))
    feed._handle(json.dumps({
        "event_type": "price_change",
        "price_changes": [{"asset_id": "T1", "price": "0.41", "size": "5", "side": "BUY"}],
    }))
    assert feed.best_bid("T1") == 0.41


def test_price_change_before_snapshot_is_ignored():
    feed = BookFeed(["T1"])
    feed._handle(json.dumps({
        "event_type": "price_change",
        "price_changes": [{"asset_id": "T1", "price": "0.41", "size": "5", "side": "BUY"}],
    }))
    assert feed.book("T1") is None


def test_handle_accepts_list_of_events():
    feed = BookFeed(["T1", "T2"])
    feed._handle(json.dumps([_book_dict("T1"), _book_dict("T2")]))
    assert feed.best_bid("T1") == 0.40
    assert feed.best_bid("T2") == 0.40


def test_bad_frame_is_ignored():
    feed = BookFeed(["T1"])
    feed._handle("not json")  # must not raise
    assert feed.book("T1") is None


def test_unknown_token_returns_none():
    feed = BookFeed(["T1"])
    assert feed.best_bid("NOPE") is None
    assert feed.staleness("NOPE") is None
    assert feed.source("NOPE") is None


def test_handle_price_change_sell_side_updates_ask():
    feed = BookFeed(["T1"])
    feed._handle(_book_msg("T1"))
    assert feed.best_ask("T1") == 0.42
    feed._handle(json.dumps({
        "event_type": "price_change",
        "price_changes": [{"asset_id": "T1", "price": "0.41", "size": "5", "side": "SELL"}],
    }))
    assert feed.best_ask("T1") == 0.41


def test_handle_malformed_size_does_not_raise():
    feed = BookFeed(["T1"])
    feed._handle(_book_msg("T1"))
    feed._handle(json.dumps({
        "event_type": "price_change",
        "price_changes": [{"asset_id": "T1", "price": "0.41", "size": "", "side": "BUY"}],
    }))  # must not raise
    assert feed.best_bid("T1") == 0.40
    assert feed.best_ask("T1") == 0.42


def test_staleness_is_nonnegative_after_update():
    feed = BookFeed(["T1"])
    feed._handle(_book_msg("T1"))
    staleness = feed.staleness("T1")
    assert isinstance(staleness, float)
    assert staleness >= 0


def _book_dict(token: str) -> dict:
    return {
        "event_type": "book",
        "asset_id": token,
        "bids": [{"price": "0.40", "size": "100"}],
        "asks": [{"price": "0.42", "size": "80"}],
    }
