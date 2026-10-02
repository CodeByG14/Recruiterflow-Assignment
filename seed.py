"""Load data/candidates.json and data/jobs.json into PostgreSQL.

    python seed.py            # seed an empty database (skips if data already exists)
    python seed.py --reset    # wipe the five tables, restart ids at 1, then reseed

Connection settings come from the same place as the API (app/config.py):
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, read from the environment
or from a .env file in the project root. Nothing is hard-coded here.
Raw, hand-written SQL only.
"""

import argparse
import json
from pathlib import Path

from app.db import connect

BASE_DIR = Path(__file__).resolve().parent  # seed.py sits in the project root
CANDIDATES_FILE = BASE_DIR / "data" / "candidates.json"
JOBS_FILE = BASE_DIR / "data" / "jobs.json"

RESET_SQL = """
TRUNCATE job_required_skills, candidate_skills, jobs, candidates, skills
RESTART IDENTITY CASCADE
"""

ALREADY_SEEDED_SQL = """
SELECT EXISTS (SELECT 1 FROM candidates)
    OR EXISTS (SELECT 1 FROM jobs) AS seeded
"""


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_or_create_skill(cur, skill_name: str) -> int:
    """Return the id of a skill, inserting it first if it does not exist.

    Select-then-insert (instead of ON CONFLICT) so this works with any
    unique-constraint layout on the skills table.
    """
    name = skill_name.strip().lower()

    cur.execute("SELECT id FROM skills WHERE lower(btrim(name)) = %s", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]

    cur.execute("INSERT INTO skills (name) VALUES (%s) RETURNING id", (name,))
    return cur.fetchone()["id"]


def seed_candidates(cur, candidates):
    for candidate in candidates:
        cur.execute(
            """
            INSERT INTO candidates (name, experience_years, availability, traits, quirk)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                candidate["name"],
                candidate["experience_years"],
                candidate["availability"],
                candidate["traits"],
                candidate["quirk"],
            ),
        )
        candidate_id = cur.fetchone()["id"]

        for skill in candidate["skills"]:
            skill_id = get_or_create_skill(cur, skill)
            cur.execute(
                """
                INSERT INTO candidate_skills (candidate_id, skill_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (candidate_id, skill_id),
            )


def seed_jobs(cur, jobs):
    for job in jobs:
        cur.execute(
            """
            INSERT INTO jobs (title, min_experience, culture_keywords, tagline)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                job["title"],
                job["min_experience"],
                job["culture_keywords"],
                job["tagline"],
            ),
        )
        job_id = cur.fetchone()["id"]

        for skill in job["required_skills"]:
            skill_id = get_or_create_skill(cur, skill)
            cur.execute(
                """
                INSERT INTO job_required_skills (job_id, skill_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (job_id, skill_id),
            )


def main():
    parser = argparse.ArgumentParser(description="Seed the Recruiter Bot database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete all existing rows (ids restart at 1) and seed again",
    )
    args = parser.parse_args()

    # Read the files first so a missing file fails before touching the database.
    candidates = load_json(CANDIDATES_FILE)
    jobs = load_json(JOBS_FILE)

    # One transaction: either everything is seeded or nothing is.
    with connect(autocommit=False) as conn:
        with conn.cursor() as cur:
            if args.reset:
                cur.execute(RESET_SQL)
            else:
                cur.execute(ALREADY_SEEDED_SQL)
                if cur.fetchone()["seeded"]:
                    print(
                        "Database already has data - nothing to do. Use --reset to reload."
                    )
                    return
            seed_candidates(cur, candidates)
            seed_jobs(cur, jobs)

    print(f"Seed completed: {len(candidates)} candidates, {len(jobs)} jobs.")


if __name__ == "__main__":
    main()
