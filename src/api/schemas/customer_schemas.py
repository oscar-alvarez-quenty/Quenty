from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from src.domain.value_objects.customer_type import CustomerType

class CustomerCreateRequest(BaseModel):
    email: EmailStr
    customer_type: CustomerType = CustomerType.SMALL
    business_name: str
    tax_id: str
    phone: str
    address: str
    
    @validator('business_name', 'tax_id', 'phone', 'address')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class CustomerUpdateRequest(BaseModel):
    customer_type: Optional[CustomerType] = None
    business_name: Optional[str] = None
    tax_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @validator('business_name', 'tax_id', 'phone', 'address', pre=True)
    def validate_not_empty_if_provided(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Field cannot be empty')
        return v.strip() if v else v

class CustomerResponse(BaseModel):
    id: str
    email: str
    customer_type: CustomerType
    business_name: str
    tax_id: str
    phone: str
    address: str
    kyc_validated: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    customers: list[CustomerResponse]
    total: int
    limit: int
    offset: int