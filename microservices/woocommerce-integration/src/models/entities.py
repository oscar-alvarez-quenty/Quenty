"""
Database Models
SQLAlchemy models for WooCommerce integration service
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, JSON, Numeric, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from typing import Optional

Base = declarative_base()


class OrderStatus(str, Enum):
    """WooCommerce order statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"
    TRASH = "trash"


class ProductType(str, Enum):
    """WooCommerce product types"""
    SIMPLE = "simple"
    VARIABLE = "variable"
    GROUPED = "grouped"
    EXTERNAL = "external"


class Store(Base):
    """WooCommerce store configuration"""
    __tablename__ = 'stores'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    consumer_key = Column(String(255), nullable=False)
    consumer_secret = Column(Text, nullable=False)  # Encrypted
    webhook_secret = Column(String(255))
    active = Column(Boolean, default=True)
    version = Column(String(10), default='wc/v3')
    timezone = Column(String(50))
    currency = Column(String(3))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    last_sync = Column(DateTime)
    metadata = Column(JSON)
    
    # Relationships
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="store", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEvent", back_populates="store", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_store_active', 'active'),
    )


class Order(Base):
    """Order synchronized from WooCommerce"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), ForeignKey('stores.id'), nullable=False)
    wc_order_id = Column(Integer, nullable=False)
    wc_order_number = Column(String(50))
    status = Column(SQLEnum(OrderStatus), nullable=False)
    
    # Customer information
    customer_id = Column(Integer)
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    
    # Financial
    currency = Column(String(3), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))
    shipping_total = Column(Numeric(10, 2))
    tax_total = Column(Numeric(10, 2))
    discount_total = Column(Numeric(10, 2))
    
    # Addresses
    billing_address = Column(JSON)
    shipping_address = Column(JSON)
    
    # Payment
    payment_method = Column(String(50))
    payment_method_title = Column(String(255))
    transaction_id = Column(String(255))
    
    # Shipping
    shipping_id = Column(Integer, ForeignKey('shipping_requests.id'))
    tracking_number = Column(String(255))
    
    # Dates
    date_created = Column(DateTime)
    date_modified = Column(DateTime)
    date_paid = Column(DateTime)
    date_completed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    delivered_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Additional data
    metadata = Column(JSON)
    notes = Column(Text)
    
    # Relationships
    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipping = relationship("ShippingRequest", back_populates="order")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'wc_order_id', name='uq_store_order'),
        Index('idx_order_status', 'status'),
        Index('idx_order_customer', 'customer_email'),
        Index('idx_order_created', 'date_created'),
        Index('idx_order_tracking', 'tracking_number'),
    )


class OrderItem(Base):
    """Order line items"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    wc_item_id = Column(Integer)
    product_id = Column(Integer)
    variation_id = Column(Integer)
    
    name = Column(String(500), nullable=False)
    sku = Column(String(100))
    quantity = Column(Integer, nullable=False)
    
    price = Column(Numeric(10, 2))
    subtotal = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))
    tax_total = Column(Numeric(10, 2))
    
    metadata = Column(JSON)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    
    __table_args__ = (
        Index('idx_item_order', 'order_id'),
        Index('idx_item_product', 'product_id'),
        Index('idx_item_sku', 'sku'),
    )


