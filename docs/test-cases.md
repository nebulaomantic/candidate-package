# Test-Case Catalog — CourseFlow ETL Pipeline & API

This is the cleaned-up version of the table I had the AI draft — see
[`ai-log.md`](ai-log.md) for the original output and my line-by-line critique
of it. A handful of cases below carry a ⚠ because the spec genuinely doesn't
say what should happen; I didn't want to just guess an expected result and
call it done, so those are also written up in [`../DECISIONS.md`](../DECISIONS.md)
and should be checked against actual pipeline behavior before treating a
failure as a defect.

| id | rule | input | expected result | priority |
|---|---|---|---|---|
| TC-001 | BR-1 | `course_id = "CRS-1001"` | Accepted; loaded into `courses` | High |
| TC-002 | BR-1 | `course_id` missing/empty | Rejected (mandatory field) | High |
| TC-003 | BR-1 | `course_id = "1001"` (no `CRS-` prefix) | Rejected (invalid format) | High |
| TC-004 | BR-1 | `course_id = "COURSE-1001"` (wrong prefix) | Rejected (invalid format) | Medium |
| TC-005 | BR-1 | `course_id = "CRS-0001"` (leading zeros) | Accepted; stored as-is | Low |
| TC-006 | BR-1 | Same `course_id` in two rows with different `last_updated` (true update) | Exactly one row survives in `courses`, resolved by BR-10 recency | High |
| TC-007 | BR-1 | Same `course_id` on two otherwise-unrelated rows (different titles/fees, not a real update) | Still resolved as a uniqueness conflict via BR-10; losing row has to be accounted for per BR-11 — not sure yet if that means a reject reason or something else, worth checking | High |
| TC-008 | BR-2 | `title = "  Intro   to   AI  "` | Normalized to `"Intro to AI"` (trimmed, internal spaces collapsed) | High |
| TC-009 | BR-2 | `title` missing or empty string | Rejected (mandatory field) | High |
| TC-010 | BR-2 | `title = "   "` (whitespace only) | Treated as empty; rejected | Medium |
| TC-011 | BR-2 | Long title (e.g. 300 chars) with irregular spacing | Full title preserved after normalization, no truncation | Medium |
| TC-012 | BR-3 | `university_id` present in `universities.csv` | Accepted | High |
| TC-013 | BR-3 | `university_id` unknown, source A | Rejected, reason `unknown_university` | High |
| TC-014 | BR-3 | `university_id` unknown, source B | Rejected, reason `unknown_university` | High |
| TC-015 | BR-3 | `university_id` empty/null | Rejected — but is the reason `unknown_university`, or does an empty value get its own mandatory-field reason? Spec doesn't say, check it | Medium |
| TC-016 | BR-4 | `level = "bachelor"` / `"BACHELOR"` / `"Bachelor"` | Mapped to `Bachelor` (case-insensitive) | High |
| TC-017 | BR-4 | `level = "bsc"`, `"bachelors"` | Mapped to `Bachelor` | High |
| TC-018 | BR-4 | `level = "msc"`, `"masters"` | Mapped to `Master` | High |
| TC-019 | BR-4 | `level = "doctorate"` | Mapped to `PhD` | High |
| TC-020 | BR-4 | `level = "diploma"` (any case) | Mapped to `Diploma` | Medium |
| TC-021 | BR-4 | `level = "undergraduate"` (unmappable) | Rejected, reason `invalid_level` | High |
| TC-022 | BR-4 | `level` missing/empty | Rejected, reason `invalid_level` | Medium |
| TC-023 | BR-5 | `delivery_mode = "online"` / `"ONLINE"` | Normalized to `Online` | High |
| TC-024 | BR-5 | `delivery_mode = "on-campus"` / `"On-Campus"` | Normalized to `On-campus` | High |
| TC-025 | BR-5 | `delivery_mode = "hybrid"` | Normalized to `Hybrid` | Medium |
| TC-026 | BR-5 | `delivery_mode = "remote"` (unrecognized) | Spec never says what happens here — don't assume rejection, go look at what the pipeline actually does | Medium |
| TC-027 | BR-6 | `fee = "15,000.00"`, currency `AUD` | `fee_usd = 9750.00` (15000 × 0.65) | High |
| TC-028 | BR-6 | `fee = "1200"`, currency `GBP` | `fee_usd = 1524.00` (1200 × 1.27) | High |
| TC-029 | BR-6 | `fee = "1000"`, currency `EUR` | `fee_usd = 1080.00` | High |
| TC-030 | BR-6 | `fee = "100000"`, currency `NPR` | `fee_usd = 750.00` (100000 × 0.0075) | High |
| TC-031 | BR-6 | Fee whose converted value lands exactly on a rounding boundary (e.g. raw `1234.565`) | Rounded to 2 decimals — need to confirm which way the pipeline rounds here, half-up and Python's default banker's rounding disagree at exactly `.xx5` | High |
| TC-032 | BR-6 | Currency code outside the rate table (e.g. `JPY`) | Not covered by the spec at all — check what actually happens instead of assuming a reject | Medium |
| TC-033 | BR-7 | `fee = 500` (positive) | Accepted | High |
| TC-034 | BR-7 | `fee = 0` | Rejected, reason `invalid_fee` | High |
| TC-035 | BR-7 | `fee = -50` | Rejected, reason `invalid_fee` | High |
| TC-036 | BR-7 | `fee = 0.01` (smallest positive) | Accepted (boundary) | Medium |
| TC-037 | BR-7 | `fee = "abc"` (non-numeric) | Rejected, reason `invalid_fee` | High |
| TC-038 | BR-8 | `intake_start = "2026-01-10"`, `intake_end = "2026-06-10"` (ISO) | Accepted | High |
| TC-039 | BR-8 | `intake_start = "25/01/2026"`, `intake_end = "25/06/2026"` (DD/MM/YYYY, unambiguous — day 25 can't be misread as a month) | Accepted, parsed day-first | High |
| TC-040 | BR-8 | `intake_start = "03/04/2026"` (DD/MM/YYYY, ambiguous — could misparse as month-first) | Parsed as 3 April 2026, not 4 March 2026 | High |
| TC-041 | BR-8 | `intake_end` before `intake_start` | Rejected, reason `invalid_intake_window` | High |
| TC-042 | BR-8 | `intake_end == intake_start` (same day) | Rejected, reason `invalid_intake_window` (must be strictly after) | High |
| TC-043 | BR-8 | `intake_end = intake_start + 1 day` | Accepted (boundary — minimum valid gap) | Medium |
| TC-044 | BR-8 | `intake_start = "2026-13-01"` (unparseable date) | Should be rejected, but don't assume the reason is `invalid_intake_window` — that name is only defined for the ordering rule, not a parse failure | Medium |
| TC-045 | BR-9 | `duration_months = 1` | Accepted (lower boundary) | High |
| TC-046 | BR-9 | `duration_months = 72` | Accepted (upper boundary) | High |
| TC-047 | BR-9 | `duration_months = 0` | Rejected, reason `invalid_duration` | High |
| TC-048 | BR-9 | `duration_months = 73` | Rejected, reason `invalid_duration` | High |
| TC-049 | BR-9 | `duration_months = -5` | Rejected, reason `invalid_duration` | Medium |
| TC-050 | BR-9 | `duration_months = 12.5` (non-integer) | Rejected, reason `invalid_duration` | Medium |
| TC-051 | BR-9 | `duration_months = "twelve"` (non-numeric) | Rejected, reason `invalid_duration` | Medium |
| TC-052 | BR-10 | Same `course_id` in both sources, different `last_updated` | Row with the more recent `last_updated` is kept | High |
| TC-053 | BR-10 | Same `course_id`, identical `last_updated` timestamp | Whatever it does, it should do the same thing every run — spec doesn't define a tie-break, so I'm testing determinism rather than a specific winner; exactly one row survives | High |
| TC-054 | BR-10 | Same `course_id` appears 3+ times across sources | Only the single most-recent record survives | Medium |
| TC-055 | BR-11 | Full run of both source files | Per source: `count(loaded) + count(rejected) == count(raw input rows)` exactly (not `>=`) | High |
| TC-056 | BR-11 | The "losing" row of a BR-10 dedup pair | This is the one I'd push back on in review — either it shows up in `rejects` with a reason, or the reconciliation math needs a third bucket for "superseded." Haven't seen the code, so not assuming an answer here | High |
| TC-057 | BR-11 | A row rejected by BR-3 (`unknown_university`) | Appears in `rejects` with correct `course_id`, `source`, and reason | High |
| TC-058 | BR-11 | A row that fails multiple rules at once (e.g. invalid level *and* invalid fee) | Appears exactly once in `rejects` with one reason — not asserting which reason wins unless the pipeline's check order turns out to be fixed and documented | Medium |
| TC-059 | BR-12 | `application_deadline` two days before `intake_start` | Accepted | High |
| TC-060 | BR-12 | `application_deadline == intake_start` | Rejected, reason `invalid_deadline` (must be strictly before) | High |
| TC-061 | BR-12 | `application_deadline` after `intake_start` | Rejected, reason `invalid_deadline` | High |
| TC-062 | BR-12 | `application_deadline` one day before `intake_start` | Accepted (boundary — minimum valid gap) | Medium |
| TC-063 | BR-12 | `application_deadline` absent/null | Rule not evaluated; record proceeds through other checks | Medium |
| TC-064 | API `GET /health` | No params | `200 {"status": "ok"}` | High |
| TC-065 | API `GET /courses` | No params (defaults) | `200`, `page=1`, `page_size=20`, `total_pages = ceil(total/20)` | High |
| TC-066 | API `GET /courses` | `page = total_pages` (last page) | `200`; returns the remainder (`total % page_size`, or a full page if evenly divisible); every record reachable across all pages combined | High |
| TC-067 | API `GET /courses` | `page = total_pages + 1` | `400` | High |
| TC-068 | API `GET /courses` | `page = 0` or negative | `400` | Medium |
| TC-069 | API `GET /courses` | `level = "BACHELOR"` (mixed/upper case) | `200`, filtered case-insensitively, identical result set to `level=bachelor` | High |
| TC-070 | API `GET /courses` | `university_id` = known id | `200`, only matching records returned | Medium |
| TC-071 | API `GET /courses` | `max_fee` = exactly a record's `fee_usd` | `200`; going with inclusive (`<=`) as the natural reading of "max," record should be included — flag it if the API disagrees | Medium |
| TC-072 | API `GET /courses/{course_id}` | Existing, well-formed `course_id` | `200` with the full matching record | High |
| TC-073 | API `GET /courses/{course_id}` | Well-formed but non-existent `course_id` | `404 {"error": ...}` | High |
| TC-074 | API `GET /courses/{course_id}` | Structurally invalid id (empty/malformed, not just "not found") | `404` (or documented alternative — distinct case from TC-073) | Low |
| TC-075 | API `POST /courses` | Valid body, no `X-API-Key` header | `401` | High |
| TC-076 | API `POST /courses` | Valid body, `X-API-Key: wrong-key` | `401` | High |
| TC-077 | API `POST /courses` | Valid body, correct key `secret-key-123` | `201`; response body reflects the created resource; record retrievable via subsequent GET | High |
| TC-078 | API `POST /courses` | Correct key, missing a required field (e.g. no `title`) | `422` | High |
| TC-079 | API `POST /courses` | Correct key, required field present with wrong type (e.g. `fee_usd: "abc"`) | `422` | Medium |
| TC-080 | API `POST /courses` | Correct key, `course_id` already exists | `409` | High |
