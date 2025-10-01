"""
Question and messaging tasks for MercadoLibre
"""
from .celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def process_question(question_id: str):
    logger.info(f"Processing question {question_id}")
    return {"status": "processed", "question_id": question_id}

@celery_app.task
def send_answer(question_id: str, answer: str):
    logger.info(f"Sending answer to question {question_id}")
    return {"status": "sent", "question_id": question_id}