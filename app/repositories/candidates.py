"""Candidate queries. Raw, hand-written SQL only; parameters are always
passed separately (%s), never concatenated into the statement."""

import psycopg

from app.models import Candidate

# One row per candidate, skills packed into a single array (no N+1 queries).
# The LEFT JOIN + FILTER keeps candidates who have no skills at all.
GET_ALL_SQL = """
SELECT c.id,
       c.name,
       c.experience_years,
       c.availability,
       c.traits,
       COALESCE(array_agg(s.name ORDER BY s.name)
                FILTER (WHERE s.id IS NOT NULL), '{}') AS skills
FROM candidates c
LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
LEFT JOIN skills s            ON s.id = cs.skill_id
GROUP BY c.id
ORDER BY c.id
"""

GET_BY_ID_SQL = """
SELECT c.id,
       c.name,
       c.experience_years,
       c.availability,
       c.traits,
       COALESCE(array_agg(s.name ORDER BY s.name)
                FILTER (WHERE s.id IS NOT NULL), '{}') AS skills
FROM candidates c
LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
LEFT JOIN skills s            ON s.id = cs.skill_id
WHERE c.id = %s
GROUP BY c.id
"""


def _to_candidate(row: dict) -> Candidate:
    return Candidate(
        id=row["id"],
        name=row["name"],
        experience_years=float(row["experience_years"]),  # NUMERIC -> Decimal -> float
        availability=row["availability"] or "",  # NULL -> "" (treated as unknown)
        traits=list(row["traits"] or []),
        skills=list(row["skills"] or []),
    )


def get_all(conn: psycopg.Connection) -> list[Candidate]:
    with conn.cursor() as cur:
        cur.execute(GET_ALL_SQL)
        return [_to_candidate(row) for row in cur.fetchall()]


def get_by_id(conn: psycopg.Connection, candidate_id: int) -> Candidate | None:
    with conn.cursor() as cur:
        cur.execute(GET_BY_ID_SQL, (candidate_id,))
        row = cur.fetchone()
    return _to_candidate(row) if row else None
