from __future__ import annotations

from crypto_trader.adapters.robinhood import RobinhoodClient
from crypto_trader.backoff import jittered_backoff


class _Resp:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self.headers = {"Date": "Mon, 09 Mar 2026 15:00:00 GMT"}
        self._payload = payload or {"results": []}
        self.text = ""

    def json(self):
        return self._payload


class _Client:
    def __init__(self):
        self.calls = 0

    def get(self, url, headers=None, timeout=None):
        self.calls += 1
        if self.calls < 3:
            return _Resp(429)
        return _Resp(200, {"results": [{"account_number": "x"}]})

    def post(self, *args, **kwargs):
        raise AssertionError("no post")


def test_jittered_backoff_is_bounded():
    delay = jittered_backoff(3, base=0.5, cap=2.0)
    assert 0 <= delay.total_seconds() <= 2.0


def test_429_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("crypto_trader.adapters.robinhood.time.sleep", lambda _s: None)
    import base64

    from nacl.signing import SigningKey

    key = SigningKey.generate()
    priv = base64.b64encode(key.encode()).decode()
    http = _Client()
    client = RobinhoodClient("rh-api-test", priv, "acct", client=http)
    data = client.get_accounts()
    assert http.calls >= 3
    assert data["results"][0]["account_number"] == "x"
    assert client.last_date_header
