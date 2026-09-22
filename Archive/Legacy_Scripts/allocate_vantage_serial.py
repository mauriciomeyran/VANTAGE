#!/usr/bin/env python3
"""Allocate VANTAGE handoff serials from a shared HTTP service.

The service is intentionally small: deploy it once on a reachable host and
let every agent call POST /allocate. SQLite provides transactional allocation.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify
except ImportError:
    Flask = None
    jsonify = None

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


def create_app() -> Any:
    if Flask is None:
        raise RuntimeError("Install Flask: python3 -m pip install flask")

    app = Flask(__name__)

    @app.post("/allocate")
    def allocate() -> Any:
        try:
            serial = allocate_serial()
            return jsonify(
                {
                    "serial": serial,
                    "authority": COUNTER_NAME,
                    "status": "ALLOCATED",
                }
            ), 200
        except Exception as exc:
            return jsonify(
                {
                    "error": "HANDOFF_SERIAL_UNAVAILABLE",
                    "detail": str(exc),
                }
            ), 503

    @app.get("/health")
    def health() -> Any:
        return jsonify({"status": "ok", "authority": COUNTER_NAME}), 200

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["next", "serve"])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    if args.command == "next":
        print(allocate_serial())
        return

    app = create_app()
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
