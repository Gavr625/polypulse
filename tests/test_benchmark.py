from polypulse.benchmark import pick_active_market


def test_pick_active_market_selects_event_with_enough_tokens():
    events = [
        {"slug": "temperature-in-nyc", "markets": [
            {"clobTokenIds": '["A1","B1"]'},
            {"clobTokenIds": '["A2","B2"]'},
            {"clobTokenIds": '["A3","B3"]'},
            {"clobTokenIds": '["A4","B4"]'},
        ]},
    ]
    picked = pick_active_market(events, min_tokens=4)
    assert picked is not None
    slug, tokens = picked
    assert slug == "temperature-in-nyc"
    assert tokens == ["A1", "A2", "A3", "A4"]


def test_pick_active_market_skips_closed_markets():
    events = [
        {"slug": "x", "markets": [{"closed": True, "clobTokenIds": '["A1","B1"]'}]},
    ]
    assert pick_active_market(events, min_tokens=1) is None


def test_pick_active_market_accepts_clobtokenids_as_list():
    events = [{"slug": "y", "markets": [{"clobTokenIds": ["A1", "B1"]}]}]
    assert pick_active_market(events, min_tokens=1) == ("y", ["A1"])


def test_pick_active_market_skips_inactive_markets():
    events = [{"slug": "z", "markets": [{"active": False, "clobTokenIds": '["A1","B1"]'}]}]
    assert pick_active_market(events, min_tokens=1) is None
