from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from crypto_trader.money import D
from crypto_trader.settings import EnvSettings
from crypto_trader.universe import normalize_symbol, parse_symbols

YAML_FIELDS = (
    "mode",
    "symbol",
    "symbols",
    "max_open_positions",
    "timeframe_seconds",
    "ema_fast",
    "ema_slow",
    "atr_period",
    "stop_atr_mult",
    "target_atr_mult",
    "poll_interval_sec",
    "max_notional_usd",
    "daily_loss_limit_usd",
    "weekly_loss_limit_usd",
    "cumulative_loss_limit_usd",
    "fee_bps",
    "spread_max_bps",
    "cost_multiple",
    "cooldown_bars",
    "max_hold_minutes",
    "htf_ema_period",
    "htf_filter_enabled",
    "htf_timeframe_seconds",
    "slippage_bps",
    "stale_quote_sec",
    "max_failed_polls",
    "min_order_size",
    "dust_notional_usd",
    "timezone",
    "session_start",
    "session_end",
    "paper_starting_cash",
    "flatten_on_session_end",
)


@dataclass
class BotConfig:
    mode: str = "paper"
    symbol: str = "BTC-USD"
    symbols: list[str] = field(default_factory=list)
    max_open_positions: int = 1
    timeframe_seconds: int = 300
    ema_fast: int = 9
    ema_slow: int = 21
    atr_period: int = 14
    stop_atr_mult: float = 1.5
    target_atr_mult: float = 2.0
    poll_interval_sec: int = 15
    max_notional_usd: Decimal = Decimal("100")
    daily_loss_limit_usd: Decimal = Decimal("50")
    weekly_loss_limit_usd: Decimal = Decimal("150")
    cumulative_loss_limit_usd: Decimal = Decimal("300")
    fee_bps: int = 100
    spread_max_bps: int = 25
    cost_multiple: Decimal = Decimal("2.0")
    cooldown_bars: int = 3
    max_hold_minutes: int = 240
    htf_ema_period: int = 50
    htf_filter_enabled: bool = False
    htf_timeframe_seconds: int = 3600
    slippage_bps: int = 5
    stale_quote_sec: int = 45
    max_failed_polls: int = 3
    min_order_size: Decimal = Decimal("0.00000001")
    dust_notional_usd: Decimal = Decimal("1")
    timezone: str = "America/Chicago"
    session_start: str = "08:00"
    session_end: str = "20:00"
    paper_starting_cash: Decimal = Decimal("10000")
    flatten_on_session_end: bool = True

    def watchlist(self) -> list[str]:
        selected = parse_symbols(self.symbols) if self.symbols else []
        if not selected:
            selected = [normalize_symbol(self.symbol)]
        return selected

    def as_public_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if key == "symbols":
                out[key] = list(self.watchlist())
            elif isinstance(value, Decimal):
                out[key] = str(value)
            else:
                out[key] = value
        out["symbol"] = self.watchlist()[0]
        return out


class ConfigError(ValueError):
    pass


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _dec_fields() -> set[str]:
    return {
        "max_notional_usd",
        "daily_loss_limit_usd",
        "weekly_loss_limit_usd",
        "cumulative_loss_limit_usd",
        "cost_multiple",
        "min_order_size",
        "dust_notional_usd",
        "paper_starting_cash",
    }


def _raw_to_config(raw: dict[str, Any]) -> BotConfig:
    kwargs: dict[str, Any] = {}
    for key in YAML_FIELDS:
        if key not in raw:
            continue
        value = raw[key]
        if key in _dec_fields():
            kwargs[key] = D(value)
        elif key == "symbols":
            kwargs[key] = parse_symbols(value)
        else:
            kwargs[key] = value
    cfg = BotConfig(**kwargs)
    if not cfg.symbols:
        cfg.symbols = cfg.watchlist()
    else:
        cfg.symbol = cfg.watchlist()[0]
    return cfg


def validate_config(cfg: BotConfig, env: EnvSettings) -> BotConfig:
    errors: list[str] = []
    if cfg.mode not in {"paper", "live"}:
        errors.append("mode must be paper or live")
    if cfg.ema_fast <= 0 or cfg.ema_slow <= 0:
        errors.append("EMA periods must be positive")
    if cfg.ema_fast >= cfg.ema_slow:
        errors.append("ema_fast must be less than ema_slow")
    if cfg.atr_period <= 0:
        errors.append("atr_period must be positive")
    if cfg.stop_atr_mult <= 0 or cfg.target_atr_mult <= 0:
        errors.append("ATR multipliers must be positive")
    if cfg.fee_bps < 0 or cfg.slippage_bps < 0 or cfg.spread_max_bps <= 0:
        errors.append("fee/slippage must be >= 0 and spread_max_bps > 0")
    if cfg.cost_multiple <= 0:
        errors.append("cost_multiple must be positive")
    if cfg.cooldown_bars < 0 or cfg.max_hold_minutes <= 0:
        errors.append("cooldown_bars must be >= 0 and max_hold_minutes > 0")
    if cfg.timeframe_seconds < 60:
        errors.append("timeframe_seconds must be >= 60")
    if cfg.stale_quote_sec < 5 or cfg.max_failed_polls < 1:
        errors.append("stale_quote_sec >= 5 and max_failed_polls >= 1")
    if cfg.max_notional_usd <= 0:
        errors.append("max_notional_usd must be positive")
    try:
        cfg.symbols = cfg.watchlist()
        cfg.symbol = cfg.symbols[0]
    except ValueError as exc:
        errors.append(str(exc))
    if cfg.max_open_positions < 1:
        errors.append("max_open_positions must be >= 1")
    try:
        from crypto_trader.timeutil import parse_hhmm, zone

        zone(cfg.timezone)
        parse_hhmm(cfg.session_start)
        parse_hhmm(cfg.session_end)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"timezone/session invalid: {exc}")
    if errors:
        raise ConfigError("; ".join(errors))

    cfg.max_notional_usd = env.cap_notional(cfg.max_notional_usd)
    cfg.daily_loss_limit_usd = env.cap_daily_loss(cfg.daily_loss_limit_usd)
    cfg.weekly_loss_limit_usd = env.cap_weekly_loss(cfg.weekly_loss_limit_usd)
    cfg.cumulative_loss_limit_usd = env.cap_cumulative_loss(cfg.cumulative_loss_limit_usd)
    cfg.poll_interval_sec = env.cap_poll(cfg.poll_interval_sec)
    cfg.max_open_positions = env.cap_open_positions(cfg.max_open_positions)
    return cfg


def load_config(path: Path, env: EnvSettings) -> BotConfig:
    yaml = _yaml()
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.load(fh) or {}
    return validate_config(_raw_to_config(dict(raw)), env)


def save_config(path: Path, updates: dict[str, Any], env: EnvSettings) -> BotConfig:
    """Write updates into the directory-mounted YAML, preserving comments."""
    yaml = _yaml()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.load(fh) or {}
    else:
        data = {}
    for key, value in updates.items():
        if key not in YAML_FIELDS:
            continue
        if key == "symbols":
            data[key] = parse_symbols(value)
        elif isinstance(value, Decimal):
            data[key] = str(value)
        elif isinstance(value, bool):
            data[key] = value
        else:
            data[key] = value
    cfg = validate_config(_raw_to_config(dict(data)), env)
    public = cfg.as_public_dict()
    for key in YAML_FIELDS:
        if key in data or key in updates:
            data[key] = public[key]
            if key in _dec_fields():
                data[key] = str(getattr(cfg, key))
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh)
    tmp.replace(path)
    return cfg
