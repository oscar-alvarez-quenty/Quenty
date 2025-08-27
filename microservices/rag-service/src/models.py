from sqlalchemy import Column, String, Integer, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False)  # microservice name
    source_table = Column(String(255), nullable=False)  # table name
    source_id = Column(String(255), nullable=False)  # record id
    document_type = Column(String(100))  # order, customer, product, etc.
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to chunks
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_source_composite', 'source', 'source_table', 'source_id'),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # 384 dimensions for all-MiniLM-L6-v2
    metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship to parent document
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    metadata = Column(JSON)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # For similarity search
    sources = Column(JSON)  # Referenced documents
    created_at = Column(DateTime, default=func.now())
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")


class IndexingJob(Base):
    __tablename__ = "indexing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    error_message = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class QueryCache(Base):
    __tablename__ = "query_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(255), unique=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(JSON)
    hits = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('idx_query_cache_expiry', 'expires_at'),
    )