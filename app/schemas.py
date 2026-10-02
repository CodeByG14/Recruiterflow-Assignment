"""Response shapes. Explicit and stable; no database internals leak out."""

from pydantic import BaseModel, Field


class CandidateMatch(BaseModel):
    """One ranked candidate for a given job."""

    candidate_id: int
    candidate_name: str
    score: float = Field(description="Final match score, 0-100")
    reason: str = Field(description="Short explanation built from the score components")


class JobMatch(BaseModel):
    """One ranked job for a given candidate."""

    job_id: int
    job_title: str
    score: float = Field(description="Final match score, 0-100")
    reason: str = Field(description="Short explanation built from the score components")


class BestMatch(BaseModel):
    """The top-scoring candidate for one job."""

    job_id: int
    job_title: str
    candidate_id: int
    candidate_name: str
    score: float = Field(description="Final match score, 0-100")
    reason: str = Field(description="Short explanation built from the score components")


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    detail: str
