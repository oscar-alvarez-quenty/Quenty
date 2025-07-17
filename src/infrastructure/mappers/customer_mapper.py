from typing import Optional
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.infrastructure.models.customer_model import CustomerModel

class CustomerMapper:
    
    def to_entity(self, model: Optional[CustomerModel]) -> Optional[Customer]:
        if not model:
            return None
        
        return Customer(
            id=CustomerId(model.id),
            email=Email(model.email),
            customer_type=model.customer_type,
            business_name=model.business_name,
            tax_id=model.tax_id,
            phone=model.phone,
            address=model.address,
            kyc_validated=model.kyc_validated,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def to_model(self, entity: Customer) -> CustomerModel:
        return CustomerModel(
            id=entity.id.value,
            email=entity.email.value,
            customer_type=entity.customer_type,
            business_name=entity.business_name,
            tax_id=entity.tax_id,
            phone=entity.phone,
            address=entity.address,
            kyc_validated=entity.kyc_validated,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )