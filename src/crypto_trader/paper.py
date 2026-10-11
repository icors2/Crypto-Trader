from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from crypto_trader.models import Order, OrderStatus, Quote, Side
from crypto_trader.money import D, fee_amount, money, qty
from crypto_trader.timeutil import now_utc

_ASSET_RE = re.compile(r"^[A-Z0-9]{1,12}$")


@dataclass
class PaperAccount:
    """Persisted paper ledger: cash, reset baseline, and asset holdings."""

    name: str = "Paper"
    cash: Decimal = Decimal("10000")
    starting_cash: Decimal = Decimal("10000")
    holdings: dict[str, Decimal] = field(default_factory=dict)

    def equity(self, marks: dict[str, Decimal] | None = None) -> Decimal:
        total = D(self.cash)
        marks = marks or {}
        for asset, holding in self.holdings.items():
            mark = marks.get(asset)
            if mark is not None:
                total += D(holding) * D(mark)
        return money(total)

    def set_name(self, name: str) -> None:
        cleaned = name.strip()
        if not cleaned or len(cleaned) > 64:
            raise ValueError("account name must be 1–64 characters")
        self.name = cleaned

    def set_cash(self, amount: Any) -> None:
        cash = D(amount)
        if cash < 0:
            raise ValueError("cash cannot be negative")
        self.cash = cash

    def set_starting_cash(self, amount: Any) -> None:
        cash = D(amount)
        if cash <= 0:
            raise ValueError("starting cash must be positive")
        self.starting_cash = cash

    def deposit(self, amount: Any) -> None:
        amt = D(amount)
        if amt <= 0:
            raise ValueError("deposit must be positive")
        self.cash += amt

    def withdraw(self, amount: Any) -> None:
        amt = D(amount)
        if amt <= 0:
            raise ValueError("withdraw must be positive")
        if amt > self.cash:
            raise ValueError("insufficient paper cash")
        self.cash -= amt

    def set_holding(self, asset: str, quantity: Any) -> None:
        ticker = normalize_asset(asset)
        holding = qty(quantity)
        if holding < 0:
            raise ValueError("holding qty cannot be negative")
        if holding == 0:
            self.holdings.pop(ticker, None)
        else:
            self.holdings[ticker] = holding

    def reset_ledger(self) -> None:
        self.cash = D(self.starting_cash)
        self.holdings = {}


def normalize_asset(asset: str) -> str:
    ticker = asset.strip().upper().split("-")[0]
    if not _ASSET_RE.match(ticker):
        raise ValueError("asset must be a short ticker like BTC")
    return ticker


def paper_view(account: PaperAccount, quote: Quote | None = None) -> dict[str, Any]:
    marks: dict[str, Decimal] = {}
    if quote is not None:
        marks[normalize_asset(quote.symbol)] = quote.mid
    return {
        "name": account.name,
        "cash": account.cash,
        "starting_cash": account.starting_cash,
        "holdings": sorted(account.holdings.items()),
        "equity": account.equity(marks),
        "marks": marks,
    }


class PaperBroker:
    """Simulated fills at bid/ask plus a separate fee (v2 quotes exclude the fee)."""

    def __init__(self, fee_bps: int, slippage_bps: int = 5) -> None:
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.orders: dict[str, Order] = {}
        self.holdings: dict[str, Decimal] = {}
        self.cash = Decimal("10000")
        self.name = "Paper"
        self.starting_cash = Decimal("10000")
        self.fail_next = False
        self.partial_fill_ratio: Decimal | None = None

    def load_account(self, account: PaperAccount) -> None:
        self.name = account.name
        self.cash = D(account.cash)
        self.starting_cash = D(account.starting_cash)
        self.holdings = {asset: D(qty_held) for asset, qty_held in account.holdings.items() if D(qty_held) != 0}

    def to_account(self) -> PaperAccount:
        return PaperAccount(
            name=self.name,
            cash=D(self.cash),
            starting_cash=D(self.starting_cash),
            holdings={asset: D(qty_held) for asset, qty_held in self.holdings.items() if D(qty_held) != 0},
        )

    def apply_account(self, account: PaperAccount) -> None:
        self.load_account(account)

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
