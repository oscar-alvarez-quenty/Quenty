from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class TokenStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OrderStatus(enum.Enum):
    CONFIRMED = "confirmed"
    PAYMENT_REQUIRED = "payment_required"
    PAYMENT_IN_PROCESS = "payment_in_process"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"
    INVALID = "invalid"


class ListingStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    UNDER_REVIEW = "under_review"
    INACTIVE = "inactive"


class QuestionStatus(enum.Enum):
    UNANSWERED = "UNANSWERED"
    ANSWERED = "ANSWERED"
    CLOSED_UNANSWERED = "CLOSED_UNANSWERED"
    UNDER_REVIEW = "UNDER_REVIEW"


class MercadoLibreAccount(Base):
    __tablename__ = "meli_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True)  # MercadoLibre user ID
    nickname = Column(String(255))
    email = Column(String(255))
    site_id = Column(String(10))  # MLA, MLB, MCO, etc.
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    token_status = Column(SQLEnum(TokenStatus), default=TokenStatus.ACTIVE)
    reputation = Column(JSON)  # Seller reputation data
    registration_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    products = relationship("MercadoLibreProduct", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("MercadoLibreOrder", back_populates="account", cascade="all, delete-orphan")
    questions = relationship("MercadoLibreQuestion", back_populates="account", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_meli_account_user', 'user_id'),
    )


class MercadoLibreProduct(Base):
    __tablename__ = "meli_products"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("meli_accounts.id", ondelete="CASCADE"))
    meli_item_id = Column(String(50), unique=True, index=True)  # MLB1234567890
    title = Column(String(500), nullable=False)
    category_id = Column(String(50))
    price = Column(Float, nullable=False)
    currency_id = Column(String(10))
    available_quantity = Column(Integer, default=0)
    sold_quantity = Column(Integer, default=0)
    buying_mode = Column(String(50))  # buy_it_now, auction
    listing_type_id = Column(String(50))  # gold_special, gold_pro, etc.
    condition = Column(String(20))  # new, used, refurbished
    permalink = Column(String(500))
    thumbnail = Column(String(500))
    pictures = Column(JSON)  # Array of picture URLs
    video_id = Column(String(100))
    descriptions = Column(JSON)
    attributes = Column(JSON)
    variations = Column(JSON)
    shipping = Column(JSON)
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE)
    health = Column(Float)  # Listing health score
    warranty = Column(String(500))
    catalog_product_id = Column(String(50))
    tags = Column(JSON)
    date_created = Column(DateTime)
    last_updated = Column(DateTime)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("MercadoLibreAccount", back_populates="products")
    inventory = relationship("MercadoLibreInventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    questions = relationship("MercadoLibreQuestion", back_populates="product", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_meli_product_item', 'meli_item_id'),
        Index('idx_meli_product_status', 'status'),
    )


class MercadoLibreInventory(Base):
    __tablename__ = "meli_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("meli_products.id", ondelete="CASCADE"), unique=True)
    available_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    sold_quantity = Column(Integer, default=0)
    last_sync = Column(DateTime)
    sync_status = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("MercadoLibreProduct", back_populates="inventory")


class MercadoLibreOrder(Base):
    __tablename__ = "meli_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("meli_accounts.id", ondelete="CASCADE"))
    meli_order_id = Column(String(50), unique=True, index=True)
    status = Column(SQLEnum(OrderStatus))
    status_detail = Column(JSON)
    date_created = Column(DateTime)
    date_closed = Column(DateTime)
    date_last_updated = Column(DateTime)
    expiration_date = Column(DateTime)
    buyer = Column(JSON)  # Buyer information
    seller = Column(JSON)  # Seller information
    order_items = Column(JSON)  # Array of order items
    total_amount = Column(Float)
    currency_id = Column(String(10))
    payments = Column(JSON)  # Payment information
    shipping = Column(JSON)  # Shipping details
    pack_id = Column(String(50))  # Cart ID if multiple items
    pickup_id = Column(String(50))
    feedback = Column(JSON)  # Buyer and seller feedback
    tags = Column(JSON)
    fulfilled = Column(Boolean, default=False)
    manufacturing_ending_date = Column(DateTime)
    mediations = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("MercadoLibreAccount", back_populates="orders")
    shipment = relationship("MercadoLibreShipment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    messages = relationship("MercadoLibreMessage", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_meli_order_id', 'meli_order_id'),
        Index('idx_meli_order_status', 'status'),
        Index('idx_meli_order_created', 'date_created'),
    )


class MercadoLibreShipment(Base):
    __tablename__ = "meli_shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("meli_orders.id", ondelete="CASCADE"), unique=True)
    shipment_id = Column(String(50), unique=True, index=True)
    status = Column(String(50))
    substatus = Column(String(50))
    tracking_number = Column(String(100))
    tracking_method = Column(String(50))
    service_id = Column(String(50))
    shipping_mode = Column(String(50))  # me2, custom, etc.
    shipping_option = Column(JSON)
    sender_address = Column(JSON)
    receiver_address = Column(JSON)
    date_created = Column(DateTime)
    last_updated = Column(DateTime)
    date_first_printed = Column(DateTime)
    logistic_type = Column(String(50))
    cost = Column(Float)
    currency_id = Column(String(10))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("MercadoLibreOrder", back_populates="shipment")


class MercadoLibreQuestion(Base):
    __tablename__ = "meli_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("meli_accounts.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("meli_products.id", ondelete="CASCADE"))
    question_id = Column(String(50), unique=True, index=True)
    status = Column(SQLEnum(QuestionStatus))
    item_id = Column(String(50))
    seller_id = Column(String(50))
    from_user_id = Column(String(50))
    text = Column(Text)
    answer = Column(JSON)  # {text, date_created, status}
    date_created = Column(DateTime)
    hold = Column(Boolean, default=False)
    deleted_from_listing = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("MercadoLibreAccount", back_populates="questions")
    product = relationship("MercadoLibreProduct", back_populates="questions")
    
    __table_args__ = (
        Index('idx_meli_question_id', 'question_id'),
        Index('idx_meli_question_status', 'status'),
    )


class MercadoLibreMessage(Base):
    __tablename__ = "meli_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("meli_orders.id", ondelete="CASCADE"))
    message_id = Column(String(50), unique=True, index=True)
    conversation_id = Column(String(50), index=True)
    from_user_id = Column(String(50))
    to_user_id = Column(String(50))
    text = Column(Text)
    attachments = Column(JSON)
    date_created = Column(DateTime)
    date_received = Column(DateTime)
    date_available = Column(DateTime)
    date_notified = Column(DateTime)
    date_read = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    order = relationship("MercadoLibreOrder", back_populates="messages")
    
    __table_args__ = (
        Index('idx_meli_message_id', 'message_id'),
        Index('idx_meli_message_conversation', 'conversation_id'),
    )


class MercadoLibreWebhook(Base):
    __tablename__ = "meli_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50))
    resource = Column(String(100))
    topic = Column(String(50))  # orders, items, questions, messages, shipments
    application_id = Column(String(50))
    attempts = Column(Integer, default=0)
    sent = Column(DateTime)
    received = Column(DateTime)
    processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    payload = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_meli_webhook_topic', 'topic'),
        Index('idx_meli_webhook_processed', 'processed'),
    )


class MercadoLibreSyncLog(Base):
    __tablename__ = "meli_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50))  # products, orders, questions, inventory
    status = Column(String(50))  # started, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime, default=func.now())