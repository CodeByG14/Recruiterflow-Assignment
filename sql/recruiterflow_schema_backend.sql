BEGIN;
-- ---------------------------------------------------------------------
-- RESET (optional): uncomment to drop everything and start clean.
-- ---------------------------------------------------------------------
-- DROP TABLE IF EXISTS job_required_skills CASCADE;
-- DROP TABLE IF EXISTS candidate_skills    CASCADE;
-- DROP TABLE IF EXISTS jobs                CASCADE;
-- DROP TABLE IF EXISTS candidates          CASCADE;
-- DROP TABLE IF EXISTS skills              CASCADE;
CREATE TABLE IF NOT EXISTS skills (
    id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT NOT NULL
                     CHECK (btrim(name) <> ''),
    name_normalized  TEXT GENERATED ALWAYS AS (lower(btrim(name))) STORED,
    CONSTRAINT skills_name_normalized_key UNIQUE (name_normalized)
);


-- ---------------------------------------------------------------------
-- candidates
-- traits is a TEXT[] (list of short labels). availability is free text
-- because the seed format is not known yet; tighten it once the data is
-- in (e.g. to an enum or a date) if the values turn out to be regular.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name              TEXT NOT NULL
                      CHECK (btrim(name) <> ''),
    experience_years  NUMERIC(4,1) NOT NULL
                      CHECK (experience_years >= 0),
    availability      TEXT,
    traits            TEXT[] NOT NULL DEFAULT '{}',
    quirk             TEXT,
    CONSTRAINT candidates_name_key UNIQUE (name)
);


-- ---------------------------------------------------------------------
-- jobs
-- min_experience = 0 is allowed (entry-level); the scoring code must
-- treat it as full experience credit rather than dividing by zero.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title             TEXT NOT NULL
                      CHECK (btrim(title) <> ''),
    min_experience    NUMERIC(4,1) NOT NULL
                      CHECK (min_experience >= 0),
    culture_keywords  TEXT[] NOT NULL DEFAULT '{}',
    tagline           TEXT,
    CONSTRAINT jobs_title_key UNIQUE (title)
);


-- ---------------------------------------------------------------------
-- candidate_skills: candidate N <-> N skill
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id  INTEGER NOT NULL
                  REFERENCES candidates (id) ON DELETE CASCADE,
    skill_id      INTEGER NOT NULL
                  REFERENCES skills (id) ON DELETE RESTRICT,
    PRIMARY KEY (candidate_id, skill_id)
);


-- ---------------------------------------------------------------------
-- job_required_skills: job N <-> N skill
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_required_skills (
    job_id    INTEGER NOT NULL
              REFERENCES jobs (id) ON DELETE CASCADE,
    skill_id  INTEGER NOT NULL
              REFERENCES skills (id) ON DELETE RESTRICT,
    PRIMARY KEY (job_id, skill_id)
);


-- ---------------------------------------------------------------------
-- Indexes
-- The composite primary keys already index lookups by candidate_id and
-- by job_id (their leading column). What they do NOT cover is the
-- reverse direction (skill -> candidates / skill -> jobs), so add those.
-- skills.name_normalized is already indexed by its UNIQUE constraint.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill_id
    ON candidate_skills (skill_id);

CREATE INDEX IF NOT EXISTS idx_job_required_skills_skill_id
    ON job_required_skills (skill_id);

COMMIT;
