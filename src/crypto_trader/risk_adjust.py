from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from crypto_trader.config import RISK_LEVELS, BotConfig
from crypto_trader.money import D, money

NAMED_PROFILES = ("conservative", "balanced", "aggressive")


@dataclass(frozen=True)
class RiskProfile:
    name: str
    cost_multiple: Decimal
    spread_max_bps: int
    notional_scale: Decimal
    cooldown_bars: int
    summary: str


PROFILES: dict[str, RiskProfile] = {
    "conservative": RiskProfile(
        name="conservative",
        cost_multiple=Decimal("2.0"),
        spread_max_bps=20,
        notional_scale=Decimal("0.50"),
        cooldown_bars=4,
        summary="Keep the default cost gate. Half size. Longer cooldown after stops.",
    ),
    "balanced": RiskProfile(
        name="balanced",
        cost_multiple=Decimal("0.25"),
        spread_max_bps=40,
        notional_scale=Decimal("0.75"),
        cooldown_bars=2,
        summary="Loosen the 5m cost gate so a typical ATR can clear fees. 75% size.",
    ),
    "aggressive": RiskProfile(
        name="aggressive",
        cost_multiple=Decimal("0.08"),
        spread_max_bps=80,
        notional_scale=Decimal("1.00"),
        cooldown_bars=1,
        summary="Allow entries when the target is a fraction of round-trip cost. Full size.",
    ),
}


@dataclass(frozen=True)
class RiskAdjustSnapshot:
    configured_level: str
    effective_level: str
    idle_minutes: float
    last_entry_at: datetime | None
    cost_multiple: Decimal
    spread_max_bps: int
    max_notional_usd: Decimal
    cooldown_bars: int
    note: str

    def as_public_dict(self) -> dict[str, str | float | int | None]:
        return {
            "configured_level": self.configured_level,
            "effective_level": self.effective_level,
            "idle_minutes": round(self.idle_minutes, 1),
            "last_entry_at": self.last_entry_at.isoformat() if self.last_entry_at else None,
            "cost_multiple": str(self.cost_multiple),
            "spread_max_bps": self.spread_max_bps,
            "max_notional_usd": str(self.max_notional_usd),
            "cooldown_bars": self.cooldown_bars,
            "note": self.note,
        }


def skip_prefix(reason: str | None) -> str:
    if not reason:
        return "unknown"
    return reason.split(":", 1)[0]


def idle_minutes(
    now: datetime,
    *,
    last_entry_at: datetime | None,
    session_opened_at: datetime | None,
    session_open: bool,
) -> float:
    if not session_open:
        return 0.0
    anchor = last_entry_at or session_opened_at
    if anchor is None:
        return 0.0
    if last_entry_at is not None and session_opened_at is not None and last_entry_at < session_opened_at:
        anchor = session_opened_at
    return max(0.0, (now - anchor).total_seconds() / 60.0)


def overlay(cfg: BotConfig, profile: RiskProfile) -> BotConfig:
    scaled = money(D(cfg.max_notional_usd) * profile.notional_scale)
    if scaled <= 0 or scaled > D(cfg.max_notional_usd):
        scaled = D(cfg.max_notional_usd)
    return replace(
        cfg,
        cost_multiple=profile.cost_multiple,
        spread_max_bps=profile.spread_max_bps,
        max_notional_usd=scaled,
        cooldown_bars=profile.cooldown_bars,
    )


def choose_auto_level(
    *,
    idle: float,
    loosen_after_min: int,
    daily_pnl: Decimal,
    daily_limit: Decimal,
) -> tuple[str, str]:
    limit = D(daily_limit)
    if limit > 0 and daily_pnl <= -(limit * Decimal("0.40")):
        return "conservative", "auto tightened: daily loss is at least 40% of the daily cap"
    wait = max(5, int(loosen_after_min))
    if idle >= wait:
        return "aggressive", f"auto loosened: no entries for {idle:.0f} min"
    return "balanced", f"auto holding balanced ({idle:.0f}/{wait} min without an entry)"


def apply_risk_level(
    cfg: BotConfig,
    *,
    now: datetime,
    last_entry_at: datetime | None = None,
    session_opened_at: datetime | None = None,
    session_open: bool = True,
    daily_pnl: Decimal = Decimal("0"),
) -> tuple[BotConfig, RiskAdjustSnapshot]:
    configured = (cfg.risk_level or "auto").strip().lower()
    if configured not in RISK_LEVELS:
        configured = "auto"
    idle = idle_minutes(
        now,
        last_entry_at=last_entry_at,
        session_opened_at=session_opened_at,
        session_open=session_open,
    )
    if configured == "manual":
        effective = "manual"
        note = "manual: using YAML cost_multiple, spread, notional, and cooldown"
        eff = cfg
    elif configured in NAMED_PROFILES:
        effective = configured
        note = PROFILES[effective].summary
        eff = overlay(cfg, PROFILES[effective])
    else:
        effective, note = choose_auto_level(
            idle=idle,
            loosen_after_min=cfg.auto_loosen_after_min,
            daily_pnl=daily_pnl,
            daily_limit=cfg.daily_loss_limit_usd,
        )
        if not session_open:
            note = "auto idle: session closed, entries blocked"
        eff = overlay(cfg, PROFILES[effective])
    snap = RiskAdjustSnapshot(
        configured_level=configured,
        effective_level=effective,
        idle_minutes=idle,
        last_entry_at=last_entry_at,
        cost_multiple=eff.cost_multiple,
        spread_max_bps=eff.spread_max_bps,
        max_notional_usd=eff.max_notional_usd,
        cooldown_bars=eff.cooldown_bars,
        note=note,
    )
    return eff, snap
