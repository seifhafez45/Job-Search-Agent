"""HTTP endpoint for career-resource Q&A ONLY."""
from fastapi import APIRouter, Depends

from app.common.dependencies import get_current_user
from app.career_rag.service import answer_study_question

router = APIRouter()


@router.get("/ask")
def ask(question: str, user=Depends(get_current_user)):
    return answer_study_question(question)
