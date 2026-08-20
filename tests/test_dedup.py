"""Task 2 — BR-10 deduplication.

Records sharing a course_id (across both sources) must collapse to a single
row, keeping the one with the most recent last_updated. Where the spec
leaves a genuine gap (identical last_updated timestamps, D-09 in
DECISIONS.md) we only assert determinism, not a specific winner.
"""
from collections import defaultdict
from datetime import datetime

from transform import transform


def _parse(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime((value or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def test_no_duplicate_course_ids_survive(db_conn):
    total = db_conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    distinct = db_conn.execute("SELECT COUNT(DISTINCT course_id) FROM courses").fetchone()[0]
    assert total == distinct


def test_dedup_keeps_most_recent_last_updated(db_conn, raw_courses_all):
    """For course_ids that appear more than once in the raw feeds and whose
    duplicate rows are all individually well-formed, the surviving row must
    be the one with the most recent last_updated (BR-10)."""
    by_id = defaultdict(list)
    for row in raw_courses_all:
        cid = (row.get("course_id") or "").strip()
        if cid:
            by_id[cid].append(row)

    loaded = {
        r["course_id"]: r["last_updated"]
        for r in db_conn.execute("SELECT course_id, last_updated FROM courses")
    }

    checked = 0
    for cid, rows in by_id.items():
        if len(rows) < 2 or cid not in loaded:
            continue
        candidate_dates = [_parse(r.get("last_updated")) for r in rows]
        if any(d is None for d in candidate_dates):
            continue  # a malformed duplicate — can't be sure it competed in the dedupe
        expected_winner = max(candidate_dates)
        assert _parse(loaded[cid]) == expected_winner, (
            f"{cid}: expected the most-recent last_updated {expected_winner} to win, "
            f"but the loaded record has last_updated={loaded[cid]}"
        )
        checked += 1

    assert checked > 0, "no clean duplicate course_id groups found in the raw data to exercise BR-10"


def test_dedup_is_deterministic(raw_courses_all, raw_universities):
    """Re-running the transform on identical input must yield the same
    winner every time. The spec doesn't define a tie-break for equal
    last_updated timestamps, but the pipeline still has to be reproducible
    (see DECISIONS.md D-09)."""
    records_1, _ = transform(raw_courses_all, raw_universities)
    records_2, _ = transform(raw_courses_all, raw_universities)

    winners_1 = {r["course_id"]: r["last_updated"] for r in records_1}
    winners_2 = {r["course_id"]: r["last_updated"] for r in records_2}
    assert winners_1 == winners_2
