"""Load step: write transformed records into the target SQLite database."""
import sqlite3
from pathlib import Path

SCHEMA = """
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS rejects;
DROP TABLE IF EXISTS universities;

CREATE TABLE universities (
    university_id TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    country       TEXT NOT NULL,
    city          TEXT NOT NULL
);

CREATE TABLE courses (
    course_id         TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    university_id     TEXT NOT NULL,
    level             TEXT NOT NULL,
    discipline        TEXT,
    fee_usd           REAL NOT NULL,
    original_fee      REAL NOT NULL,
    original_currency TEXT NOT NULL,
    intake_start      TEXT NOT NULL,
    intake_end        TEXT NOT NULL,
    duration_months   INTEGER,
    delivery_mode     TEXT NOT NULL,
    url               TEXT,
    last_updated      TEXT NOT NULL,
    source            TEXT NOT NULL
);

CREATE TABLE rejects (
    course_id TEXT,
    source    TEXT,
    reason    TEXT NOT NULL
);
"""


def load(records: list[dict], rejects: list[dict], universities: dict[str, dict], db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)

        conn.executemany(
            "INSERT INTO universities VALUES (?, ?, ?, ?)",
            [(u["university_id"], u["name"], u["country"], u["city"])
             for u in universities.values()],
        )

        conn.executemany(
            """INSERT INTO courses VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(
                r["course_id"],
                r["title"][:50],
                r["university_id"],
                r["level"],
                r["discipline"],
                r["fee_usd"],
                r["original_fee"],
                r["original_currency"],
                r["intake_start"],
                r["intake_end"],
                r["duration_months"],
                r["delivery_mode"],
                r["url"],
                r["last_updated"],
                r["source"],
            ) for r in records],
        )

        conn.executemany(
            "INSERT INTO rejects VALUES (?, ?, ?)",
            [(r["course_id"], r["source"], r["reason"]) for r in rejects],
        )

        conn.commit()
    finally:
        conn.close()
