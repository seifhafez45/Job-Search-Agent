"""
Nudge/branching decision logic ONLY: given a score and progress, decide whether
to repeat the current topic, advance to the next day, or nudge the user to take
a break. Pure decision function — no LLM call, no DB access, easy to unit test.
"""

REPEAT_THRESHOLD = 5.0
BREAK_STREAK_THRESHOLD = 2  # consecutive low scores before suggesting a break


def decide_next_action(score: float, recent_scores: list[float]) -> str:
    """Returns one of: 'repeat_topic' | 'advance' | 'nudge_break'."""
    low_streak = sum(1 for s in (recent_scores + [score])[-BREAK_STREAK_THRESHOLD:] if s < REPEAT_THRESHOLD)
    if low_streak >= BREAK_STREAK_THRESHOLD:
        return "nudge_break"
    if score < REPEAT_THRESHOLD:
        return "repeat_topic"
    return "advance"
