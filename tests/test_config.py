from __future__ import annotations

from decimal import Decimal

import pytest

from crypto_trader.config import BotConfig, ConfigError, load_config, save_config, validate_config


def test_ui_cannot_raise_hard_ceiling(env_settings):
    cfg = BotConfig(max_notional_usd=Decimal("500"))
    capped = validate_config(cfg, env_settings)
    assert capped.max_notional_usd == Decimal("100")


def test_fast_ema_must_be_below_slow(env_settings):
    cfg = BotConfig(ema_fast=21, ema_slow=9)
    with pytest.raises(ConfigError):
        validate_config(cfg, env_settings)


def test_yaml_roundtrip_keeps_comment_file(env_settings):
    path = env_settings.config_path
    original = path.read_text(encoding="utf-8")
    assert "calibrate" in original
    save_config(path, {"fee_bps": 85}, env_settings)
    text = path.read_text(encoding="utf-8")
    assert "calibrate" in text
    loaded = load_config(path, env_settings)
    assert loaded.fee_bps == 85
