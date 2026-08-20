# Defect Report — CourseFlow ETL Pipeline

Found while automating Task 2 (`tests/`) against the business-rule spec in
[ASSESSMENT.md](ASSESSMENT.md). Each defect is reproducible against the
current `data/raw/*` sources and demonstrated by an automated test that
asserts the spec, not current behavior. See [DECISIONS.md](DECISIONS.md)
for the judgment calls behind a few of these (linked per item).

---

### DEFECT-01 — BR-3 unknown-university check only runs for source B rows, not source A

- **Severity:** Critical
- **Component:** `etl/transform.py`
- **Steps to reproduce:**
  1. Run `python etl/run_pipeline.py`.
  2. `SELECT c.course_id FROM courses c LEFT JOIN universities u ON c.university_id = u.university_id WHERE u.university_id IS NULL;`
- **Expected:** BR-3 — "Records referring to an unknown university are
  rejected with reason `unknown_university` — this applies to **both
  sources**." No loaded row should reference a nonexistent
  `university_id`.
- **Actual:** `transform.py` guards the check with
  `if row.get("_source") == "A" and university_id not in universities`, so
  source-B rows with an unknown university are never rejected — they load
  straight through. Reproduces with real data: `CRS-2011` and `CRS-2012`
  (both from `courses_source_b.json`) are loaded referencing a
  `university_id` absent from `universities.csv`.
- **Demonstrated by:** `tests/test_referential_integrity.py::test_every_loaded_course_references_a_known_university`, `::test_unknown_university_is_rejected_source_b`

---

### DEFECT-02 — BR-10 dedup keeps the *earliest* `last_updated`, not the most recent

- **Severity:** Critical
- **Component:** `etl/transform.py`
- **Steps to reproduce:**
  1. Run `python etl/run_pipeline.py`.
  2. Find a `course_id` with duplicate raw rows across sources, e.g.
     `CRS-1005`, and compare its raw `last_updated` values against the
     loaded row's `last_updated`.
- **Expected:** BR-10 — "records are deduplicated by `course_id`, keeping
  the record with the **most recent** `last_updated`, across both
  sources."
- **Actual:** `transform()` sorts valid records **ascending** by
  `last_updated` and keeps the first record seen per `course_id`
  (`if record["course_id"] not in deduped: deduped[...] = record`) — i.e.
  it keeps the *oldest* record, the exact opposite of the spec. Reproduces
  with real data: `CRS-1005` loads with `last_updated = 2026-04-09` even
  though a `2026-08-01` duplicate exists and should have won.
- **Demonstrated by:** `tests/test_dedup.py::test_dedup_keeps_most_recent_last_updated`

---

### DEFECT-03 — `course_id` format (`CRS-<number>`) is never validated

- **Severity:** Major
- **Component:** `etl/transform.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `course_id = "1001"` (no prefix) or `"COURSE-1001"` (wrong prefix); both
  are accepted and loaded as-is.
- **Expected:** BR-1 — `course_id` "format `CRS-<number>`" is a stated
  requirement; a malformed id should be rejected (see `docs/test-cases.md`
  TC-003/TC-004).
- **Actual:** The only check performed is `if not course_id: reject(...)`
  — there is no format/regex validation at all, so any non-empty string is
  accepted as a `course_id`.
- **Demonstrated by:** `tests/test_transform_rules.py::test_course_id_format[1001-False]`, `[COURSE-1001-False]`

---

### DEFECT-04 — `fee_usd` truncates cents instead of rounding to 2 decimal places

- **Severity:** Major (financial correctness)
- **Component:** `etl/transform.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `fee = "1234.56"`, `currency = "USD"`.
- **Expected:** BR-6 — fees are "stored in `fee_usd` **rounded to 2
  decimal places, preserving cents**." Expected `fee_usd = 1234.56`.
