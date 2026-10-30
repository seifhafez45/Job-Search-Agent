# ============================================================
# الملف ده: طبقة الـ HTTP الخاصة بالـ skill_gap (Endpoints)
#
# فايدته:
# - بيستقبل الطلبات من الـ frontend أو من باقي الفريق
#
# بيعمل إيه:
# - POST /skill-gap/analyze: بيستقبل profile + job
# - بيمرّرهم لـ service.py
# - بيحوّل الأخطاء لـ HTTP status مناسب (502 لو الـ LLM رجّع رد غلط)
#
# ملحوظة: الـ prefix والـ tags بيتحددوا في app/main.py مش هنا.
# مفيش فيه منطق، شغله استقبال وتمرير وإرجاع بس.
# ============================================================
"""HTTP layer for skill-gap analysis. No logic here; delegates to service.py."""
from fastapi import APIRouter, HTTPException

from app.schemas.skill_gap import SkillGapRequest, SkillGapResult
from app.skill_gap.service import SkillGapError, analyze_skill_gap

router = APIRouter()


@router.post("/analyze", response_model=SkillGapResult)
async def analyze(req: SkillGapRequest) -> SkillGapResult:
    try:
        return await analyze_skill_gap(req)
    except SkillGapError as e:
        raise HTTPException(status_code=502, detail=str(e))