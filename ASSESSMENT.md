# QA Automation Assessment — CourseFlow ETL Pipeline

**Format:** take-home | **Time budget:** Submit by 5PM Friday, 21 August 2026 | **Role:** QA Engineer (Automation)

## Scenario

You have joined the QA team for **CourseFlow**, a pipeline that aggregates
university course catalogs from two partner feeds (`courses_source_a.csv`,
`courses_source_b.json`), cleans and merges them per the business rules below,
loads them into a database, and serves them through a REST API.

The development team believes the pipeline is production-ready. **Your job is to
find out whether that's true.** You are not asked to fix any pipeline or API
code — a QA engineer's deliverable here is detection, evidence, and clear
reporting.

**Important:** your automated tests must assert the *specification* (the
business rules and API spec in this document), not the current behavior of the
code. If a well-written test fails, that may be a defect — investigate,
decide, and report. Failing tests that expose real defects are a success, not
a problem. Do not modify your assertions to make the suite pass against buggy
behavior.

## Ground rules

- **AI tools are allowed and encouraged** (ChatGPT, Claude, Copilot, etc.) —
  but you must keep a log (see Task 1) and you remain fully accountable for
  everything you submit. Expect to explain and modify any part of your work
  live in the review call.
- Work in a **git repository with incremental commits** as you go. A single
  bulk commit at the end is not acceptable.
- Keep a **`DECISIONS.md`** — whenever a rule is ambiguous, the docs and data
  disagree, or you make a judgment call, record it there. This file is scored.
- Python + Pytest is the expected stack for automation (matching the project),
  Postman/Newman is acceptable for the API task if you prefer it.

## Business Rules (transform specification)

The pipeline must apply these rules to every record from both sources:

- **BR-1** `course_id` is mandatory, format `CRS-<number>`, and unique in the
  target `courses` table.
- **BR-2** `title` is mandatory. Whitespace is normalized (trimmed, internal
  runs of spaces collapsed), and the **full title is preserved** in the target.
- **BR-3** `university_id` must exist in `universities.csv`. Records referring
  to an unknown university are rejected with reason `unknown_university` —
  this applies to **both sources**.
- **BR-4** `level` is mapped case-insensitively to one of
  `Bachelor | Master | PhD | Diploma` (accepted variants include
  `bachelors`, `bsc`, `masters`, `msc`, `doctorate`). Unmappable values are
  rejected with reason `invalid_level`.
- **BR-5** `delivery_mode` is normalized case-insensitively to
  `On-campus | Online | Hybrid`.
- **BR-6** `fee` is numeric; comma thousand-separators are allowed
  (`"15,000.00"` is valid). Fees are converted to USD using this fixed rate
  table and stored in `fee_usd` **rounded to 2 decimal places, preserving
  cents**:
  `USD 1.0 | AUD 0.65 | GBP 1.27 | EUR 1.08 | NPR 0.0075`.
- **BR-7** the fee must be a positive amount; invalid fees are rejected with
  reason `invalid_fee`.
- **BR-8** dates are accepted in ISO `YYYY-MM-DD` **or** `DD/MM/YYYY` format.
  `intake_end` must be after `intake_start`; violations are rejected with
  reason `invalid_intake_window`.
- **BR-9** `duration_months` is an integer between 1 and 72; anything else is
  rejected with reason `invalid_duration`.
- **BR-10** records are deduplicated by `course_id`, keeping the record with
  the **most recent `last_updated`**, across both sources.
- **BR-11** every rejected record must appear in the `rejects` table with its
  `course_id`, `source`, and reason. **No record may silently disappear**:
  for every input row, either it is loaded into `courses` (possibly losing a
  dedupe) or it appears in `rejects`.
- **BR-12** if a record includes an `application_deadline`, it must fall
  strictly before `intake_start`; violations are rejected with reason
  `invalid_deadline`.

## API Specification

Base URL: `http://127.0.0.1:8000` (run via `uvicorn api.main:app --port 8000`).

