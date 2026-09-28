#!/usr/bin/env python3
"""Allocate VANTAGE handoff serials via CLI.

Serial allocation is performed exclusively via terminal/CLI as per Kernel norms.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get(
    "VANTAGE_SERIAL_DB",
    str(Path(__file__).resolve().parent.parent.parent / "state" / "vantage_handoff_counter.sqlite3"),
))
COUNTER_NAME = "GLOBAL_VANTAGE_COUNTER"


def initialize(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL CHECK(value >= 0)
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO counters(name, value) VALUES (?, ?)",
        (COUNTER_NAME, 0),
    )
    conn.commit()


def allocate_serial() -> str:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        initialize(conn)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE counters SET value = value + 1 WHERE name = ?",
            (COUNTER_NAME,),
        )
        row = conn.execute(
            "SELECT value FROM counters WHERE name = ?",
            (COUNTER_NAME,),
        ).fetchone()
        if row is None:
            raise RuntimeError("GLOBAL_VANTAGE_COUNTER is unavailable")
        return f"HO-{row[0]:06d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["next"])
    args = parser.parse_args()

    if args.command == "next":
        print(allocate_serial())
        return


if __name__ == "__main__":
    main()
