"""Database utilities for the FastAPI app.

The services still rely on lightweight SQLite row access for now, but the
module also exposes a SQLAlchemy session factory so new code (such as the CSV
seeding script) can share the same engine and models.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "database" / "nfl_gm_sim.db"
DB_PATH = Path(os.environ.get("NFL_GM_DB_PATH", DEFAULT_DB_PATH))


def _resolve_db_path(path: Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.environ.get("NFL_GM_DB_PATH", DEFAULT_DB_PATH))


ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False, future=True)
SessionLocal.configure(bind=ENGINE)


def configure_engine(path: Path | None = None) -> None:
    """Reconfigure the shared SQLAlchemy engine/sessionmaker."""

    global DB_PATH, ENGINE
    DB_PATH = _resolve_db_path(path)
    if "ENGINE" in globals():
        try:
            ENGINE.dispose()
        except NameError:
            pass
    ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)
    SessionLocal.configure(bind=ENGINE)


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


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session bound to the shared engine."""

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
