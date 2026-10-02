"""GET /candidates/{id}/matches - ranked jobs for one candidate."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.params import IdPath
from app.db import get_conn
from app.repositories import candidates as candidates_repo
from app.repositories import jobs as jobs_repo
from app.schemas import ErrorResponse, JobMatch
from app.services import matching

router = APIRouter(tags=["matches"])


@router.get(
    "/candidates/{candidate_id}/matches",
    response_model=list[JobMatch],
    responses={404: {"model": ErrorResponse}},
    summary="Ranked jobs for a candidate",
)
def candidate_matches(
    candidate_id: IdPath,
    include_unqualified: bool = Query(
        False, description="Also list jobs with no matching required skill (score 0)"
    ),
    conn: psycopg.Connection = Depends(get_conn),
):
    candidate = candidates_repo.get_by_id(conn, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

    jobs = jobs_repo.get_all(conn)
    ranked = matching.rank_jobs_for_candidate(candidate, jobs, include_unqualified)
    return [
        JobMatch(job_id=j.id, job_title=j.title, score=r.score, reason=r.reason)
        for j, r in ranked
    ]
