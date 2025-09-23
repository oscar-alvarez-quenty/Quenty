import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from langchain.schema import Document as LangchainDoc
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from ..models import DocumentChunk, Document, Message, Conversation, QueryCache
from ..config import settings
from .embedding_service import EmbeddingService
import openai
from transformers import pipeline

logger = logging.getLogger(__name__)


class LocalLLM(LLM):
    """Custom LLM wrapper for local models"""
    
    pipeline: Any = None
    
    def __init__(self):
        super().__init__()
        # Initialize a local text generation model
        self.pipeline = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-medium",
            max_length=500,
            temperature=0.7
        )
    
    @property
    def _llm_type(self) -> str:
        return "local"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        response = self.pipeline(prompt)[0]['generated_text']
        if stop:
            for stop_token in stop:
                if stop_token in response:
                    response = response.split(stop_token)[0]
        return response


class RAGService:
    """Main RAG service for querying and generating responses"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._initialize_llm()
        self._create_prompt_template()
    
    def _initialize_llm(self):
        """Initialize the language model"""
        if settings.use_local_models:
            self.llm = LocalLLM()
        else:
            # Use OpenAI
            from langchain.llms import OpenAI
            self.llm = OpenAI(
                openai_api_key=settings.openai_api_key,
                model_name=settings.openai_model,
                temperature=0.7
            )
    
    def _create_prompt_template(self):
        """Create the prompt template for RAG"""
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question", "history"],
            template="""You are a helpful assistant for the Quenty logistics platform. 
Use the following context and conversation history to answer the user's question accurately.
If you don't have enough information to answer completely, say so.

Context from the database:
{context}

Conversation history:
{history}

User Question: {question}

Assistant Response:"""
        )
    
    async def query(
        self,
        db: AsyncSession,
        query_text: str,
        conversation_id: Optional[int] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Process a RAG query and generate a response"""
        
        # Check cache if enabled
        if use_cache:
            cached_response = await self._get_cached_response(db, query_text)
            if cached_response:
                return cached_response
        
        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            db, conversation_id, user_id
        )
        
        # Get relevant documents
        relevant_docs = await self._retrieve_relevant_documents(db, query_text)
        
        # Get conversation history
        history = await self._get_conversation_history(db, conversation.id)
        
        # Generate response
        response = await self._generate_response(
            query_text, relevant_docs, history
        )
        
        # Save message to conversation
        await self._save_message(
            db, conversation.id, "user", query_text, None
        )
        await self._save_message(
            db, conversation.id, "assistant", response["answer"], response["sources"]
        )
        
        # Cache the response
        if use_cache:
            await self._cache_response(db, query_text, response)
        
        await db.commit()
        
        return {
            "conversation_id": conversation.id,
            "query": query_text,
            "answer": response["answer"],
            "sources": response["sources"],
            "confidence": response["confidence"]
        }
    
    async def _retrieve_relevant_documents(
        self,
        db: AsyncSession,
        query_text: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using vector similarity search"""
        
        top_k = top_k or settings.top_k_results
        
        # Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(query_text)
        
        # Perform vector similarity search using pgvector
        query_sql = text("""
            SELECT 
                dc.id,
                dc.content,
                dc.document_id,
                d.source,
                d.source_table,
                d.source_id,
                d.metadata,
                dc.embedding <=> CAST(:embedding AS vector) AS distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        
        result = await db.execute(
            query_sql,
            {"embedding": str(query_embedding), "limit": top_k}
        )
        
        documents = []
        for row in result:
            # Calculate similarity score from distance
            similarity = 1 - row.distance if row.distance < 1 else 0
            
            if similarity >= settings.similarity_threshold:
                documents.append({
                    "content": row.content,
                    "source": f"{row.source}.{row.source_table}",
                    "source_id": row.source_id,
                    "metadata": row.metadata,
                    "similarity": similarity
                })
        
        return documents
    
    async def _generate_response(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        history: str
    ) -> Dict[str, Any]:
        """Generate a response using the LLM and retrieved documents"""
        
        # Prepare context from documents
        context = self._prepare_context(documents)
        
        # Generate response using LLM chain
        chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
        try:
            answer = await chain.arun(
                context=context,
                question=query,
                history=history
            )
            
            # Extract sources
            sources = [
                {
                    "source": doc["source"],
                    "source_id": doc["source_id"],
                    "similarity": doc["similarity"]
                }
                for doc in documents[:3]  # Top 3 sources
            ]
            
            # Calculate confidence based on document similarities
            confidence = sum(doc["similarity"] for doc in documents[:3]) / 3 if documents else 0.0
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "sources": [],
                "confidence": 0.0
            }
    
    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """Prepare context string from retrieved documents"""
        
        if not documents:
            return "No relevant information found in the database."
        
        context_parts = []
        for idx, doc in enumerate(documents, 1):
            context_parts.append(
                f"[Source {idx}: {doc['source']}]\n{doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    async def _get_or_create_conversation(
        self,
        db: AsyncSession,
        conversation_id: Optional[int],
        user_id: Optional[str]
    ) -> Conversation:
        """Get existing conversation or create a new one"""
        
        if conversation_id:
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            session_id=hashlib.md5(f"{datetime.utcnow()}".encode()).hexdigest(),
            user_id=user_id
        )
        db.add(conversation)
        await db.flush()
        return conversation
    
    async def _get_conversation_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 10
    ) -> str:
        """Get conversation history as a formatted string"""
        
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        
        # Format history
        history_parts = []
        for message in reversed(messages):
            role = "User" if message.role == "user" else "Assistant"
            history_parts.append(f"{role}: {message.content}")
        
        return "\n".join(history_parts) if history_parts else "No previous conversation"
    
    async def _save_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None
    ):
        """Save a message to the conversation"""
        
        # Generate embedding for the message
        embedding = await self.embedding_service.get_embedding(content)
        
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            embedding=embedding,
            sources=sources
        )
        db.add(message)
    
    async def _get_cached_response(
        self,
        db: AsyncSession,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        result = await db.execute(
            select(QueryCache)
            .where(
                QueryCache.query_hash == query_hash,
                QueryCache.expires_at > datetime.utcnow()
            )
        )
        cached = result.scalar_one_or_none()
        
        if cached:
            # Update hit count
            cached.hits += 1
            await db.commit()
            
            return {
                "query": query,
                "answer": cached.response,
                "sources": cached.sources or [],
                "confidence": 1.0,
                "cached": True
            }
        
        return None
    
    async def _cache_response(
        self,
        db: AsyncSession,
        query: str,
        response: Dict[str, Any]
    ):
        """Cache a response for future use"""
        
        query_hash = hashlib.md5(query.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.cache_ttl)
        
        # Check if cache entry already exists
        result = await db.execute(
            select(QueryCache).where(QueryCache.query_hash == query_hash)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing cache
            existing.response = response["answer"]
            existing.sources = response["sources"]
            existing.expires_at = expires_at
            existing.hits = 1
        else:
            # Create new cache entry
            cache_entry = QueryCache(
                query_hash=query_hash,
                query=query,
                response=response["answer"],
                sources=response["sources"],
                expires_at=expires_at
            )
            db.add(cache_entry)
    
    async def get_similar_questions(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """Get similar previously asked questions"""
        
        # Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        
        # Search for similar messages
        query_sql = text("""
            SELECT DISTINCT content
            FROM messages
            WHERE role = 'user'
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        
        result = await db.execute(
            query_sql,
            {"embedding": str(query_embedding), "limit": limit}
        )
        
        return [row.content for row in result]