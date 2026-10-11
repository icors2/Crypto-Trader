from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from nacl.signing import SigningKey

from crypto_trader.backoff import jittered_backoff
from crypto_trader.clock import skew_warning
from crypto_trader.models import Order, OrderStatus, Quote, Side
from crypto_trader.money import D
from crypto_trader.timeutil import now_utc

BASE_URL = "https://trading.robinhood.com"


class RobinhoodError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _status(value: str | None) -> OrderStatus:
    mapping = {
        "open": OrderStatus.OPEN,
        "canceled": OrderStatus.CANCELED,
        "partially_filled": OrderStatus.PARTIALLY_FILLED,
        "filled": OrderStatus.FILLED,
        "failed": OrderStatus.FAILED,
    }
    if not value:
        return OrderStatus.UNKNOWN
    return mapping.get(value, OrderStatus.UNKNOWN)


class RobinhoodClient:
    """Official Crypto Trading API v2. No unofficial SDKs."""

    def __init__(
        self,
        api_key: str,
        private_key_b64: str,
        account_number: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        seed = base64.b64decode(private_key_b64)
        self.private_key = SigningKey(seed)
        self.account_number = account_number
        self.client = client or httpx.Client(timeout=15.0)
        self.last_date_header: str | None = None

    def _sign(self, method: str, path: str, body: str, timestamp: str) -> dict[str, str]:
        message = f"{self.api_key}{timestamp}{path}{method}{body}"
        signed = self.private_key.sign(message.encode("utf-8"))
        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signed.signature).decode("utf-8"),
            "x-timestamp": timestamp,
        }

    def request(self, method: str, path: str, body: dict | None = None) -> Any:
        payload = json.dumps(body) if body else ""
        timestamp = str(int(time.time()))
        headers = self._sign(method, path, payload, timestamp)
        url = BASE_URL + path
        last_error: Exception | None = None
        for attempt in range(5):
            try:
                if method == "GET":
                    resp = self.client.get(url, headers=headers, timeout=15.0)
                else:
                    resp = self.client.post(
                        url,
                        headers=headers,
                        json=body if body else None,
                        timeout=15.0,
                    )
                self.last_date_header = resp.headers.get("Date")
                if resp.status_code == 429:
                    delay = jittered_backoff(attempt)
                    time.sleep(delay.total_seconds())
                    timestamp = str(int(time.time()))
                    headers = self._sign(method, path, payload, timestamp)
                    last_error = RobinhoodError("429", 429)
                    continue
                if resp.status_code >= 400:
                    try:
                        data = resp.json()
                    except json.JSONDecodeError:
                        data = {"error": resp.text}
                    raise RobinhoodError(
                        f"HTTP {resp.status_code}",
                        status_code=resp.status_code,
                        payload=data,
                    )
                return resp.json()
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(jittered_backoff(attempt).total_seconds())
        raise RobinhoodError(f"request failed: {last_error}")

    def get_accounts(self) -> Any:
        return self.request("GET", "/api/v2/crypto/trading/accounts/")

    def get_holdings(self, account_number: str | None = None, *asset_codes: str) -> Any:
        acct = account_number or self.account_number
        params: dict[str, Any] = {"account_number": acct}
        query = urlencode(params)
        if asset_codes:
            extra = "&".join(f"asset_code={c}" for c in asset_codes)
            query = f"{query}&{extra}"
        return self.request("GET", f"/api/v2/crypto/trading/holdings/?{query}")

    def get_best_bid_ask(self, symbol: str) -> Quote:
        path = f"/api/v2/crypto/marketdata/best_bid_ask/?symbol={symbol}"
        data = self.request("GET", path)
        results = data.get("results") or data
        row = results[0] if isinstance(results, list) else results
        return Quote(
            ts=now_utc(),
            symbol=symbol,
            bid=D(row["bid"]),
            ask=D(row["ask"]),
            source="robinhood",
        )

    def get_estimated_price(self, symbol: str, side: str, quantity: str) -> Any:
        path = (
            f"/api/v2/crypto/trading/estimated_price/"
            f"?symbol={symbol}&side={side}&quantity={quantity}"
        )
        return self.request("GET", path)

    def place_order(
        self,
        client_order_id: str,
        side: str,
        symbol: str,
        asset_quantity: str,
        account_number: str | None = None,
        order_type: str = "market",
    ) -> Order:
        acct = account_number or self.account_number
        if not acct:
            raise RobinhoodError("account_number required for v2 orders")
        body = {
            "client_order_id": client_order_id,
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": {"asset_quantity": asset_quantity},
        }
        path = f"/api/v2/crypto/trading/orders/?account_number={acct}"
        data = self.request("POST", path, body)
        return self._order_from_api(data, symbol=symbol, side=side, qty=asset_quantity)

    def get_order(self, order_id: str, account_number: str | None = None) -> Any:
        acct = account_number or self.account_number
        path = f"/api/v2/crypto/trading/orders/{order_id}/?account_number={acct}"
        return self.request("GET", path)

    def get_orders(self, account_number: str | None = None, created_at_start: str | None = None) -> Any:
        acct = account_number or self.account_number
        start = created_at_start or "2020-01-01T00:00:00Z"
        path = f"/api/v2/crypto/trading/orders/?account_number={acct}&created_at_start={start}"
        return self.request("GET", path)

    def find_order_by_client_id(self, client_order_id: str) -> Order | None:
        data = self.get_orders()
        results = data.get("results") if isinstance(data, dict) else data
        if not results:
            return None
        for row in results:
            if row.get("client_order_id") == client_order_id:
                return self._order_from_api(row)
        return None

    def startup_clock_warning(self) -> str | None:
        try:
            self.get_accounts()
        except RobinhoodError:
            return None
        return skew_warning(self.last_date_header)

    @staticmethod
    def _order_from_api(data: dict, symbol: str | None = None, side: str | None = None, qty: str | None = None) -> Order:
        filled = data.get("filled_asset_quantity") or "0"
        avg = data.get("average_price")
        fee = data.get("fee_charged") or "0"
        return Order(
            client_order_id=data.get("client_order_id") or "",
            broker_order_id=data.get("id"),
            symbol=data.get("symbol") or symbol or "",
            side=Side(data.get("side") or side or "buy"),
            qty=D(data.get("market_order_config", {}).get("asset_quantity") or qty or "0"),
            filled_qty=D(filled),
            average_price=D(avg) if avg else None,
            fee_charged=D(fee),
            status=_status(data.get("state")),
            submitted_at=now_utc(),
            raw=data,
        )
