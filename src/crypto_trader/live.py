from __future__ import annotations

import uuid
from decimal import Decimal

from crypto_trader.adapters.robinhood import RobinhoodClient
from crypto_trader.models import Order, Quote, Side


class LiveBroker:
    """Robinhood v2 execution. Bot-managed stops only — no exchange stop_loss backstop."""

    def __init__(self, client: RobinhoodClient) -> None:
        self.client = client

    def get_quote(self, symbol: str, fallback: Quote) -> Quote:
        return self.client.get_best_bid_ask(symbol)

    def place_order(self, side: Side, symbol: str, qty: Decimal, quote: Quote) -> Order:
        client_id = str(uuid.uuid4())
        return self.client.place_order(
            client_order_id=client_id,
            side=side.value,
            symbol=symbol,
            asset_quantity=str(qty),
        )

    def get_order(self, client_order_id: str) -> Order | None:
        return self.client.find_order_by_client_id(client_order_id)
