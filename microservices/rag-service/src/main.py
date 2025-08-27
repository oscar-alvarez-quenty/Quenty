from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from .database import get_db, init_database, microservice_connector
from .services import RAGService, IngestionService
from .config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Conversation, Message, IndexingJob, Document
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
query_counter = Counter('rag_queries_total', 'Total number of RAG queries')
query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration in seconds')
ingestion_counter = Counter('rag_ingestions_total', 'Total number of data ingestions')


# Request/Response models
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's question")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID")
    user_id: Optional[str] = Field(None, description="User identifier")
    use_cache: bool = Field(True, description="Whether to use cached responses")


class QueryResponse(BaseModel):
    conversation_id: int
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    cached: Optional[bool] = False


class IngestionRequest(BaseModel):
    source: str = Field(..., description="Microservice name")
    table_name: str = Field(..., description="Table to ingest from")
    query: Optional[str] = Field(None, description="Custom SQL query")


class ConversationHistory(BaseModel):
    conversation_id: int
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_support: bool


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RAG Service...")
    await init_database()
    logger.info("RAG Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Service...")
    await microservice_connector.close_all()
    logger.info("RAG Service shut down successfully")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG-powered chat service for Quenty logistics platform",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = RAGService()
ingestion_service = IngestionService()


@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        await db.execute(select(Document).limit(1))
        
        # Check vector extension
        result = await db.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        vector_version = result.scalar()
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            database="connected",
            vector_support=bool(vector_version)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process a RAG query"""
    query_counter.inc()
    
    start_time = time.time()
    try:
        result = await rag_service.query(
            db=db,
            query_text=request.query,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            use_cache=request.use_cache
        )
        
        query_duration.observe(time.time() - start_time)
        
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_data(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Ingest data from a microservice"""
    ingestion_counter.inc()
    
    try:
        # Start ingestion in background
        background_tasks.add_task(
            ingestion_service.ingest_from_microservice,
            db,
            request.source,
            request.table_name,
            request.query
        )
        
        return {
            "message": "Ingestion started",
            "source": request.source,
            "table": request.table_name
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/all")
async def ingest_all_data(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Ingest data from all microservices"""
    try:
        background_tasks.add_task(
            ingestion_service.ingest_all_microservices,
            db
        )
        
        return {
            "message": "Full ingestion started",
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Full ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history"""
    try:
        # Get conversation
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        return ConversationHistory(
            conversation_id=conversation.id,
            messages=[
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "sources": msg.sources,
                    "created_at": msg.created_at
                }
                for msg in messages
            ],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/similar-questions")
async def get_similar_questions(
    query: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Get similar previously asked questions"""
    try:
        similar = await rag_service.get_similar_questions(db, query, limit)
        return {"query": query, "similar_questions": similar}
    except Exception as e:
        logger.error(f"Failed to get similar questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ingestion-jobs")
async def get_ingestion_jobs(
    status: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get ingestion job history"""
    try:
        query = select(IndexingJob).order_by(IndexingJob.created_at.desc()).limit(limit)
        
        if status:
            query = query.where(IndexingJob.status == status)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return {
            "jobs": [
                {
                    "id": job.id,
                    "source": job.source,
                    "status": job.status,
                    "total_records": job.total_records,
                    "processed_records": job.processed_records,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "error_message": job.error_message
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get ingestion jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/stats")
async def get_document_stats(db: AsyncSession = Depends(get_db)):
    """Get document statistics"""
    try:
        # Get total documents
        result = await db.execute("SELECT COUNT(*) FROM documents")
        total_docs = result.scalar()
        
        # Get total chunks
        result = await db.execute("SELECT COUNT(*) FROM document_chunks")
        total_chunks = result.scalar()
        
        # Get documents by source
        result = await db.execute("""
            SELECT source, COUNT(*) as count 
            FROM documents 
            GROUP BY source
        """)
        by_source = {row.source: row.count for row in result}
        
        # Get documents by type
        result = await db.execute("""
            SELECT document_type, COUNT(*) as count 
            FROM documents 
            GROUP BY document_type
        """)
        by_type = {row.document_type: row.count for row in result}
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "documents_by_source": by_source,
            "documents_by_type": by_type
        }
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)