from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from crypto_trader.config import BotConfig
from crypto_trader.risk_adjust import PROFILES, apply_risk_level, overlay, skip_prefix


def test_manual_leaves_yaml_knobs():
    cfg = BotConfig(risk_level="manual", cost_multiple=Decimal("2.0"), spread_max_bps=25)
    now = datetime(2026, 3, 9, 15, 0, tzinfo=UTC)
    eff, snap = apply_risk_level(cfg, now=now, session_open=True)
    assert snap.effective_level == "manual"
    assert eff.cost_multiple == Decimal("2.0")
    assert eff.spread_max_bps == 25
    assert eff.max_notional_usd == cfg.max_notional_usd


def test_named_profile_scales_notional_down_only():
    cfg = BotConfig(risk_level="conservative", max_notional_usd=Decimal("100"))
    now = datetime(2026, 3, 9, 15, 0, tzinfo=UTC)
    eff, snap = apply_risk_level(cfg, now=now)
    assert snap.effective_level == "conservative"
    assert eff.cost_multiple == PROFILES["conservative"].cost_multiple
    assert eff.max_notional_usd == Decimal("50.00")
    assert eff.max_notional_usd <= cfg.max_notional_usd


def test_auto_starts_balanced_then_loosens():
    cfg = BotConfig(risk_level="auto", auto_loosen_after_min=60)
    opened = datetime(2026, 3, 9, 14, 0, tzinfo=UTC)
    early = opened + timedelta(minutes=10)
    eff, snap = apply_risk_level(
        cfg, now=early, session_opened_at=opened, session_open=True, daily_pnl=Decimal("0")
    )
    assert snap.effective_level == "balanced"
    assert eff.cost_multiple == PROFILES["balanced"].cost_multiple

    late = opened + timedelta(minutes=90)
    _eff2, snap2 = apply_risk_level(
        cfg, now=late, session_opened_at=opened, session_open=True, daily_pnl=Decimal("0")
    )
    assert snap2.effective_level == "aggressive"
    assert "loosened" in snap2.note


def test_auto_tightens_on_daily_loss():
    cfg = BotConfig(risk_level="auto", daily_loss_limit_usd=Decimal("50"), auto_loosen_after_min=60)
    opened = datetime(2026, 3, 9, 14, 0, tzinfo=UTC)
    now = opened + timedelta(minutes=90)
    _eff, snap = apply_risk_level(
        cfg,
        now=now,
        session_opened_at=opened,
        session_open=True,
        daily_pnl=Decimal("-21"),
    )
    assert snap.effective_level == "conservative"
    assert "tightened" in snap.note


def test_yesterday_entry_does_not_count_as_idle():
    cfg = BotConfig(risk_level="auto", auto_loosen_after_min=60)
    opened = datetime(2026, 3, 9, 13, 0, tzinfo=UTC)
    yesterday = datetime(2026, 3, 8, 18, 0, tzinfo=UTC)
    now = opened + timedelta(minutes=10)
    _eff, snap = apply_risk_level(
        cfg,
        now=now,
        last_entry_at=yesterday,
        session_opened_at=opened,
        session_open=True,
    )
    assert snap.idle_minutes < 15
    assert snap.effective_level == "balanced"


def test_overlay_never_raises_notional():
    cfg = BotConfig(max_notional_usd=Decimal("100"))
    hot = PROFILES["aggressive"]
    assert hot.notional_scale == Decimal("1.00")
    eff = overlay(cfg, hot)
    assert eff.max_notional_usd <= cfg.max_notional_usd


def test_skip_prefix_strips_detail():
    assert skip_prefix("cost_unaware: target 1 < need 2") == "cost_unaware"
    assert skip_prefix(None) == "unknown"
