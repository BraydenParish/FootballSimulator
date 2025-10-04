from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from fastapi.testclient import TestClient
from database import load_data

@pytest.fixture()
def api_client(tmp_path_factory, monkeypatch) -> TestClient:
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.db"
    monkeypatch.setenv("NFL_GM_DB_PATH", str(db_path))

    import backend.app.db as db_module

    importlib.reload(db_module)
    importlib.reload(load_data)
    load_data.main()

    import backend.main as backend_main

    importlib.reload(backend_main)

    client = TestClient(backend_main.app)
    yield client
    client.close()
