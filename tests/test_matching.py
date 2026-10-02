import pytest

from app.models import Candidate, Job, MatchResult
from app.services import matching as m
from tests.fixtures import BY_NAME, BY_TITLE, CANDIDATES, JOBS


# ----------------------------------------------------------------- skills
class TestSkillOverlap:
    def test_full_overlap(self):
        score, matched = m.skill_overlap(["a", "b", "c"], ["a", "b"])
        assert score == 100.0 and matched == ["a", "b"]

    def test_partial_overlap(self):
        score, matched = m.skill_overlap(["a"], ["a", "b", "c"])
        assert score == pytest.approx(33.333, abs=0.01) and matched == ["a"]

    def test_zero_overlap(self):
        assert m.skill_overlap(["x"], ["a", "b"]) == (0.0, [])

    def test_extra_candidate_skills_are_not_rewarded(self):
        many, _ = m.skill_overlap(["a", "b", "x", "y", "z"], ["a", "b"])
        few, _ = m.skill_overlap(["a", "b"], ["a", "b"])
        assert many == few == 100.0

    def test_normalisation_case_space_underscore(self):
        score, _ = m.skill_overlap(
            [" PATTERN recognition ", "Deduction"], ["pattern-recognition", "deduction"]
        )
        assert score == 100.0

    def test_job_without_required_skills_is_full_credit_not_a_crash(self):
        assert m.skill_overlap(["a"], []) == (100.0, [])


# ------------------------------------------------------------- experience
class TestExperienceFit:
    def test_exceeds_minimum(self):
        assert m.experience_fit(8, 3) == 100.0

    def test_exactly_meets_minimum(self):
        assert m.experience_fit(3, 3) == 100.0

    def test_below_minimum_scales_linearly(self):
        assert m.experience_fit(2, 3) == pytest.approx(66.667, abs=0.01)

    def test_zero_experience_below_minimum(self):
        assert m.experience_fit(0, 3) == 0.0

    def test_zero_minimum_is_full_credit_not_division_by_zero(self):
        assert m.experience_fit(0, 0) == 100.0


# ---------------------------------------------------------------- culture
class TestCultureFit:
    def test_exact_match(self):
        score, matched = m.culture_fit(["analytical", "blunt"], ["analytical", "autonomous"])
        assert score == 50.0 and matched == ["analytical"]

    def test_hyphen_token_rule(self):
        score, matched = m.culture_fit(["calm"], ["decisive", "calm-under-pressure"])
        assert score == 50.0 and matched == ["calm-under-pressure"]

    def test_no_overlap(self):
        assert m.culture_fit(["blunt"], ["analytical"]) == (0.0, [])

    def test_job_without_keywords_is_full_credit(self):
        assert m.culture_fit(["blunt"], []) == (100.0, [])

    def test_partial_word_is_not_a_match(self):
        # 'cal' is not a hyphen-part of 'calm-under-pressure'
        assert m.culture_fit(["cal"], ["calm-under-pressure"]) == (0.0, [])


# ----------------------------------------------------------- availability
class TestAvailability:
    @pytest.mark.parametrize(
        "value,expected",
        [("Immediate", 1.0), ("2 weeks", 0.95), ("Not looking", 0.70),
         ("  not   LOOKING ", 0.70), ("next year", 1.0)],
    )
    def test_multiplier(self, value, expected):
        assert m.availability_multiplier(value) == expected

    def test_rank_order(self):
        ranks = [m.availability_rank(a) for a in ["Immediate", "2 weeks", "Not looking", "???"]]
        assert ranks == sorted(ranks) and len(set(ranks)) == 4


