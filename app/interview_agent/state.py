"""
Agent orchestration layer: ties planner.py, tools.py, scorer.py, and nudge.py
together around the PracticeSession DB state. This is the ONLY module that
runs the agent's full loop (this is what makes it an 'agent' rather than a
single LLM call — it plans, acts, evaluates, and re-plans across turns).
"""
import json

from sqlalchemy.orm import Session

from app.models.practice_session import PracticeSession
from app.interview_agent.planner import build_plan
from app.interview_agent.tools import generate_question, save_answer
from app.interview_agent.scorer import score_answer
from app.interview_agent.nudge import decide_next_action


def start_session(db: Session, user_id: int, target_role: str, days: int) -> PracticeSession:
    plan = build_plan(db, user_id, target_role, days)
    session = PracticeSession(user_id=user_id, target_role=target_role, plan_json=json.dumps(plan))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_next_question(db: Session, session: PracticeSession) -> str:
    plan = json.loads(session.plan_json)
    day_plan = next(d for d in plan["days"] if d["day_number"] == session.current_day)
    return generate_question(day_plan["topic"], day_plan["focus_areas"], session.target_role)


def submit_answer(db: Session, session: PracticeSession, day_number: int, question: str, user_answer: str) -> dict:
    result = score_answer(question, user_answer)
    save_answer(db, session.id, day_number, question, user_answer, result["score"], result["feedback"])

    recent_scores = [a.score for a in session.answers[-3:]]
    next_action = decide_next_action(result["score"], recent_scores)

    if next_action == "advance":
        plan = json.loads(session.plan_json)
        if session.current_day < len(plan["days"]):
            session.current_day += 1
        else:
            session.status = "completed"
        db.commit()

    return {**result, "next_action": next_action}
