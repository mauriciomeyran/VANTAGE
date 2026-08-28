#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"
DB_PATH = Path(
    os.environ.get(
        "VANTAGE_COUNTER_DB",
        STATE_DIR / "vantage_handoff_counter.sqlite3",
    )
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS counters (
    name TEXT PRIMARY KEY,
    value INTEGER NOT NULL CHECK (value >= 0)
);

INSERT OR IGNORE INTO counters(name, value)
VALUES ('GLOBAL_VANTAGE_COUNTER', 0);
"""


def next_serial() -> str:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.executescript(SCHEMA)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            UPDATE counters
            SET value = value + 1
            WHERE name = 'GLOBAL_VANTAGE_COUNTER'
            """
        )
        row = conn.execute(
            """
            SELECT value
            FROM counters
            WHERE name = 'GLOBAL_VANTAGE_COUNTER'
            """
        ).fetchone()

        if row is None:
            raise RuntimeError("GLOBAL_VANTAGE_COUNTER no inicializado")

        return f"HO-{row[0]:06d}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Allocates the next VANTAGE handoff serial."
    )
    parser.add_argument("command", choices=["next"])
    args = parser.parse_args()

    if args.command == "next":
        print(next_serial())


if __name__ == "__main__":
    main()
