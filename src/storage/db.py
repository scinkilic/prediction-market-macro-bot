from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List

DB_PATH = Path("data/market_snapshots.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                ticker TEXT NOT NULL,
                title TEXT,
                status TEXT,
                event_ticker TEXT,
                market_type TEXT,
                yes_bid REAL,
                yes_ask REAL,
                last_price REAL,
                volume REAL,
                open_interest REAL,
                close_time TEXT,
                expiration_time TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_snapshots_ticker_time "
            "ON market_snapshots (ticker, captured_at)"
        )
        conn.commit()
    finally:
        conn.close()


def insert_market_snapshots(captured_at: str, markets: Iterable[Dict[str, Any]]) -> int:
    conn = get_connection()
    inserted = 0

    try:
        rows: List[tuple] = []
        for market in markets:
            rows.append(
                (
                    captured_at,
                    market.get("ticker"),
                    market.get("title"),
                    market.get("status"),
                    market.get("event_ticker"),
                    market.get("market_type"),
                    market.get("yes_bid"),
                    market.get("yes_ask"),
                    market.get("last_price"),
                    market.get("volume"),
                    market.get("open_interest"),
                    market.get("close_time"),
                    market.get("expiration_time"),
                )
            )

        conn.executemany(
            """
            INSERT INTO market_snapshots (
                captured_at,
                ticker,
                title,
                status,
                event_ticker,
                market_type,
                yes_bid,
                yes_ask,
                last_price,
                volume,
                open_interest,
                close_time,
                expiration_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        inserted = len(rows)
        conn.commit()
        return inserted
    finally:
        conn.close()


def get_distinct_capture_times(limit: int = 20) -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT captured_at
            FROM market_snapshots
            ORDER BY captured_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [row["captured_at"] for row in rows]
    finally:
        conn.close()


def get_snapshots_for_capture_time(captured_at: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM market_snapshots
            WHERE captured_at = ?
            """,
            (captured_at,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
