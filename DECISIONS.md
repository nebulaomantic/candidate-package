D-01 — Reject reason for "unknown currency"
Context: BR-6 lists valid currencies (USD/AUD/GBP/EUR/NPR) but doesn't say what reject reason to use if a fee has a currency not in that list. The code lumps it in with invalid_fee.
Decision: treat unknown currency as invalid_fee (matches current code) — but flag it as a spec gap, not confirmed-correct behavior.
Affects: BR-6, BR-7.
D-02 — Missing mandatory-field reject reasons aren't named in the spec
Context: BR-1/2/3 say course_id/title/university_id are mandatory, but the spec never gives explicit reject-reason strings for "missing" (only for "unknown_university"). The code invented missing_course_id, missing_title, missing_university_id.
Decision: accept these as reasonable, but note them as undocumented reason codes your tests should still check exist and are spelled consistently.
Affects: BR-1, BR-2, BR-3.
D-03 — last_updated has no explicit reject rule in the spec
Context: the spec never says what happens if last_updated itself is missing/unparseable, but it's needed for BR-10's dedupe logic. The code rejects it as invalid_last_updated.
Decision: treat this as implied by BR-10 (you can't dedupe without a valid date) — accept the code's reason name.
Affects: BR-10.
D-04 — Interpreting "the fee must be a positive amount" (BR-7)
Context: is a fee of 0 invalid, or only negative? Spec says "positive," so decide explicitly: positive = strictly greater than 0.
Decision: fee == 0 is rejected (matches code's fee <= 0 check) — confirmed correct, not a defect.
Affects: BR-7.
D-05 — Whether duration_months is actually optional
Context: BR-9 says it must be "an integer between 1 and 72... anything else is rejected." That reads like blank/0 should be rejected, but the code treats blank/0 as a valid "unknown" (null) value instead.
Decision: siding with the literal spec text — treat this as a genuine defect (already logged), not a legitimate "duration is optional" interpretation. State this explicitly since someone could argue it the other way.
Affects: BR-9.
D-06 — Date format ambiguity: what if a date matches neither format?
Context: spec says accept ISO or DD/MM/YYYY. It doesn't say what happens to a totally malformed date string, but BR-11 ("no record may silently disappear") implies it must be rejected, not dropped.
Decision: treat any unparseable date as a reject candidate (e.g., reason invalid_date or similar) — the current silent-drop behavior is a defect, not an acceptable interpretation.
Affects: BR-8, BR-11.
D-07 — Does "case-insensitive" filtering apply to max_fee?
Context: spec says "Filters are case-insensitive," listed alongside level, university_id, max_fee — but max_fee is a number, so case doesn't apply to it.
Decision: interpreting "case-insensitive" as applying only to the two text filters (level, university_id).
Affects: API spec, /courses tests.
D-08 — Whether university_id filter should also be case-insensitive if IDs are always uppercase in source data
Context: check the raw data — if university_id values are always consistently cased in practice, is the case-insensitivity requirement purely defensive?
Decision: test it anyway since the spec states it explicitly, regardless of whether current sample data happens to hide the bug.
Affects: API spec.
D-09 — BR-10 tie-break when duplicate last_updated timestamps are identical
Context: BR-10 says keep the record with the most recent last_updated, but doesn't say what to do if two records sharing a course_id have the exact same last_updated. Some deterministic choice must exist for the pipeline to be reproducible.
Decision: test only that behavior is deterministic (same input always yields the same surviving record) rather than asserting which source/row wins, since the spec doesn't pick one. Note this as a spec gap, not a defect, unless the pipeline is actually non-deterministic across runs.
Affects: BR-10.
D-10 — BR-11 accounting for the "losing" row of a BR-10 dedup pair
Context: BR-11 says "for every input row, either it is loaded into courses (possibly losing a dedupe) or it appears in rejects." Read literally, this means the row that loses a dedupe must still be traceable — either it shows up in rejects with a reason (e.g. duplicate_superseded), or the reconciliation math (raw count vs. loaded+rejected) is expected to come up short by exactly the number of dedup losers.
Decision: treat the reconciliation check as raw_count == loaded_count + rejected_count + dedup_loser_count, verifying dedup losers specifically (by course_id) rather than requiring every loser to appear in rejects — the spec's parenthetical "(possibly losing a dedupe)" reads as an explicit third bucket, not a hidden case of rejects. Flag as a spec-wording ambiguity worth confirming against actual pipeline behavior.
Affects: BR-10, BR-11.
D-11 — Rounding mode for fee_usd (half-up vs. banker's rounding)
Context: BR-6 says round to 2 decimal places but doesn't specify the rounding mode. Python's built-in round() uses banker's rounding (round-half-to-even), which can disagree with the "expected" half-up rounding at exact .xx5 boundaries.
Decision: test with a fee that lands exactly on a rounding boundary and assert against whatever the pipeline actually implements, documenting the observed mode here rather than assuming — if it's banker's rounding via bare round(), flag it as worth a code comment/defect since financial conversions conventionally round half-up.
Affects: BR-6.
D-12 — Reject-reason precedence when a record fails multiple rules at once
Context: the spec defines one reason string per rule (invalid_level, invalid_fee, etc.) but never says which reason wins when a record independently violates more than one rule.
Decision: don't assert a specific winning reason unless the pipeline's rule-check order is documented/stable; instead assert that exactly one reason is recorded and it's one of the violated rules' valid reasons. Revisit if the pipeline turns out to check rules in a fixed, documented order.
Affects: BR-11.
D-13 — Inclusive vs. exclusive boundary on the max_fee filter
Context: the API spec says GET /courses supports a max_fee filter but doesn't state whether a course exactly at max_fee is included.
Decision: assume inclusive (fee_usd <= max_fee) as the conventional reading of "max," and test accordingly — flag as a defect if the implementation is exclusive, since that's the less intuitive reading of the word "max."
Affects: API spec.
