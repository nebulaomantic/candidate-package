"""Task 2 — BR-3 referential integrity.

Every loaded course must reference a university that exists in
universities.csv, and a record referring to an unknown university must be
rejected with reason `unknown_university` — for records from *both* sources
(the spec is explicit about this).
"""
from transform import transform


def test_every_loaded_course_references_a_known_university(db_conn):
    orphans = db_conn.execute(
        """
        SELECT c.course_id FROM courses c
        LEFT JOIN universities u ON c.university_id = u.university_id
        WHERE u.university_id IS NULL
        """
    ).fetchall()
    assert orphans == [], f"courses referencing unknown universities: {[r['course_id'] for r in orphans]}"


def test_unknown_university_is_rejected_source_a(raw_courses_a, raw_universities):
    row = next(r for r in raw_courses_a if r["university_id"] in raw_universities).copy()
    row["university_id"] = "UNI-DOES-NOT-EXIST"
    row["course_id"] = "CRS-TEST-UNKNOWN-A"

    _, rejects = transform([row], raw_universities)

    assert rejects and rejects[0]["reason"] == "unknown_university"


def test_unknown_university_is_rejected_source_b(raw_courses_b, raw_universities):
    row = next(iter(raw_courses_b)).copy()
    row["university_id"] = "UNI-DOES-NOT-EXIST"
    row["course_id"] = "CRS-TEST-UNKNOWN-B"

    _, rejects = transform([row], raw_universities)

    # BR-3 explicitly states this applies to both sources.
    assert rejects and rejects[0]["reason"] == "unknown_university"
