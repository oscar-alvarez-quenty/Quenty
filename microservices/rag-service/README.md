# Quenty RAG Service

## Overview

The RAG (Retrieval-Augmented Generation) Service is an AI-powered chat assistant that connects to all Quenty microservices' databases to provide intelligent answers about the entire application state. It uses vector embeddings and semantic search to retrieve relevant information and generate contextual responses.

## Features

- **Multi-Database Connectivity**: Connects to all microservice databases (auth, customer, order, carrier, analytics, franchise, international, microcredit, pickup, reverse logistics)
- **Vector Search**: Uses PostgreSQL with pgvector extension for efficient similarity search
- **Local AI Models**: Supports both local models (sentence-transformers) and OpenAI API
- **Conversation Management**: Maintains conversation history and context
- **Intelligent Caching**: Caches responses for frequently asked questions
- **Web Chat Interface**: Beautiful, responsive chat client
- **Data Ingestion Pipeline**: Automated ingestion from all microservices
- **Real-time Updates**: Background tasks for continuous data synchronization

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Chat Client (HTML/JS)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 FastAPI REST API                         │
│                    Port: 8011                            │
├──────────────────────────────────────────────────────────┤
│                   RAG Service Layer                      │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Embedding  │  │   LangChain  │  │   Ingestion    │  │
│  │  Service   │  │   RAG Engine │  │    Service     │  │
│  └────────────┘  └──────────────┘  └────────────────┘  │
├──────────────────────────────────────────────────────────┤
│                  Database Connectors                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Auth │ Customer │ Order │ Carrier │ Analytics  │  │
│  │  Franchise │ International │ Microcredit │ etc   │  │
│  └──────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│            Vector Database (PostgreSQL + pgvector)       │
│                     Redis Cache                          │
└──────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 15+ with pgvector extension
- Python 3.11+
- Redis

### Quick Start

1. **Build and start the service:**
```bash
docker-compose up -d rag-service
```

2. **Initialize the database:**
```bash
docker exec -it quenty-rag alembic upgrade head
```

3. **Ingest data from all microservices:**
```bash
curl -X POST http://localhost:8011/ingest/all
```

4. **Access the chat interface:**
Open your browser and navigate to:
```
http://localhost:8011/chat-client/
```

## API Endpoints

### Health Check
```http
GET /health
```

### Query Endpoint
```http
POST /query
Content-Type: application/json

{
  "query": "What are the recent orders?",
  "conversation_id": null,
  "user_id": "user123",
  "use_cache": true
}
```

### Data Ingestion

**Ingest from specific microservice:**
```http
POST /ingest
Content-Type: application/json

{
  "source": "order",
  "table_name": "orders",
  "query": "SELECT * FROM orders WHERE created_at > '2024-01-01'"
}
```

**Ingest from all microservices:**
```http
POST /ingest/all
```

### Conversation Management

**Get conversation history:**
```http
GET /conversations/{conversation_id}
```

### Similar Questions
```http
GET /similar-questions?query=your+question&limit=5
```

### Document Statistics
```http
GET /documents/stats
```

### Metrics (Prometheus)
```http
GET /metrics
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Main RAG database URL | `postgresql://postgres:quenty123@db:5432/rag_db` |
| `VECTOR_DB_URL` | Vector database URL | Same as DATABASE_URL |
| `REDIS_URL` | Redis cache URL | `redis://localhost:6379/2` |
| `USE_LOCAL_MODELS` | Use local AI models | `true` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-3.5-turbo` |
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-ada-002` |
| `LOCAL_EMBEDDING_MODEL` | Local embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Text chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |
| `TOP_K_RESULTS` | Number of results to retrieve | `5` |
| `SIMILARITY_THRESHOLD` | Minimum similarity score | `0.7` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `3600` |

### Microservice Database URLs

Configure connections to all microservices:
- `AUTH_DB_URL`
- `CUSTOMER_DB_URL`
- `ORDER_DB_URL`
- `CARRIER_DB_URL`
- `ANALYTICS_DB_URL`
- `FRANCHISE_DB_URL`
- `INTERNATIONAL_DB_URL`
- `MICROCREDIT_DB_URL`
- `PICKUP_DB_URL`
- `REVERSE_LOGISTICS_DB_URL`

