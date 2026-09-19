"""
Stale-application detection (Phase 7 stretch). Pure logic: given applications,
return which ones haven't moved status in N days. No notification/send
mechanism implemented yet — this returns the list for whatever channel
(email/UI banner) the team wires up later.
"""
from datetime import datetime, timedelta

from app.models.application import Application

STALE_AFTER_DAYS = 14


def find_stale_applications(applications: list[Application]) -> list[Application]:
    cutoff = datetime.utcnow() - timedelta(days=STALE_AFTER_DAYS)
    return [
        a for a in applications
        if a.status == "applied" and a.last_updated and a.last_updated < cutoff
    ]
