from typing import Optional, List
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.domain.repositories.customer_repository import CustomerRepository
from src.api.schemas.customer_schemas import CustomerCreateRequest, CustomerUpdateRequest

class CustomerApplicationService:
    
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository
    
    async def create_customer(self, request: CustomerCreateRequest) -> Customer:
        # Check if email already exists
        email = Email(request.email)
        existing_customer = await self.customer_repository.find_by_email(email)
        if existing_customer:
            raise ValueError("Customer with this email already exists")
        
        # Create new customer
        customer = Customer(
            email=email,
            customer_type=request.customer_type,
            business_name=request.business_name,
            tax_id=request.tax_id,
            phone=request.phone,
            address=request.address
        )
        
        return await self.customer_repository.save(customer)
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        return await self.customer_repository.find_by_id(CustomerId.from_string(customer_id))
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        return await self.customer_repository.find_by_email(Email(email))
    
    async def update_customer(self, customer_id: str, request: CustomerUpdateRequest) -> Customer:
        customer = await self.customer_repository.find_by_id(CustomerId.from_string(customer_id))
        if not customer:
            raise ValueError("Customer not found")
        
        # Update fields if provided
        if request.customer_type is not None:
            customer.customer_type = request.customer_type
        if request.business_name is not None:
            customer.business_name = request.business_name
        if request.tax_id is not None:
            customer.tax_id = request.tax_id
        if request.phone is not None:
            customer.phone = request.phone
        if request.address is not None:
            customer.address = request.address
        
        return await self.customer_repository.save(customer)
    
    async def validate_customer_kyc(self, customer_id: str) -> Customer:
        customer = await self.customer_repository.find_by_id(CustomerId.from_string(customer_id))
        if not customer:
            raise ValueError("Customer not found")
        
        customer.validate_kyc()
        return await self.customer_repository.save(customer)
    
    async def deactivate_customer(self, customer_id: str) -> Customer:
        customer = await self.customer_repository.find_by_id(CustomerId.from_string(customer_id))
        if not customer:
            raise ValueError("Customer not found")
        
        customer.deactivate()
        return await self.customer_repository.save(customer)
    
    async def list_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        return await self.customer_repository.find_all(limit=limit, offset=offset)