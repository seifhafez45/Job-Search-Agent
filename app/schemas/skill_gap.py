# ============================================================
# الملف ده: عقد البيانات (Schema) الخاص بالـ skill_gap
#
# فايدته:
# - بيحدد شكل الداتا الداخلة للـ API (Input): الـ profile + الوظيفة
# - بيحدد شكل الداتا الراجعة (Output): النسبة والنقاط القوية والمهارات الناقصة
#
# بيعمل إيه:
# - بيستورد ProfileOut و JobPosting الموجودين، فمفيش حقل بيتعرّف مرتين
# - ده الملف اللي بتتفق عليه مع Person 4 وباقي الفريق
#
# مفيش فيه منطق خالص، تعريفات بس.
# ============================================================
"""Pydantic shapes for the skill-gap API. Reuses ProfileOut and JobPosting so no field is defined twice."""
from pydantic import BaseModel, Field

from app.schemas.job import JobPosting
from app.schemas.profile import ProfileOut


class SkillGapRequest(BaseModel):
    profile: ProfileOut
    job: JobPosting


class SkillGapResult(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    strengths: list[str] = []
    missing_skills: list[str] = []
    recommendations: list[str] = []
    reasoning: str = ""