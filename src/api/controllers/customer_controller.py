"""Controlador API para gestión de clientes.

Este módulo contiene los endpoints REST para operaciones CRUD
de clientes, incluyendo creación, consulta, actualización y
validación KYC.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.api.schemas.customer_schemas import (
    CustomerCreateRequest, 
    CustomerUpdateRequest, 
    CustomerResponse,
    CustomerListResponse
)
from src.application.services.customer_application_service import CustomerApplicationService
from src.infrastructure.database.database import get_db
from src.infrastructure.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

async def get_customer_service(db: AsyncSession = Depends(get_db)) -> CustomerApplicationService:
    """Factory para obtener el servicio de aplicación de clientes.
    
    Args:
        db: Sesión de base de datos inyectada
        
    Returns:
        CustomerApplicationService: Servicio configurado con dependencias
    """
    customer_repo = SQLAlchemyCustomerRepository(db)
    return CustomerApplicationService(customer_repo)

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CustomerCreateRequest,
    service: CustomerApplicationService = Depends(get_customer_service)
):
    """Crea un nuevo cliente en la plataforma.
    
    Args:
        request: Datos del cliente a crear
        service: Servicio de aplicación inyectado
        
    Returns:
        CustomerResponse: Datos del cliente creado
        
    Raises:
        HTTPException: 400 si los datos son inválidos
    """
    try:
        customer = await service.create_customer(request)
        return CustomerResponse(
            id=str(customer.id.value),
            email=customer.email.value,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            address=customer.address,
            kyc_validated=customer.kyc_validated,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    service: CustomerApplicationService = Depends(get_customer_service)
):
    """Obtiene un cliente por su ID.
    
    Args:
        customer_id: ID del cliente a consultar
        service: Servicio de aplicación inyectado
        
    Returns:
        CustomerResponse: Datos del cliente
        
    Raises:
        HTTPException: 404 si el cliente no existe
    """
    try:
        customer = await service.get_customer_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        return CustomerResponse(
            id=str(customer.id.value),
            email=customer.email.value,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            address=customer.address,
            kyc_validated=customer.kyc_validated,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    service: CustomerApplicationService = Depends(get_customer_service)
):
    """Actualiza los datos de un cliente.
    
    Args:
        customer_id: ID del cliente a actualizar
        request: Nuevos datos del cliente
        service: Servicio de aplicación inyectado
        
    Returns:
        CustomerResponse: Cliente actualizado
        
    Raises:
        HTTPException: 400 si los datos son inválidos
    """
    try:
        customer = await service.update_customer(customer_id, request)
        return CustomerResponse(
            id=str(customer.id.value),
            email=customer.email.value,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            address=customer.address,
            kyc_validated=customer.kyc_validated,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{customer_id}/validate-kyc", response_model=CustomerResponse)
async def validate_kyc(
    customer_id: str,
    service: CustomerApplicationService = Depends(get_customer_service)
):
    """Valida el KYC (Know Your Customer) de un cliente.
    
    Marca al cliente como validado KYC, habilitándolo para
    servicios avanzados como envíos internacionales.
    
    Args:
        customer_id: ID del cliente a validar
        service: Servicio de aplicación inyectado
        
    Returns:
        CustomerResponse: Cliente con KYC validado
        
    Raises:
        HTTPException: 400 si la validación falla
    """
    try:
        customer = await service.validate_customer_kyc(customer_id)
        return CustomerResponse(
            id=str(customer.id.value),
            email=customer.email.value,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            address=customer.address,
            kyc_validated=customer.kyc_validated,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    limit: int = 100,
    offset: int = 0,
    service: CustomerApplicationService = Depends(get_customer_service)
):
    """Obtiene una lista paginada de clientes.
    
    Args:
        limit: Número máximo de clientes a retornar (por defecto 100)
        offset: Número de clientes a omitir para paginación (por defecto 0)
        service: Servicio de aplicación inyectado
        
    Returns:
        CustomerListResponse: Lista paginada de clientes
    """
    customers = await service.list_customers(limit=limit, offset=offset)
    customer_responses = [
        CustomerResponse(
            id=str(customer.id.value),
            email=customer.email.value,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            address=customer.address,
            kyc_validated=customer.kyc_validated,
            is_active=customer.is_active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
        for customer in customers
    ]
    
    return CustomerListResponse(
        customers=customer_responses,
        total=len(customer_responses),
        limit=limit,
        offset=offset
    )