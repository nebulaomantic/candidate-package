"""Task 2 — transformation-rule unit tests, run directly against
`transform()` with synthetic rows.

These encode the positive/negative/boundary cases from
docs/test-cases.md (TC- ids referenced in comments) as executable
assertions of the *specification* in ASSESSMENT.md, independent of whatever
the current sample data happens to contain.
"""
import pytest

from transform import transform


@pytest.fixture()
def valid_uni_id(raw_universities):
    return next(iter(raw_universities))


@pytest.fixture()
def base_row(valid_uni_id):
    """A minimally valid row. Individual tests override just the field
    under test."""
    return {
        "course_id": "CRS-9001",
        "title": "Test Course",
        "university_id": valid_uni_id,
        "level": "Bachelor",
        "discipline": "Testing",
        "fee": "1000",
        "currency": "USD",
        "intake_start": "2026-01-10",
        "intake_end": "2026-06-10",
        "duration_months": "12",
        "delivery_mode": "Online",
        "url": "https://example.test/crs-9001",
        "last_updated": "2026-01-01",
        "_source": "A",
    }


def run(row, universities):
    valid, rejects = transform([row], universities)
    return (valid[0] if valid else None), (rejects[0] if rejects else None)


# --- BR-1 -------------------------------------------------------------------

@pytest.mark.parametrize("course_id, should_be_valid", [
    ("CRS-1001", True),       # TC-001
    ("", False),              # TC-002
    ("1001", False),          # TC-003 - missing CRS- prefix
    ("COURSE-1001", False),   # TC-004 - wrong prefix
    ("CRS-0001", True),       # TC-005 - leading zeros, still valid
])
def test_course_id_format(base_row, raw_universities, course_id, should_be_valid):
    base_row["course_id"] = course_id
    valid, rejected = run(base_row, raw_universities)
    if should_be_valid:
        assert valid is not None and rejected is None
    else:
        assert valid is None and rejected is not None


# --- BR-2 -------------------------------------------------------------------

def test_title_whitespace_is_normalized_and_preserved(base_row, raw_universities):
    base_row["title"] = "  Intro   to   AI  "  # TC-008
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None
    assert valid["title"] == "Intro to AI"


@pytest.mark.parametrize("title", ["", "   "])  # TC-009, TC-010
def test_missing_or_blank_title_is_rejected(base_row, raw_universities, title):
    base_row["title"] = title
    valid, rejected = run(base_row, raw_universities)
    assert valid is None and rejected is not None


def test_long_title_is_preserved_in_full(base_row, raw_universities):
    """BR-2: 'the full title is preserved in the target' — no truncation."""
    long_title = "Advanced " * 40 + "Studies"  # 300+ chars after normalizing
    base_row["title"] = long_title
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None
    assert valid["title"] == " ".join(long_title.split())
    assert len(valid["title"]) == len(" ".join(long_title.split()))


# --- BR-4 --------------------------------------------------------------------

@pytest.mark.parametrize("level, expected", [
    ("bachelor", "Bachelor"), ("BACHELOR", "Bachelor"), ("Bachelor", "Bachelor"),  # TC-016
    ("bsc", "Bachelor"), ("bachelors", "Bachelor"),                                # TC-017
    ("msc", "Master"), ("masters", "Master"),                                     # TC-018
    ("doctorate", "PhD"),                                                         # TC-019
    ("diploma", "Diploma"), ("DIPLOMA", "Diploma"),                               # TC-020
])
def test_level_is_mapped_case_insensitively(base_row, raw_universities, level, expected):
    base_row["level"] = level
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None, rejected
    assert valid["level"] == expected


@pytest.mark.parametrize("level", ["undergraduate", "", "xyz"])  # TC-021, TC-022
def test_unmappable_level_is_rejected(base_row, raw_universities, level):
    base_row["level"] = level
    valid, rejected = run(base_row, raw_universities)
    assert valid is None
    assert rejected["reason"] == "invalid_level"


# --- BR-5 --------------------------------------------------------------------

@pytest.mark.parametrize("mode, expected", [
    ("online", "Online"), ("ONLINE", "Online"),        # TC-023
    ("on-campus", "On-campus"), ("On-Campus", "On-campus"),  # TC-024
    ("hybrid", "Hybrid"), ("HYBRID", "Hybrid"),         # TC-025
])
def test_delivery_mode_is_normalized_case_insensitively(base_row, raw_universities, mode, expected):
    base_row["delivery_mode"] = mode
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None, rejected
    assert valid["delivery_mode"] == expected


# --- BR-6 --------------------------------------------------------------------

@pytest.mark.parametrize("fee, currency, expected_fee_usd", [
    ("15,000.00", "AUD", 9750.00),   # TC-027 - comma thousand separator
    ("1200", "GBP", 1524.00),        # TC-028
    ("1000", "EUR", 1080.00),        # TC-029
    ("100000", "NPR", 750.00),       # TC-030
    ("1234.56", "USD", 1234.56),     # cents must be preserved, not truncated
])
def test_fee_conversion_to_usd(base_row, raw_universities, fee, currency, expected_fee_usd):
    base_row["fee"] = fee
    base_row["currency"] = currency
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None, rejected
    assert valid["fee_usd"] == pytest.approx(expected_fee_usd, abs=0.001)


# --- BR-7 --------------------------------------------------------------------

