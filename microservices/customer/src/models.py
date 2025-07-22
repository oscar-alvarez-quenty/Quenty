from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class CustomerProfile(Base):
    """Customer-specific profile information"""
    __tablename__ = "customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)  # Reference to Auth service
    
    # Customer-specific information
    customer_type = Column(String(50), default="individual")  # individual, business
    credit_limit = Column(Float, default=0.0)
    credit_used = Column(Float, default=0.0)
    payment_terms = Column(Integer, default=30)  # days
    preferred_payment_method = Column(String(50))
    
    # Shipping preferences
    default_shipping_address = Column(JSON)  # Stored as JSON
    billing_address = Column(JSON)  # Stored as JSON
    shipping_preferences = Column(JSON)  # Special instructions, delivery preferences
    
    # Customer status and settings
    customer_status = Column(String(50), default="active")  # active, suspended, vip
    loyalty_points = Column(Integer, default=0)
    discount_percentage = Column(Float, default=0.0)
    
    # Communication preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    marketing_emails = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    support_tickets = relationship("SupportTicket", back_populates="customer")
    customer_notes = relationship("CustomerNote", back_populates="customer")

class SupportTicket(Base):
    """Customer support tickets"""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(255), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"), nullable=False)
    
    # Ticket information
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100))  # billing, shipping, technical, general
    priority = Column(String(50), default="medium")  # low, medium, high, urgent
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    
    # Assignment
    assigned_to = Column(String(255))  # User ID from Auth service
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="support_tickets")
    ticket_messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    """Messages within support tickets"""
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    
    # Message content
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal note vs customer message
    sender_id = Column(String(255), nullable=False)  # User ID from Auth service
    sender_type = Column(String(50), nullable=False)  # customer, agent, system
    
    # Attachments
    attachments = Column(JSON)  # List of attachment URLs/references
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="ticket_messages")

class CustomerNote(Base):
    """Internal notes about customers"""
    __tablename__ = "customer_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"), nullable=False)
    
    # Note content
    note = Column(Text, nullable=False)
    category = Column(String(100))  # general, payment, shipping, complaint
    is_important = Column(Boolean, default=False)
    
    # Note metadata
    created_by = Column(String(255), nullable=False)  # User ID from Auth service
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("CustomerProfile", back_populates="customer_notes")

class CustomerInteraction(Base):
    """Track customer interactions"""
    __tablename__ = "customer_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(100), nullable=False)  # call, email, chat, meeting
    subject = Column(String(500))
    description = Column(Text)
    outcome = Column(String(500))
    
    # Interaction metadata
    interaction_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    handled_by = Column(String(255))  # User ID from Auth service
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)