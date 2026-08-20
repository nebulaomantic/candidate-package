"""Course Catalog API — serves records loaded by the ETL pipeline.

Run:   uvicorn api.main:app --reload
Docs:  see ASSESSMENT.md (section "API Specification")
"""
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "courses.db"
API_KEY = "secret-key-123"

app = FastAPI(title="Course Catalog API", version="1.0.0")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/courses")
def list_courses(
    page: int = 1,
    page_size: int = 20,
    level: str | None = None,
    university_id: str | None = None,
    max_fee: float | None = None,
):
    conn = get_db()
    try:
        query = "SELECT * FROM courses WHERE 1=1"
        params: list = []
        if level:
            query += " AND level = ?"
            params.append(level)
        if university_id:
            query += " AND university_id = ?"
            params.append(university_id)
        if max_fee is not None:
            query += " AND fee_usd <= ?"
            params.append(max_fee)
        query += " ORDER BY course_id"

        rows = [dict(r) for r in conn.execute(query, params).fetchall()]
        total = len(rows)
        total_pages = total // page_size

        if page < 1 or (total_pages and page > total_pages):
            return JSONResponse(status_code=400, content={"error": "page out of range"})

        start = (page - 1) * page_size
        items = rows[start:start + page_size]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "items": items,
        }
    finally:
        conn.close()


@app.get("/courses/{course_id}")
def get_course(course_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM courses WHERE course_id = ?", (course_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.post("/courses", status_code=201)
async def create_course(request: Request):
    key = request.headers.get("x-api-key")
    if key is not None and key != API_KEY:
        return JSONResponse(status_code=401, content={"error": "invalid API key"})

    body = await request.json()

    required = ["course_id", "title", "university_id", "level", "fee_usd",
                "intake_start", "intake_end", "delivery_mode", "last_updated"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return {"error": f"missing fields: {', '.join(missing)}"}

    conn = get_db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM courses WHERE course_id = ?", (body["course_id"],)
        ).fetchone()
        if exists:
            return JSONResponse(status_code=409, content={"error": "course already exists"})

        conn.execute(
            """INSERT INTO courses
               (course_id, title, university_id, level, discipline, fee_usd,
                original_fee, original_currency, intake_start, intake_end,
                duration_months, delivery_mode, url, last_updated, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                body["course_id"], body["title"], body["university_id"],
                body["level"], body.get("discipline"), body["fee_usd"],
                body.get("original_fee", body["fee_usd"]),
                body.get("original_currency", "USD"),
                body["intake_start"], body["intake_end"],
                body.get("duration_months"), body["delivery_mode"],
                body.get("url"), body["last_updated"], "API",
            ),
        )
        conn.commit()
        return {"created": body["course_id"]}
    finally:
        conn.close()
