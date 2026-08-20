"""Task 2 — rejects table correctness: the right rows, with the right
reasons (BR-11).
"""

# Reason codes named explicitly by the spec. Others (missing_course_id,
# missing_title, missing_university_id, invalid_last_updated, ...) are
# undocumented but reasonable inventions by the pipeline — see DECISIONS.md
# D-02/D-03. We only assert on the ones the spec actually names.
SPEC_NAMED_REASONS = {
    "unknown_university",   # BR-3
    "invalid_level",        # BR-4
    "invalid_fee",          # BR-7
    "invalid_intake_window",  # BR-8
    "invalid_duration",     # BR-9
    "invalid_deadline",     # BR-12
}


def test_rejects_table_is_not_empty(db_conn):
    """A sanity check: with 50k raw rows across two messy source feeds, a
    suite that finds zero rejects almost certainly has a wiring problem."""
    n = db_conn.execute("SELECT COUNT(*) FROM rejects").fetchone()[0]
    assert n > 0


def test_every_reject_reason_is_a_known_code(db_conn):
    seen = {r["reason"] for r in db_conn.execute("SELECT DISTINCT reason FROM rejects")}
    unexpected = seen - SPEC_NAMED_REASONS - {
        "missing_course_id", "missing_title", "missing_university_id",
        "invalid_last_updated", "invalid_delivery_mode",
    }
    assert unexpected == set(), f"unrecognized reject reason code(s): {unexpected}"


def test_no_loaded_course_has_a_non_positive_fee(db_conn):
    """BR-7 must hold for every loaded record, not just at reject time."""
    bad_fee_loaded = db_conn.execute(
        "SELECT course_id FROM courses WHERE fee_usd <= 0"
    ).fetchall()
    assert bad_fee_loaded == []


def test_no_loaded_course_has_an_invalid_intake_window(db_conn):
    """BR-8 must hold for every loaded record, not just at reject time."""
    bad_window = db_conn.execute(
        "SELECT course_id FROM courses WHERE intake_end <= intake_start"
    ).fetchall()
    assert bad_window == []
