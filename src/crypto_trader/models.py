from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Mode(StrEnum):
    PAPER = "paper"
    LIVE = "live"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    DUST = "dust"


class HaltReason(StrEnum):
    NONE = "none"
    STOP_FILE = "stop_file"
    SESSION = "session"
    DAILY_LOSS = "daily_loss"
    WEEKLY_LOSS = "weekly_loss"
    CUMULATIVE_LOSS = "cumulative_loss"
    STALE_QUOTE = "stale_quote"
    MANUAL = "manual"
    PAUSED = "paused"


class ExitReason(StrEnum):
    STOP = "stop"
    TARGET = "target"
    MAX_HOLD = "max_hold"
    FLATTEN = "flatten"
    MANUAL = "manual"


@dataclass(frozen=True)
class Bar:
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")


@dataclass(frozen=True)
class Quote:
    ts: datetime
    symbol: str
    bid: Decimal
    ask: Decimal
    source: str = "unknown"

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid


@dataclass
class Order:
    client_order_id: str
    symbol: str
    side: Side
    qty: Decimal
    status: OrderStatus = OrderStatus.PENDING
    broker_order_id: str | None = None
    filled_qty: Decimal = Decimal("0")
    average_price: Decimal | None = None
    fee_charged: Decimal = Decimal("0")
    submitted_at: datetime | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class Position:
    id: int | None
    symbol: str
    qty: Decimal
    entry_price: Decimal
    stop: Decimal
    target: Decimal
    opened_at: datetime
    entry_fee: Decimal
    cost_basis: Decimal
    status: PositionStatus = PositionStatus.OPEN
    client_order_id: str | None = None


@dataclass
class Trade:
    id: int | None
    opened_at: datetime
    closed_at: datetime
    symbol: str
    side: str
    qty: Decimal
    entry_price: Decimal
    exit_price: Decimal
    entry_fee: Decimal
    exit_fee: Decimal
    pnl: Decimal
    cost_basis: Decimal
    reason: str
    mode: str


@dataclass(frozen=True)
class Indicators:
    ema_fast: Decimal
    ema_slow: Decimal
    atr: Decimal
    prev_ema_fast: Decimal
    prev_ema_slow: Decimal
    htf_ema: Decimal | None = None
    htf_close: Decimal | None = None


@dataclass(frozen=True)
class Signal:
    enter_long: bool
    skip_reason: str | None = None
