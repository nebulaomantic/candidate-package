"""Shared fixtures for the CourseFlow test suite.

Layout:
  - `built_db` rebuilds data/courses.db from the current raw sources once per
    session, so every test run starts from a known, deterministic state
    (see README: "Re-running the pipeline fully rebuilds the database").
  - Data-validation tests (Task 2 / Task 3) read directly from `built_db` via
    `db_conn`.
  - API tests (Task 4) get their own per-test copy of the db (`api_db_path`)
    so that mutating calls (POST /courses) never leak state into other tests.
"""
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "courses.db"

sys.path.insert(0, str(BASE_DIR / "etl"))
sys.path.insert(0, str(BASE_DIR))

from extract import extract_source_a, extract_source_b, extract_universities  # noqa: E402
from transform import transform  # noqa: E402
from load import load  # noqa: E402

# ---------------------------------------------------------------------------
# Business-rule constants tests should assert against (the spec), not
# whatever the pipeline happens to implement.
# ---------------------------------------------------------------------------
SPEC_FX_RATES = {
    "USD": 1.0,
    "AUD": 0.65,
    "GBP": 1.27,
    "EUR": 1.08,
    "NPR": 0.0075,
}
SPEC_LEVELS = {"Bachelor", "Master", "PhD", "Diploma"}
SPEC_DELIVERY_MODES = {"On-campus", "Online", "Hybrid"}
API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = "secret-key-123"


# ---------------------------------------------------------------------------
# Raw source fixtures — used for reconciliation (BR-11) and referential
# checks (BR-3) against what the pipeline actually loaded.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def raw_courses_a():
    return extract_source_a(RAW_DIR)


@pytest.fixture(scope="session")
def raw_courses_b():
    return extract_source_b(RAW_DIR)


@pytest.fixture(scope="session")
def raw_universities():
    return extract_universities(RAW_DIR)


@pytest.fixture(scope="session")
def raw_courses_all(raw_courses_a, raw_courses_b):
    return raw_courses_a + raw_courses_b


# ---------------------------------------------------------------------------
# Pipeline output — rebuilt fresh at the start of the session so tests never
# depend on whatever state was left in data/courses.db by a previous run.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def built_db(raw_courses_all, raw_universities):
    """Run the real ETL pipeline once and return the resulting db path."""
    records, rejects = transform(raw_courses_all, raw_universities)
    load(records, rejects, raw_universities, DB_PATH)
    return DB_PATH


@pytest.fixture()
def db_conn(built_db):
    """A fresh read-only connection per test, closed automatically."""
    conn = sqlite3.connect(built_db)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API fixtures — each test gets an isolated copy of the built db so POST
# /courses (or any future mutating endpoint) can't affect other tests.
# ---------------------------------------------------------------------------
@pytest.fixture()
def api_db_path(built_db, tmp_path, monkeypatch):
    import api.main as api_main

    isolated_db = tmp_path / "courses.db"
    shutil.copyfile(built_db, isolated_db)
    monkeypatch.setattr(api_main, "DB_PATH", isolated_db)
    return isolated_db


@pytest.fixture()
def api_client(api_db_path):
    import api.main as api_main

    with TestClient(api_main.app, base_url=API_BASE_URL) as client:
        yield client


@pytest.fixture()
def auth_headers():
    return {"X-API-Key": API_KEY}
