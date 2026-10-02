"""Plain data objects passed between layers.

The repository layer builds these from SQL rows. The matching service only
ever sees these objects, never SQL, so it can be tested without a database.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Candidate:
    id: int
    name: str
    experience_years: float
    availability: str
    traits: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Job:
    id: int
    title: str
    min_experience: float
    culture_keywords: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MatchResult:
    """Score for one candidate/job pair, plus everything needed to explain it."""

    score: float  # final, 0-100, rounded to 1 decimal
    skill_score: float  # 0-100
    experience_score: float  # 0-100
    culture_score: float  # 0-100
    availability_multiplier: float  # 1.0 = no penalty
    matched_skills: list[str]
    matched_culture: list[str]
    reason: str
