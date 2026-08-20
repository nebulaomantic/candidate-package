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








## Critique

I read each and every row in AI's table one at a time and checked each one against
the actual spec text. The easy cases (
valid input, invalid input) were fine. The problems showed up in the
trickier cases where the AI guessed instead of checking, or copied
a pattern from one rule onto the another rule what it didn't actually apply.
Here's what I found and fixed in `docs/test-cases.md`.

**TC-053's row-count check doesn't actually prove anything.** It says
`loaded + rejected >= raw input count`. But `>=` would still pass even if
some rows quietly went missing and BR-11 says that's exactly what must
never happen. So I made it a strict `==` check instead. While looking at
this, I also noticed a real question the spec never answers: when two
duplicate rows get deduped, what happens to the one that loses? It's not
loaded, and the spec doesn't say it goes into `rejects` either. I didn't
want to just guess, so I wrote this open question down in `DECISIONS.md`.

**TC-038 tested the wrong date.** It used `10/01/2026` and called it safe
either way you read it. That's actually not true — 10 is a valid month
(October), so this date has two valid readings too: 10 January 2026
day-first, or 1 October 2026 if misread month-first. Both parse fine, they
just disagree. (I caught myself making the same mistake the AI made here —
assuming "10 looks like a day" without checking that 10 is also a legal
month number.) The real risk with BR-8 is any date where both numbers are
12 or under, like `03/04/2026` — reading it the wrong way still gives a
valid-looking date, just the wrong one, and nothing errors to warn you. A
genuinely safe, unambiguous test date needs a number over 12 in one slot,
like `25/01/2026` — 25 can't be a month, so a parser reading the format
wrong would fail loudly instead of quietly returning the wrong date. I
fixed TC-039 in `test-cases.md` to use `25/01/2026` for the unambiguous
case, and kept `03/04/2026` (TC-040) as the genuinely risky one.

**TC-042 made up an error reason.** It said a broken date like
`2026-13-01` gets rejected with `invalid_intake_window`. But the spec only
defines that reason for when `intake_end` isn't after `intake_start` — it
says nothing about a date that's simply broken and can't be read at all.
The AI seems to have reused the nearest-sounding reason instead of checking
if it actually fits. I changed the expected result to just "rejected"
without naming a reason, and flagged it as something to confirm against the
real pipeline.

**Two cases assumed "reject" without the spec saying so.** One is an
unrecognized `delivery_mode` like `"remote"` (BR-5 never defines a reject
reason for this at all). The other is a currency not in the conversion
table, like `JPY` (BR-6's rate table just stops, with no stated fallback).
I think the AI assumed "reject" here because every other rule in the doc
rejects bad input, so it pattern-matched instead of noticing these two
rules don't actually say that. I kept both cases but reworded them to say
this needs to be checked against real behavior, not assumed.

**One priority was set too low.** TC-030, about fee rounding at a tricky
boundary (like `.xx5`), was marked Medium. A rounding mistake is a money
mistake, so I bumped it to High — it doesn't matter that the input is a
narrow edge case, the consequence still matters.

**A rule wasn't tested from enough angles.** BR-1 (unique `course_id`) only
had one case, and that case was really about the dedupe logic in BR-10
(same course, updated later). It never tested a plain accidental
collision — two unrelated rows that happen to share an id by mistake, with
no update involved. I added that as its own case.

**A couple of API cases stopped one step too early.** For a successful
`POST /courses`, the AI checked the status code and that the record could
be fetched afterward, but never checked what the response body itself
contained. If the API is supposed to hand back the created record, that
should be checked directly. Separately, the only "missing field" test for
`422` was for a field that's absent — I added a second case for a field
that's present but the wrong type (like text where a number is expected),
since those can be handled by different code paths. Same idea for
`GET /courses/{course_id}`: the only "not found" case used a well-formed id
that simply doesn't exist. I added a second case for an id that's just
badly formed, since that's a different kind of "not found."

**Priority levels felt like defaults, not decisions.** A lot of the
High/Medium/Low picks looked automatic rather than reasoned. I redid them
based on how bad it would be if that case failed: anything touching data
correctness or money (BR-1, BR-6, BR-7, BR-10, BR-11) stays High even for
its edge cases, because a failure there can quietly corrupt the whole
dataset, not just one row.

The final, corrected list of test cases is in `docs/test-cases.md`.