## Database Schema

### Main Tables

1. **documents**: Stores original documents from microservices
2. **document_chunks**: Stores text chunks with vector embeddings
3. **conversations**: Manages chat conversations
4. **messages**: Stores conversation messages
5. **indexing_jobs**: Tracks data ingestion jobs
6. **query_cache**: Caches frequently asked questions

## Usage Examples

### Python Client

```python
import requests

# Initialize conversation
response = requests.post('http://localhost:8011/query', json={
    'query': 'Show me all pending orders',
    'use_cache': True
})

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Confidence: {data['confidence']}")
print(f"Sources: {data['sources']}")
```

### JavaScript Client

```javascript
async function askQuestion(query) {
    const response = await fetch('http://localhost:8011/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: query,
            use_cache: true
        })
    });
    
    const data = await response.json();
    console.log('Answer:', data.answer);
    console.log('Sources:', data.sources);
}

askQuestion('What is the status of shipment #12345?');
```

## Sample Queries

The RAG service can answer various questions about your logistics platform:

1. **Orders**
   - "What are the recent orders?"
   - "Show me orders with status 'pending'"
   - "What is the total order value for today?"

2. **Customers**
   - "Show customer information for ID 123"
   - "How many active customers do we have?"
   - "List customers from New York"

3. **Shipments**
   - "What is the status of tracking number ABC123?"
   - "Show all international shipments"
   - "List delayed shipments"

4. **Analytics**
   - "Show me revenue metrics"
   - "What is the franchise performance?"
   - "Display customer analytics"

5. **Operations**
   - "Show pending pickup requests"
   - "List active microcredit applications"
   - "What are the recent returns?"

## Development

### Local Development

1. **Install dependencies:**
```bash
cd microservices/rag-service
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run migrations:**
```bash
alembic upgrade head
```

4. **Start the service:**
```bash
uvicorn src.main:app --reload --port 8011
```

### Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

## Monitoring

### Prometheus Metrics

The service exposes metrics at `/metrics`:
- `rag_queries_total`: Total number of queries
- `rag_query_duration_seconds`: Query response time
- `rag_ingestions_total`: Total data ingestions

### Health Checks

The `/health` endpoint provides:
- Service status
- Database connectivity
- Vector extension status

## Troubleshooting

### Common Issues

1. **pgvector extension not found:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Out of memory with local models:**
Adjust the model or use OpenAI API:
```bash
USE_LOCAL_MODELS=false
OPENAI_API_KEY=your-key
```

3. **Slow query performance:**
- Increase `TOP_K_RESULTS` for better context
- Enable caching with `use_cache=true`
- Check vector index: 
```sql
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

4. **Data not updating:**
Trigger manual ingestion:
```bash
curl -X POST http://localhost:8011/ingest/all
```

## Security Considerations

1. **API Authentication**: Implement JWT tokens for production
2. **Database Credentials**: Use secrets management
3. **Input Sanitization**: Queries are sanitized before processing
4. **Rate Limiting**: Implement rate limiting for production
5. **Data Privacy**: Ensure compliance with data protection regulations

## Performance Optimization

1. **Vector Indexing**: Use IVFFlat or HNSW indexes for large datasets
2. **Caching Strategy**: Redis caching for frequent queries
3. **Batch Processing**: Bulk ingestion for better performance
4. **Connection Pooling**: Optimized database connection pools
5. **Async Operations**: Fully async architecture for scalability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This service is part of the Quenty logistics platform and follows the same licensing terms.

## Support

For issues and questions:
- Check the troubleshooting section
- Review existing GitHub issues
- Contact the development team

## Roadmap

- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Advanced analytics dashboard
- [ ] Real-time data streaming
- [ ] Distributed vector search
- [ ] Fine-tuned domain models
- [ ] Export conversation history
- [ ] Advanced prompt engineering