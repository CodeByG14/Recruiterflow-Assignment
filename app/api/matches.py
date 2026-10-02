"""GET /matches/best - the top candidate for every job."""

import psycopg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.repositories import candidates as candidates_repo
from app.repositories import jobs as jobs_repo
from app.schemas import BestMatch
from app.services import matching

router = APIRouter(tags=["matches"])


@router.get(
    "/matches/best",
    response_model=list[BestMatch],
    summary="Best candidate for each job",
)
def best_matches(conn: psycopg.Connection = Depends(get_conn)):
    # Two queries total, then score every pair in memory.
    jobs = jobs_repo.get_all(conn)
    candidates = candidates_repo.get_all(conn)
    return [
        BestMatch(
            job_id=j.id,
            job_title=j.title,
            candidate_id=c.id,
            candidate_name=c.name,
            score=r.score,
            reason=r.reason,
        )
        for j, c, r in matching.best_candidate_per_job(jobs, candidates)
    ]