# ------------------------------------------------------------ final score
class TestScoreCandidateForJob:
    def test_sherlock_backend_detective(self):
        r = m.score_candidate_for_job(BY_NAME["Sherlock H."], BY_TITLE["Backend Detective"])
        assert (r.skill_score, r.experience_score, r.culture_score) == (100.0, 100.0, 50.0)
        assert r.score == 92.5  # 60 + 25 + 7.5

    def test_availability_penalty_2_weeks(self):
        r = m.score_candidate_for_job(BY_NAME["Olivia P."], BY_TITLE["Incident Commander"])
        assert r.score == 87.9  # 92.5 * 0.95 = 87.875 -> 87.9

    def test_availability_penalty_not_looking(self):
        r = m.score_candidate_for_job(BY_NAME["Michael S."], BY_TITLE["Sales Engineer"])
        assert r.score == 50.8  # (40 + 25 + 7.5) * 0.70

    def test_not_looking_flips_sales_engineer_ranking(self):
        michael = m.score_candidate_for_job(BY_NAME["Michael S."], BY_TITLE["Sales Engineer"])
        dwight = m.score_candidate_for_job(BY_NAME["Dwight S."], BY_TITLE["Sales Engineer"])
        assert dwight.score > michael.score
        # without the penalty Michael would win
        assert michael.score / michael.availability_multiplier > dwight.score

    def test_zero_skill_overlap_is_gated_to_zero(self):
        # Ron: 15 years, but no Backend Detective skills
        r = m.score_candidate_for_job(BY_NAME["Ron S."], BY_TITLE["Backend Detective"])
        assert r.skill_score == 0 and r.experience_score == 100.0
        assert r.score == 0.0

    def test_below_minimum_experience_reduces_score(self):
        senior = Job(1, "J", 6, [], ["a"])
        junior = Candidate(1, "Jr", 3, "Immediate", [], ["a"])
        r = m.score_candidate_for_job(junior, senior)
        assert r.experience_score == 50.0
        assert r.score == pytest.approx(0.60 * 100 + 0.25 * 50 + 0.15 * 100)

    def test_deterministic(self):
        c, j = BY_NAME["Sherlock H."], BY_TITLE["Backend Detective"]
        assert m.score_candidate_for_job(c, j) == m.score_candidate_for_job(c, j)

    def test_score_is_within_0_100_for_every_pair(self):
        for c in CANDIDATES:
            for j in JOBS:
                assert 0.0 <= m.score_candidate_for_job(c, j).score <= 100.0

    def test_weights_sum_to_one(self):
        assert m.WEIGHT_SKILL + m.WEIGHT_EXPERIENCE + m.WEIGHT_CULTURE == pytest.approx(1.0)


# ---------------------------------------------------------------- ordering
class TestOrdering:
    @staticmethod
    def _res(score, skill=100.0, culture=0.0):
        return MatchResult(score, skill, 100.0, culture, 1.0, [], [], "")

    def test_higher_score_first(self):
        assert m._sort_key(self._res(80), "Immediate", 9) < m._sort_key(self._res(70), "Immediate", 1)

    def test_tie_on_score_higher_skill_first(self):
        a = m._sort_key(self._res(70, skill=100), "Immediate", 9)
        b = m._sort_key(self._res(70, skill=50), "Immediate", 1)
        assert a < b

    def test_tie_on_skill_higher_culture_first(self):
        a = m._sort_key(self._res(70, culture=50), "Immediate", 9)
        b = m._sort_key(self._res(70, culture=0), "Immediate", 1)
        assert a < b

    def test_tie_on_culture_sooner_availability_first(self):
        a = m._sort_key(self._res(70), "Immediate", 9)
        b = m._sort_key(self._res(70), "Not looking", 1)
        assert a < b

    def test_full_tie_lower_id_first(self):
        assert m._sort_key(self._res(70), "Immediate", 1) < m._sort_key(self._res(70), "Immediate", 2)


# ------------------------------------------------------------------ ranking
class TestRankings:
    def test_job_matches_backend_detective(self):
        ranked = m.rank_candidates_for_job(BY_TITLE["Backend Detective"], CANDIDATES)
        assert [c.name for c, _ in ranked] == ["Sherlock H.", "Sheldon C."]

    def test_unqualified_hidden_by_default_but_available(self):
        job = BY_TITLE["Backend Detective"]
        assert len(m.rank_candidates_for_job(job, CANDIDATES, include_unqualified=True)) == 15

    def test_sales_engineer_order(self):
        ranked = m.rank_candidates_for_job(BY_TITLE["Sales Engineer"], CANDIDATES)
        names = [c.name for c, _ in ranked]
        assert names[0] == "Dwight S."
        assert names.index("Michael S.") == 2

    def test_exact_tie_resolved_by_id(self):
        ranked = m.rank_candidates_for_job(BY_TITLE["Engineering Manager, Chaos Team"], CANDIDATES)
        (first, r1), (second, r2) = ranked[0], ranked[1]
        assert r1.score == r2.score == 52.5
        assert (first.name, second.name) == ("Leslie K.", "Ted L.")  # ids 4 < 13

    def test_candidate_direction_uses_same_scoring(self):
        sherlock = BY_NAME["Sherlock H."]
        ranked = m.rank_jobs_for_candidate(sherlock, JOBS)
        assert [j.title for j, _ in ranked] == ["Backend Detective"]
        direct = m.score_candidate_for_job(sherlock, BY_TITLE["Backend Detective"])
        assert ranked[0][1] == direct

    def test_best_candidate_per_job(self):
        best = {j.title: c.name for j, c, _ in m.best_candidate_per_job(JOBS, CANDIDATES)}
        assert best == {
            "Backend Detective": "Sherlock H.",
            "Rapid Prototyping Engineer": "Rick S.",
            "Developer Relations Lead": "Elle W.",
            "Engineering Manager, Chaos Team": "Leslie K.",
            "Incident Commander": "Olivia P.",
            "Sales Engineer": "Dwight S.",
        }

    def test_best_skips_jobs_nobody_qualifies_for(self):
        nobody = Job(99, "Ghost", 1, [], ["not-a-skill"])
        assert m.best_candidate_per_job([nobody], CANDIDATES) == []
