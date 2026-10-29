"""Staged integration test for app/tailoring/cover_letter.py (REAL Tavily + REAL LLM).

Stages (each isolated, a failure in one does not stop the rest):
  1. Tavily search      raw results, key configured, results mention the company
  2. research_company   raw LLM brief, UNRELIABLE flag, citations, length
  3. draft_cover_letter length, cliches, citation markers, odd unicode, grounding words
  4. critique (good)    critic output is valid JSON (not silently failing open)
  5. critique (bad)     critic must catch a deliberately fabricated letter
  6. full pipeline      score progression per iteration + final letter

Every intermediate result goes to the trace file. A PASS/FAIL table is printed at the end.

Env vars (all optional):
  COMPANY=Stripe  JOB_TITLE="Backend Engineer"  MAX_REVISIONS=2
  TRACE_FILE=/app/tests/pipeline_trace.txt
"""
import importlib
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

try:
    sys.stdout.reconfigure(encoding="utf-8")   # avoid Windows console eating unicode
except Exception:
    pass

# ---- edit these ----
MODULE = "app.tailoring.cover_letter"
COMPANY = os.getenv("COMPANY", "Stripe")        # use a REAL company, not a made-up one
JOB_TITLE = os.getenv("JOB_TITLE", "Backend Engineer")
MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "2"))
TRACE_FILE = Path(os.getenv("TRACE_FILE", "/app/tests/pipeline_trace.txt"))
# --------------------

mod = importlib.import_module(MODULE)

JD = ("We are hiring a Python backend engineer with FastAPI, PostgreSQL and Docker "
      "experience to build and scale payment APIs.")
SUMMARY = "Backend developer, 3 years of Python, FastAPI and PostgreSQL."
BULLETS = [
    "Built a FastAPI service handling 50k requests/day",
    "Cut PostgreSQL query time by 40% through indexing",
    "Containerised 5 services with Docker",
]
BAD_LETTER = (
    "Dear Hiring Team,\n\nI am so passionate about this role. As a former Staff Engineer at Google "
    "I led a team of 20 engineers and built Kubernetes clusters serving 10 million users. "
    "I hold a PhD in distributed systems and speak five languages. I am a team player and "
    "excited to apply.\n\nSincerely,\nCandidate"
)
CLICHES = ["i am excited to apply", "passionate", "team player", "fast-paced"]
ODD_CHARS = "\u202f\u00a0\u2011\u2010\u2009\u200b"

# ------------------------------------------------------------------ helpers
lines, checks, ctx, LLM_LOG = [], [], {}, []


def add(title, body=""):
    lines.extend(["", "=" * 72, title, "=" * 72, str(body)])


def check(name, ok, detail=""):
    ok = bool(ok)
    checks.append((name, ok, detail))
    add(f"CHECK [{'PASS' if ok else 'FAIL'}] {name}", detail)


def run_stage(name, fn):
    add(f"STAGE: {name}")
    print(f"-> {name}")
    try:
        fn()
    except Exception as e:
        tb = traceback.format_exc()
        check(f"{name}: no exception", False, f"{type(e).__name__}: {e}")
        add(f"{name}: TRACEBACK", tb)


# Record every LLM call (role, latency, raw output) while still calling the real client
_real_complete = mod.complete
_ROLES = ("RESEARCH_COMPANY_SYSTEM_PROMPT", "DRAFT_SYSTEM_PROMPT",
          "CRITIQUE_SYSTEM_PROMPT", "COVER_LETTER_SYSTEM_PROMPT")


def recording_complete(system_prompt, user_prompt, *a, **kw):
    role = next((r.replace("_SYSTEM_PROMPT", "") for r in _ROLES
                 if system_prompt == getattr(mod, r, None)), "UNKNOWN")
    t = time.time()
    out = _real_complete(system_prompt, user_prompt, *a, **kw)
    LLM_LOG.append({"role": role, "seconds": round(time.time() - t, 1), "output": out})
    return out


def last_raw(role, since):
    for entry in reversed(LLM_LOG[since:]):
        if entry["role"] == role:
            return entry["output"]
    return None


