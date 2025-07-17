from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, DECIMAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.infrastructure.database.database import Base
import uuid

class WalletModel(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, unique=True)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    credit_limit = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    customer = relationship("CustomerModel", back_populates="wallet")
    transactions = relationship("WalletTransactionModel", back_populates="wallet")

class WalletTransactionModel(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    wallet = relationship("WalletModel", back_populates="transactions")