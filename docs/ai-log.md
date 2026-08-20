# AI Log

## Prompt 1

> Read the business rules (BR-1 to BR-12) and API table from assessment.md and
> write a test-case table with columns: id, rule, input, expected result,
> priority — covering positive, negative, and boundary cases.

## Raw AI Output

| id | rule | input | expected result | priority |
|---|---|---|---|---|
| TC-001 | BR-1 | `course_id = "CRS-1001"` | Accepted; loaded into `courses` | High |
| TC-002 | BR-1 | `course_id` missing/empty | Rejected (mandatory field) | High |
| TC-003 | BR-1 | `course_id = "1001"` (wrong format, no prefix) | Rejected (invalid format) | High |
| TC-004 | BR-1 | `course_id = "COURSE-1001"` (wrong prefix) | Rejected (invalid format) | Medium |
| TC-005 | BR-1 | `course_id = "CRS-0001"` (leading zeros) | Accepted; stored as-is | Low |
| TC-006 | BR-1 | Two input rows share the same `course_id` (from either/both sources) | Only one row present in `courses`; resolved per BR-10, not silently duplicated | High |
| TC-007 | BR-2 | `title = "  Intro   to   AI  "` | Normalized to `"Intro to AI"` (trimmed, internal spaces collapsed) | High |
| TC-008 | BR-2 | `title` missing or empty string | Rejected (mandatory field) | High |
| TC-009 | BR-2 | `title = "   "` (whitespace only) | Treated as empty/missing; rejected | Medium |
| TC-010 | BR-2 | Very long title (e.g. 300 chars) with mixed spacing | Full title preserved after whitespace normalization, no truncation | Medium |
| TC-011 | BR-3 | `university_id` present in `universities.csv` | Accepted | High |
| TC-012 | BR-3 | `university_id` not present in `universities.csv`, source A | Rejected, reason `unknown_university` | High |
| TC-013 | BR-3 | `university_id` not present in `universities.csv`, source B | Rejected, reason `unknown_university` | High |
| TC-014 | BR-3 | `university_id` empty/null | Rejected, reason `unknown_university` (or mandatory-field reason — confirm in DECISIONS.md) | Medium |
| TC-015 | BR-4 | `level = "bachelor"` / `"BACHELOR"` / `"Bachelor"` | Mapped to `Bachelor` (case-insensitive) | High |
| TC-016 | BR-4 | `level = "bsc"`, `"bachelors"` | Mapped to `Bachelor` | High |
| TC-017 | BR-4 | `level = "msc"`, `"masters"` | Mapped to `Master` | High |
| TC-018 | BR-4 | `level = "doctorate"` | Mapped to `PhD` | High |
| TC-019 | BR-4 | `level = "diploma"` (any case) | Mapped to `Diploma` | Medium |
| TC-020 | BR-4 | `level = "undergraduate"` (unmappable) | Rejected, reason `invalid_level` | High |
| TC-021 | BR-4 | `level` missing/empty | Rejected, reason `invalid_level` | Medium |
| TC-022 | BR-5 | `delivery_mode = "online"` / `"ONLINE"` | Normalized to `Online` | High |
| TC-023 | BR-5 | `delivery_mode = "on-campus"` / `"On-Campus"` | Normalized to `On-campus` | High |
| TC-024 | BR-5 | `delivery_mode = "hybrid"` | Normalized to `Hybrid` | Medium |
| TC-025 | BR-5 | `delivery_mode = "remote"` (unrecognized) | Behavior undefined by spec — flag as ambiguity; expect rejection or defined fallback | Medium |
| TC-026 | BR-6 | `fee = "15,000.00"`, currency `AUD` | Converted: `15000.00 * 0.65 = 9750.00` → `fee_usd = 9750.00` | High |
| TC-027 | BR-6 | `fee = "1200"`, currency `GBP` | `fee_usd = 1524.00` (1200 * 1.27) | High |
| TC-028 | BR-6 | `fee = "1000"`, currency `EUR` | `fee_usd = 1080.00` | High |
| TC-029 | BR-6 | `fee = "100000"`, currency `NPR` | `fee_usd = 750.00` (100000 * 0.0075) | High |
| TC-030 | BR-6 | `fee` value producing 3rd-decimal rounding (e.g. `fee_usd` raw = `1234.565`) | Rounded to 2 decimals per standard rounding (verify half-up vs banker's rounding — DECISIONS.md) | Medium |
| TC-031 | BR-6 | Currency code not in rate table (e.g. `JPY`) | Rejected or flagged — behavior undefined by spec; note as ambiguity | Medium |
| TC-032 | BR-7 | `fee = 500` (positive) | Accepted | High |
| TC-033 | BR-7 | `fee = 0` | Rejected, reason `invalid_fee` | High |
| TC-034 | BR-7 | `fee = -50` | Rejected, reason `invalid_fee` | High |
| TC-035 | BR-7 | `fee = 0.01` (smallest positive) | Accepted (boundary) | Medium |
| TC-036 | BR-7 | `fee = "abc"` (non-numeric) | Rejected, reason `invalid_fee` | High |
| TC-037 | BR-8 | `intake_start = "2026-01-10"`, `intake_end = "2026-06-10"` (ISO) | Accepted | High |
| TC-038 | BR-8 | `intake_start = "10/01/2026"`, `intake_end = "10/06/2026"` (DD/MM/YYYY) | Accepted, parsed correctly (not misread as MM/DD) | High |
| TC-039 | BR-8 | `intake_end` before `intake_start` | Rejected, reason `invalid_intake_window` | High |
| TC-040 | BR-8 | `intake_end == intake_start` (same day) | Rejected, reason `invalid_intake_window` (must be strictly after) | High |
| TC-041 | BR-8 | `intake_end = intake_start + 1 day` | Accepted (boundary — minimum valid gap) | Medium |
| TC-042 | BR-8 | `intake_start = "2026-13-01"` (malformed/invalid date) | Rejected, reason `invalid_intake_window` (or dedicated parse-error reason) | Medium |
| TC-043 | BR-9 | `duration_months = 1` | Accepted (lower boundary) | High |
| TC-044 | BR-9 | `duration_months = 72` | Accepted (upper boundary) | High |
| TC-045 | BR-9 | `duration_months = 0` | Rejected, reason `invalid_duration` | High |
| TC-046 | BR-9 | `duration_months = 73` | Rejected, reason `invalid_duration` | High |
| TC-047 | BR-9 | `duration_months = -5` | Rejected, reason `invalid_duration` | Medium |
| TC-048 | BR-9 | `duration_months = 12.5` (non-integer) | Rejected, reason `invalid_duration` | Medium |
| TC-049 | BR-9 | `duration_months = "twelve"` (non-numeric) | Rejected, reason `invalid_duration` | Medium |
| TC-050 | BR-10 | Same `course_id` in both sources with different `last_updated` | Row with the more recent `last_updated` is kept; the other does not appear as a silent loss | High |
| TC-051 | BR-10 | Same `course_id`, identical `last_updated` timestamp | Deterministic tie-break applied (document choice in DECISIONS.md); exactly one row kept | Medium |
| TC-052 | BR-10 | Duplicate `course_id` values appear 3+ times across sources | Only the single most-recent record survives; others accounted for | Medium |
| TC-053 | BR-11 | Full run of `courses_source_a.csv` + `courses_source_b.json` | `count(courses) + count(rejects) >= input row count` for every source, honoring dedupe from BR-10 | High |
| TC-054 | BR-11 | A row rejected by BR-3 (`unknown_university`) | Appears in `rejects` with correct `course_id`, `source`, and reason | High |
| TC-055 | BR-11 | A row that fails multiple rules at once (e.g. bad level AND bad fee) | Appears exactly once in `rejects` with one (primary/first-detected) reason — confirm precedence order in DECISIONS.md | Medium |
| TC-056 | BR-12 | `application_deadline` two days before `intake_start` | Accepted | High |
| TC-057 | BR-12 | `application_deadline == intake_start` | Rejected, reason `invalid_deadline` (must be strictly before) | High |
| TC-058 | BR-12 | `application_deadline` after `intake_start` | Rejected, reason `invalid_deadline` | High |
| TC-059 | BR-12 | `application_deadline` one day before `intake_start` | Accepted (boundary — minimum valid gap) | Medium |
| TC-060 | BR-12 | `application_deadline` absent/null | Not evaluated by this rule; record proceeds through other checks | Medium |
| TC-061 | API `GET /health` | No params | `200 {"status": "ok"}` | High |
| TC-062 | API `GET /courses` | No params (defaults) | `200`, `page=1`, `page_size=20`, correct `total_pages = ceil(total/20)` | High |
| TC-063 | API `GET /courses` | `page` = `total_pages` (last page) | `200`, returns remainder records (`total % page_size`, or full page if evenly divisible); every record reachable across all pages | High |
| TC-064 | API `GET /courses` | `page = total_pages + 1` | `400` | High |
| TC-065 | API `GET /courses` | `page = 0` or negative | `400` | Medium |
| TC-066 | API `GET /courses` | `level = "BACHELOR"` (mixed/upper case) | `200`, filtered case-insensitively, same result as `"bachelor"` | High |
| TC-067 | API `GET /courses` | `university_id` = known id | `200`, only matching records returned | Medium |
| TC-068 | API `GET /courses` | `max_fee` = boundary value equal to a record's `fee_usd` | `200`, record with `fee_usd == max_fee` included (inclusive boundary — confirm in DECISIONS.md) | Medium |
| TC-069 | API `GET /courses/{course_id}` | Existing `course_id` | `200` with full matching record | High |
| TC-070 | API `GET /courses/{course_id}` | Non-existent `course_id` | `404 {"error": ...}` | High |
| TC-071 | API `POST /courses` | Valid body, no `X-API-Key` header | `401` | High |
| TC-072 | API `POST /courses` | Valid body, `X-API-Key: wrong-key` | `401` | High |
| TC-073 | API `POST /courses` | Valid body, correct key `secret-key-123` | `201`, record created and retrievable via GET | High |
| TC-074 | API `POST /courses` | Correct key, missing required field (e.g. no `title`) | `422` | High |
| TC-075 | API `POST /courses` | Correct key, `course_id` already exists | `409` | High |

---

*Note: this table is the raw AI output for Task 1.*