def words(text):
    return len(text.split())


def strip_fences(raw):
    return raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


# ------------------------------------------------------------------ stages
def s1_search():
    key = getattr(mod.settings, "tavily_api_key", None)
    check("Tavily API key configured", bool(key), "set" if key else "MISSING (settings.tavily_api_key)")
    queries = [(f"{COMPANY} company overview products mission", 4),
               (f"{COMPANY} recent news announcements 2026", 3)]
    all_results = []
    for q, n in queries:
        res = mod._web_search(q, n)
        body = "\n\n".join(
            f"[{i}] {r.get('title')}\n    {r.get('url')}\n    {(r.get('content') or '')[:300]}"
            for i, r in enumerate(res, 1)) or "(no results)"
        add(f"Tavily query: {q!r}  (max {n})", body)
        check(f"search returned results: {q}", len(res) > 0, f"{len(res)} results")
        all_results += res
    check("every result has title/url/content",
          all(r.get(k) for r in all_results for k in ("title", "url", "content")))
    hits = sum(COMPANY.lower() in ((r.get("title") or "") + (r.get("content") or "")).lower()
               for r in all_results)
    check("results actually mention the company", hits > 0, f"{hits}/{len(all_results)} results mention it")


def s2_research():
    start = len(LLM_LOG)
    brief = mod.research_company(COMPANY, JOB_TITLE)
    raw = last_raw("RESEARCH_COMPANY", start)
    add("research_company: raw LLM output",
        raw if raw is not None else "(no LLM call happened: search failed or returned nothing)")
    add("research_company: returned brief", brief or "(empty)")
    check("LLM was called (search gave usable sources)", raw is not None)
    check("LLM did not answer UNRELIABLE", raw is not None and "UNRELIABLE" not in raw)
    check("brief is non-empty", bool(brief.strip()))
    check("brief has citations like [1]", re.search(r"\[\d+\]", brief or ""))
    check("brief <= ~200 words", words(brief) <= 230, f"{words(brief)} words")
    ctx["brief"] = brief


def s3_draft():
    start = len(LLM_LOG)
    letter = mod.draft_cover_letter(SUMMARY, JOB_TITLE, COMPANY, JD, ctx.get("brief", ""), BULLETS)
    add("draft_cover_letter: output", letter)
    low = letter.lower()
    check("draft length 200-400 words", 200 <= words(letter) <= 400, f"{words(letter)} words")
    check("no citation markers like [2]", not re.search(r"\[\d+\]", letter))
    found = [c for c in CLICHES if c in low]
    check("no banned cliches", not found, f"found: {found}")
    bad = sorted({hex(ord(c)) for c in letter if c in ODD_CHARS})
    check("no odd unicode spaces/hyphens", not bad, f"found: {bad}")
    check("mentions the company", COMPANY.lower() in low)
    check("mentions a candidate skill (FastAPI)", "fastapi" in low)
    ctx["letter"] = letter


def s4_critique_good():
    start = len(LLM_LOG)
    result = mod.critique_cover_letter(ctx["letter"], JOB_TITLE, COMPANY, JD,
                                       ctx.get("brief", ""), SUMMARY, BULLETS)
    raw = last_raw("CRITIQUE", start)
    add("critique (real draft): raw LLM output", raw)
    add("critique (real draft): parsed result", json.dumps(result, indent=2))
    parsed_ok = True
    try:
        json.loads(raw)
    except Exception as e:
        parsed_ok = False
        add("JSON parse error on raw critique", f"{type(e).__name__}: {e}")
    check("critic output is valid JSON as-is", parsed_ok,
          "if this fails the code silently fails open with score 8 (add fence stripping)")
    try:
        json.loads(strip_fences(raw))
        check("critic output is valid JSON after fence stripping", True)
    except Exception:
        check("critic output is valid JSON after fence stripping", False)
    check("score is an int 1-10", isinstance(result["score"], int) and 1 <= result["score"] <= 10,
          f"score={result['score']}")


