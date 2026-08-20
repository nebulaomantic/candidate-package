-- ============================================================================
-- Task 3 — SQL validation queries against data/courses.db
--
-- Run with: sqlite3 data/courses.db < sql/validation_queries.sql
-- or paste individual queries into any SQLite client.
--
-- For every query below: a NON-EMPTY result is a finding to investigate
-- (in several cases below, a known defect from DEFECTS.md). An empty result
-- means that particular check found no anomalies.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Duplicate course_id — should be none.
--
-- courses.course_id is the PRIMARY KEY, so SQLite itself already prevents
-- duplicates from being inserted. This query is a defence-in-depth check
-- (e.g. against a schema change, or if this is ever run on a raw staging
-- table before the PK is enforced) and also doubles as evidence that BR-10
-- dedup produced at most one surviving row per course_id.
-- ----------------------------------------------------------------------------
SELECT course_id, COUNT(*) AS n
FROM courses
GROUP BY course_id
HAVING COUNT(*) > 1;


-- ----------------------------------------------------------------------------
-- 2. Courses referencing universities that don't exist (BR-3).
--
-- Every loaded course must reference a university_id present in the
-- universities table. A non-empty result here is a BR-3 violation: the
-- record should have been rejected with reason unknown_university.
--
-- Known defect: DEFECT-01 — the unknown-university check in transform.py
-- only runs for source-A rows, so source-B rows with an unknown
-- university load through unrejected. Expect CRS-2011 / CRS-2012 here.
-- ----------------------------------------------------------------------------
SELECT c.course_id, c.source, c.university_id
FROM courses c
LEFT JOIN universities u ON c.university_id = u.university_id
WHERE u.university_id IS NULL;


-- ----------------------------------------------------------------------------
-- 3. Fee anomalies: non-positive, NULL, or suspiciously round-tripped (BR-6/BR-7).
--
-- 3a. Non-positive or NULL fee_usd — should never have been loaded (BR-7
--     requires fees to be a positive amount; invalid fees are rejected).
-- ----------------------------------------------------------------------------
SELECT course_id, source, original_fee, original_currency, fee_usd
FROM courses
WHERE fee_usd IS NULL OR fee_usd <= 0;

-- 3b. fee_usd that isn't rounded to 2 decimal places (BR-6: "rounded to 2
--     decimal places, preserving cents"). Comparing the stored value to
--     itself rounded to 2dp catches both truncation and other precision
--     loss.
--
-- Known defect: DEFECT-04 — fee_usd = int(fee * rate) truncates to a whole
-- number instead of rounding to 2dp, so this will flag essentially every
-- converted (non-USD) row system-wide.
-- ----------------------------------------------------------------------------
SELECT course_id, source, original_fee, original_currency, fee_usd,
       ROUND(fee_usd, 2) AS expected_rounded
FROM courses
WHERE fee_usd <> ROUND(fee_usd, 2);

-- 3c. "Suspiciously round-tripped" fees: recompute fee_usd from
--     original_fee/original_currency using the BR-6 rate table and compare
--     to the stored fee_usd. A mismatch beyond a cent of rounding slack
--     means the stored conversion doesn't match the spec's fixed rates.
-- ----------------------------------------------------------------------------
SELECT course_id, source, original_fee, original_currency, fee_usd,
       ROUND(
           original_fee * CASE original_currency
               WHEN 'USD' THEN 1.0
               WHEN 'AUD' THEN 0.65
               WHEN 'GBP' THEN 1.27
               WHEN 'EUR' THEN 1.08
               WHEN 'NPR' THEN 0.0075
               ELSE NULL
           END, 2
       ) AS recomputed_fee_usd
FROM courses
WHERE ABS(
          fee_usd - ROUND(
              original_fee * CASE original_currency
                  WHEN 'USD' THEN 1.0
                  WHEN 'AUD' THEN 0.65
                  WHEN 'GBP' THEN 1.27
                  WHEN 'EUR' THEN 1.08
                  WHEN 'NPR' THEN 0.0075
                  ELSE NULL
              END, 2
          )
      ) > 0.01
   OR original_currency NOT IN ('USD', 'AUD', 'GBP', 'EUR', 'NPR');


-- ----------------------------------------------------------------------------
-- 4. Intake-date anomalies (BR-8, BR-12).
--
-- 4a. intake_end not strictly after intake_start (BR-8: violations should
--     be rejected with reason invalid_intake_window, so none should load).
--     Dates are stored as ISO YYYY-MM-DD text, which sorts/compares
--     correctly as a string.
-- ----------------------------------------------------------------------------
SELECT course_id, source, intake_start, intake_end
FROM courses
WHERE intake_end <= intake_start;

-- 4b. Malformed intake dates — anything that doesn't match ISO
--     YYYY-MM-DD. If BR-8's DD/MM/YYYY acceptance is implemented
--     correctly, dates should always be normalized to ISO before storage;
--     anything else stored here is a normalization bug.
-- ----------------------------------------------------------------------------
SELECT course_id, source, intake_start, intake_end
FROM courses
WHERE intake_start NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
   OR intake_end   NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';

-- Note: BR-12 (application_deadline strictly before intake_start) cannot be
-- checked here — see DEFECT-08: application_deadline is never extracted
-- and has no column in the courses schema, so there is nothing to query.


-- ----------------------------------------------------------------------------
-- 5. Aggregate reconciliation: per source, loaded + rejected vs. raw input
--    counts (BR-11).
--
-- This query only reconciles what's already inside courses.db (loaded +
-- rejected per source). The raw input counts per source
-- (courses_source_a.csv / courses_source_b.json row counts) live outside
-- SQLite and must be compared externally, e.g.:
--   wc -l data/raw/courses_source_a.csv        (minus header)
--   python -c "import json; print(len(json.load(open('data/raw/courses_source_b.json'))))"
--
-- Per DECISIONS.md D-10, a discrepancy of raw_count - (loaded + rejected)
-- greater than zero is expected to equal the number of BR-10 dedup
-- "losers" for that source (rows that lost a dedupe and were neither
-- loaded nor rejected) — anything beyond that is a silent-disappearance
-- bug (see DEFECT-06 for a confirmed case: unparseable intake dates
-- disappear from both courses and rejects entirely).
-- ----------------------------------------------------------------------------
SELECT
    source,
    (SELECT COUNT(*) FROM courses c WHERE c.source = t.source) AS loaded_count,
    (SELECT COUNT(*) FROM rejects r WHERE r.source = t.source) AS rejected_count,
    (SELECT COUNT(*) FROM courses c WHERE c.source = t.source)
        + (SELECT COUNT(*) FROM rejects r WHERE r.source = t.source) AS loaded_plus_rejected
FROM (SELECT DISTINCT source FROM courses UNION SELECT DISTINCT source FROM rejects) AS t;

-- 5b. Reject reasons breakdown per source, useful context alongside the
--     reconciliation above (which reasons are firing, and for how many
--     rows).
-- ----------------------------------------------------------------------------
SELECT source, reason, COUNT(*) AS n
FROM rejects
GROUP BY source, reason
ORDER BY source, reason;
