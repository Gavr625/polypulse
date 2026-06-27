from polypulse.orderbook import OrderBook


def _snap(book: OrderBook) -> None:
    book.apply_snapshot(
        bids=[{"price": "0.40", "size": "100"}, {"price": "0.39", "size": "50"}],
        asks=[{"price": "0.42", "size": "80"}, {"price": "0.45", "size": "20"}],
        ts=1000.0,
    )


def test_snapshot_sets_best_bid_and_ask():
    b = OrderBook()
    _snap(b)
    assert b.best_bid() == 0.40
    assert b.best_ask() == 0.42


def test_mid_and_spread():
    b = OrderBook()
    _snap(b)
    assert b.mid() == 0.41
    assert round(b.spread(), 10) == 0.02


def test_empty_book_returns_none():
    b = OrderBook()
    assert b.best_bid() is None
    assert b.best_ask() is None
    assert b.mid() is None
    assert b.spread() is None


def test_apply_change_updates_level():
    b = OrderBook()
    _snap(b)
    b.apply_change(side="BUY", price="0.41", size=10.0, ts=1001.0)
    assert b.best_bid() == 0.41


def test_apply_change_zero_size_removes_level():
    b = OrderBook()
    _snap(b)
    b.apply_change(side="BUY", price="0.40", size=0.0, ts=1002.0)
    assert b.best_bid() == 0.39  # top bid removed, next remains


def test_sorted_levels():
    b = OrderBook()
    _snap(b)
    assert b.bid_levels() == [(0.40, 100.0), (0.39, 50.0)]
    assert b.ask_levels() == [(0.42, 80.0), (0.45, 20.0)]


def test_snapshot_is_independent_copy():
    b = OrderBook()
    _snap(b)
    copy = b.snapshot()
    b.apply_change(side="SELL", price="0.42", size=0.0, ts=1003.0)
    assert copy.best_ask() == 0.42      # copy unaffected
    assert b.best_ask() == 0.45         # original changed


def test_source_and_ts_tracked():
    b = OrderBook()
    b.apply_snapshot(bids=[{"price": "0.5", "size": "1"}], asks=[], ts=1234.0, source="rest")
    assert b.ts == 1234.0
    assert b.source == "rest"


def test_apply_change_unknown_side_is_ignored():
    b = OrderBook()
    _snap(b)
    b.apply_change(side="WAT", price="0.43", size=10.0, ts=1004.0)
    assert b.best_ask() == 0.42  # unchanged; not corrupted into asks


def test_non_numeric_price_does_not_freeze_book():
    b = OrderBook()
    _snap(b)
    b.apply_change(side="BUY", price="oops", size=5.0, ts=1005.0)  # must not poison
    assert b.best_bid() == 0.40
    b.apply_change(side="BUY", price="0.41", size=5.0, ts=1006.0)  # subsequent update still works
    assert b.best_bid() == 0.41


def test_snapshot_skips_non_numeric_price():
    b = OrderBook()
    b.apply_snapshot(
        bids=[{"price": "bad", "size": "1"}, {"price": "0.30", "size": "2"}],
        asks=[],
        ts=2000.0,
    )
    assert b.best_bid() == 0.30  # bad level dropped, good level kept
