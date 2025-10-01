import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import MercadoLibreQuestion, MercadoLibreAccount, MercadoLibreProduct, QuestionStatus
from .meli_client import MercadoLibreClient

logger = logging.getLogger(__name__)


class QuestionService:
    """Service for managing MercadoLibre questions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_questions(
        self,
        account: MercadoLibreAccount,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync questions from MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        sync_stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            offset = 0
            limit = 50
            
            while True:
                # Get questions from MercadoLibre
                response = await client.get_questions(
                    seller_id=account.user_id,
                    status=status_filter,
                    offset=offset,
                    limit=limit
                )
                
                questions = response.get("results", [])
                if not questions:
                    break
                
                # Process each question
                for question_data in questions:
                    try:
                        await self._sync_question_to_db(account, question_data)
                        sync_stats["updated"] += 1
                    except Exception as e:
                        logger.error(f"Failed to sync question {question_data['id']}: {str(e)}")
                        sync_stats["failed"] += 1
                        sync_stats["errors"].append({
                            "question_id": question_data["id"],
                            "error": str(e)
                        })
                
                sync_stats["total"] += len(questions)
                
                if len(questions) < limit:
                    break
                
                offset += limit
            
            await self.db.commit()
            logger.info(f"Question sync completed: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Question sync failed: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _sync_question_to_db(
        self,
        account: MercadoLibreAccount,
        question_data: Dict[str, Any]
    ):
        """Sync single question to database"""
        
        # Get product if exists
        product = None
        if question_data.get("item_id"):
            result = await self.db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.meli_item_id == question_data["item_id"]
                )
            )
            product = result.scalar_one_or_none()
        
        # Check if question exists
        result = await self.db.execute(
            select(MercadoLibreQuestion).where(
                MercadoLibreQuestion.question_id == str(question_data["id"])
            )
        )
        question = result.scalar_one_or_none()
        
        # Map status
        status_mapping = {
            "UNANSWERED": QuestionStatus.UNANSWERED,
            "ANSWERED": QuestionStatus.ANSWERED,
            "CLOSED_UNANSWERED": QuestionStatus.CLOSED_UNANSWERED,
            "UNDER_REVIEW": QuestionStatus.UNDER_REVIEW
        }
        
        question_fields = {
            "account_id": account.id,
            "product_id": product.id if product else None,
            "question_id": str(question_data["id"]),
            "status": status_mapping.get(question_data["status"], QuestionStatus.UNANSWERED),
            "item_id": question_data.get("item_id"),
            "seller_id": str(question_data.get("seller_id")),
            "from_user_id": str(question_data.get("from", {}).get("id")),
            "text": question_data.get("text"),
            "answer": question_data.get("answer"),
            "date_created": self._parse_datetime(question_data.get("date_created")),
            "hold": question_data.get("hold", False),
            "deleted_from_listing": question_data.get("deleted_from_listing", False)
        }
        
        if question:
            # Update existing question
            for key, value in question_fields.items():
                setattr(question, key, value)
        else:
            # Create new question
            question = MercadoLibreQuestion(**question_fields)
            self.db.add(question)
    
    async def answer_question(
        self,
        account: MercadoLibreAccount,
        question_id: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """Answer a question on MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Send answer to MercadoLibre
            response = await client.answer_question(question_id, answer_text)
            
            # Update local database
            result = await self.db.execute(
                select(MercadoLibreQuestion).where(
                    MercadoLibreQuestion.question_id == question_id
                )
            )
            question = result.scalar_one_or_none()
            
            if question:
                question.status = QuestionStatus.ANSWERED
                question.answer = {
                    "text": answer_text,
                    "date_created": datetime.utcnow().isoformat(),
                    "status": "ACTIVE"
                }
            
            await self.db.commit()
            
            return {
                "success": True,
                "question_id": question_id,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question {question_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_unanswered_questions(
        self,
        account: MercadoLibreAccount,
        item_id: Optional[str] = None
    ) -> List[MercadoLibreQuestion]:
        """Get unanswered questions"""
        
        query = select(MercadoLibreQuestion).where(
            MercadoLibreQuestion.account_id == account.id,
            MercadoLibreQuestion.status == QuestionStatus.UNANSWERED
        )
        
        if item_id:
            query = query.where(MercadoLibreQuestion.item_id == item_id)
        
        result = await self.db.execute(
            query.order_by(MercadoLibreQuestion.date_created.desc())
        )
        
        return result.scalars().all()
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from MercadoLibre API"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None