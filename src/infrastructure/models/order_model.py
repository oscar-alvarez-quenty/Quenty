from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, DECIMAL, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.infrastructure.database.database import Base
from src.domain.entities.order import OrderStatus, ServiceType
import uuid

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    # Recipient information
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(20), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_address = Column(Text, nullable=False)
    recipient_city = Column(String(100), nullable=False)
    recipient_country = Column(String(100), nullable=False, default="Colombia")
    recipient_postal_code = Column(String(20), nullable=True)
    
    # Package information
    package_length_cm = Column(DECIMAL(8, 2), nullable=False)
    package_width_cm = Column(DECIMAL(8, 2), nullable=False)
    package_height_cm = Column(DECIMAL(8, 2), nullable=False)
    package_weight_kg = Column(DECIMAL(8, 3), nullable=False)
    declared_value = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    
    service_type = Column(SQLEnum(ServiceType), nullable=False, default=ServiceType.NATIONAL)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    origin_address = Column(Text, nullable=False)
    origin_city = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    
    quoted_price = Column(DECIMAL(10, 2), nullable=True)
    estimated_delivery_days = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    customer = relationship("CustomerModel", back_populates="orders")
    guide = relationship("GuideModel", back_populates="order", uselist=False)