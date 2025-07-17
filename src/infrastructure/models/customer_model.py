from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.infrastructure.database.database import Base
from src.domain.value_objects.customer_type import CustomerType
import uuid

class CustomerModel(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    customer_type = Column(SQLEnum(CustomerType), nullable=False, default=CustomerType.SMALL)
    business_name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    kyc_validated = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    orders = relationship("OrderModel", back_populates="customer")
    wallet = relationship("WalletModel", back_populates="customer", uselist=False)
    microcredits = relationship("MicrocreditModel", back_populates="customer")