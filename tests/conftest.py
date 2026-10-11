from __future__ import annotations

import os
import shutil

os.environ.setdefault("START_LOOP", "0")
os.environ.setdefault("UI_PASSWORD", "secret")
os.environ.setdefault("UI_SESSION_SECRET", "test-secret-key")

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_trader.config import BotConfig
from crypto_trader.models import Bar
from crypto_trader.settings import EnvSettings


@pytest.fixture
def env_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> EnvSettings:
    cfg_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    cfg_dir.mkdir()
    data_dir.mkdir()
    src = Path("config/config.yaml")
    shutil.copy(src, cfg_dir / "config.yaml")
    monkeypatch.setenv("CONFIG_DIR", str(cfg_dir))
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("UI_PASSWORD", "secret")
    monkeypatch.setenv("UI_SESSION_SECRET", "test-secret-key")
    monkeypatch.setenv("MAX_NOTIONAL_USD", "100")
    monkeypatch.setenv("BIND_HOST", "127.0.0.1")
    return EnvSettings()


@pytest.fixture
def cfg() -> BotConfig:
    return BotConfig()


def make_bars(n: int, start: float = 100.0, step: float = 0.2) -> list[Bar]:
    bars: list[Bar] = []
    ts = datetime(2026, 3, 9, 14, 0, tzinfo=UTC)
    price = Decimal(str(start))
    for i in range(n):
        nxt = price + Decimal(str(step))
        high = max(price, nxt) + Decimal("0.4")
        low = min(price, nxt) - Decimal("0.4")
        bars.append(
            Bar(
                ts=ts + timedelta(minutes=5 * i),
                open=price,
                high=high,
                low=low,
                close=nxt,
                volume=Decimal("10"),
            )
        )
        price = nxt
    return bars
