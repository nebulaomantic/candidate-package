"""Extract step: read raw course sources and the university reference table."""
import csv
import json
from pathlib import Path


def extract_source_a(raw_dir: Path) -> list[dict]:
    with open(raw_dir / "courses_source_a.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_source"] = "A"
    return rows


def extract_source_b(raw_dir: Path) -> list[dict]:
    with open(raw_dir / "courses_source_b.json", encoding="utf-8") as f:
        rows = json.load(f)
    for r in rows:
        r["_source"] = "B"
    return rows


def extract_universities(raw_dir: Path) -> dict[str, dict]:
    with open(raw_dir / "universities.csv", newline="", encoding="utf-8") as f:
        return {r["university_id"]: r for r in csv.DictReader(f)}


def extract_all(raw_dir: Path) -> tuple[list[dict], dict[str, dict]]:
    courses = extract_source_a(raw_dir) + extract_source_b(raw_dir)
    universities = extract_universities(raw_dir)
    return courses, universities
