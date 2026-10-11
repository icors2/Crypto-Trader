from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from crypto_trader.config import BotConfig
from crypto_trader.models import HaltReason, Position, Quote
from crypto_trader.money import D, money
from crypto_trader.timeutil import chicago_day_key, chicago_week_key


@dataclass
class RiskState:
    daily_pnl: Decimal = Decimal("0")
    weekly_pnl: Decimal = Decimal("0")
    cumulative_pnl: Decimal = Decimal("0")
    day_key: str = ""
    week_key: str = ""
    manual_resume_required: bool = False
    halt_reason: HaltReason = HaltReason.NONE
    paused: bool = False
    resume_weekly_floor: Decimal | None = None
    resume_cumulative_floor: Decimal | None = None


@dataclass
class RiskEngine:
    cfg: BotConfig
    state: RiskState = field(default_factory=RiskState)

    def mark_day(self, now) -> None:
        day = chicago_day_key(now, self.cfg.timezone)
        week = chicago_week_key(now, self.cfg.timezone)
        if self.state.day_key and self.state.day_key != day:
            self.state.daily_pnl = Decimal("0")
            if self.state.halt_reason == HaltReason.DAILY_LOSS:
                self.state.halt_reason = HaltReason.NONE
                self.state.paused = False
        if self.state.week_key and self.state.week_key != week:
            self.state.weekly_pnl = Decimal("0")
            self.state.resume_weekly_floor = None
        self.state.day_key = day
        self.state.week_key = week

    def record_realized(self, pnl: Decimal) -> None:
        self.state.daily_pnl += pnl
        self.state.weekly_pnl += pnl
        self.state.cumulative_pnl += pnl

    def unrealized(self, position: Position | None, quote: Quote | None) -> Decimal:
        if position is None or quote is None:
            return Decimal("0")
        return money((quote.bid - position.entry_price) * position.qty - position.entry_fee)

    def check(
        self,
        now,
        position: Position | None = None,
        quote: Quote | None = None,
        *,
        stop_file: bool = False,
        session_open: bool = True,
    ) -> HaltReason:
        self.mark_day(now)
        if stop_file:
            self.state.paused = True
            self.state.halt_reason = HaltReason.STOP_FILE
            return HaltReason.STOP_FILE
        if self.state.manual_resume_required:
            self.state.paused = True
            return self.state.halt_reason
        if not session_open:
            self.state.halt_reason = HaltReason.SESSION
            return HaltReason.SESSION

        unreal = self.unrealized(position, quote)
        daily = self.state.daily_pnl + unreal
        weekly = self.state.weekly_pnl + unreal
        cumulative = self.state.cumulative_pnl + unreal

        if self._breached(cumulative, self.cfg.cumulative_loss_limit_usd, self.state.resume_cumulative_floor):
            self.state.manual_resume_required = True
            self.state.paused = True
            self.state.halt_reason = HaltReason.CUMULATIVE_LOSS
            return HaltReason.CUMULATIVE_LOSS
        if self._breached(weekly, self.cfg.weekly_loss_limit_usd, self.state.resume_weekly_floor):
            self.state.manual_resume_required = True
            self.state.paused = True
            self.state.halt_reason = HaltReason.WEEKLY_LOSS
            return HaltReason.WEEKLY_LOSS
        if daily <= -D(self.cfg.daily_loss_limit_usd):
            self.state.paused = True
            self.state.halt_reason = HaltReason.DAILY_LOSS
            return HaltReason.DAILY_LOSS

        if self.state.halt_reason == HaltReason.SESSION:
            self.state.halt_reason = HaltReason.NONE
        if self.state.halt_reason == HaltReason.DAILY_LOSS and daily > -D(
            self.cfg.daily_loss_limit_usd
        ):
            self.state.halt_reason = HaltReason.NONE
            self.state.paused = False
        return HaltReason.NONE

    def manual_resume(self) -> None:
        self.state.manual_resume_required = False
        self.state.paused = False
        self.state.halt_reason = HaltReason.NONE
        self.state.resume_weekly_floor = self.state.weekly_pnl
        self.state.resume_cumulative_floor = self.state.cumulative_pnl

    def reset_daily(self) -> None:
        self.state.daily_pnl = Decimal("0")
        if self.state.halt_reason == HaltReason.DAILY_LOSS:
            self.state.halt_reason = HaltReason.NONE
            self.state.paused = False

    def reset_risk_counters(self) -> None:
        self.state.daily_pnl = Decimal("0")
        self.state.weekly_pnl = Decimal("0")
        self.state.cumulative_pnl = Decimal("0")
        self.state.resume_weekly_floor = None
        self.state.resume_cumulative_floor = None
        self.manual_resume()

    @staticmethod
    def _breached(pnl: Decimal, limit: Decimal, floor: Decimal | None) -> bool:
        if pnl > -D(limit):
            return False
        if floor is None:
            return True
        return pnl < floor

    def size_qty(self, price: Decimal) -> Decimal:
        if price <= 0:
            return Decimal("0")
        return (D(self.cfg.max_notional_usd) / price).quantize(Decimal("0.00000001"))
