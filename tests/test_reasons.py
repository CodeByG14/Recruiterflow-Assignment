from app.models import Candidate, Job
from app.services.matching import score_candidate_for_job
from tests.fixtures import BY_NAME, BY_TITLE


def reason(candidate, job):
    return score_candidate_for_job(candidate, job).reason


def test_strong_match_reason():
    r = reason(BY_NAME["Sherlock H."], BY_TITLE["Backend Detective"])
    assert r == (
        "Matches all required skills (3/3), exceeds the 3-year experience minimum, "
        "and fits the culture on 'analytical'."
    )


def test_partial_skills_and_no_culture():
    r = reason(BY_NAME["Dwight S."], BY_TITLE["Sales Engineer"])
    assert "Matches 2 of 3 required skills" in r
    assert "has no culture-keyword overlap" in r


def test_not_looking_is_named_when_it_costs_points():
    r = reason(BY_NAME["Michael S."], BY_TITLE["Sales Engineer"])
    assert r.endswith("Score reduced: not currently looking.")


def test_two_weeks_is_named_when_it_costs_points():
    r = reason(BY_NAME["Olivia P."], BY_TITLE["Incident Commander"])
    assert r.endswith("Score reduced: available in 2 weeks.")


def test_no_availability_note_when_immediate():
    r = reason(BY_NAME["Sherlock H."], BY_TITLE["Backend Detective"])
    assert "Score reduced" not in r


def test_gated_reason():
    r = reason(BY_NAME["Ron S."], BY_TITLE["Backend Detective"])
    assert r == "No required skills matched, so this is not a match."


def test_below_minimum_experience_is_explained():
    job = Job(1, "J", 5, [], ["a"])
    cand = Candidate(1, "C", 3, "Immediate", [], ["a"])
    assert "falls short of the 5-year experience minimum (has 3)" in reason(cand, job)


def test_meets_minimum_experience():
    job = Job(1, "J", 3, [], ["a"])
    cand = Candidate(1, "C", 3, "Immediate", [], ["a"])
    assert "meets the 3-year experience minimum" in reason(cand, job)


def test_job_without_keywords_omits_culture_clause():
    job = Job(1, "J", 3, [], ["a"])
    cand = Candidate(1, "C", 5, "Immediate", ["x"], ["a"])
    assert "culture" not in reason(cand, job)


def test_reason_is_deterministic():
    c, j = BY_NAME["Leslie K."], BY_TITLE["Engineering Manager, Chaos Team"]
    assert reason(c, j) == reason(c, j)
