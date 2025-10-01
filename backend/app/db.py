"""Lightweight SQLite access helpers for the FastAPI app."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "database" / "nfl_gm_sim.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Context manager that yields a SQLite connection with row access."""

    connection = _connect()
    try:
        yield connection
    finally:
        connection.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a SQLite row object into a plain dictionary."""

    return {key: row[key] for key in row.keys()}