class Product(Base):
    """Product synchronized from WooCommerce"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), ForeignKey('stores.id'), nullable=False)
    wc_product_id = Column(Integer, nullable=False)
    
    name = Column(String(500), nullable=False)
    slug = Column(String(500))
    sku = Column(String(100))
    type = Column(SQLEnum(ProductType), default=ProductType.SIMPLE)
    status = Column(String(20), default='publish')
    
    # Pricing
    price = Column(Numeric(10, 2))
    regular_price = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))
    
    # Stock
    manage_stock = Column(Boolean, default=False)
    stock_quantity = Column(Integer)
    in_stock = Column(Boolean, default=True)
    stock_status = Column(String(20))
    
    # Physical properties
    weight = Column(Numeric(10, 3))
    length = Column(Numeric(10, 2))
    width = Column(Numeric(10, 2))
    height = Column(Numeric(10, 2))
    
    # Descriptions
    description = Column(Text)
    short_description = Column(Text)
    
    # Categories and tags
    categories = Column(JSON)
    tags = Column(JSON)
    
    # Images
    images = Column(JSON)
    
    # Dates
    date_created = Column(DateTime)
    date_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Additional data
    attributes = Column(JSON)
    metadata = Column(JSON)
    
    # Relationships
    store = relationship("Store", back_populates="products")
    variations = relationship("ProductVariation", back_populates="product", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'wc_product_id', name='uq_store_product'),
        Index('idx_product_sku', 'sku'),
        Index('idx_product_status', 'status'),
        Index('idx_product_stock', 'stock_status'),
    )


class ProductVariation(Base):
    """Product variations for variable products"""
    __tablename__ = 'product_variations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    wc_variation_id = Column(Integer, nullable=False)
    
    sku = Column(String(100))
    price = Column(Numeric(10, 2))
    regular_price = Column(Numeric(10, 2))
    sale_price = Column(Numeric(10, 2))
    
    manage_stock = Column(Boolean, default=False)
    stock_quantity = Column(Integer)
    in_stock = Column(Boolean, default=True)
    
    weight = Column(Numeric(10, 3))
    dimensions = Column(JSON)
    
    attributes = Column(JSON)
    image = Column(JSON)
    metadata = Column(JSON)
    
    # Relationships
    product = relationship("Product", back_populates="variations")
    
    __table_args__ = (
        Index('idx_variation_product', 'product_id'),
        Index('idx_variation_sku', 'sku'),
    )


class Customer(Base):
    """Customer synchronized from WooCommerce"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), ForeignKey('stores.id'), nullable=False)
    wc_customer_id = Column(Integer, nullable=False)
    
    email = Column(String(255), nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    billing_address = Column(JSON)
    shipping_address = Column(JSON)
    
    date_created = Column(DateTime)
    date_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    metadata = Column(JSON)
    
    # Relationships
    store = relationship("Store", back_populates="customers")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'wc_customer_id', name='uq_store_customer'),
        Index('idx_customer_email', 'email'),
    )


class ShippingRequest(Base):
    """Shipping requests for orders"""
    __tablename__ = 'shipping_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    carrier = Column(String(50), nullable=False)
    service_type = Column(String(50))
    tracking_number = Column(String(255))
    label_url = Column(Text)
    label_data = Column(Text)  # Base64 encoded
    
    cost = Column(Numeric(10, 2))
    currency = Column(String(3))
    
    status = Column(String(50), default='created')
    current_location = Column(String(500))
    estimated_delivery = Column(DateTime)
    delivered_at = Column(DateTime)
    
    tracking_events = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    metadata = Column(JSON)
    
    # Relationships
    order = relationship("Order", back_populates="shipping")
    
    __table_args__ = (
        Index('idx_shipping_order', 'order_id'),
        Index('idx_shipping_tracking', 'tracking_number'),
        Index('idx_shipping_status', 'status'),
    )


class WebhookEvent(Base):
    """Webhook events received from WooCommerce"""
    __tablename__ = 'webhook_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), ForeignKey('stores.id'), nullable=False)
    webhook_id = Column(String(100))
    
    topic = Column(String(50), nullable=False)
    resource = Column(String(50))
    event = Column(String(50))
    
    payload = Column(JSON, nullable=False)
    signature = Column(String(255))
    
    status = Column(String(20), default='pending')  # pending, processing, processed, failed, skipped
    error = Column(Text)
    result = Column(JSON)
    
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    store = relationship("Store", back_populates="webhooks")
    
    __table_args__ = (
        Index('idx_webhook_store', 'store_id'),
        Index('idx_webhook_topic', 'topic'),
        Index('idx_webhook_status', 'status'),
        Index('idx_webhook_received', 'received_at'),
    )


class SyncLog(Base):
    """Synchronization logs"""
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50), ForeignKey('stores.id'), nullable=False)
    
    sync_type = Column(String(50), nullable=False)  # orders, products, customers, inventory
    status = Column(String(20), nullable=False)  # started, completed, failed
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    items_processed = Column(Integer, default=0)
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    errors = Column(JSON)
    metadata = Column(JSON)
    
    __table_args__ = (
        Index('idx_sync_store', 'store_id'),
        Index('idx_sync_type', 'sync_type'),
        Index('idx_sync_started', 'started_at'),
    )


class Notification(Base):
    """Notifications sent to customers"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(50))
    order_id = Column(Integer)
    customer_email = Column(String(255))
    
    type = Column(String(50), nullable=False)  # order_confirmation, shipping_update, etc.
    subject = Column(String(500))
    content = Column(Text)
    
    status = Column(String(20), default='pending')  # pending, sent, failed
    sent_at = Column(DateTime)
    error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    metadata = Column(JSON)
    
    __table_args__ = (
        Index('idx_notification_order', 'order_id'),
        Index('idx_notification_email', 'customer_email'),
        Index('idx_notification_status', 'status'),
    )


# Export models
__all__ = [
    'Base',
    'Store',
    'Order',
    'OrderItem',
    'Product',
    'ProductVariation',
    'Customer',
    'ShippingRequest',
    'WebhookEvent',
    'SyncLog',
    'Notification',
    'OrderStatus',
    'ProductType'
]