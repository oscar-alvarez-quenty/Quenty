import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from ..config import settings
import hashlib
import json
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.use_local = settings.use_local_models
        self.redis_client = None
        
        if self.use_local:
            # Initialize local embedding model
            self.model = SentenceTransformer(settings.local_embedding_model)
            logger.info(f"Loaded local embedding model: {settings.local_embedding_model}")
        else:
            # Use OpenAI embeddings
            if settings.openai_api_key:
                openai.api_key = settings.openai_api_key
            else:
                logger.warning("OpenAI API key not set, falling back to local model")
                self.use_local = True
                self.model = SentenceTransformer(settings.local_embedding_model)
        
        # Initialize Redis for caching
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for caching embeddings"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        
        # Check cache first
        if self.redis_client:
            cache_key = self._get_cache_key(text)
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.debug(f"Cache read failed: {e}")
        
        # Generate embedding
        if self.use_local:
            embedding = self._get_local_embedding(text)
        else:
            embedding = await self._get_openai_embedding(text)
        
        # Cache the embedding
        if self.redis_client and embedding:
            try:
                await self.redis_client.setex(
                    self._get_cache_key(text),
                    settings.cache_ttl,
                    json.dumps(embedding)
                )
            except Exception as e:
                logger.debug(f"Cache write failed: {e}")
        
        return embedding
    
    def _get_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model"""
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Normalize the embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate local embedding: {e}")
            return []
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await openai.Embedding.acreate(
                model=settings.embedding_model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Failed to generate OpenAI embedding: {e}")
            # Fallback to local model
            if hasattr(self, 'model'):
                return self._get_local_embedding(text)
            return []
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        
        if self.use_local:
            return self._get_local_embeddings_batch(texts)
        else:
            return await self._get_openai_embeddings_batch(texts)
    
    def _get_local_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using local model"""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Normalize embeddings
            normalized = []
            for embedding in embeddings:
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                normalized.append(embedding.tolist())
            
            return normalized
        except Exception as e:
            logger.error(f"Failed to generate local embeddings batch: {e}")
            return [[] for _ in texts]
    
    async def _get_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API"""
        try:
            response = await openai.Embedding.acreate(
                model=settings.embedding_model,
                input=texts
            )
            return [item['embedding'] for item in response['data']]
        except Exception as e:
            logger.error(f"Failed to generate OpenAI embeddings batch: {e}")
            # Fallback to local model
            if hasattr(self, 'model'):
                return self._get_local_embeddings_batch(texts)
            return [[] for _ in texts]
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def close(self):
        """Clean up resources"""
        if self.redis_client:
            await self.redis_client.close()