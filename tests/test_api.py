"""Task 4 — API test automation.

Covers the API Specification table in ASSESSMENT.md: health check,
pagination (including the very last page), case-insensitive filters,
unknown course id -> 404, missing/wrong API key -> 401, bad payload -> 422,
duplicate course_id -> 409, and reachability of every loaded record through
pagination.

Per the assessment ground rules, these assert the *spec*, not whatever
api/main.py currently does -- a failing test here is evidence for
DEFECTS.md, not a signal to relax the assertion.
"""
import math

import pytest


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
def test_health_check(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /courses -- pagination
# ---------------------------------------------------------------------------
def test_courses_first_page_defaults(api_client):
    resp = api_client.get("/courses")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["items"]) <= 20


def test_total_pages_is_ceil_of_total_over_page_size(api_client):
    """Spec: total_pages = ceil(total / page_size)."""
    resp = api_client.get("/courses", params={"page_size": 20})
    body = resp.json()
    expected_total_pages = math.ceil(body["total"] / body["page_size"]) if body["total"] else 0
    assert body["total_pages"] == expected_total_pages


def test_last_page_is_reachable_and_holds_the_remainder(api_client):
    """The very last page must be reachable, and must hold exactly the
    remainder of records (total - full_pages * page_size), not 400 and not
    silently empty."""
    page_size = 37  # deliberately not a divisor of the total, to force a
    #                 partial last page
    resp = api_client.get("/courses", params={"page_size": page_size})
    body = resp.json()
    total, total_pages = body["total"], body["total_pages"]
    assert total_pages == math.ceil(total / page_size)

    last_page_resp = api_client.get(
        "/courses", params={"page": total_pages, "page_size": page_size}
    )
    assert last_page_resp.status_code == 200, (
        f"last page {total_pages} must be reachable, got "
        f"{last_page_resp.status_code}: {last_page_resp.text}"
    )
    expected_last_page_count = total - (total_pages - 1) * page_size
    assert len(last_page_resp.json()["items"]) == expected_last_page_count


def test_page_zero_returns_400(api_client):
    resp = api_client.get("/courses", params={"page": 0})
    assert resp.status_code == 400


def test_page_beyond_last_returns_400(api_client):
    resp = api_client.get("/courses", params={"page_size": 20})
    total_pages = resp.json()["total_pages"]
    resp = api_client.get(
        "/courses", params={"page": total_pages + 1, "page_size": 20}
    )
    assert resp.status_code == 400


def test_every_loaded_record_is_reachable_through_pagination(api_client, db_conn):
    """Walk every page and confirm the union of course_ids returned equals
    every course_id actually loaded -- nothing skipped, nothing duplicated."""
    page_size = 500
    seen_ids = []
    page = 1
    while True:
        resp = api_client.get("/courses", params={"page": page, "page_size": page_size})
        assert resp.status_code == 200, f"page {page} failed: {resp.status_code} {resp.text}"
        body = resp.json()
        items = body["items"]
        if not items:
            break
        seen_ids.extend(item["course_id"] for item in items)
        if page >= body["total_pages"]:
            break
        page += 1

    expected_ids = {
        row["course_id"] for row in db_conn.execute("SELECT course_id FROM courses")
    }
    assert len(seen_ids) == len(set(seen_ids)), "pagination returned a duplicate course_id"
    assert set(seen_ids) == expected_ids, (
        f"missing: {expected_ids - set(seen_ids)!r}, "
        f"unexpected: {set(seen_ids) - expected_ids!r}"
    )


# ---------------------------------------------------------------------------
# GET /courses -- filters
# ---------------------------------------------------------------------------
def test_level_filter_is_case_insensitive(api_client, db_conn):
    known_level = db_conn.execute(
        "SELECT level FROM courses LIMIT 1"
    ).fetchone()["level"]

    resp_exact = api_client.get(
        "/courses", params={"level": known_level, "page_size": 1000}
    )
    resp_upper = api_client.get(
        "/courses", params={"level": known_level.upper(), "page_size": 1000}
    )
    resp_lower = api_client.get(
        "/courses", params={"level": known_level.lower(), "page_size": 1000}
    )
    assert resp_exact.status_code == resp_upper.status_code == resp_lower.status_code == 200
    assert resp_exact.json()["total"] > 0
    assert resp_upper.json()["total"] == resp_exact.json()["total"]
    assert resp_lower.json()["total"] == resp_exact.json()["total"]


