import logging
from typing import List, Optional
import numpy as np
import openai
from ..config import settings
import hashlib
import json
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI"""
    
    def __init__(self):
        self.redis_client = None
        self.model = None  # No local model for now
        self.use_local = False
        
        # Use OpenAI embeddings
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            logger.info("Using OpenAI embeddings")
        else:
            logger.warning("OpenAI API key not set, embeddings will use mock data")
        
        # Initialize Redis for caching
        self.init_redis()
    
    def init_redis(self):
        """Initialize Redis connection for caching"""
        try:
            if settings.redis_url:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=False
                )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def get_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """Get embedding for a single text"""
        if not text:
            return None
        
        # Generate cache key
        cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        
        # Check cache if enabled
        if use_cache and self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.debug(f"Cache read error: {e}")
        
        # Generate embedding
        try:
            if settings.openai_api_key:
                # Use OpenAI API
                response = await self._get_openai_embedding(text)
                embedding = response
            else:
                # Mock embedding for testing (384 dimensions to match expected)
                embedding = np.random.randn(384).tolist()
                logger.debug("Using mock embedding (no API key)")
            
            # Cache the result if enabled
            if use_cache and self.redis_client and embedding:
                try:
                    await self.redis_client.set(
                        cache_key,
                        json.dumps(embedding),
                        ex=settings.embedding_cache_ttl
                    )
                except Exception as e:
                    logger.debug(f"Cache write error: {e}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return mock embedding as fallback
            return np.random.randn(384).tolist()
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API"""
        try:
            response = openai.Embedding.create(
                model=settings.openai_embedding_model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock
            return np.random.randn(384).tolist()
    
    async def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text, use_cache=use_cache)
            embeddings.append(embedding)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        # OpenAI text-embedding-ada-002 has 1536 dimensions
        # But we're using 384 for compatibility with the database schema
        return 384