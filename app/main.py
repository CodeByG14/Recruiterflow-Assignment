"""Recruiter Bot - FastAPI application.

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""

import logging

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api import candidates, jobs, matches
from app.db import connect
from app.schemas import ErrorResponse, HealthResponse

logger = logging.getLogger("recruiter_bot")

app = FastAPI(
    title="Recruiter Bot",
    version="1.0.0",
    description=(
        "Ranks candidates for jobs (and jobs for candidates) with a "
        "deterministic score: 60% skill overlap, 25% experience fit, "
        "15% culture fit, then an availability multiplier."
    ),
)

app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(matches.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
    tags=["health"],
    summary="Liveness plus a database connectivity check",
)
def health():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
    except psycopg.Error:
        logger.exception("Health check: database unreachable")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# Database failures: log the real error server-side, return a generic message.
# Never send SQL text, hostnames, credentials or stack traces to the client.
# (Starlette picks the most specific handler, so OperationalError wins.)
# ---------------------------------------------------------------------------
@app.exception_handler(psycopg.OperationalError)
async def database_unavailable(request, exc):
    logger.error("Database unavailable: %s", exc)
    return JSONResponse(status_code=503, content=ErrorResponse(detail="Database unavailable").model_dump())


@app.exception_handler(psycopg.Error)
async def database_error(request, exc):
    logger.error("Database error", exc_info=exc)
    return JSONResponse(status_code=500, content=ErrorResponse(detail="Internal server error").model_dump())
