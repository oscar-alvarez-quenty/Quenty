from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"
    VIEWER = "viewer"

# Base Models
class BaseTimestamp(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = Field(UserRole.CUSTOMER, description="User role")
    company_id: Optional[str] = Field(None, description="Associated company ID")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")
    password_confirm: str = Field(..., description="Password confirmation")