@pytest.mark.parametrize("fee, should_be_valid", [
    ("500", True),    # TC-033
    ("0", False),     # TC-034
    ("-50", False),   # TC-035
    ("0.01", True),   # TC-036 - smallest positive
    ("abc", False),   # TC-037
])
def test_fee_must_be_positive(base_row, raw_universities, fee, should_be_valid):
    base_row["fee"] = fee
    valid, rejected = run(base_row, raw_universities)
    if should_be_valid:
        assert rejected is None, rejected
    else:
        assert rejected is not None and rejected["reason"] == "invalid_fee"


# --- BR-8 --------------------------------------------------------------------

def test_iso_dates_are_accepted(base_row, raw_universities):
    base_row["intake_start"] = "2026-01-10"  # TC-038
    base_row["intake_end"] = "2026-06-10"
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None
    assert valid is not None


def test_ddmmyyyy_dates_are_accepted(base_row, raw_universities):
    """BR-8: 'dates are accepted in ISO YYYY-MM-DD or DD/MM/YYYY format'."""
    base_row["intake_start"] = "25/01/2026"  # TC-039
    base_row["intake_end"] = "25/06/2026"
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None, rejected
    assert valid is not None, "row was silently dropped instead of being accepted (BR-8 DD/MM/YYYY support)"


def test_ambiguous_ddmmyyyy_is_parsed_day_first(base_row, raw_universities):
    base_row["intake_start"] = "03/04/2026"  # TC-040 - 3 April, not 4 March
    base_row["intake_end"] = "03/05/2026"
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None, rejected
    assert valid is not None, "row was silently dropped instead of being accepted (BR-8 DD/MM/YYYY support)"
    assert valid["intake_start"] == "2026-04-03"


@pytest.mark.parametrize("start, end", [
    ("2026-06-10", "2026-01-10"),  # TC-041 - end before start
    ("2026-01-10", "2026-01-10"),  # TC-042 - equal, must be strictly after
])
def test_intake_window_ordering_is_enforced(base_row, raw_universities, start, end):
    base_row["intake_start"] = start
    base_row["intake_end"] = end
    valid, rejected = run(base_row, raw_universities)
    assert valid is None
    assert rejected["reason"] == "invalid_intake_window"


def test_intake_window_minimum_gap_is_accepted(base_row, raw_universities):
    base_row["intake_start"] = "2026-01-10"  # TC-043
    base_row["intake_end"] = "2026-01-11"
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None
    assert valid is not None


def test_unparseable_date_is_rejected_not_silently_dropped(base_row, raw_universities):
    """BR-11: 'no record may silently disappear'. An unparseable date must
    still surface as a reject with a reason, not vanish (DECISIONS.md D-06)."""
    base_row["intake_start"] = "not-a-date"  # TC-044
    valid, rejects = transform([base_row], raw_universities)
    assert valid == []
    assert rejects != [], "row was silently dropped instead of appearing in rejects"


# --- BR-9 --------------------------------------------------------------------

@pytest.mark.parametrize("duration, should_be_valid", [
    (1, True),     # TC-045 - lower boundary
    (72, True),    # TC-046 - upper boundary
    (0, False),    # TC-047
    (73, False),   # TC-048
    (-5, False),   # TC-049
])
def test_duration_bounds(base_row, raw_universities, duration, should_be_valid):
    base_row["duration_months"] = str(duration)
    valid, rejected = run(base_row, raw_universities)
    if should_be_valid:
        assert rejected is None, rejected
        assert valid["duration_months"] == duration
    else:
        assert rejected is not None and rejected["reason"] == "invalid_duration"


@pytest.mark.parametrize("duration", ["12.5", "twelve"])  # TC-050, TC-051
def test_duration_non_integer_is_rejected(base_row, raw_universities, duration):
    base_row["duration_months"] = duration
    valid, rejected = run(base_row, raw_universities)
    assert rejected is not None and rejected["reason"] == "invalid_duration"


def test_duration_is_mandatory_per_literal_spec_text(base_row, raw_universities):
    """BR-9 reads 'an integer between 1 and 72 ... anything else is
    rejected' as mandatory. Flagged as a known defect if this fails —
    see DECISIONS.md D-05."""
    base_row["duration_months"] = ""
    valid, rejected = run(base_row, raw_universities)
    assert rejected is not None and rejected["reason"] == "invalid_duration"


# --- BR-12 -------------------------------------------------------------------

def test_deadline_strictly_before_intake_start_is_accepted(base_row, raw_universities):
    base_row["application_deadline"] = "2026-01-05"  # TC-059, intake_start=2026-01-10
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None


@pytest.mark.parametrize("deadline", ["2026-01-10", "2026-01-15"])  # TC-060, TC-061
def test_deadline_not_strictly_before_intake_start_is_rejected(base_row, raw_universities, deadline):
    base_row["application_deadline"] = deadline
    valid, rejected = run(base_row, raw_universities)
    assert rejected is not None and rejected["reason"] == "invalid_deadline"


def test_deadline_one_day_before_is_accepted(base_row, raw_universities):
    base_row["application_deadline"] = "2026-01-09"  # TC-062, minimum valid gap
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None


def test_absent_deadline_does_not_block_the_record(base_row, raw_universities):
    base_row.pop("application_deadline", None)  # TC-063
    valid, rejected = run(base_row, raw_universities)
    assert rejected is None