def s5_critique_bad():
    start = len(LLM_LOG)
    result = mod.critique_cover_letter(BAD_LETTER, JOB_TITLE, COMPANY, JD,
                                       ctx.get("brief", ""), SUMMARY, BULLETS)
    add("critique (fabricated letter): raw LLM output", last_raw("CRITIQUE", start))
    add("critique (fabricated letter): parsed result", json.dumps(result, indent=2))
    check("critic scores fabricated letter below pass (8)", result["score"] < 8, f"score={result['score']}")
    check("critic reports issues / unsupported claims", len(result["issues"]) > 0,
          f"{len(result['issues'])} issues")


def s6_full_pipeline():
    progress = {"drafts": 0, "critiques": []}
    orig_draft, orig_crit = mod.draft_cover_letter, mod.critique_cover_letter

    def draft_spy(*a, **kw):
        progress["drafts"] += 1
        out = orig_draft(*a, **kw)
        label = "INITIAL DRAFT" if progress["drafts"] == 1 else f"REVISION #{progress['drafts'] - 1}"
        fb = kw.get("feedback")
        add(f"pipeline: {label}",
            (("feedback addressed:\n" + json.dumps(fb["issues"], indent=2) + "\n\n") if fb else "") + out)
        return out

    def crit_spy(*a, **kw):
        out = orig_crit(*a, **kw)
        progress["critiques"].append(out["score"])
        add(f"pipeline: CRITIQUE #{len(progress['critiques'])}",
            f"score: {out['score']}\nissues:\n{json.dumps(out['issues'], indent=2)}")
        return out

    with patch.object(mod, "draft_cover_letter", draft_spy), \
         patch.object(mod, "critique_cover_letter", crit_spy):
        letter, brief = mod.generate_cover_letter_with_critique(
            SUMMARY, JOB_TITLE, COMPANY, JD, BULLETS, max_revisions=MAX_REVISIONS)

    add("pipeline: score progression", progress["critiques"])
    add("pipeline: FINAL LETTER", letter)
    add("pipeline: FINAL BRIEF", brief or "(empty)")
    check("pipeline returned a non-empty letter", bool(letter.strip()))
    check(f"drafts <= 1 + max_revisions ({1 + MAX_REVISIONS})", progress["drafts"] <= 1 + MAX_REVISIONS,
          f"{progress['drafts']} drafts")
    check("critic ran at least once", len(progress["critiques"]) >= 1)
    if len(progress["critiques"]) > 1:
        check("score did not get worse overall", progress["critiques"][-1] >= progress["critiques"][0],
              f"scores: {progress['critiques']}")
    check("critic is not stuck on a constant 8 with no issues (fail-open smell)",
          not (len(progress["critiques"]) == 1 and progress["critiques"][0] == 8),
          f"scores: {progress['critiques']}")
    ctx["final"] = letter


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    add("RUN INFO", f"{datetime.now().isoformat(timespec='seconds')}\n"
                    f"company={COMPANY}  job_title={JOB_TITLE}  max_revisions={MAX_REVISIONS}")

    with patch.object(mod, "complete", recording_complete):
        run_stage("1. Tavily search", s1_search)
        run_stage("2. research_company", s2_research)
        run_stage("3. draft_cover_letter", s3_draft)
        if "letter" in ctx:
            run_stage("4. critique (real draft)", s4_critique_good)
        run_stage("5. critique (fabricated letter)", s5_critique_bad)
        run_stage("6. full pipeline", s6_full_pipeline)

    add("LLM CALL LOG", "\n".join(f"{i:>2}. {e['role']:<18} {e['seconds']:>5}s  {len(e['output'])} chars"
                                  for i, e in enumerate(LLM_LOG, 1)))

    summary = "\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}" + (f"  ({d})" if d and not ok else "")
                        for n, ok, d in checks)
    add("SUMMARY", summary)

    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACE_FILE.write_text("\n".join(lines).lstrip("\n") + "\n", encoding="utf-8")

    print("\n" + summary)
    if "final" in ctx:
        print("\nFINAL LETTER:\n" + ctx["final"])
    failed = sum(not ok for _, ok, _ in checks)
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed. Trace: {TRACE_FILE}")
    sys.exit(1 if failed else 0)