import pytest
import asyncio
import httpx
from typing import Dict, Any
import json
import time


class TestRAGSystem:
    """Integration tests for RAG system"""
    
    BASE_URL = "http://localhost:8011"
    
    @pytest.fixture
    async def client(self):
        """Create async HTTP client"""
        async with httpx.AsyncClient() as client:
            yield client
    
    async def test_health_check(self, client):
        """Test health endpoint"""
        response = await client.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["database"] == "connected"
        assert "vector_support" in data
    
    async def test_simple_query(self, client):
        """Test basic query functionality"""
        query_data = {
            "query": "What is the system status?",
            "use_cache": False
        }
        
        response = await client.post(
            f"{self.BASE_URL}/query",
            json=query_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "conversation_id" in data
        assert "query" in data
        assert "answer" in data
        assert "sources" in data
        assert "confidence" in data
        assert data["query"] == query_data["query"]
    
    async def test_conversation_continuity(self, client):
        """Test conversation context is maintained"""
        # First query
        response1 = await client.post(
            f"{self.BASE_URL}/query",
            json={"query": "Show me recent orders", "use_cache": False}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        conversation_id = data1["conversation_id"]
        
        # Follow-up query using same conversation
        response2 = await client.post(
            f"{self.BASE_URL}/query",
            json={
                "query": "What about their status?",
                "conversation_id": conversation_id,
                "use_cache": False
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["conversation_id"] == conversation_id
    
    async def test_get_conversation_history(self, client):
        """Test retrieving conversation history"""
        # Create a conversation
        response = await client.post(
            f"{self.BASE_URL}/query",
            json={"query": "Test message", "use_cache": False}
        )
        conversation_id = response.json()["conversation_id"]
        
        # Get conversation history
        history_response = await client.get(
            f"{self.BASE_URL}/conversations/{conversation_id}"
        )
        assert history_response.status_code == 200
        
        history = history_response.json()
        assert history["conversation_id"] == conversation_id
        assert len(history["messages"]) >= 2  # User and assistant messages
        assert any(msg["role"] == "user" for msg in history["messages"])
        assert any(msg["role"] == "assistant" for msg in history["messages"])
    
    async def test_similar_questions(self, client):
        """Test similar questions feature"""
        response = await client.get(
            f"{self.BASE_URL}/similar-questions",
            params={"query": "order status", "limit": 3}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "similar_questions" in data
        assert isinstance(data["similar_questions"], list)
    
    async def test_document_statistics(self, client):
        """Test document statistics endpoint"""
        response = await client.get(f"{self.BASE_URL}/documents/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_documents" in stats
        assert "total_chunks" in stats
        assert "documents_by_source" in stats
        assert "documents_by_type" in stats
    
    async def test_ingestion_jobs_status(self, client):
        """Test ingestion jobs endpoint"""
        response = await client.get(
            f"{self.BASE_URL}/ingestion-jobs",
            params={"limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
    
    async def test_cache_functionality(self, client):
        """Test that caching works correctly"""
        query_data = {
            "query": "What is 2+2?",
            "use_cache": True
        }
        
        # First query (not cached)
        start_time = time.time()
        response1 = await client.post(
            f"{self.BASE_URL}/query",
            json=query_data
        )
        first_duration = time.time() - start_time
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second query (should be cached)
        start_time = time.time()
        response2 = await client.post(
            f"{self.BASE_URL}/query",
            json=query_data
        )
        second_duration = time.time() - start_time
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Cached response should be faster
        assert second_duration < first_duration
        # Content should be the same
        assert data1["answer"] == data2["answer"]
    
    async def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = await client.get(f"{self.BASE_URL}/metrics")
        assert response.status_code == 200
        assert "rag_queries_total" in response.text
        assert "rag_query_duration_seconds" in response.text
        assert "rag_ingestions_total" in response.text


class TestRAGQueries:
    """Test various types of queries"""
    
    BASE_URL = "http://localhost:8011"
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient() as client:
            yield client
    
    @pytest.mark.parametrize("query,expected_keywords", [
        ("Show me customer information", ["customer", "profile"]),
        ("What are recent orders?", ["order", "recent"]),
        ("Display shipment status", ["shipment", "status"]),
        ("Show franchise performance", ["franchise", "performance"]),
        ("List pickup requests", ["pickup", "request"]),
    ])
    async def test_domain_specific_queries(
        self,
        client,
        query: str,
        expected_keywords: list
    ):
        """Test that domain-specific queries return relevant information"""
        response = await client.post(
            f"{self.BASE_URL}/query",
            json={"query": query, "use_cache": False}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["answer"]
        
        # Check if response contains expected context
        answer_lower = data["answer"].lower()
        assert any(
            keyword.lower() in answer_lower 
            for keyword in expected_keywords
        ), f"Expected keywords {expected_keywords} not found in answer"


class TestDataIngestion:
    """Test data ingestion functionality"""
    
    BASE_URL = "http://localhost:8011"
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient() as client:
            yield client
    
    async def test_single_table_ingestion(self, client):
        """Test ingesting data from a single table"""
        ingestion_data = {
            "source": "customer",
            "table_name": "customers"
        }
        
        response = await client.post(
            f"{self.BASE_URL}/ingest",
            json=ingestion_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Ingestion started"
        assert data["source"] == "customer"
        assert data["table"] == "customers"
    
    async def test_full_ingestion(self, client):
        """Test ingesting data from all microservices"""
        response = await client.post(f"{self.BASE_URL}/ingest/all")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Full ingestion started"
        assert data["status"] == "processing"


def run_integration_tests():
    """Run all integration tests"""
    print("Starting RAG System Integration Tests...")
    print("=" * 60)
    
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    print("""
    RAG System Test Suite
    =====================
    
    Before running tests, ensure:
    1. RAG service is running on port 8011
    2. Database is initialized
    3. Some data has been ingested
    
    Run with: python test_rag_system.py
    """)
    
    run_integration_tests()