from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class StockMovementType(PyEnum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    sku = Column(String(255), unique=True, nullable=False)
    category = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    weight = Column(Float)
    dimensions = Column(JSON)  # {"length": 10, "width": 5, "height": 3}
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    company_id = Column(String(255), nullable=False)  # References Company from Customer service
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer)
    location = Column(String(255))
    batch_number = Column(String(255))
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_items")

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(50), nullable=False)  # StockMovementType enum
    quantity = Column(Integer, nullable=False)
    reference_number = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)  # User ID from Customer service
    
    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"))
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="pending")
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    customer_id = Column(String(255), nullable=False)  # References User from Customer service
    company_id = Column(String(255), nullable=False)   # References Company from Customer service
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Foreign Keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")