def test_university_id_filter_is_case_insensitive(api_client, db_conn):
    known_uni = db_conn.execute(
        "SELECT university_id FROM courses LIMIT 1"
    ).fetchone()["university_id"]

    resp_exact = api_client.get(
        "/courses", params={"university_id": known_uni, "page_size": 1000}
    )
    resp_swapped = api_client.get(
        "/courses", params={"university_id": _swap_case(known_uni), "page_size": 1000}
    )
    assert resp_exact.json()["total"] > 0
    assert resp_swapped.json()["total"] == resp_exact.json()["total"]


def test_max_fee_filter_is_inclusive(api_client, db_conn):
    """DECISIONS.md D-13: a course exactly at max_fee is included."""
    boundary_fee = db_conn.execute(
        "SELECT fee_usd FROM courses ORDER BY fee_usd LIMIT 1"
    ).fetchone()["fee_usd"]

    resp = api_client.get("/courses", params={"max_fee": boundary_fee, "page_size": 1000})
    assert resp.status_code == 200
    fees = [item["fee_usd"] for item in resp.json()["items"]]
    assert boundary_fee in fees


def _swap_case(value: str) -> str:
    return value.swapcase()


# ---------------------------------------------------------------------------
# GET /courses/{course_id}
# ---------------------------------------------------------------------------
def test_get_existing_course_returns_200_with_record(api_client, db_conn):
    course_id = db_conn.execute("SELECT course_id FROM courses LIMIT 1").fetchone()["course_id"]
    resp = api_client.get(f"/courses/{course_id}")
    assert resp.status_code == 200
    assert resp.json()["course_id"] == course_id


def test_get_unknown_course_returns_404_with_error_body(api_client):
    resp = api_client.get("/courses/CRS-does-not-exist")
    assert resp.status_code == 404
    assert "error" in resp.json()


# ---------------------------------------------------------------------------
# POST /courses -- auth
# ---------------------------------------------------------------------------
def _new_course_payload(course_id="CRS-99001"):
    return {
        "course_id": course_id,
        "title": "Test Course",
        "university_id": "UNI-001",
        "level": "Master",
        "fee_usd": 1000.0,
        "intake_start": "2027-01-01",
        "intake_end": "2027-06-01",
        "delivery_mode": "Online",
        "last_updated": "2027-01-01",
    }


def test_post_missing_api_key_returns_401(api_client):
    resp = api_client.post("/courses", json=_new_course_payload())
    assert resp.status_code == 401


def test_post_wrong_api_key_returns_401(api_client):
    resp = api_client.post(
        "/courses", json=_new_course_payload(), headers={"X-API-Key": "wrong-key"}
    )
    assert resp.status_code == 401


def test_post_valid_request_returns_201(api_client, auth_headers):
    resp = api_client.post(
        "/courses", json=_new_course_payload(), headers=auth_headers
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# POST /courses -- validation and conflicts
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("missing_field", [
    "course_id", "title", "university_id", "level", "fee_usd",
    "intake_start", "intake_end", "delivery_mode", "last_updated",
])
def test_post_missing_required_field_returns_422(api_client, auth_headers, missing_field):
    payload = _new_course_payload(course_id="CRS-99002")
    del payload[missing_field]
    resp = api_client.post("/courses", json=payload, headers=auth_headers)
    assert resp.status_code == 422, (
        f"missing '{missing_field}' should be 422, got {resp.status_code}: {resp.text}"
    )


def test_post_duplicate_course_id_returns_409(api_client, auth_headers):
    payload = _new_course_payload(course_id="CRS-99003")
    first = api_client.post("/courses", json=payload, headers=auth_headers)
    assert first.status_code == 201

    second = api_client.post("/courses", json=payload, headers=auth_headers)
    assert second.status_code == 409
