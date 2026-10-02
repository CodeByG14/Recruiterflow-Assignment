# Recruiterflow - Candidate Matching System

## About

RecruiterFlow is prototyping **Recruiter Bot** — a backend service that ingests candidate profiles and job openings, then ranks the best matches for each. To keep things fun, the test data features a cast of well-known fictional characters with invented skills and quirks. Somewhere out there, Sherlock Holmes is applying to be a backend detective, and Michael Scott wants to be a sales engineer.

This project builds the backend that makes those matches happen.

---

## What's Implemented

### **Core Features**

**1. Data Ingestion**
- Seed script (`seed.py`) loads candidates and jobs from JSON files (`data/candidates.json`, `data/jobs.json`)
- Automatic database seeding on Docker startup

**2. Database Schema (Raw SQL Only)**
- 5 tables: `candidates`, `jobs`, `skills`, `candidate_skills`, `job_required_skills`
- Hand-written DDL in `sql/recruiterflow_schema_backend.sql`
- **No ORM or query builders** — all queries are raw, hand-written SQL

**3. Matching API**
- `GET /jobs/{id}/matches` — Ranked candidates for a job with scores and reasons
- `GET /candidates/{id}/matches` — Ranked jobs for a candidate (reverse matching)
- `GET /health` — Health check endpoint

**4. Matching Algorithm**
The scoring system combines three signals, each scored 0–100, then applies an availability multiplier:

- **60% - Skill Overlap:** share of the job's required skills the candidate has (matched ÷ required). Extra skills are not penalised. If no required skill matches, the score is 0.
- **25% - Experience Fit:** `min(candidate years ÷ job minimum years, 1)`. Falling short is penalised proportionally; exceeding the minimum earns no bonus.
- **15% - Culture Fit:** share of the job's culture keywords matched by a candidate trait (exact match, or the trait is a hyphen-separated part of the keyword, e.g. `calm` matches `calm-under-pressure`).
- **Availability Multiplier:** applied to the final score: Immediate ×1.00, 2 weeks ×0.95, Not looking ×0.70.

Ties are broken by skill score, then culture score, then sooner availability, then lower id. Each result includes a short reason generated from these same components.

All database access uses raw, hand-written SQL; scoring runs in Python.

### **Tech Stack**

- **Language:** Python 3.12
- **Framework:** FastAPI
- **Database:** PostgreSQL (raw SQL, no ORM)
- **Database Driver:** psycopg 3
- **Deployment:** Docker & Docker Compose
- **Testing:** pytest

### **Bonus Features**

✅ Comprehensive test suite  
✅ Interactive API documentation (FastAPI/Swagger UI)  
✅ Docker setup for one-command deployment  
✅ Health check endpoint with database connectivity test

---

## Design Decisions and Trade-offs

**How a match is scored.** Each candidate-job pair gets three signals on a 0–100 scale, combined as 60% skill overlap, 25% experience fit and 15% culture fit, then multiplied by an availability factor. Skill overlap is the share of the job's *required* skills the candidate has (matched ÷ required). It is deliberately not Jaccard: extra skills a candidate has do not lower the score, because a job only cares whether its requirements are met. Experience fit is `min(candidate years ÷ minimum years, 1)`. Falling short is penalised proportionally, and exceeding the minimum earns no bonus. Skills carry the most weight because they are the clearest signal of fit in the data. Experience mostly acts as a qualifier, since most candidates already exceed the minimums.

**Gate.** If none of a job's required skills match, the score is 0 whatever the experience or culture. Without this, a candidate with no relevant skills but 15 years of experience would outscore a partial match. Zero-score pairs are hidden by default; `?include_unqualified=true` shows them.

**Culture and availability.** Traits are compared with the job's culture keywords, by exact match or when the trait is a hyphen-separated part of the keyword (`calm` matches `calm-under-pressure`). Overlap in the seed data is sparse, so culture gets only 15%. I did not add a synonym list because it would be hand-tuned to this dataset, so near-synonyms such as "enthusiastic" and "energetic" are a known miss. Availability is a multiplier: 1.0 for Immediate, 0.95 for 2 weeks and 0.70 for Not looking. I penalise instead of excluding because several of the most experienced candidates are "Not looking", and excluding them would leave their own match lists empty. This is visible in the data: on skills and culture alone Michael S. is the best Sales Engineer match, but the penalty puts him third behind Dwight S. and Ted L., and the reason text says why.

**Ordering and reasons.** Ties break on final score, then skill score, then culture score, then sooner availability, then lower id, so results are fully deterministic. Reasons are built from templates using the same components as the score, so they always explain the number. No AI is used at runtime.

**Architecture trade-offs.** There is no `matches` table. Scores are computed per request from current data, so they can never go stale, at the cost of recomputing each time. That is fine at this size; at scale I would pre-filter candidates in SQL through the skill tables and cache results. All database access is raw, hand-written SQL, but the scoring itself runs in Python. That keeps the formula in one pure function that is unit-tested without a database, at the cost of the logic not living in SQL. I also considered a "title relevance" signal using a role-to-skills map and dropped it: the skills are not role-specific, the map would be built around the seed data, and it mostly double-counts skills already scored.

