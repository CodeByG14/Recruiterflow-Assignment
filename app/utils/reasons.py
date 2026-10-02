"""Deterministic, template-based match reasons. No AI, no per-character text.

The reason is assembled from the same components that produced the score, so
it always explains the number instead of just repeating it.
"""

from app.models import Candidate, Job

# Only shown when availability actually reduced the score.
_AVAILABILITY_PHRASE = {
    "2 weeks": "available in 2 weeks",
    "not looking": "not currently looking",
}


def _years(value: float) -> str:
    return f"{value:g}"  # 3.0 -> "3", 2.5 -> "2.5"


def _join(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def build_reason(
    candidate: Candidate,
    job: Job,
    *,
    matched_skills: list[str],
    matched_culture: list[str],
    multiplier: float,
    gated: bool,
) -> str:
    if gated:
        return "No required skills matched, so this is not a match."

    parts: list[str] = []

    # Skills
    total = len(job.required_skills)
    if total == 0:
        parts.append("Has no specific skill requirements to meet")
    elif len(matched_skills) == total:
        parts.append(f"Matches all required skills ({total}/{total})")
    else:
        parts.append(f"Matches {len(matched_skills)} of {total} required skills")

    # Experience
    have, need = candidate.experience_years, job.min_experience
    if need <= 0:
        parts.append("no experience minimum applies")
    elif have > need:
        parts.append(f"exceeds the {_years(need)}-year experience minimum")
    elif have == need:
        parts.append(f"meets the {_years(need)}-year experience minimum")
    else:
        parts.append(
            f"falls short of the {_years(need)}-year experience minimum "
            f"(has {_years(have)})"
        )

    # Culture (skip entirely if the job lists no keywords)
    if job.culture_keywords:
        if matched_culture:
            quoted = [f"'{k}'" for k in matched_culture]
            parts.append(f"fits the culture on {_join(quoted)}")
        else:
            parts.append("has no culture-keyword overlap")

    reason = _join(parts) + "."

    # Availability
    if multiplier < 1.0:
        key = " ".join(candidate.availability.lower().split())
        phrase = _AVAILABILITY_PHRASE.get(key, f"availability is '{candidate.availability}'")
        reason += f" Score reduced: {phrase}."

    return reason
