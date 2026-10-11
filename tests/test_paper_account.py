from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from fastapi.testclient import TestClient

from crypto_trader.app import Runtime, create_app
from crypto_trader.db import Database
from crypto_trader.models import Position, PositionStatus, Trade
from crypto_trader.paper import PaperAccount, PaperBroker, normalize_asset
from crypto_trader.timeutil import now_utc


def _logged_in(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    rt.health.touch(reason="ok")
    app = create_app(rt, start_loop=False)
    client = TestClient(app)
    client.post("/login", data={"password": "secret"})
    return client, rt


def test_paper_account_mutations():
    acct = PaperAccount(cash=Decimal("1000"), starting_cash=Decimal("1000"))
    acct.deposit("250.50")
    assert acct.cash == Decimal("1250.50")
    acct.withdraw("50")
    assert acct.cash == Decimal("1200.50")
    acct.set_holding("btc-usd", "0.25")
    assert acct.holdings["BTC"] == Decimal("0.25")
    acct.set_holding("BTC", "0")
    assert "BTC" not in acct.holdings
    acct.set_cash("800")
    acct.set_starting_cash("2000")
    acct.reset_ledger()
    assert acct.cash == Decimal("2000")
    assert acct.holdings == {}


def test_paper_account_rejects_bad_values():
    acct = PaperAccount(cash=Decimal("10"))
    with pytest.raises(ValueError, match="negative"):
        acct.set_cash("-1")
    with pytest.raises(ValueError, match="insufficient"):
        acct.withdraw("11")
    with pytest.raises(ValueError, match="positive"):
        acct.deposit("0")
    with pytest.raises(ValueError, match="ticker"):
        normalize_asset("??")


def test_paper_ledger_survives_restart(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    acct = rt.broker.to_account()
    acct.set_cash("7777.25")
    acct.set_holding("BTC", "0.25")
    acct.set_name("Sim book")
    rt.broker.apply_account(acct)
    rt.persist_paper()

    rt2 = Runtime(env_settings, start_loop=False)
    assert rt2.broker.cash == Decimal("7777.25")
    assert rt2.broker.holdings["BTC"] == Decimal("0.25")
    assert rt2.broker.name == "Sim book"


def test_database_round_trip(tmp_path):
    db = Database(tmp_path / "t.db")
    acct = PaperAccount(name="Desk", cash=Decimal("50"), starting_cash=Decimal("100"), holdings={"ETH": Decimal("2")})
    db.save_paper_account(acct, datetime(2026, 3, 9, 15, 0, tzinfo=UTC))
    loaded = db.load_paper_account(Decimal("10000"))
    assert loaded.name == "Desk"
    assert loaded.cash == Decimal("50")
    assert loaded.starting_cash == Decimal("100")
    assert loaded.holdings == {"ETH": Decimal("2")}


def test_admin_set_cash_deposit_withdraw_holding(env_settings):
    client, rt = _logged_in(env_settings)
    saved = client.post(
        "/paper/account",
        data={"name": "Practice", "cash": "5000", "starting_cash": "8000"},
        follow_redirects=False,
    )
    assert saved.status_code == 303
    assert rt.broker.cash == Decimal("5000")
    assert rt.broker.starting_cash == Decimal("8000")
    assert rt.broker.name == "Practice"
    assert rt.cfg.paper_starting_cash == Decimal("8000")

    dep = client.post("/paper/deposit", data={"amount": "250"}, follow_redirects=False)
    assert dep.status_code == 303
    assert rt.broker.cash == Decimal("5250")

    wd = client.post("/paper/withdraw", data={"amount": "250"}, follow_redirects=False)
    assert wd.status_code == 303
    assert rt.broker.cash == Decimal("5000")

    hold = client.post("/paper/holding", data={"asset": "ETH", "qty": "1.5"}, follow_redirects=False)
    assert hold.status_code == 303
    assert rt.broker.holdings["ETH"] == Decimal("1.5")

    over = client.post("/paper/withdraw", data={"amount": "99999"})
    assert over.status_code == 200
    assert b"insufficient" in over.content


def test_admin_reset_paper_account(env_settings):
    client, rt = _logged_in(env_settings)
    rt.broker.cash = Decimal("12")
    rt.broker.holdings["BTC"] = Decimal("0.4")
    rt.broker.starting_cash = Decimal("10000")
    rt.persist_paper()
    rt.risk.record_realized(Decimal("-9"))
    rt.db.insert_position(
        Position(
            id=None,
            symbol="BTC-USD",
            qty=Decimal("0.4"),
            entry_price=Decimal("100"),
            stop=Decimal("95"),
            target=Decimal("110"),
            opened_at=now_utc(),
            entry_fee=Decimal("1"),
            cost_basis=Decimal("41"),
            status=PositionStatus.OPEN,
        )
    )
    rt.db.insert_trade(
        Trade(
            id=None,
            opened_at=datetime(2026, 3, 9, 15, 0, tzinfo=UTC),
            closed_at=datetime(2026, 3, 9, 15, 10, tzinfo=UTC),
            symbol="BTC-USD",
            side="long",
            qty=Decimal("0.01"),
            entry_price=Decimal("100"),
            exit_price=Decimal("101"),
            entry_fee=Decimal("0.10"),
            exit_fee=Decimal("0.10"),
            pnl=Decimal("0.80"),
            cost_basis=Decimal("1.10"),
            reason="target",
            mode="paper",
        )
    )
    resp = client.post(
        "/paper/reset",
        data={"reset_risk": "on", "wipe_history": "on"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert rt.broker.cash == Decimal("10000")
    assert rt.broker.holdings == {}
    assert rt.db.open_position() is None
    assert rt.db.all_trades() == []
    assert rt.risk.state.daily_pnl == Decimal("0")


def test_paper_broker_to_account_round_trip():
    broker = PaperBroker(fee_bps=100)
    broker.cash = Decimal("42")
    broker.holdings["SOL"] = Decimal("3")
    broker.name = "A"
    broker.starting_cash = Decimal("99")
    again = PaperBroker(fee_bps=100)
    again.load_account(broker.to_account())
    assert again.cash == Decimal("42")
    assert again.holdings["SOL"] == Decimal("3")
    assert again.name == "A"
    assert again.starting_cash == Decimal("99")
