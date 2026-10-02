"""The real seed data as plain objects, so tests need no database.

IDs follow seed order (1..15 candidates, 1..6 jobs), which is what the
identity columns produce when seeding an empty database in this order.
"""

from app.models import Candidate, Job


def _c(id, name, years, availability, traits, skills):
    return Candidate(id, name, years, availability, list(traits), list(skills))


def _j(id, title, min_exp, culture, skills):
    return Job(id, title, min_exp, list(culture), list(skills))


CANDIDATES = [
    _c(1, "Sherlock H.", 8, "Immediate", ["analytical", "blunt"], ["deduction", "forensics", "pattern-recognition"]),
    _c(2, "Hermione G.", 4, "2 weeks", ["detail-oriented", "overachiever"], ["public-speaking", "research", "time-management"]),
    _c(3, "Tony S.", 12, "Not looking", ["confident", "innovative"], ["leadership", "rapid-prototyping", "systems-design"]),
    _c(4, "Leslie K.", 6, "Immediate", ["tenacious", "organized"], ["project-management", "public-speaking", "stakeholder-management"]),
    _c(5, "Ron S.", 15, "Not looking", ["stubborn", "principled"], ["minimalism", "negotiation", "woodworking"]),
    _c(6, "Rick S.", 20, "Immediate", ["genius", "reckless"], ["chemistry", "rapid-prototyping", "systems-design"]),
    _c(7, "Elle W.", 3, "Immediate", ["optimistic", "sharp"], ["persuasion", "public-speaking", "research"]),
    _c(8, "MacGyver", 10, "2 weeks", ["calm", "improviser"], ["chemistry", "rapid-prototyping", "resourcefulness", "systems-design"]),
    _c(9, "Sheldon C.", 9, "Immediate", ["rigid", "brilliant"], ["pattern-recognition", "research", "theoretical-analysis"]),
    _c(10, "Katniss E.", 5, "Immediate", ["resilient", "decisive"], ["crisis-management", "precision", "strategy"]),
    _c(11, "Michael S.", 11, "Not looking", ["enthusiastic", "chaotic"], ["public-speaking", "sales", "team-building"]),
    _c(12, "Olivia P.", 13, "2 weeks", ["decisive", "intense"], ["crisis-management", "leadership", "negotiation", "strategy"]),
    _c(13, "Ted L.", 7, "Immediate", ["empathetic", "persistent"], ["mentorship", "optimism", "public-speaking", "team-building"]),
    _c(14, "Miranda P.", 18, "Not looking", ["demanding", "decisive"], ["leadership", "negotiation", "precision", "stakeholder-management"]),
    _c(15, "Dwight S.", 9, "Immediate", ["intense", "loyal"], ["loyalty", "negotiation", "sales", "security"]),
]

JOBS = [
    _j(1, "Backend Detective", 3, ["analytical", "autonomous"], ["deduction", "forensics", "pattern-recognition"]),
    _j(2, "Rapid Prototyping Engineer", 2, ["innovative", "fast-paced"], ["rapid-prototyping", "systems-design"]),
    _j(3, "Developer Relations Lead", 2, ["energetic", "curious"], ["public-speaking", "research"]),
    _j(4, "Engineering Manager, Chaos Team", 5, ["empathetic", "organized"], ["leadership", "stakeholder-management", "team-building"]),
    _j(5, "Incident Commander", 4, ["decisive", "calm-under-pressure"], ["crisis-management", "negotiation", "strategy"]),
    _j(6, "Sales Engineer", 3, ["enthusiastic", "persistent"], ["negotiation", "public-speaking", "sales"]),
]

BY_NAME = {c.name: c for c in CANDIDATES}
BY_TITLE = {j.title: j for j in JOBS}
