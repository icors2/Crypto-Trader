from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from crypto_trader.money import D


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    max_notional_usd: Decimal = Field(default=Decimal("100"))
    max_daily_loss_usd: Decimal = Field(default=Decimal("50"))
    max_weekly_loss_usd: Decimal = Field(default=Decimal("150"))
    max_cumulative_loss_usd: Decimal = Field(default=Decimal("300"))
    min_poll_interval_sec: int = Field(default=5)
    max_open_positions: int = Field(default=10)

    ui_password_hash: str | None = None
    ui_password: str | None = None
    ui_session_secret: str = "change-me-in-production"
    secure_cookies: bool = False
    bind_host: str = "127.0.0.1"
    port: int = 8000

    data_dir: Path = Path("data")
    config_dir: Path = Path("config")

    robinhood_api_key: str | None = None
    robinhood_private_key: str | None = None
    robinhood_account_number: str | None = None

    ntfy_topic: str | None = None
    ntfy_url: str = "https://ntfy.sh"

    def cap_notional(self, requested: Decimal) -> Decimal:
        return min(D(requested), D(self.max_notional_usd))

    def cap_daily_loss(self, requested: Decimal) -> Decimal:
        return min(D(requested), D(self.max_daily_loss_usd))

    def cap_weekly_loss(self, requested: Decimal) -> Decimal:
        return min(D(requested), D(self.max_weekly_loss_usd))

    def cap_cumulative_loss(self, requested: Decimal) -> Decimal:
        return min(D(requested), D(self.max_cumulative_loss_usd))

    def cap_poll(self, requested: int) -> int:
        return max(int(requested), int(self.min_poll_interval_sec))

    def cap_open_positions(self, requested: int) -> int:
        return max(1, min(int(requested), int(self.max_open_positions)))

    @property
    def config_path(self) -> Path:
        return self.config_dir / "config.yaml"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "trader.db"

    @property
    def stop_path(self) -> Path:
        return self.data_dir / "STOP"