**Known limits.** The weights and multipliers are judgment calls, not learned from hiring outcomes. Skill matching is exact (no synonyms or skill levels), `quirk` and `tagline` are stored but not scored, and the API opens a database connection per request instead of using a pool. With more time I would make the weights configurable and add pagination.

## Setup

You can set up this project in two ways: using Docker (recommended) or manually without Docker.

---

## Option A: Docker Setup (Recommended)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/CodeByG14/Recruiterflow-Assignment
   cd Recruiterflow-Assignment
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Open `.env` and fill in the `DB_PASSWORD` field:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=recruiterflow
   DB_USER=recruiter
   DB_PASSWORD=your_secure_password_here
   ```

3. **Build and start all services**
   ```bash
   docker compose up --build
   ```
   
   Or run in detached mode (background):
   ```bash
   docker compose up --build -d
   ```

4. **Access the application**
   - Interactive API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### What Happens Automatically

When you run `docker compose up`, the following happens automatically:

1. ✅ PostgreSQL container starts
2. ✅ Database schema is created from `sql/recruiterflow_schema_backend.sql`
3. ✅ Database is seeded with candidates and jobs from `data/` folder
4. ✅ FastAPI backend starts and connects to the database

### Additional Docker Commands

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

**Stop containers:**
```bash
docker compose down
```

**Reset everything (including database):**
```bash
docker compose down -v
```

**Manually re-seed database:**
```bash
docker compose run --rm seed python seed.py --reset
```

**Check running containers:**
```bash
docker compose ps
```

---

## Option B: Manual Setup (Without Docker)

### Prerequisites
- Python 3.12 or higher installed
- PostgreSQL 12+ installed and running

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/CodeByG14/Recruiterflow-Assignment
   cd Recruiterflow-Assignment
   ```

2. **Create and activate virtual environment**
   
   Create virtual environment:
   ```bash
   python -m venv .venv
   ```
   
   Activate it:
   - **Linux/Mac:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     .venv\Scripts\activate
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   
   Create the database:
   ```bash
   createdb recruiterflow
   ```
   
   Create a database user (if not exists):
   ```bash
   psql -c "CREATE USER recruiter WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE recruiterflow TO recruiter;"
   ```

5. **Load database schema**
   ```bash
   psql -U recruiter -d recruiterflow -f sql/recruiterflow_schema_backend.sql
   ```
   
   You'll be prompted for the password you set for the `recruiter` user.

6. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Open `.env` and update the values:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=recruiterflow
   DB_USER=recruiter
   DB_PASSWORD=your_password_here
   ```

7. **Seed the database**
   ```bash
   python seed.py
   ```
   
   This will load candidates and jobs from the `data/` folder into the database.
   
   To reset and re-seed:
   ```bash
   python seed.py --reset
   ```

8. **Start the application**
   ```bash
   fastapi dev app/main.py
   ```
   
   The API will be available at:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

---

## 🧪 Testing the API (Using curl)

Once the application is running (via Docker or manual setup), you can test the following endpoints using curl commands:

### **Available Endpoints**

#### **1. Get Ranked Candidates for a Job**
```bash
GET /jobs/{job_id}/matches
```

Returns a ranked list of candidates that match the specified job, with scores and reasons.

**Example:**
```bash
curl http://localhost:8000/jobs/1/matches
```

---

#### **2. Get Ranked Jobs for a Candidate**
```bash
GET /candidates/{candidate_id}/matches
```

Returns a ranked list of jobs that match the specified candidate, with scores and reasons.

**Example:**
```bash
curl http://localhost:8000/candidates/1/matches
```

---

#### **3. Get Best Candidate for Each Job**
```bash
GET /matches/best
```

Returns the best matching candidate for each job opening.

**Example:**
```bash
curl http://localhost:8000/matches/best
```

---

### **Interactive API Documentation**

For a complete list of endpoints with interactive testing, visit:
- **Swagger UI:** http://localhost:8000/docs

---

## 🧪 Running Tests

Run the test suite with:
```bash
pytest
```
## Use of AI Tools

I used two AI tools. I started with **ChatGPT** to understand the task in detail: the requirements, the matching problem and the possible approaches. Then I wrote my own plan (`plan.md`) covering the stack, schema, endpoints and scoring idea.

I then used **Claude** as a design and pair-programming partner. I stay the lead, so I discussed my ideas and challenged them against the real seed data before letting it write anything. For example, I dropped my original "title relevance" signal after we looked at the data, and added culture fit and an availability multiplier instead. Only once the approach matched my own did I let Claude produce an initial implementation (scoring module, repositories, API, tests, Docker setup). I then built on top of it: ran the tests and curl checks against my own database, fixed the project layout, adapted `seed.py`, the Docker files and the README, and reviewed the algorithm and its trade-offs.

I use AI for readiness and productivity, to understand a problem faster and get a solid starting point.
