# Personal Job Search & Application Agent

A conversational assistant that supports a job seeker end-to-end: CV → structured
profile → job search → skill-gap analysis → tailored applications → interview prep →
organized tracking.

## Design principle

Every feature uses the **simplest technology that actually fits the task** — not the
flashiest one. Five approaches are mixed deliberately:

| Approach | Used for | Where |
|---|---|---|
| **Normal LLM** | Reasoning/writing on info already at hand | `cv_extraction/`, `skill_gap/`, `tailoring/` |
| **RAG** | Answers depending on external, changing content | `career_rag/` (Phase 5), `job_rag/` (Phase 7 stretch) |
| **Agent** | Multi-step planning + runtime branching | `interview_agent/` (the one agent in the system) |
| **Memory** | Persistent facts about the user | `memory/` |
| **Normal software** | Plain infra, no AI needed | `auth/`, `job_search/`, `application_tracker/`, `storage/` |

Only **one** agent exists in this system — the interview-prep planner. Everything
that can be a plain LLM call or plain code deliberately is one, instead of being
wrapped in agent machinery it doesn't need.

## Repository structure

```
job-search-agent/
├── app/
│   ├── main.py                 # FastAPI app assembly only — mounts routers
│   ├── config.py                # Single source of settings (env vars)
│   ├── database.py              # DB engine/session setup only
│   │
│   ├── models/                  # SQLAlchemy tables (Phase 1 — the foundation)
│   ├── schemas/                 # Pydantic request/response contracts (API shape, decoupled from DB)
│   ├── common/                  # Cross-cutting: exceptions, logging, shared dependencies
│   │
│   ├── auth/                    # Normal software — signup/login/JWT
│   ├── storage/                 # Normal software — raw resume file storage
│   ├── memory/                  # Memory pillar — assembles persistent user context
│   ├── llm/                     # Shared LLM client — every "Normal LLM" module uses this
│   │
│   ├── cv_extraction/           # Normal LLM — Phase 2: resume file → structured profile
│   ├── job_search/              # Normal software — Phase 3: structured job API search
│   ├── skill_gap/               # Normal LLM — Phase 4a: CV vs. posting comparison
│   ├── tailoring/                # Normal LLM — Phase 4b: resume bullets + cover letters
│   ├── career_rag/              # RAG — Phase 5: scrape/embed/retrieve study resources
│   ├── interview_agent/         # Agent — Phase 6: adaptive day-by-day interview prep
│   ├── application_tracker/     # Normal software — Phase 1/7: CRUD + stale-application nudges
│   └── job_rag/                 # RAG (stretch) — Phase 7: semantic/loose job search
│
├── migrations/                  # Alembic migrations (schema changes over time)
├── scripts/                     # One-off/batch jobs: seed_db.py, ingest_career_resources.py
├── tests/                       # One test file per feature module, mirrors app/ 1:1
├── frontend/                    # Placeholder — point any client at the API (see frontend/README.md)
│
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── alembic.ini
```

### Module rules (why nothing overlaps)

- Every feature folder has **one router.py** (HTTP only) and **one service.py**
  (orchestration only). Routers never contain business logic; services never
  touch `Request`/`Response` objects.
- **`models/`** = database shape. **`schemas/`** = API shape. They are never the
  same file, so a schema change doesn't force a migration and vice versa.
- Anything that calls the LLM imports `complete()` from **`llm/client.py`** —
  no feature module instantiates its own Anthropic client.
- Anything that needs persistent facts about the user calls
  **`memory/memory_store.py`** — no feature module hand-rolls its own multi-table
  join for "what do we know about this user."
- `career_rag/` and `job_rag/` both use the shared `vector_store.py` machinery
  from `career_rag/`, just with different collection names — the Chroma wrapper
  itself is written once.
- File parsing (`cv_extraction/parser.py`) is separate from file storage
  (`storage/resume_storage.py`) is separate from LLM interpretation
  (`cv_extraction/service.py`) — three distinct concerns, three distinct files.

## Setup

```bash
cp .env.example .env          # fill in ANTHROPIC_API_KEY, DATABASE_URL, etc.
pip install -r requirements.txt

# Option A: quick local dev (no migration history)
python -m scripts.seed_db

# Option B: proper migrations
alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn app.main:app --reload
```

Or via Docker:

```bash
docker-compose up --build
```

API docs are auto-generated at `http://localhost:8000/docs`.

## Build order (matches the phases)

1. **Foundations** — `models/`, `auth/`, `storage/`
2. **Core pipeline** — `cv_extraction/` → `memory/`
3. **Structured search** — `job_search/`
4. **Skill-gap + tailoring** — `skill_gap/`, `tailoring/`
5. **Career-resource RAG** — `career_rag/`
6. **Interview-prep Agent** — `interview_agent/` (depends on 2, 4, 5)
7. **Stretch** — `job_rag/`, `application_tracker/reminders.py`, market-insight summaries

## Running tests

```bash
pytest tests/ -v
```
