from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import httpx

from crypto_trader.clock import skew_warning
from crypto_trader.models import Bar, Quote
from crypto_trader.money import D

COINBASE_EXCHANGE = "https://api.exchange.coinbase.com"


class CoinbaseError(RuntimeError):
    pass


class CoinbaseFeed:
    """Public Coinbase Exchange candles — used for indicators in paper and live."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=15.0)
        self.last_date_header: str | None = None

    def get_candles(self, symbol: str, granularity: int, limit: int = 300) -> list[Bar]:
        resp = self.client.get(
            f"{COINBASE_EXCHANGE}/products/{symbol}/candles",
            params={"granularity": granularity},
            headers={"User-Agent": "crypto-trader/0.1"},
        )
        self.last_date_header = resp.headers.get("Date")
        if resp.status_code == 429:
            raise CoinbaseError("429")
        resp.raise_for_status()
        rows = resp.json()
        bars = [
            Bar(
                ts=datetime.fromtimestamp(int(row[0]), tz=UTC),
                low=D(row[1]),
                high=D(row[2]),
                open=D(row[3]),
                close=D(row[4]),
                volume=D(row[5]),
            )
            for row in rows
        ]
        bars.sort(key=lambda b: b.ts)
        return bars[-limit:]

    def get_ticker(self, symbol: str) -> Quote:
        resp = self.client.get(
            f"{COINBASE_EXCHANGE}/products/{symbol}/ticker",
            headers={"User-Agent": "crypto-trader/0.1"},
        )
        self.last_date_header = resp.headers.get("Date")
        if resp.status_code == 429:
            raise CoinbaseError("429")
        resp.raise_for_status()
        data = resp.json()
        bid = D(data.get("bid") or data["price"])
        ask = D(data.get("ask") or data["price"])
        ts = datetime.now(tz=UTC)
        return Quote(ts=ts, symbol=symbol, bid=bid, ask=ask, source="coinbase")

    def startup_clock_warning(self) -> str | None:
        try:
            resp = self.client.get(
                f"{COINBASE_EXCHANGE}/time",
                headers={"User-Agent": "crypto-trader/0.1"},
            )
            self.last_date_header = resp.headers.get("Date")
        except httpx.HTTPError:
            return None
        return skew_warning(self.last_date_header)


def synthetic_quote(symbol: str, last: Decimal, half_spread_bps: int = 5) -> Quote:
    from datetime import UTC, datetime

    from crypto_trader.money import apply_bps

    mid = last
    bid = apply_bps(mid, half_spread_bps, adverse=False)
    ask = apply_bps(mid, half_spread_bps, adverse=True)
    return Quote(ts=datetime.now(tz=UTC), symbol=symbol, bid=bid, ask=ask, source="synthetic")
