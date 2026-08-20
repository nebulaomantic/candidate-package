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
