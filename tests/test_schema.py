"""Task 2 — schema and mandatory-field checks on the `courses` and `rejects`
target tables (BR-1, BR-2, BR-3 mandatory-field halves).
"""
import re

COURSE_ID_RE = re.compile(r"^CRS-\d+$")

MANDATORY_COLUMNS = [
    "course_id", "title", "university_id", "level", "fee_usd",
    "intake_start", "intake_end", "delivery_mode", "last_updated", "source",
]


def test_courses_table_has_expected_columns(db_conn):
    cols = {row[1] for row in db_conn.execute("PRAGMA table_info(courses)")}
    expected = {
        "course_id", "title", "university_id", "level", "discipline",
        "fee_usd", "original_fee", "original_currency", "intake_start",
        "intake_end", "duration_months", "delivery_mode", "url",
        "last_updated", "source",
    }
    assert expected <= cols


def test_rejects_table_has_expected_columns(db_conn):
    cols = {row[1] for row in db_conn.execute("PRAGMA table_info(rejects)")}
    assert {"course_id", "source", "reason"} <= cols


def test_no_nulls_or_blanks_in_mandatory_columns(db_conn):
    for column in MANDATORY_COLUMNS:
        n = db_conn.execute(
            f"SELECT COUNT(*) FROM courses WHERE {column} IS NULL OR {column} = ''"
        ).fetchone()[0]
        assert n == 0, f"{n} courses row(s) have a blank/NULL {column}"


def test_course_id_is_unique(db_conn):
    """BR-1: course_id is unique in the target table (also enforced by the PK)."""
    total = db_conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    distinct = db_conn.execute("SELECT COUNT(DISTINCT course_id) FROM courses").fetchone()[0]
    assert total == distinct


def test_course_id_matches_required_format(db_conn):
    """BR-1: course_id must be CRS-<number>."""
    bad = [
        r["course_id"] for r in db_conn.execute("SELECT course_id FROM courses")
        if not COURSE_ID_RE.match(r["course_id"])
    ]
    assert bad == [], f"course_id(s) not matching CRS-<number>: {bad[:10]}"


def test_reject_reasons_are_never_blank(db_conn):
    n = db_conn.execute(
        "SELECT COUNT(*) FROM rejects WHERE reason IS NULL OR reason = ''"
    ).fetchone()[0]
    assert n == 0
