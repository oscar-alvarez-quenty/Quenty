"""Implementación de repositorio de clientes usando SQLAlchemy.

Este módulo implementa el patrón Repository para la persistencia
de entidades Customer usando SQLAlchemy como ORM y PostgreSQL
como base de datos.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.infrastructure.models.customer_model import CustomerModel
from src.infrastructure.mappers.customer_mapper import CustomerMapper


class SQLAlchemyCustomerRepository(CustomerRepository):
    """Repositorio de clientes implementado con SQLAlchemy.
    
    Proporciona operaciones CRUD para entidades Customer,
    manejando la conversión entre entidades de dominio y modelos
    de base de datos a través de mappers.
    
    Attributes:
        session: Sesión asíncrona de SQLAlchemy
        mapper: Mapper para conversión entre entidad y modelo
    """
    
    def __init__(self, session: AsyncSession):
        """Inicializa el repositorio con una sesión de base de datos.
        
        Args:
            session: Sesión asíncrona de SQLAlchemy
        """
        self.session = session
        self.mapper = CustomerMapper()
    
    async def save(self, customer: Customer) -> Customer:
        """Guarda o actualiza un cliente en la base de datos.
        
        Si el cliente ya existe (por ID), actualiza sus datos.
        Si no existe, crea un nuevo registro.
        
        Args:
            customer: Entidad Customer a persistir
            
        Returns:
            Customer: Entidad actualizada con datos de la base de datos
            
        Raises:
            SQLAlchemyError: Si ocurre un error en la base de datos
        """
        model = self.mapper.to_model(customer)
        
        # Verificar si el cliente existe
        existing = await self.session.get(CustomerModel, customer.id.value)
        if existing:
            # Actualizar cliente existente
            for key, value in model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            model = existing
        else:
            # Agregar nuevo cliente
            self.session.add(model)
        
        await self.session.commit()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)
    
    async def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]:
        """Busca un cliente por su ID.
        
        Args:
            customer_id: ID del cliente a buscar
            
        Returns:
            Customer o None si no se encuentra
        """
        model = await self.session.get(CustomerModel, customer_id.value)
        return self.mapper.to_entity(model) if model else None
    
    async def find_by_email(self, email: Email) -> Optional[Customer]:
        """Busca un cliente por su dirección de correo electrónico.
        
        Args:
            email: Email del cliente a buscar
            
        Returns:
            Customer o None si no se encuentra
        """
        stmt = select(CustomerModel).where(CustomerModel.email == email.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Obtiene una lista paginada de todos los clientes.
        
        Args:
            limit: Número máximo de clientes a retornar
            offset: Número de clientes a omitir para paginación
            
        Returns:
            Lista de entidades Customer
        """
        stmt = select(CustomerModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete(self, customer_id: CustomerId) -> bool:
        """Elimina un cliente de la base de datos.
        
        Args:
            customer_id: ID del cliente a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existía
            
        Note:
            Esta operación puede fallar si existen referencias
            de integridad (orders, etc.)
        """
        model = await self.session.get(CustomerModel, customer_id.value)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False
    
    async def exists_by_email(self, email: Email) -> bool:
        """Verifica si existe un cliente con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            bool: True si existe un cliente con ese email
        """
        customer = await self.find_by_email(email)
        return customer is not None