"""Test for app/tailoring/cover_letter.py::generate_cover_letter_with_critique

MOCK=1 (default): LLM + Tavily are mocked, 3 scenarios are run and asserted.
MOCK=0          : real LLM + real Tavily, one run (costs tokens).

Intermediate results (company brief, every draft, every critique) are written to
tests/cover_letter_trace.txt. The final letter is printed to the console.
"""
import importlib
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# ---- edit these ----
MODULE = "app.tailoring.cover_letter"
TRACE_FILE = Path(__file__).parent / "cover_letter_trace.txt"   # lives in tests/
# --------------------

mod = importlib.import_module(MODULE)
MOCK = os.getenv("MOCK", "1") == "1"

JOB_TITLE = "Backend Engineer"
COMPANY = "Acme Corp"
JD = "We are hiring a Python backend engineer with FastAPI, PostgreSQL and Docker experience."
SUMMARY = "Backend developer, 3 years of Python, FastAPI and PostgreSQL."
BULLETS = [
    "Built a FastAPI service handling 50k requests/day",
    "Cut PostgreSQL query time by 40% through indexing",
    "Containerised 5 services with Docker",
]


class Trace:
    """Collects intermediate results and writes them to a text file."""

    def __init__(self):
        self.lines = []

    def add(self, title, body=""):
        self.lines += ["", "=" * 70, title, "=" * 70, str(body)]

    def save(self):
        TRACE_FILE.write_text("\n".join(self.lines).lstrip("\n") + "\n", encoding="utf-8")


def run_scenario(name, trace, critique_replies=None, max_revisions=3, pass_score=8):
    """Run the pipeline once, logging every intermediate step into `trace`.

    critique_replies: raw strings the mocked critique LLM returns, in order (MOCK only).
    """
    trace.add(f"SCENARIO: {name}",
              f"max_revisions={max_revisions}, pass_score={pass_score}, "
              f"mode={'MOCK' if MOCK else 'REAL'}")

    counters = {"draft": 0, "critique": 0}

    # ---- spies: call the real function, log what went in/out ----
    orig_research = mod.research_company
    orig_draft = mod.draft_cover_letter
    orig_critique = mod.critique_cover_letter

    def research_spy(company, job_title):
        out = orig_research(company, job_title)
        trace.add("STEP: COMPANY BRIEF", out or "(empty - research failed or returned nothing)")
        return out

    def draft_spy(*args, **kwargs):
        counters["draft"] += 1
        n = counters["draft"]
        feedback = kwargs.get("feedback")
        label = "INITIAL DRAFT" if n == 1 else f"REVISION #{n - 1}"
        out = orig_draft(*args, **kwargs)
        body = ""
        if feedback:
            body += "Feedback addressed:\n" + json.dumps(feedback["issues"], indent=2) + "\n\n"
        trace.add(f"STEP: {label}", body + out)
        return out

    def critique_spy(*args, **kwargs):
        counters["critique"] += 1
        out = orig_critique(*args, **kwargs)
        trace.add(f"STEP: CRITIQUE #{counters['critique']}",
                  f"score  : {out['score']}\nissues :\n{json.dumps(out['issues'], indent=2)}")
        return out

    # ---- mocked LLM / search (MOCK only) ----
    replies = list(critique_replies or [])
    draft_calls = {"n": 0}

    def fake_complete(system_prompt, user_prompt, *a, **kw):
        if system_prompt == mod.RESEARCH_COMPANY_SYSTEM_PROMPT:
            return "Acme Corp builds logistics software [1]. Launched a routing API in 2026 [2]."
        if system_prompt == mod.CRITIQUE_SYSTEM_PROMPT:
            return replies.pop(0)
        if system_prompt == mod.DRAFT_SYSTEM_PROMPT:
            draft_calls["n"] += 1
            return f"MOCK LETTER v{draft_calls['n']}"
        raise AssertionError("unexpected system prompt")

    fake_search = lambda query, n=4: [
        {"title": "Acme overview", "url": "https://acme.example/about", "content": "Acme builds logistics software. " * 5},
        {"title": "Acme news", "url": "https://acme.example/news", "content": "Acme launched a routing API. " * 5},
    ]

    patches = [
        patch.object(mod, "research_company", research_spy),
        patch.object(mod, "draft_cover_letter", draft_spy),
        patch.object(mod, "critique_cover_letter", critique_spy),
    ]
    if MOCK:
        patches += [patch.object(mod, "complete", fake_complete),
                    patch.object(mod, "_web_search", fake_search)]

    for p in patches:
        p.start()
    try:
        letter, brief = mod.generate_cover_letter_with_critique(
            SUMMARY, JOB_TITLE, COMPANY, JD, BULLETS,
            max_revisions=max_revisions, pass_score=pass_score,
        )
    finally:
        for p in patches:
            p.stop()

    trace.add("FINAL OUTPUT (letter)", letter)
    trace.add("FINAL OUTPUT (brief)", brief or "(empty)")
    trace.add("COUNTS", f"drafts={counters['draft']}, critiques={counters['critique']}")
    return letter, brief, counters


def crit(score, issues=None, unsupported=None):
    return json.dumps({"score": score, "issues": issues or [], "unsupported_claims": unsupported or []})


if __name__ == "__main__":
    trace = Trace()
    trace.add("RUN INFO", f"{datetime.now().isoformat(timespec='seconds')}  mode={'MOCK' if MOCK else 'REAL'}")

    if MOCK:
        # 1) Improves over time: 5 -> 7 -> 9. Expect 3 drafts, 3 critiques, final = v3
        letter, brief, c = run_scenario(
            "improves until pass",
            trace,
            critique_replies=[
                crit(5, ["Too generic"], ["Claims 10 years of experience"]),
                crit(7, ["Mention Docker"]),
                crit(9),
            ],
        )
        assert letter == "MOCK LETTER v3" and c == {"draft": 3, "critique": 3}, (letter, c)
        assert "[1]" in brief
        print("1) improves until pass     -> OK, final letter:", letter)

        # 2) Never passes: loop must stop at max_revisions. Expect 1 + 2 = 3 drafts
        letter, brief, c = run_scenario(
            "never passes -> capped by max_revisions",
            trace,
            critique_replies=[crit(3, ["Bad"])] * 2,
            max_revisions=2,
        )
        assert c == {"draft": 3, "critique": 2}, c
        print("2) capped at max_revisions -> OK, final letter:", letter)

        # 3) Critique returns garbage: fails open, no revisions. Expect 1 draft
        letter, brief, c = run_scenario(
            "critique returns invalid JSON -> fail open",
            trace,
            critique_replies=["not json at all"],
        )
        assert c == {"draft": 1, "critique": 1}, c
        print("3) invalid critique JSON   -> OK (fail open), final letter:", letter)
    else:
        letter, brief, c = run_scenario("real run", trace)
        print("FINAL LETTER:\n", letter)
        print("\nBRIEF:\n", brief)

    trace.save()
    print(f"\nIntermediate results written to {TRACE_FILE}")