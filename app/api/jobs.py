"""GET /jobs/{id}/matches - ranked candidates for one job."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.params import IdPath
from app.db import get_conn
from app.repositories import candidates as candidates_repo
from app.repositories import jobs as jobs_repo
from app.schemas import CandidateMatch, ErrorResponse
from app.services import matching

router = APIRouter(tags=["matches"])


@router.get(
    "/jobs/{job_id}/matches",
    response_model=list[CandidateMatch],
    responses={404: {"model": ErrorResponse}},
    summary="Ranked candidates for a job",
)
def job_matches(
    job_id: IdPath,
    include_unqualified: bool = Query(
        False, description="Also list candidates with no matching required skill (score 0)"
    ),
    conn: psycopg.Connection = Depends(get_conn),
):
    job = jobs_repo.get_by_id(conn, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    candidates = candidates_repo.get_all(conn)
    ranked = matching.rank_candidates_for_job(job, candidates, include_unqualified)
    return [
        CandidateMatch(
            candidate_id=c.id, candidate_name=c.name, score=r.score, reason=r.reason
        )
        for c, r in ranked
    ]
