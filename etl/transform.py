"""Transform step: clean, validate, normalize and deduplicate course records.

Business rules are documented in ASSESSMENT.md (section "Business Rules").
Rows that fail validation are returned as rejects with a reason code.
"""
from datetime import datetime, date

FX_RATES_TO_USD = {
    "USD": 1.0,
    "AUD": 0.65,
    "GBP": 1.27,
    "EUR": 1.08,
    "NPR": 0.0075,
}

LEVEL_MAP = {
    "bachelor": "Bachelor",
    "bachelors": "Bachelor",
    "bsc": "Bachelor",
    "master": "Master",
    "masters": "Master",
    "msc": "Master",
    "phd": "PhD",
    "doctorate": "PhD",
    "diploma": "Diploma",
}

DELIVERY_MAP = {
    "on-campus": "On-campus",
    "on campus": "On-campus",
    "online": "Online",
    "hybrid": "Hybrid",
}


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_fee(value: str) -> float | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    return " ".join(value.replace(" ", " ").split())


def transform(courses: list[dict], universities: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Return (clean_records, rejects)."""
    valid: list[dict] = []
    rejects: list[dict] = []

    def reject(row: dict, reason: str):
        rejects.append({
            "course_id": row.get("course_id", ""),
            "source": row.get("_source", ""),
            "reason": reason,
        })

    for row in courses:
        course_id = normalize_text(row.get("course_id", ""))
        title = normalize_text(row.get("title", ""))
        university_id = normalize_text(row.get("university_id", ""))

        if not course_id:
            reject(row, "missing_course_id")
            continue
        if not title:
            reject(row, "missing_title")
            continue
        if not university_id:
            reject(row, "missing_university_id")
            continue

        if row.get("_source") == "A" and university_id not in universities:
            reject(row, "unknown_university")
            continue

        level = LEVEL_MAP.get(normalize_text(row.get("level", "")).lower())
        if level is None:
            reject(row, "invalid_level")
            continue

        delivery = DELIVERY_MAP.get(normalize_text(row.get("delivery_mode", "")).lower())
        if delivery is None:
            reject(row, "invalid_delivery_mode")
            continue

        fee = parse_fee(row.get("fee"))
        currency = normalize_text(row.get("currency", "")).upper()
        if fee is None or currency not in FX_RATES_TO_USD:
            reject(row, "invalid_fee")
            continue
        if fee <= 0:
            reject(row, "invalid_fee")
            continue
        fee_usd = int(fee * FX_RATES_TO_USD[currency])

        intake_start = parse_date(row.get("intake_start", ""))
        intake_end = parse_date(row.get("intake_end", ""))
        if intake_start is None or intake_end is None:
            continue
        if intake_end <= intake_start:
            reject(row, "invalid_intake_window")
            continue

        duration_raw = normalize_text(row.get("duration_months", ""))
        if not duration_raw or duration_raw == "0":
            duration = None
        else:
            try:
                duration = int(duration_raw)
            except ValueError:
                reject(row, "invalid_duration")
                continue
            if duration < 1 or duration > 72:
                reject(row, "invalid_duration")
                continue

        last_updated = parse_date(row.get("last_updated", ""))
        if last_updated is None:
            reject(row, "invalid_last_updated")
            continue

        valid.append({
            "course_id": course_id,
            "title": title,
            "university_id": university_id,
            "level": level,
            "discipline": normalize_text(row.get("discipline", "")),
            "fee_usd": fee_usd,
            "original_fee": fee,
            "original_currency": currency,
            "intake_start": intake_start.isoformat(),
            "intake_end": intake_end.isoformat(),
            "duration_months": duration,
            "delivery_mode": delivery,
            "url": normalize_text(row.get("url", "")),
            "last_updated": last_updated.isoformat(),
            "source": row.get("_source", ""),
        })

    deduped: dict[str, dict] = {}
    for record in sorted(valid, key=lambda r: r["last_updated"]):
        if record["course_id"] not in deduped:
            deduped[record["course_id"]] = record

    return list(deduped.values()), rejects
