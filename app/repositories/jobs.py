"""Job queries. Raw, hand-written SQL only; parameters are always passed
separately (%s), never concatenated into the statement."""

import psycopg

from app.models import Job

# One row per job, required skills packed into a single array (no N+1 queries).
GET_ALL_SQL = """
SELECT j.id,
       j.title,
       j.min_experience,
       j.culture_keywords,
       COALESCE(array_agg(s.name ORDER BY s.name)
                FILTER (WHERE s.id IS NOT NULL), '{}') AS required_skills
FROM jobs j
LEFT JOIN job_required_skills jr ON jr.job_id = j.id
LEFT JOIN skills s               ON s.id = jr.skill_id
GROUP BY j.id
ORDER BY j.id
"""

GET_BY_ID_SQL = """
SELECT j.id,
       j.title,
       j.min_experience,
       j.culture_keywords,
       COALESCE(array_agg(s.name ORDER BY s.name)
                FILTER (WHERE s.id IS NOT NULL), '{}') AS required_skills
FROM jobs j
LEFT JOIN job_required_skills jr ON jr.job_id = j.id
LEFT JOIN skills s               ON s.id = jr.skill_id
WHERE j.id = %s
GROUP BY j.id
"""


def _to_job(row: dict) -> Job:
    return Job(
        id=row["id"],
        title=row["title"],
        min_experience=float(row["min_experience"]),  # NUMERIC -> Decimal -> float
        culture_keywords=list(row["culture_keywords"] or []),
        required_skills=list(row["required_skills"] or []),
    )


def get_all(conn: psycopg.Connection) -> list[Job]:
    with conn.cursor() as cur:
        cur.execute(GET_ALL_SQL)
        return [_to_job(row) for row in cur.fetchall()]


def get_by_id(conn: psycopg.Connection, job_id: int) -> Job | None:
    with conn.cursor() as cur:
        cur.execute(GET_BY_ID_SQL, (job_id,))
        row = cur.fetchone()
    return _to_job(row) if row else None
