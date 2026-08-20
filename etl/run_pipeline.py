"""Run the full course ETL pipeline: extract -> transform -> load.

Usage:  python etl/run_pipeline.py
Output: data/courses.db (SQLite)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract import extract_all          # noqa: E402
from transform import transform          # noqa: E402
from load import load                    # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "courses.db"


def main():
    courses, universities = extract_all(RAW_DIR)
    print(f"extracted : {len(courses)} course rows, {len(universities)} universities")

    records, rejects = transform(courses, universities)
    print(f"transformed: {len(records)} valid records, {len(rejects)} rejected")

    load(records, rejects, universities, DB_PATH)
    print(f"loaded     : {DB_PATH}")


if __name__ == "__main__":
    main()
