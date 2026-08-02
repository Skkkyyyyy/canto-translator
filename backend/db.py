"""SQLite store for user-submitted glossary entries.

Submissions live here, not in data/*.csv. The CSVs are the read-only glossary
that rag.py scans on every request — an unreviewed entry landing there would
immediately affect live translations.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ["DB_PATH"]) if "DB_PATH" in os.environ else Path(__file__).parent / "data" / "contributions.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contributions (
    id            TEXT PRIMARY KEY,
    kind          TEXT NOT NULL,               -- token | sentence
    intent        TEXT NOT NULL,               -- new | correction
    token         TEXT NOT NULL,               -- romanized word, or the whole sentence
    cantonese     TEXT NOT NULL DEFAULT '',
    mandarin      TEXT NOT NULL DEFAULT '',
    english       TEXT NOT NULL DEFAULT '',
    function      TEXT NOT NULL DEFAULT '',    -- part of speech, matches the CSV Function column
    example       TEXT NOT NULL DEFAULT '',
    note          TEXT NOT NULL DEFAULT '',
    contributor   TEXT NOT NULL DEFAULT '',
    source_text   TEXT NOT NULL DEFAULT '',    -- what the user had typed into the translator
    source_output TEXT NOT NULL DEFAULT '',    -- what we answered, as JSON
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    reject_reason TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    reviewed_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_contributions_status ON contributions(status, created_at);
CREATE INDEX IF NOT EXISTS idx_contributions_token ON contributions(token);

CREATE TABLE IF NOT EXISTS translations (
    id                 TEXT PRIMARY KEY,
    input_text         TEXT NOT NULL,
    use_rag            INTEGER NOT NULL DEFAULT 1,
    retrieved_context  TEXT NOT NULL DEFAULT '',   -- rag() matches, as JSON
    reasoning          TEXT NOT NULL DEFAULT '',
    result             TEXT NOT NULL DEFAULT '',
    model              TEXT NOT NULL DEFAULT '',
    latency_ms         INTEGER NOT NULL DEFAULT 0,
    cache_hit          INTEGER NOT NULL DEFAULT 0,
    error              TEXT NOT NULL DEFAULT '',
    created_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_translations_created_at ON translations(created_at);
"""


@contextmanager
def connect():
    """One connection per call — FastAPI runs sync endpoints across threads."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


def log_translation(
    input_text: str,
    use_rag: bool,
    retrieved_context: str = "",
    reasoning: str = "",
    result: str = "",
    model: str = "",
    latency_ms: int = 0,
    cache_hit: bool = False,
    error: str = "",
):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO translations (
                id, input_text, use_rag, retrieved_context, reasoning,
                result, model, latency_ms, cache_hit, error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                input_text,
                int(use_rag),
                retrieved_context,
                reasoning,
                result,
                model,
                latency_ms,
                int(cache_hit),
                error,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