- **Actual:** `fee_usd = int(fee * FX_RATES_TO_USD[currency])` truncates to
  an integer, discarding cents entirely. Actual `fee_usd = 1234`. This
  affects every converted fee, not just edge cases — cents are lost
  system-wide, and rounding mode (half-up vs. banker's) is moot because
  cents never survive at all (see DECISIONS.md D-11 for the rounding-mode
  question this defect preempts).
- **Demonstrated by:** `tests/test_transform_rules.py::test_fee_conversion_to_usd[1234.56-USD-1234.56]`

---

### DEFECT-05 — BR-8: `DD/MM/YYYY` dates are not accepted at all

- **Severity:** Major
- **Component:** `etl/transform.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `intake_start = "25/01/2026"`, `intake_end = "25/06/2026"`.
- **Expected:** BR-8 — "dates are accepted in ISO `YYYY-MM-DD` **or**
  `DD/MM/YYYY` format."
- **Actual:** `parse_date()` only calls
  `datetime.strptime(value, "%Y-%m-%d")`; any `DD/MM/YYYY` value fails to
  parse and returns `None`. The row is then silently dropped (see
  DEFECT-06) rather than accepted.
- **Demonstrated by:** `tests/test_transform_rules.py::test_ddmmyyyy_dates_are_accepted`, `::test_ambiguous_ddmmyyyy_is_parsed_day_first`

---

### DEFECT-06 — Unparseable/invalid intake dates are silently dropped instead of rejected

- **Severity:** Critical (violates BR-11's no-silent-disappearance guarantee)
- **Component:** `etl/transform.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `intake_start = "not-a-date"`. The row is absent from both the returned
  `records` and `rejects` lists.
- **Expected:** BR-11 — "**No record may silently disappear**: for every
  input row, either it is loaded into `courses` (possibly losing a
  dedupe) or it appears in `rejects`." An unparseable date is not
  mentioned explicitly by BR-8, but BR-11 requires it be traceable
  somewhere (see DECISIONS.md D-06).
- **Actual:**
  ```python
  if intake_start is None or intake_end is None:
      continue          # <-- no reject() call; row vanishes from all output
  ```
  This is a genuine silent-disappearance bug, not just a missing reason
  code: the row is in neither `courses` nor `rejects`.
- **Demonstrated by:** `tests/test_transform_rules.py::test_unparseable_date_is_rejected_not_silently_dropped`

  Note: this same code path is also how DEFECT-05 (`DD/MM/YYYY`) manifests
  as a silent drop rather than a loud rejection — fixing BR-8 date parsing
  without also fixing this `continue` would still leave truly malformed
  dates disappearing silently.

---

### DEFECT-07 — BR-9: blank/`0` `duration_months` is treated as an optional null, not rejected

- **Severity:** Minor–Major (judgment call — see DECISIONS.md D-05)
- **Component:** `etl/transform.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `duration_months = ""` or `"0"`.
- **Expected:** BR-9 — "`duration_months` is an integer between 1 and 72;
  **anything else is rejected**." Read literally, a blank or `0` value is
  "anything else" and should be rejected with reason `invalid_duration`.
- **Actual:**
  ```python
  if not duration_raw or duration_raw == "0":
      duration = None      # accepted as "unknown", not rejected
  ```
  The row loads successfully with `duration_months = NULL` instead of
  being rejected. DECISIONS.md (D-05) records this as a deliberate stance
  taken against the literal spec text, not an oversight in the test
  suite — flagging here because a reasonable engineer could read BR-9 as
  making duration optional instead; worth confirming intent in review.
- **Demonstrated by:** `tests/test_transform_rules.py::test_duration_bounds[0-False]`, `::test_duration_is_mandatory_per_literal_spec_text`

---

### DEFECT-08 — BR-12 (`application_deadline`) is entirely unimplemented

- **Severity:** Major
- **Component:** `etl/transform.py`, `etl/extract.py`
- **Steps to reproduce:** Call `transform()` on a synthetic row with
  `application_deadline` equal to or after `intake_start`.
- **Expected:** BR-12 — "if a record includes an `application_deadline`,
  it must fall strictly before `intake_start`; violations are rejected
  with reason `invalid_deadline`."
- **Actual:** `application_deadline` is never read anywhere in
  `extract.py` or `transform.py`. There is no validation, no
  `invalid_deadline` reason code, and no column for it in the `courses`
  schema (`etl/load.py`) — the field is dropped on the floor regardless
  of its value.
- **Demonstrated by:** `tests/test_transform_rules.py::test_deadline_not_strictly_before_intake_start_is_rejected[2026-01-10]`, `[2026-01-15]`

---

## Summary

| ID | Rule | Severity | Test |
|---|---|---|---|
| DEFECT-01 | BR-3 | Critical | `test_referential_integrity.py` |
| DEFECT-02 | BR-10 | Critical | `test_dedup.py` |
| DEFECT-03 | BR-1 | Major | `test_transform_rules.py::test_course_id_format` |
| DEFECT-04 | BR-6 | Major | `test_transform_rules.py::test_fee_conversion_to_usd` |
| DEFECT-05 | BR-8 | Major | `test_transform_rules.py::test_ddmmyyyy_dates_are_accepted` |
| DEFECT-06 | BR-8 / BR-11 | Critical | `test_transform_rules.py::test_unparseable_date_is_rejected_not_silently_dropped` |
| DEFECT-07 | BR-9 | Minor–Major | `test_transform_rules.py::test_duration_bounds[0-False]` |
| DEFECT-08 | BR-12 | Major | `test_transform_rules.py::test_deadline_not_strictly_before_intake_start_is_rejected` |

API defects (Task 4) will be appended here once that suite is written.