| Endpoint | Spec |
|---|---|
| `GET /health` | `200 {"status": "ok"}` |
| `GET /courses` | Paginated list. Query params: `page` (default 1), `page_size` (default 20), `level`, `university_id`, `max_fee`. `total_pages = ceil(total / page_size)`. **Every record must be reachable through pagination.** Filters are **case-insensitive**. A `page` outside `1..total_pages` returns `400`. |
| `GET /courses/{course_id}` | `200` with the record, or `404` with `{"error": ...}` if it does not exist. |
| `POST /courses` | Requires header `X-API-Key` (use `secret-key-123`). Missing **or** wrong key → `401`. Valid request → `201`. Missing/invalid required fields → `422`. Duplicate `course_id` → `409`. Required fields: `course_id, title, university_id, level, fee_usd, intake_start, intake_end, delivery_mode, last_updated`. |

---

## Your Tasks

### Task 1 — Test design, with AI assistance (~2h)

Produce a test-case catalog for the business rules (BR-1 … BR-12): positive,
negative, and boundary cases, each with id, rule reference, input, expected
result, and priority.

You are **explicitly encouraged to use an AI assistant** for this task, and we
evaluate *how* you use it. Submit in `docs/`:

1. `ai-log.md` — the actual prompts you used and the raw AI output (paste or
   screenshot).
2. A short written **critique**: what the AI got wrong, missed, invented, or
   over-generalized, and what you changed and why.
3. `test-cases.md` — your final, corrected test-case catalog.

### Task 2 — Data validation suite with Pytest (~4h)

Automate validation of the pipeline output (`data/courses.db`) against the raw
sources and the business rules. Your suite should cover at minimum:

- schema and mandatory-field checks on the target table;
- **row-count reconciliation**: every source row accounted for (BR-11);
- deduplication correctness (BR-10);
- transformation rules: fee conversion (BR-6), level/delivery normalization
  (BR-4/5), date validation (BR-8), duration bounds (BR-9);
- referential integrity (BR-3);
- rejects table correctness (right rows, right reasons).

Structure it as a real suite: fixtures, parametrization where it helps, clear
test names, deterministic runs.

### Task 3 — SQL validation (~1.5h)

In `sql/validation_queries.sql` (or pytest-wrapped, your choice), write SQL
against `data/courses.db` that finds:

1. duplicate `course_id`s (should be none);
2. courses referencing universities that don't exist;
3. fee anomalies (non-positive, NULL, or suspiciously round-tripped values);
4. intake-date anomalies;
5. an aggregate reconciliation: per source, `loaded + rejected` vs. raw input
   counts.

Comment each query with what it checks and what a non-empty result means.

### Task 4 — API test automation (~3h)

An automated suite (Pytest + requests/httpx, or Postman collection + Newman)
covering the API specification: status codes, auth behavior, response
contract, pagination correctness (including the **last** page), filter
behavior, and negative cases. Include at least one test proving every loaded
record is reachable through pagination.

### Task 5 — CI + reporting (~1.5h)

1. A **GitHub Actions workflow** (or, if you prefer, a `run_tests.sh`) that:
   installs dependencies, runs the pipeline, starts the API, runs your full
   suite, and publishes a JUnit XML and/or HTML report as an artifact.
2. **`DEFECTS.md`** — a Jira-style defect report for every issue you found:
   id, title, severity, affected component, steps to reproduce, expected vs.
   actual, and which of your automated tests demonstrates it.

---

## Submission checklist

- [ ] Git repository (GitHub link or zip **including `.git/`**) with incremental commits
- [ ] `tests/` — data validation + API suites (Task 2, 4)
- [ ] `sql/validation_queries.sql` (Task 3)
- [ ] `docs/test-cases.md` + `docs/ai-log.md` + AI critique (Task 1)
- [ ] `DEFECTS.md` (Task 5)
- [ ] `DECISIONS.md` — assumptions and judgment calls
- [ ] CI workflow or `run_tests.sh` + a sample test report (Task 5)
- [ ] `README.md` — exactly how to run your suite from a clean checkout

After submission there will be a ~45-minute review call where you will walk
through your work, modify a test live against a small requirement change, and
analyze a new data sample.
