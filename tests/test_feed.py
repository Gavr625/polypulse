import asyncio
import json
import time
import types

import polypulse.feed as feed_mod
from polypulse.feed import BookFeed
from polypulse.orderbook import OrderBook
from tests.conftest import FakeConnect, FakeWS


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


def test_sync_callback_is_called():
    seen = []
    feed = BookFeed(["T1"], on_update=lambda tid, ev: seen.append((tid, ev["event_type"])))
    feed._handle(_book_msg("T1"))
    assert seen == [("T1", "book")]


def test_sync_callback_exception_does_not_propagate():
    def boom(tid, ev):
        raise ValueError("boom")
    feed = BookFeed(["T1"], on_update=boom)
    feed._handle(_book_msg("T1"))  # must not raise
    assert feed.best_bid("T1") == 0.40  # book still updated


def test_async_callback_is_awaited():
    seen = []

    async def cb(tid, ev):
        await asyncio.sleep(0)
        seen.append(tid)

    async def run():
        feed = BookFeed(["T1"], on_update=cb)
        feed._handle(_book_msg("T1"))
        await asyncio.sleep(0.01)  # let the scheduled task run
        return seen

    assert asyncio.run(run()) == ["T1"]


def test_async_callback_exception_does_not_propagate():
    async def boom(tid, ev):
        raise ValueError("boom")

    async def run():
        feed = BookFeed(["T1"], on_update=boom)
        feed._handle(_book_msg("T1"))      # schedules the async callback
        await asyncio.sleep(0.01)          # let it run and raise (caught in _await_cb)
        return feed.best_bid("T1")

    assert asyncio.run(run()) == 0.40      # book updated, exception did not propagate


def test_run_subscribes_and_applies_then_reconnects(monkeypatch):
    # First connection yields one book frame then ends; second connection is
    # used to assert resubscription, after which we stop the feed.
    ws1 = FakeWS([_book_msg("T1")])
    ws2 = FakeWS([])
    conns = [ws1, ws2]
    made = []

    feed = BookFeed(["T1"], rest_fallback=False, max_backoff=0.01)

    def fake_connect(*a, **k):
        ws = conns.pop(0)
        made.append(ws)
        if not conns:           # on the 2nd connection, stop after it drains
            feed.stop()
        return FakeConnect(ws)

    monkeypatch.setattr(feed_mod, "websockets", types.SimpleNamespace(connect=fake_connect))

    asyncio.run(asyncio.wait_for(feed.run(), timeout=2.0))

    assert feed.best_bid("T1") == 0.40                       # frame applied
    assert json.loads(ws1.sent[0])["assets_ids"] == ["T1"]  # subscribed
    assert json.loads(ws2.sent[0])["assets_ids"] == ["T1"]  # resubscribed after reconnect
    assert len(made) == 2


def test_heartbeat_sends_ping():
    feed = BookFeed(["T1"], ping_interval=0.01)
    ws = FakeWS([])

    async def run():
        task = asyncio.create_task(feed._heartbeat(ws))
        await asyncio.sleep(0.1)
        task.cancel()

    asyncio.run(run())
    assert "PING" in ws.sent


def test_watchdog_closes_when_silent():
    feed = BookFeed(["T1"], watchdog_timeout=0.02)
    ws = FakeWS([])
    feed._last_frame_ts = time.time() - 10.0  # already stale

    asyncio.run(asyncio.wait_for(feed._watchdog(ws), timeout=1.0))
    assert ws.closed is True


def test_watchdog_stays_alive_while_frames_arrive():
    feed = BookFeed(["T1"], watchdog_timeout=0.5)
    ws = FakeWS([])

    async def run():
        feed._last_frame_ts = time.time()
        wd = asyncio.create_task(feed._watchdog(ws))
        for _ in range(5):
            await asyncio.sleep(0.05)
            feed._last_frame_ts = time.time()  # simulate PONG/data keeping it alive
        alive = not wd.done()
        wd.cancel()
        return alive

    assert asyncio.run(run()) is True
    assert ws.closed is False


def test_stop_closes_live_connection(monkeypatch):
    # A continuously-streaming connection (PONG frames keep it live but are skipped).
    ws = FakeWS(["PONG"] * 5000)
    feed = BookFeed(["T1"], rest_fallback=False)
    monkeypatch.setattr(
        feed_mod, "websockets",
        types.SimpleNamespace(connect=lambda *a, **k: FakeConnect(ws)),
    )

    async def run():
        task = asyncio.create_task(feed.run())
        await asyncio.sleep(0.02)            # let it connect and start streaming
        feed.stop()                          # must close the live ws → loop ends promptly
        await asyncio.wait_for(task, timeout=1.0)
        return ws.closed

    assert asyncio.run(run()) is True
