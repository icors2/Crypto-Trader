from __future__ import annotations

import uuid
from decimal import Decimal

from crypto_trader.models import Order, OrderStatus, Quote, Side
from crypto_trader.money import D, fee_amount
from crypto_trader.timeutil import now_utc


class PaperBroker:
    """Simulated fills at bid/ask plus a separate fee (v2 quotes exclude the fee)."""

    def __init__(self, fee_bps: int, slippage_bps: int = 5) -> None:
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.orders: dict[str, Order] = {}
        self.holdings: dict[str, Decimal] = {}
        self.cash = Decimal("10000")
        self.fail_next = False
        self.partial_fill_ratio: Decimal | None = None

    def get_quote(self, symbol: str, fallback: Quote) -> Quote:
        return fallback

    def place_order(self, side: Side, symbol: str, qty: Decimal, quote: Quote) -> Order:
        client_id = str(uuid.uuid4())
        order = Order(
            client_order_id=client_id,
            symbol=symbol,
            side=side,
            qty=qty,
            status=OrderStatus.PENDING,
            submitted_at=now_utc(),
        )
        self.orders[client_id] = order
        if self.fail_next:
            self.fail_next = False
            return order
        fill_qty = qty
        if self.partial_fill_ratio is not None:
            fill_qty = qty * self.partial_fill_ratio
            self.partial_fill_ratio = None
        price = quote.ask if side is Side.BUY else quote.bid
        from crypto_trader.fills import paper_buy_fill, paper_sell_fill

        fill_price = paper_buy_fill(price, self.slippage_bps) if side is Side.BUY else paper_sell_fill(price, self.slippage_bps)
        fee = fee_amount(fill_price * fill_qty, self.fee_bps)
        order.filled_qty = fill_qty
        order.average_price = fill_price
        order.fee_charged = fee
        order.status = OrderStatus.FILLED if fill_qty == qty else OrderStatus.PARTIALLY_FILLED
        asset = symbol.split("-")[0]
        if side is Side.BUY:
            self.cash -= fill_price * fill_qty + fee
            self.holdings[asset] = self.holdings.get(asset, Decimal("0")) + fill_qty
        else:
            self.cash += fill_price * fill_qty - fee
            self.holdings[asset] = self.holdings.get(asset, Decimal("0")) - fill_qty
        return order

    def get_order(self, client_order_id: str) -> Order | None:
        return self.orders.get(client_order_id)

    def confirm(self, client_order_id: str, quote: Quote) -> Order:
        order = self.orders[client_order_id]
        if order.status is not OrderStatus.PENDING:
            return order
        return self.place_order(order.side, order.symbol, order.qty, quote)

    def holding_qty(self, symbol: str) -> Decimal:
        asset = symbol.split("-")[0]
        return D(self.holdings.get(asset, Decimal("0")))
