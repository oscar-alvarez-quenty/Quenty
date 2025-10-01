"""
Database models for Shopify Integration
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ShopifyStore(Base):
    """Store configuration and credentials"""
    __tablename__ = 'shopify_stores'
    
    id = Column(Integer, primary_key=True, index=True)
    store_domain = Column(String(255), unique=True, nullable=False, index=True)
    store_name = Column(String(255))
    access_token = Column(Text)  # Encrypted
    api_key = Column(String(255))  # Encrypted
    api_secret = Column(String(255))  # Encrypted
    webhook_secret = Column(String(255))  # Encrypted
    
    # Store info
    email = Column(String(255))
    phone = Column(String(50))
    currency = Column(String(10))
    timezone = Column(String(100))
    country_code = Column(String(10))
    
    # Integration settings
    is_active = Column(Boolean, default=True)
    sync_products = Column(Boolean, default=True)
    sync_orders = Column(Boolean, default=True)
    sync_customers = Column(Boolean, default=True)
    sync_inventory = Column(Boolean, default=True)
    
    # OAuth info
    scopes = Column(JSON)
    installed_at = Column(DateTime, default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)
    
    # Relationships
    webhooks = relationship("ShopifyWebhook", back_populates="store", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="store", cascade="all, delete-orphan")
    products = relationship("ShopifyProduct", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("ShopifyOrder", back_populates="store", cascade="all, delete-orphan")
    customers = relationship("ShopifyCustomer", back_populates="store", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_store_domain_active', 'store_domain', 'is_active'),
    )


class ShopifyWebhook(Base):
    """Webhook registrations"""
    __tablename__ = 'shopify_webhooks'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    shopify_webhook_id = Column(String(50), index=True)
    topic = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    format = Column(String(10), default='json')
    api_version = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="webhooks")
    events = relationship("WebhookEvent", back_populates="webhook", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'topic', name='uq_store_topic'),
        Index('idx_webhook_store_topic', 'store_id', 'topic'),
    )


class WebhookEvent(Base):
    """Webhook event log"""
    __tablename__ = 'webhook_events'
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey('shopify_webhooks.id'), nullable=False)
    event_id = Column(String(100), unique=True, index=True)
    topic = Column(String(100), nullable=False)
    
    # Event data
    headers = Column(JSON)
    payload = Column(JSON)
    
    # Processing
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    processed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    received_at = Column(DateTime, default=func.now())
    
    # Relationships
    webhook = relationship("ShopifyWebhook", back_populates="events")
    
    __table_args__ = (
        Index('idx_event_status_received', 'status', 'received_at'),
    )


class ShopifyProduct(Base):
    """Cached product data"""
    __tablename__ = 'shopify_products'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    shopify_product_id = Column(String(50), nullable=False, index=True)
    
    # Product info
    title = Column(String(255), nullable=False)
    body_html = Column(Text)
    vendor = Column(String(255))
    product_type = Column(String(255))
    handle = Column(String(255))
    status = Column(String(20))
    tags = Column(Text)
    
    # Pricing
    price_min = Column(Float)
    price_max = Column(Float)
    compare_at_price_min = Column(Float)
    compare_at_price_max = Column(Float)
    
    # Inventory
    total_inventory = Column(Integer, default=0)
    tracks_inventory = Column(Boolean, default=True)
    
    # SEO
    seo_title = Column(String(255))
    seo_description = Column(Text)
    
    # Shopify dates
    shopify_created_at = Column(DateTime)
    shopify_updated_at = Column(DateTime)
    published_at = Column(DateTime)
    
    # Local timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="products")
    variants = relationship("ShopifyVariant", back_populates="product", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'shopify_product_id', name='uq_store_product'),
        Index('idx_product_store_status', 'store_id', 'status'),
    )


class ShopifyVariant(Base):
    """Product variant data"""
    __tablename__ = 'shopify_variants'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('shopify_products.id'), nullable=False)
    shopify_variant_id = Column(String(50), nullable=False, index=True)
    
    # Variant info
    title = Column(String(255))
    sku = Column(String(255), index=True)
    barcode = Column(String(255))
    position = Column(Integer)
    
    # Pricing
    price = Column(Float)
    compare_at_price = Column(Float)
    
    # Inventory
    inventory_quantity = Column(Integer, default=0)
    inventory_item_id = Column(String(50))
    requires_shipping = Column(Boolean, default=True)
    
    # Physical properties
    weight = Column(Float)
    weight_unit = Column(String(10))
    
    # Options
    option1 = Column(String(255))
    option2 = Column(String(255))
    option3 = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("ShopifyProduct", back_populates="variants")
    
    __table_args__ = (
        Index('idx_variant_sku', 'sku'),
    )


class ShopifyOrder(Base):
    """Cached order data"""
    __tablename__ = 'shopify_orders'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    shopify_order_id = Column(String(50), nullable=False, index=True)
    order_number = Column(String(50), index=True)
    
    # Customer info
    customer_id = Column(Integer, ForeignKey('shopify_customers.id'))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Financial
    total_price = Column(Float)
    subtotal_price = Column(Float)
    total_tax = Column(Float)
    total_discounts = Column(Float)
    total_shipping = Column(Float)
    currency = Column(String(10))
    financial_status = Column(String(20))
    
    # Fulfillment
    fulfillment_status = Column(String(20))
    total_line_items = Column(Integer, default=0)
    
    # Status
    status = Column(String(20))
    cancel_reason = Column(String(255))
    cancelled_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Shopify dates
    shopify_created_at = Column(DateTime)
    shopify_updated_at = Column(DateTime)
    processed_at = Column(DateTime)
    
    # Local timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="orders")
    customer = relationship("ShopifyCustomer", back_populates="orders")
    line_items = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'shopify_order_id', name='uq_store_order'),
        Index('idx_order_store_status', 'store_id', 'status'),
        Index('idx_order_created', 'shopify_created_at'),
    )


class OrderLineItem(Base):
    """Order line item data"""
    __tablename__ = 'order_line_items'
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('shopify_orders.id'), nullable=False)
    shopify_line_item_id = Column(String(50), index=True)
    
    # Product info
    product_id = Column(String(50))
    variant_id = Column(String(50))
    sku = Column(String(255))
    title = Column(String(255))
    variant_title = Column(String(255))
    
    # Quantities and pricing
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total_discount = Column(Float)
    
    # Fulfillment
    fulfillable_quantity = Column(Integer)
    fulfillment_status = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    order = relationship("ShopifyOrder", back_populates="line_items")


class ShopifyCustomer(Base):
    """Cached customer data"""
    __tablename__ = 'shopify_customers'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    shopify_customer_id = Column(String(50), nullable=False, index=True)
    
    # Customer info
    email = Column(String(255), index=True)
    phone = Column(String(50))
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    # Marketing
    accepts_marketing = Column(Boolean, default=False)
    marketing_opt_in_level = Column(String(50))
    
    # Status
    state = Column(String(20))  # enabled, disabled, invited, declined
    verified_email = Column(Boolean, default=False)
    tax_exempt = Column(Boolean, default=False)
    tags = Column(Text)
    
    # Statistics
    orders_count = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Shopify dates
    shopify_created_at = Column(DateTime)
    shopify_updated_at = Column(DateTime)
    
    # Local timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="customers")
    orders = relationship("ShopifyOrder", back_populates="customer")
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('store_id', 'shopify_customer_id', name='uq_store_customer'),
        Index('idx_customer_store_email', 'store_id', 'email'),
    )


class CustomerAddress(Base):
    """Customer address data"""
    __tablename__ = 'customer_addresses'
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('shopify_customers.id'), nullable=False)
    shopify_address_id = Column(String(50))
    
    # Address info
    address1 = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(255))
    province = Column(String(255))
    province_code = Column(String(10))
    country = Column(String(255))
    country_code = Column(String(10))
    zip = Column(String(20))
    
    # Contact
    name = Column(String(255))
    phone = Column(String(50))
    company = Column(String(255))
    
    # Flags
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("ShopifyCustomer", back_populates="addresses")


class SyncLog(Base):
    """Synchronization log"""
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    sync_type = Column(String(50), nullable=False)  # products, orders, customers, inventory
    
    # Sync details
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    direction = Column(String(20), default='import')  # import, export
    
    # Statistics
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="sync_logs")
    
    __table_args__ = (
        Index('idx_sync_store_type_status', 'store_id', 'sync_type', 'status'),
        Index('idx_sync_created', 'created_at'),
    )


class InventoryLocation(Base):
    """Inventory locations"""
    __tablename__ = 'inventory_locations'
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey('shopify_stores.id'), nullable=False)
    shopify_location_id = Column(String(50), nullable=False, index=True)
    
    # Location info
    name = Column(String(255), nullable=False)
    address1 = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(255))
    province = Column(String(255))
    country = Column(String(255))
    country_code = Column(String(10))
    zip = Column(String(20))
    phone = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('store_id', 'shopify_location_id', name='uq_store_location'),
    )


class InventoryLevel(Base):
    """Inventory levels per location"""
    __tablename__ = 'inventory_levels'
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey('inventory_locations.id'), nullable=False)
    shopify_inventory_item_id = Column(String(50), nullable=False)
    variant_id = Column(Integer, ForeignKey('shopify_variants.id'))
    
    # Quantities
    available = Column(Integer, default=0)
    incoming = Column(Integer, default=0)
    committed = Column(Integer, default=0)
    
    # Timestamps
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('location_id', 'shopify_inventory_item_id', name='uq_location_item'),
        Index('idx_inventory_location_item', 'location_id', 'shopify_inventory_item_id'),
    )