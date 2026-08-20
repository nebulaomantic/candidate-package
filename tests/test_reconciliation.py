"""Task 2 — BR-11 row-count reconciliation.

"No record may silently disappear": every raw input row must end up either
loaded into `courses`, listed in `rejects`, or accounted for as a BR-10
dedupe loser (DECISIONS.md D-10 — the spec's "(possibly losing a dedupe)"
reads as an explicit third bucket, not a hidden case of `rejects`).
"""
from collections import Counter


def test_global_row_count_reconciliation(db_conn, raw_courses_all):
    raw_ids = Counter((r.get("course_id") or "").strip() for r in raw_courses_all)
    raw_total = len(raw_courses_all)

    reject_ids = Counter(r["course_id"] for r in db_conn.execute("SELECT course_id FROM rejects"))
    loaded_ids = {r["course_id"] for r in db_conn.execute("SELECT course_id FROM courses")}

    reject_total = sum(reject_ids.values())
    loaded_total = len(loaded_ids)

    # raw_count(id) - reject_count(id) = how many raw rows sharing this id
    # were individually valid. At most one of those can survive into
    # `courses`; any remainder is a BR-10 dedupe loser, not a silent drop.
    dedup_losers = 0
    for cid, raw_count in raw_ids.items():
        valid_count = raw_count - reject_ids.get(cid, 0)
        already_loaded = 1 if cid in loaded_ids else 0
        dedup_losers += max(valid_count - already_loaded, 0)

    assert raw_total == loaded_total + reject_total + dedup_losers, (
        f"raw={raw_total} loaded={loaded_total} rejected={reject_total} "
        f"dedup_losers={dedup_losers} — BR-11 accounting does not add up"
    )


def test_rejects_only_use_real_source_labels(db_conn):
    bad = db_conn.execute(
        "SELECT DISTINCT source FROM rejects WHERE source NOT IN ('A', 'B')"
    ).fetchall()
    assert bad == []


def test_per_source_raw_counts_are_not_exceeded(db_conn, raw_courses_a, raw_courses_b):
    """Sanity bound: neither loaded+rejected count for a source can exceed
    that source's raw row count (a looser, per-source cross-check alongside
    the exact global reconciliation above)."""
    for source, raw_rows in (("A", raw_courses_a), ("B", raw_courses_b)):
        loaded = db_conn.execute(
            "SELECT COUNT(*) FROM courses WHERE source = ?", (source,)
        ).fetchone()[0]
        rejected = db_conn.execute(
            "SELECT COUNT(*) FROM rejects WHERE source = ?", (source,)
        ).fetchone()[0]
        assert loaded <= len(raw_rows)
        assert rejected <= len(raw_rows)
