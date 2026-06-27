import io
import json

import polypulse.rest as rest


def test_fetch_book_builds_url_and_parses(monkeypatch):
    captured = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        payload = {"bids": [{"price": "0.4", "size": "1"}], "asks": []}
        return FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(rest.urllib.request, "urlopen", fake_urlopen)

    data = rest.fetch_book("TOKEN123", timeout=5.0)
    assert data["bids"][0]["price"] == "0.4"
    assert captured["url"].endswith("token_id=TOKEN123")
    assert captured["timeout"] == 5.0


def test_fetch_book_url_encodes_token_id(monkeypatch):
    captured = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        payload = {"bids": [], "asks": []}
        return FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(rest.urllib.request, "urlopen", fake_urlopen)

    rest.fetch_book("a b&c")
    assert captured["url"].endswith("token_id=a%20b%26c")


def test_get_json_parses(monkeypatch):
    captured = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        return FakeResp(json.dumps({"hello": "world"}).encode())

    monkeypatch.setattr(rest.urllib.request, "urlopen", fake_urlopen)

    data = rest.get_json("https://example.com/x", timeout=7.0)
    assert data == {"hello": "world"}
    assert captured["url"] == "https://example.com/x"
    assert captured["timeout"] == 7.0
