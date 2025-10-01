from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
import logging
from ..database import get_db
from ..models import MercadoLibreAccount, MercadoLibreQuestion, QuestionStatus
from ..services.question_service import QuestionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_questions(
    account_id: int,
    status: Optional[str] = None,
    item_id: Optional[str] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List questions for an account"""
    try:
        query = select(MercadoLibreQuestion).where(
            MercadoLibreQuestion.account_id == account_id
        )
        
        if status:
            status_enum = QuestionStatus[status.upper()]
            query = query.where(MercadoLibreQuestion.status == status_enum)
        
        if item_id:
            query = query.where(MercadoLibreQuestion.item_id == item_id)
        
        query = query.offset(offset).limit(limit).order_by(MercadoLibreQuestion.date_created.desc())
        
        result = await db.execute(query)
        questions = result.scalars().all()
        
        return {
            "questions": [
                {
                    "id": q.id,
                    "question_id": q.question_id,
                    "item_id": q.item_id,
                    "status": q.status.value,
                    "text": q.text,
                    "answer": q.answer,
                    "from_user_id": q.from_user_id,
                    "date_created": q.date_created
                }
                for q in questions
            ],
            "total": len(questions),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unanswered")
async def get_unanswered_questions(
    account_id: int,
    item_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get unanswered questions"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        service = QuestionService(db)
        questions = await service.get_unanswered_questions(account, item_id)
        
        return {
            "questions": [
                {
                    "id": q.id,
                    "question_id": q.question_id,
                    "item_id": q.item_id,
                    "text": q.text,
                    "from_user_id": q.from_user_id,
                    "date_created": q.date_created
                }
                for q in questions
            ],
            "total": len(questions)
        }
    except Exception as e:
        logger.error(f"Failed to get unanswered questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{question_id}/answer")
async def answer_question(
    question_id: str,
    answer_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Answer a question"""
    try:
        # Get question
        result = await db.execute(
            select(MercadoLibreQuestion).where(
                MercadoLibreQuestion.question_id == question_id
            )
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        if question.status == QuestionStatus.ANSWERED:
            raise HTTPException(status_code=400, detail="Question already answered")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == question.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = QuestionService(db)
        result = await service.answer_question(
            account,
            question_id,
            answer_data.get("text", "")
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_questions(
    account_id: int,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Sync questions from MercadoLibre"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        service = QuestionService(db)
        result = await service.sync_questions(account, status_filter)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))