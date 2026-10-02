"""Matching engine: pure functions, no SQL, no HTTP.

    base  = 0.60*skill + 0.25*experience + 0.15*culture      (each 0-100)
    base  = 0                                   if skill == 0   (gate)
    final = round(base * availability_multiplier, 1)
"""

import re

from app.models import Candidate, Job, MatchResult
from app.utils.reasons import build_reason

# ---------------------------------------------------------------------------
# Tunable constants - everything you need to explain or change is here.
# ---------------------------------------------------------------------------
WEIGHT_SKILL = 0.60
WEIGHT_EXPERIENCE = 0.25
WEIGHT_CULTURE = 0.15

AVAILABILITY_MULTIPLIER = {
    "immediate": 1.00,
    "2 weeks": 0.95,
    "not looking": 0.70,
}
UNKNOWN_AVAILABILITY_MULTIPLIER = 1.00  # unknown value: no bonus, no penalty

# Lower rank = preferred when everything else ties.
AVAILABILITY_RANK = {"immediate": 0, "2 weeks": 1, "not looking": 2}
UNKNOWN_AVAILABILITY_RANK = 3


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """'Pattern Recognition', ' pattern_recognition ' -> 'pattern-recognition'."""
    return re.sub(r"[\s_]+", "-", text.strip().lower())


def _availability_key(availability: str) -> str:
    return " ".join(availability.lower().split())


# ---------------------------------------------------------------------------
# Component 1: skill overlap
# ---------------------------------------------------------------------------
def skill_overlap(
    candidate_skills: list[str], required_skills: list[str]
) -> tuple[float, list[str]]:
    """matched required skills / total required skills, as 0-100.

    Returns (score, matched skills in the job's display form).
    A job with no required skills gives 100 (nothing to fall short of).
    """
    required = {normalize(s): s for s in required_skills if s.strip()}
    if not required:
        return 100.0, []
    have = {normalize(s) for s in candidate_skills}
    matched = [display for norm, display in required.items() if norm in have]
    return 100.0 * len(matched) / len(required), matched


# ---------------------------------------------------------------------------
# Component 2: experience fit
# ---------------------------------------------------------------------------
def experience_fit(years: float, min_experience: float) -> float:
    """min(years / min_experience, 1) as 0-100. No minimum = full credit."""
    if min_experience <= 0:
        return 100.0
    return 100.0 * min(years / min_experience, 1.0)


# ---------------------------------------------------------------------------
# Component 3: culture fit (candidate traits vs job culture keywords)
# ---------------------------------------------------------------------------
def _trait_matches_keyword(trait: str, keyword: str) -> bool:
    """Exact match, or every hyphen-part of the trait is inside the keyword.

    'calm' matches 'calm-under-pressure'. No synonym list needed.
    """
    t, k = normalize(trait), normalize(keyword)
    if not t or not k:
        return False
    return t == k or set(t.split("-")) <= set(k.split("-"))


def culture_fit(
    traits: list[str], culture_keywords: list[str]
) -> tuple[float, list[str]]:
    """job keywords matched by some trait / total job keywords, as 0-100.

    A job with no keywords gives 100 (no culture requirement to miss).
    """
    keywords = [k for k in culture_keywords if k.strip()]
    if not keywords:
        return 100.0, []
    matched = [k for k in keywords if any(_trait_matches_keyword(t, k) for t in traits)]
    return 100.0 * len(matched) / len(keywords), matched


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------
def availability_multiplier(availability: str) -> float:
    return AVAILABILITY_MULTIPLIER.get(
        _availability_key(availability), UNKNOWN_AVAILABILITY_MULTIPLIER
    )


def availability_rank(availability: str) -> int:
    return AVAILABILITY_RANK.get(
        _availability_key(availability), UNKNOWN_AVAILABILITY_RANK
    )


# ---------------------------------------------------------------------------
# The one scoring function used by all three endpoints
# ---------------------------------------------------------------------------
def score_candidate_for_job(candidate: Candidate, job: Job) -> MatchResult:
    skill, matched_skills = skill_overlap(candidate.skills, job.required_skills)
    experience = experience_fit(candidate.experience_years, job.min_experience)
    culture, matched_culture = culture_fit(candidate.traits, job.culture_keywords)
    multiplier = availability_multiplier(candidate.availability)

    gated = skill == 0.0
    base = 0.0 if gated else (
        WEIGHT_SKILL * skill
        + WEIGHT_EXPERIENCE * experience
        + WEIGHT_CULTURE * culture
    )
    # The tiny epsilon stops float noise from flipping x.x5 rounding cases
    # (e.g. 87.875 must round to 87.9, not 87.8).
    score = round(base * multiplier + 1e-9, 1)

    reason = build_reason(
        candidate,
        job,
        matched_skills=matched_skills,
        matched_culture=matched_culture,
        multiplier=multiplier,
        gated=gated,
    )
    return MatchResult(
        score=score,
        skill_score=skill,
        experience_score=experience,
        culture_score=culture,
        availability_multiplier=multiplier,
        matched_skills=matched_skills,
        matched_culture=matched_culture,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Ordering: score, skill, culture, availability (sooner first), id
# ---------------------------------------------------------------------------
def _sort_key(result: MatchResult, availability: str, entity_id: int) -> tuple:
    return (
        -result.score,
        -result.skill_score,
        -result.culture_score,
        availability_rank(availability),
        entity_id,
    )


def rank_candidates_for_job(
    job: Job, candidates: list[Candidate], include_unqualified: bool = False
) -> list[tuple[Candidate, MatchResult]]:
    """Ranked candidates for one job. Score-0 (no skill overlap) are hidden
    unless include_unqualified is True."""
    scored = [(c, score_candidate_for_job(c, job)) for c in candidates]
    if not include_unqualified:
        scored = [(c, r) for c, r in scored if r.score > 0]
    scored.sort(key=lambda p: _sort_key(p[1], p[0].availability, p[0].id))
    return scored


def rank_jobs_for_candidate(
    candidate: Candidate, jobs: list[Job], include_unqualified: bool = False
) -> list[tuple[Job, MatchResult]]:
    """Ranked jobs for one candidate (reverse direction, same scoring fn)."""
    scored = [(j, score_candidate_for_job(candidate, j)) for j in jobs]
    if not include_unqualified:
        scored = [(j, r) for j, r in scored if r.score > 0]
    scored.sort(key=lambda p: _sort_key(p[1], candidate.availability, p[0].id))
    return scored


def best_candidate_per_job(
    jobs: list[Job], candidates: list[Candidate]
) -> list[tuple[Job, Candidate, MatchResult]]:
    """Top candidate for each job. Jobs nobody qualifies for are skipped."""
    best = []
    for job in jobs:
        ranked = rank_candidates_for_job(job, candidates)
        if ranked:
            candidate, result = ranked[0]
            best.append((job, candidate, result))
    return best
