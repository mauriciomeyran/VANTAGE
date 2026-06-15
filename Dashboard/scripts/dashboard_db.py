import json
import sqlite3
import time
import uuid

from datetime import datetime
from contextlib import contextmanager

from dashboard_config import DB_PATH


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS instances (
                instance_id     TEXT PRIMARY KEY,
                notion_page_id  TEXT NOT NULL,
                state           TEXT NOT NULL DEFAULT 'BLOCKED',
                version_id      INTEGER NOT NULL DEFAULT 1,
                event_sequence  INTEGER NOT NULL DEFAULT 0,
                correlation_id  TEXT NOT NULL,
                operator_id     TEXT NOT NULL DEFAULT 'human',
                payload         TEXT NOT NULL,
                proposed_patch  TEXT,
                block_reason    TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id              TEXT PRIMARY KEY,
                instance_id     TEXT NOT NULL,
                sequence        INTEGER NOT NULL,
                correlation_id  TEXT NOT NULL,
                causation_id    TEXT,
                event_type      TEXT NOT NULL,
                payload         TEXT NOT NULL,
                timestamp_unix  INTEGER NOT NULL,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (instance_id)
                REFERENCES instances(instance_id)
            );

            CREATE INDEX IF NOT EXISTS idx_audit_instance
            ON audit_events(instance_id, sequence);

            CREATE INDEX IF NOT EXISTS idx_instances_notion
            ON instances(notion_page_id);

            CREATE INDEX IF NOT EXISTS idx_instances_state
            ON instances(state);
        ''')


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def append_event(
    conn,
    instance_id,
    sequence,
    correlation_id,
    causation_id,
    event_type,
    payload,
):
    now = datetime.utcnow().isoformat()

    conn.execute(
        '''
        INSERT INTO audit_events
        (
            id,
            instance_id,
            sequence,
            correlation_id,
            causation_id,
            event_type,
            payload,
            timestamp_unix,
            created_at
        )
        VALUES (?,?,?,?,?,?,?,?,?)
        ''',
        (
            str(uuid.uuid4()),
            instance_id,
            sequence,
            correlation_id,
            causation_id,
            event_type,
            json.dumps(payload),
            int(time.time()),
            now,
        ),
    )
