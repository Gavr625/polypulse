import polypulse.markets as markets
from polypulse.markets import Market, list_markets, tokens_for_slug


def _fake_events():
    return [
        {
            "slug": "event-1",
            "title": "Event One",
            "endDate": "2026-07-01T00:00:00Z",
            "markets": [
                {
                    "slug": "m-open-str",
                    "question": "Q open str?",
                    "conditionId": "0xcond1",
                    "clobTokenIds": '["tokA", "tokB"]',
                    "outcomes": '["Yes", "No"]',
                    "volume24hr": "123.5",
                },
                {
                    "slug": "m-open-list",
                    "question": "Q open list?",
                    "conditionId": "0xcond2",
                    "clobTokenIds": ["tokC", "tokD"],
                    "outcomes": ["Up", "Down"],
                },
                {
                    "slug": "m-closed",
                    "question": "Q closed?",
                    "conditionId": "0xcond3",
                    "clobTokenIds": ["tokE", "tokF"],
                    "closed": True,
                },
                {
                    "slug": "m-inactive",
                    "question": "Q inactive?",
                    "conditionId": "0xcond4",
                    "clobTokenIds": ["tokG"],
                    "active": False,
                },
                {
                    "slug": "m-notokens",
                    "question": "Q none?",
                    "conditionId": "0xcond5",
                },
            ],
        },
    ]


def test_list_markets_parses_open_markets(monkeypatch):
    monkeypatch.setattr(markets, "get_json", lambda url, timeout=20.0: _fake_events())
    mkts = list_markets(tag="weather")
    assert {m.slug for m in mkts} == {"m-open-str", "m-open-list"}
    by_slug = {m.slug: m for m in mkts}
    assert by_slug["m-open-str"].token_ids == ["tokA", "tokB"]   # JSON-string parsed
    assert by_slug["m-open-list"].token_ids == ["tokC", "tokD"]  # list parsed
    assert by_slug["m-open-str"].outcomes == ["Yes", "No"]
    assert by_slug["m-open-str"].condition_id == "0xcond1"
    assert by_slug["m-open-str"].question == "Q open str?"
    assert by_slug["m-open-str"].volume_24h == 123.5
    assert isinstance(by_slug["m-open-list"], Market)


def test_list_markets_includes_closed_when_requested(monkeypatch):
    monkeypatch.setattr(markets, "get_json", lambda url, timeout=20.0: _fake_events())
    slugs = {m.slug for m in list_markets(closed=True)}
    assert "m-closed" in slugs and "m-inactive" in slugs


def test_list_markets_builds_url(monkeypatch):
    seen = {}

    def fake(url, timeout=20.0):
        seen["url"] = url
        return []

    monkeypatch.setattr(markets, "get_json", fake)
    list_markets(tag="weather", limit=5)
    assert "tag_slug=weather" in seen["url"]
    assert "limit=5" in seen["url"]


def test_tokens_for_slug(monkeypatch):
    monkeypatch.setattr(markets, "get_json", lambda url, timeout=20.0: _fake_events())
    mkts = list_markets()
    assert tokens_for_slug(mkts, "m-open-list") == ["tokC", "tokD"]
    assert tokens_for_slug(mkts, "nope") == []
