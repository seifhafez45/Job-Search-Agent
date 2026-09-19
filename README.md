# Personal Job Search & Application Agent

A conversational assistant that helps a job seeker through the entire job
search process: turning a CV into a structured profile, finding relevant
openings, spotting skill gaps, tailoring applications, preparing for
interviews, and keeping the whole search organized.

## Design principle

This system deliberately uses **five different approaches**, chosen per
task rather than defaulting to "add more AI":

| Approach | Used for | Where in the repo |
|---|---|---|
| **Normal LLM** | CV extraction, skill-gap comparison, resume/cover-letter tailoring | `llm/` |
| **RAG** | Career-resource Q&A ("what should I study for X?") | `rag/` |
| **Agent** | Interview-prep planner (adaptive day-by-day schedule, scoring, branching, nudges) | `agent/` |
| **Memory** | Persistent user profile, skill-gap history, practice history | `memory/` |
| **Normal software** | Job search filters, application tracker, reminders, auth | `job_search/`, `application_tracker/`, `auth/` |

There is exactly **one agent** in this system (the interview-prep
planner). Everything that doesn't need multi-step runtime branching is
deliberately implemented as a simpler, cheaper, more predictable
component.

## Repository layout

```
job_search_agent/
├── config/                # App configuration (env vars → typed settings)
├── database/              # Schema (SQL + ORM) and connection management
├── auth/                  # Password hashing, JWT, register/login logic
├── storage/                # Resume / generated-file storage on disk
├── memory/                 # Persistent user memory: schemas + read/write layer
├── llm/                    # "Normal LLM" tasks
│   ├── llm_client.py        #   single point of contact with the model provider
│   ├── cv_extraction.py     #   CV text → structured profile (Phase 2)
│   ├── skill_gap_analyzer.py#   profile vs. posting comparison (Phase 4)
│   ├── resume_tailor.py     #   resume bullet rewriting (Phase 4)
│   ├── cover_letter_generator.py
│   └── prompts/             #   every prompt template lives here, nowhere else
├── job_search/              # Phase 3: structured search against a live job API
├── rag/                     # Phase 5: career-resource RAG
│   ├── ingestion/            #   scrape + chunk
│   ├── embedding_service.py  #   text → vector
│   ├── vector_store.py       #   vector storage/query
│   └── retrieval_service.py  #   retrieval + grounded answer generation
├── agent/                   # Phase 6: the ONE agent — interview-prep planner
│   ├── planner.py             #   plan structure + adaptive sequencing
│   ├── mock_qna_scorer.py     #   scores a single mock answer
│   ├── nudge_engine.py        #   decides when to nudge the user
│   ├── agent_state.py         #   state object passed between the above
│   └── interview_prep_agent.py#   public entry point tying it together
├── application_tracker/     # Plain CRUD: applications + reminders
├── conversational/          # Intent classification + dispatch to the right module
├── api/                     # FastAPI app; routes are thin — logic lives upstream
├── utils/                   # Cross-cutting helpers (logging, file-type validation)
└── tests/                   # One test file per module under test
```

### One responsibility per file

Every file's docstring states what it **solely owns** and which
neighboring file owns the related concern it does *not* handle (e.g.
`llm/cv_extraction.py` calls `llm/llm_client.py` for the actual API call,
`llm/prompts/cv_extraction_prompt.py` for what to say, and
`memory/memory_store.py` to persist the result — it does none of those
three things itself). This is intentional: it's what let a 5-person team
build in parallel without merge conflicts (see the division of work
below, provided separately).

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in your real keys

python -c "from database.db import init_db; init_db()"

uvicorn api.main:app --reload
```

## Build order (matches the project's phased plan)

1. **Foundations** — `database/`, `auth/`, `storage/`
2. **Core pipeline** — `llm/cv_extraction.py` → `memory/`
3. **Structured search** — `job_search/`
4. **Skill-gap + tailoring** — `llm/skill_gap_analyzer.py`, `llm/resume_tailor.py`, `llm/cover_letter_generator.py`
5. **Career-resource RAG** — `rag/`
6. **Interview-prep Agent** — `agent/`
7. **Stretch** — semantic job search RAG, stale-application nudges, salary/market insights (not yet implemented — natural extension points are `rag/` and `application_tracker/`)

## Notes on this scaffold

This repo is a structural scaffold: every file is real, importable Python
with correct responsibilities, signatures, and cross-module wiring, but
some bodies are simplified (e.g. a single job-API provider, a basic
intent classifier) so the **architecture** — not incidental provider
details — is what stands out. Swapping providers, adding providers, or
hardening any single piece touches exactly one file, by design.
