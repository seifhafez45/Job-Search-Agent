"""
Unit tests for app/interview_agent/: nudge.py decision logic (pure function, no mocks needed)
is the highest-value test target here — covers repeat/advance/nudge_break branching.
"""
from app.interview_agent.nudge import decide_next_action


def test_advance_on_high_score():
    assert decide_next_action(score=8.0, recent_scores=[7.0]) == "advance"


def test_repeat_on_low_score():
    assert decide_next_action(score=3.0, recent_scores=[6.0]) == "repeat_topic"


def test_nudge_break_on_low_streak():
    assert decide_next_action(score=3.0, recent_scores=[4.0]) == "nudge_break"
