from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from crypto_trader.models import Order, OrderStatus, Position, PositionStatus, Quote, Side, Trade
from crypto_trader.money import D
from crypto_trader.paper import PaperAccount

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    bid TEXT NOT NULL,
    ask TEXT NOT NULL,
    mid TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    qty TEXT NOT NULL,
    entry_price TEXT NOT NULL,
    stop TEXT NOT NULL,
    target TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    entry_fee TEXT NOT NULL,
    cost_basis TEXT NOT NULL,
    status TEXT NOT NULL,
    client_order_id TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    client_order_id TEXT PRIMARY KEY,
    broker_order_id TEXT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty TEXT NOT NULL,
    filled_qty TEXT NOT NULL,
    average_price TEXT,
    fee_charged TEXT NOT NULL DEFAULT '0',
    status TEXT NOT NULL,
    submitted_at TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY,
    opened_at TEXT NOT NULL,
    closed_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty TEXT NOT NULL,
    entry_price TEXT NOT NULL,
    exit_price TEXT NOT NULL,
    entry_fee TEXT NOT NULL,
    exit_fee TEXT NOT NULL,
    pnl TEXT NOT NULL,
    cost_basis TEXT NOT NULL,
    reason TEXT NOT NULL,
    mode TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config_audit (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    old_json TEXT NOT NULL,
    new_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    level TEXT NOT NULL,
    kind TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_account (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    cash TEXT NOT NULL,
    starting_cash TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_holdings (
    asset TEXT PRIMARY KEY,
    qty TEXT NOT NULL
);
"""


def _iso(ts: datetime) -> str:
    return ts.isoformat()


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.RLock()
        self._local = threading.local()
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def _raw(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, check_same_thread=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        return conn

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = self._raw()
        yield conn

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        with self._write_lock, self.connect() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def set_meta(self, key: str, value: str) -> None:
        with self.write() as conn:
            conn.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def close_open_positions(self) -> None:
        with self.write() as conn:
            conn.execute(
                "UPDATE positions SET status='closed', qty='0' WHERE status IN ('open','dust')"
            )

    def load_paper_account(self, default_cash) -> PaperAccount:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM paper_account WHERE id=1").fetchone()
            holds = conn.execute("SELECT asset, qty FROM paper_holdings").fetchall()
        holdings = {r["asset"]: D(r["qty"]) for r in holds if D(r["qty"]) != 0}
        if row is None:
            return PaperAccount(name="Paper", cash=D(default_cash), starting_cash=D(default_cash), holdings=holdings)
        return PaperAccount(
            name=row["name"],
            cash=D(row["cash"]),
            starting_cash=D(row["starting_cash"]),
            holdings=holdings,
        )

    def save_paper_account(self, account: PaperAccount, ts: datetime) -> None:
        with self.write() as conn:
            conn.execute(
                """
                INSERT INTO paper_account(id, name, cash, starting_cash, updated_at)
                VALUES(1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    cash=excluded.cash,
                    starting_cash=excluded.starting_cash,
                    updated_at=excluded.updated_at
                """,
                (account.name, str(account.cash), str(account.starting_cash), _iso(ts)),
            )
            conn.execute("DELETE FROM paper_holdings")
            for asset, qty in account.holdings.items():
                if D(qty) == 0:
                    continue
                conn.execute(
                    "INSERT INTO paper_holdings(asset, qty) VALUES(?, ?)",
                    (asset.upper(), str(D(qty))),
                )

    def wipe_paper_history(self) -> None:
        with self.write() as conn:
            conn.execute("DELETE FROM trades")
            conn.execute("DELETE FROM orders")
            conn.execute("UPDATE positions SET status='closed', qty='0' WHERE status IN ('open','dust')")

    def record_quote(self, quote: Quote) -> None:
        with self.write() as conn:
            conn.execute(
                "INSERT INTO quotes(ts, symbol, bid, ask, mid, source) VALUES(?,?,?,?,?,?)",
                (
                    _iso(quote.ts),
                    quote.symbol,
                    str(quote.bid),
                    str(quote.ask),
                    str(quote.mid),
                    quote.source,
                ),
            )

    def record_event(self, level: str, kind: str, message: str, ts: datetime) -> None:
        with self.write() as conn:
            conn.execute(
                "INSERT INTO events(ts, level, kind, message) VALUES(?,?,?,?)",
                (_iso(ts), level, kind, message),
            )

    def record_config_audit(self, ts: datetime, actor: str, old_json: str, new_json: str) -> None:
        with self.write() as conn:
            conn.execute(
                "INSERT INTO config_audit(ts, actor, old_json, new_json) VALUES(?,?,?,?)",
                (_iso(ts), actor, old_json, new_json),
            )

    def upsert_order(self, order: Order) -> None:
        with self.write() as conn:
            conn.execute(
                """
                INSERT INTO orders(client_order_id, broker_order_id, symbol, side, qty, filled_qty,
                    average_price, fee_charged, status, submitted_at, raw_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(client_order_id) DO UPDATE SET
                    broker_order_id=excluded.broker_order_id,
                    filled_qty=excluded.filled_qty,
                    average_price=excluded.average_price,
                    fee_charged=excluded.fee_charged,
                    status=excluded.status,
                    raw_json=excluded.raw_json
                """,
                (
                    order.client_order_id,
                    order.broker_order_id,
                    order.symbol,
                    order.side.value,
                    str(order.qty),
                    str(order.filled_qty),
                    str(order.average_price) if order.average_price is not None else None,
                    str(order.fee_charged),
                    order.status.value,
                    _iso(order.submitted_at) if order.submitted_at else None,
                    str(order.raw),
                ),
            )

    def get_order(self, client_order_id: str) -> Order | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE client_order_id=?", (client_order_id,)
            ).fetchone()
        return self._order_from_row(row) if row else None

    def pending_orders(self) -> list[Order]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM orders WHERE status IN ('pending','open','partially_filled')"
            ).fetchall()
        return [self._order_from_row(r) for r in rows]

    def open_positions(self) -> list[Position]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE status='open' ORDER BY id ASC"
            ).fetchall()
        return [self._position_from_row(r) for r in rows]

    def open_position(self, symbol: str | None = None) -> Position | None:
        with self.connect() as conn:
            if symbol:
                row = conn.execute(
                    "SELECT * FROM positions WHERE status='open' AND symbol=? ORDER BY id DESC LIMIT 1",
                    (symbol,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM positions WHERE status='open' ORDER BY id DESC LIMIT 1"
                ).fetchone()
        return self._position_from_row(row) if row else None

    def insert_position(self, pos: Position) -> Position:
        with self.write() as conn:
            cur = conn.execute(
                """
                INSERT INTO positions(symbol, qty, entry_price, stop, target, opened_at,
                    entry_fee, cost_basis, status, client_order_id)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    pos.symbol,
                    str(pos.qty),
                    str(pos.entry_price),
                    str(pos.stop),
                    str(pos.target),
                    _iso(pos.opened_at),
                    str(pos.entry_fee),
                    str(pos.cost_basis),
                    pos.status.value,
                    pos.client_order_id,
                ),
            )
            pos.id = int(cur.lastrowid)
        return pos

    def update_position(self, pos: Position) -> None:
        if pos.id is None:
            raise ValueError("position id required")
        with self.write() as conn:
            conn.execute(
                """
                UPDATE positions SET qty=?, status=?, stop=?, target=? WHERE id=?
                """,
                (str(pos.qty), pos.status.value, str(pos.stop), str(pos.target), pos.id),
            )

    def insert_trade(self, trade: Trade) -> Trade:
        with self.write() as conn:
            cur = conn.execute(
                """
                INSERT INTO trades(opened_at, closed_at, symbol, side, qty, entry_price, exit_price,
                    entry_fee, exit_fee, pnl, cost_basis, reason, mode)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    _iso(trade.opened_at),
                    _iso(trade.closed_at),
                    trade.symbol,
                    trade.side,
                    str(trade.qty),
                    str(trade.entry_price),
                    str(trade.exit_price),
                    str(trade.entry_fee),
                    str(trade.exit_fee),
                    str(trade.pnl),
                    str(trade.cost_basis),
                    trade.reason,
                    trade.mode,
                ),
            )
            trade.id = int(cur.lastrowid)
        return trade

    def list_trades(self, limit: int = 200) -> list[Trade]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._trade_from_row(r) for r in rows]

    def all_trades(self) -> list[Trade]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY id ASC").fetchall()
        return [self._trade_from_row(r) for r in rows]

    def recent_events(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            )

    def list_config_audit(self, limit: int = 25) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM config_audit ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            )

    def backup(self, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as src, sqlite3.connect(dest) as dst:
            src.backup(dst)

    @staticmethod
    def _order_from_row(row: sqlite3.Row) -> Order:
        return Order(
            client_order_id=row["client_order_id"],
            broker_order_id=row["broker_order_id"],
            symbol=row["symbol"],
            side=Side(row["side"]),
            qty=D(row["qty"]),
            filled_qty=D(row["filled_qty"]),
            average_price=D(row["average_price"]) if row["average_price"] else None,
            fee_charged=D(row["fee_charged"]),
            status=OrderStatus(row["status"]),
            submitted_at=_parse_ts(row["submitted_at"]) if row["submitted_at"] else None,
        )

    @staticmethod
    def _position_from_row(row: sqlite3.Row) -> Position:
        return Position(
            id=row["id"],
            symbol=row["symbol"],
            qty=D(row["qty"]),
            entry_price=D(row["entry_price"]),
            stop=D(row["stop"]),
            target=D(row["target"]),
            opened_at=_parse_ts(row["opened_at"]),
            entry_fee=D(row["entry_fee"]),
            cost_basis=D(row["cost_basis"]),
            status=PositionStatus(row["status"]),
            client_order_id=row["client_order_id"],
        )

    @staticmethod
    def _trade_from_row(row: sqlite3.Row) -> Trade:
        return Trade(
            id=row["id"],
            opened_at=_parse_ts(row["opened_at"]),
            closed_at=_parse_ts(row["closed_at"]),
            symbol=row["symbol"],
            side=row["side"],
            qty=D(row["qty"]),
            entry_price=D(row["entry_price"]),
            exit_price=D(row["exit_price"]),
            entry_fee=D(row["entry_fee"]),
            exit_fee=D(row["exit_fee"]),
            pnl=D(row["pnl"]),
            cost_basis=D(row["cost_basis"]),
            reason=row["reason"],
            mode=row["mode"],
        )
