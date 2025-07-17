from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.domain.entities.international_shipping import (
    InternationalShipment, KYCValidation, InternationalDocument, CustomsDeclaration
)
from src.infrastructure.models.international_shipping_models import (
    InternationalShipmentModel, KYCValidationModel, 
    InternationalDocumentModel, CustomsDeclarationModel
)
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class InternationalShippingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_shipment(self, shipment: InternationalShipment) -> InternationalShipment:
        """Crear nuevo envío internacional"""
        shipment_model = InternationalShipmentModel(
            shipment_id=shipment.shipment_id,
            guide_id=shipment.guide_id.value,
            customer_id=shipment.customer_id.value,
            destination_country=shipment.destination_country,
            declared_value_amount=shipment.declared_value.amount,
            declared_value_currency=shipment.declared_value.currency,
            created_at=shipment.created_at,
            updated_at=shipment.updated_at,
            customs_status=shipment.customs_status.value,
            customs_tracking_number=shipment.customs_tracking_number,
            estimated_customs_clearance_date=shipment.estimated_customs_clearance_date,
            actual_customs_clearance_date=shipment.actual_customs_clearance_date,
            customs_fees_amount=shipment.customs_fees.amount,
            customs_fees_currency=shipment.customs_fees.currency,
            insurance_amount_amount=shipment.insurance_amount.amount,
            insurance_amount_currency=shipment.insurance_amount.currency,
            compliance_status=shipment.compliance_status,
            compliance_notes=shipment.compliance_notes
        )
        
        self.session.add(shipment_model)
        await self.session.commit()
        await self.session.refresh(shipment_model)
        
        return shipment

    async def get_shipment(self, shipment_id: str) -> Optional[InternationalShipment]:
        """Obtener envío por ID"""
        stmt = (
            select(InternationalShipmentModel)
            .options(
                selectinload(InternationalShipmentModel.documents),
                selectinload(InternationalShipmentModel.customs_declaration),
                selectinload(InternationalShipmentModel.kyc_validation)
            )
            .where(InternationalShipmentModel.shipment_id == shipment_id)
        )
        
        result = await self.session.execute(stmt)
        shipment_model = result.scalar_one_or_none()
        
        if shipment_model:
            return self._model_to_entity(shipment_model)
        return None

    async def update_shipment(self, shipment: InternationalShipment) -> InternationalShipment:
        """Actualizar envío internacional"""
        stmt = (
            update(InternationalShipmentModel)
            .where(InternationalShipmentModel.shipment_id == shipment.shipment_id)
            .values(
                updated_at=shipment.updated_at,
                customs_status=shipment.customs_status.value,
                customs_tracking_number=shipment.customs_tracking_number,
                estimated_customs_clearance_date=shipment.estimated_customs_clearance_date,
                actual_customs_clearance_date=shipment.actual_customs_clearance_date,
                customs_fees_amount=shipment.customs_fees.amount,
                customs_fees_currency=shipment.customs_fees.currency,
                insurance_amount_amount=shipment.insurance_amount.amount,
                insurance_amount_currency=shipment.insurance_amount.currency,
                compliance_status=shipment.compliance_status,
                compliance_notes=shipment.compliance_notes
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return shipment

    async def get_shipments_by_customer(self, customer_id: CustomerId) -> List[InternationalShipment]:
        """Obtener envíos por cliente"""
        stmt = (
            select(InternationalShipmentModel)
            .options(
                selectinload(InternationalShipmentModel.documents),
                selectinload(InternationalShipmentModel.customs_declaration)
            )
            .where(InternationalShipmentModel.customer_id == customer_id.value)
            .order_by(InternationalShipmentModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        shipment_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in shipment_models]

    async def get_shipments_by_destination(self, country: str) -> List[InternationalShipment]:
        """Obtener envíos por país destino"""
        stmt = (
            select(InternationalShipmentModel)
            .where(InternationalShipmentModel.destination_country == country)
            .order_by(InternationalShipmentModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        shipment_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in shipment_models]

    async def get_shipments_by_customs_status(self, status: str) -> List[InternationalShipment]:
        """Obtener envíos por estado aduanero"""
        stmt = (
            select(InternationalShipmentModel)
            .where(InternationalShipmentModel.customs_status == status)
            .order_by(InternationalShipmentModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        shipment_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in shipment_models]

    # KYC Validation methods
    async def create_kyc_validation(self, kyc_validation: KYCValidation) -> KYCValidation:
        """Crear validación KYC"""
        kyc_model = KYCValidationModel(
            kyc_id=kyc_validation.kyc_id,
            customer_id=kyc_validation.customer_id.value,
            provider=kyc_validation.provider,
            status=kyc_validation.status.value,
            created_at=kyc_validation.created_at,
            updated_at=kyc_validation.updated_at,
            submitted_documents=",".join(f"{k}:{v}" for k, v in kyc_validation.submitted_documents.items()),
            validation_results=str(kyc_validation.validation_results),
            expiry_date=kyc_validation.expiry_date,
            rejection_reasons=",".join(kyc_validation.rejection_reasons),
            approval_date=kyc_validation.approval_date,
            approved_by=kyc_validation.approved_by,
            validation_score=kyc_validation.validation_score,
            risk_level=kyc_validation.risk_level
        )
        
        self.session.add(kyc_model)
        await self.session.commit()
        await self.session.refresh(kyc_model)
        
        return kyc_validation

    async def get_kyc_validation(self, kyc_id: str) -> Optional[KYCValidation]:
        """Obtener validación KYC por ID"""
        stmt = select(KYCValidationModel).where(KYCValidationModel.kyc_id == kyc_id)
        result = await self.session.execute(stmt)
        kyc_model = result.scalar_one_or_none()
        
        if kyc_model:
            return self._kyc_model_to_entity(kyc_model)
        return None

    async def get_kyc_by_customer(self, customer_id: CustomerId) -> List[KYCValidation]:
        """Obtener validaciones KYC por cliente"""
        stmt = (
            select(KYCValidationModel)
            .where(KYCValidationModel.customer_id == customer_id.value)
            .order_by(KYCValidationModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        kyc_models = result.scalars().all()
        
        return [self._kyc_model_to_entity(model) for model in kyc_models]

    async def update_kyc_validation(self, kyc_validation: KYCValidation) -> KYCValidation:
        """Actualizar validación KYC"""
        stmt = (
            update(KYCValidationModel)
            .where(KYCValidationModel.kyc_id == kyc_validation.kyc_id)
            .values(
                status=kyc_validation.status.value,
                updated_at=kyc_validation.updated_at,
                submitted_documents=",".join(f"{k}:{v}" for k, v in kyc_validation.submitted_documents.items()),
                validation_results=str(kyc_validation.validation_results),
                expiry_date=kyc_validation.expiry_date,
                rejection_reasons=",".join(kyc_validation.rejection_reasons),
                approval_date=kyc_validation.approval_date,
                approved_by=kyc_validation.approved_by,
                validation_score=kyc_validation.validation_score,
                risk_level=kyc_validation.risk_level
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return kyc_validation

    # International Document methods
    async def create_document(self, document: InternationalDocument) -> InternationalDocument:
        """Crear documento internacional"""
        doc_model = InternationalDocumentModel(
            document_id=document.document_id,
            guide_id=document.guide_id.value,
            document_type=document.document_type.value,
            customer_id=document.customer_id.value,
            created_at=document.created_at,
            updated_at=document.updated_at,
            file_url=document.file_url,
            translated_file_url=document.translated_file_url,
            is_translated=document.is_translated,
            target_language=document.target_language,
            validation_status=document.validation_status,
            validation_notes=document.validation_notes,
            validated_by=document.validated_by,
            validated_at=document.validated_at,
            metadata=str(document.metadata)
        )
        
        self.session.add(doc_model)
        await self.session.commit()
        await self.session.refresh(doc_model)
        
        return document

    async def get_documents_by_guide(self, guide_id: GuideId) -> List[InternationalDocument]:
        """Obtener documentos por guía"""
        stmt = (
            select(InternationalDocumentModel)
            .where(InternationalDocumentModel.guide_id == guide_id.value)
            .order_by(InternationalDocumentModel.created_at)
        )
        
        result = await self.session.execute(stmt)
        doc_models = result.scalars().all()
        
        return [self._document_model_to_entity(model) for model in doc_models]

    # Customs Declaration methods
    async def create_customs_declaration(self, declaration: CustomsDeclaration) -> CustomsDeclaration:
        """Crear declaración aduanera"""
        customs_model = CustomsDeclarationModel(
            declaration_id=declaration.declaration_id,
            guide_id=declaration.guide_id.value,
            declared_value_amount=declaration.declared_value.amount,
            declared_value_currency=declaration.declared_value.currency,
            product_description=declaration.product_description,
            product_category=declaration.product_category,
            quantity=declaration.quantity,
            weight_kg=declaration.weight_kg,
            country_of_origin=declaration.country_of_origin,
            hs_code=declaration.hs_code,
            purpose=declaration.purpose
        )
        
        self.session.add(customs_model)
        await self.session.commit()
        await self.session.refresh(customs_model)
        
        return declaration

    async def get_customs_declaration_by_guide(self, guide_id: GuideId) -> Optional[CustomsDeclaration]:
        """Obtener declaración aduanera por guía"""
        stmt = (
            select(CustomsDeclarationModel)
            .where(CustomsDeclarationModel.guide_id == guide_id.value)
        )
        
        result = await self.session.execute(stmt)
        customs_model = result.scalar_one_or_none()
        
        if customs_model:
            return self._customs_model_to_entity(customs_model)
        return None

    async def search_shipments(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[InternationalShipment]:
        """Buscar envíos con filtros"""
        conditions = []
        
        if filters.get('customer_id'):
            conditions.append(InternationalShipmentModel.customer_id == filters['customer_id'])
        
        if filters.get('destination_country'):
            conditions.append(InternationalShipmentModel.destination_country == filters['destination_country'])
        
        if filters.get('customs_status'):
            conditions.append(InternationalShipmentModel.customs_status == filters['customs_status'])
        
        if filters.get('compliance_status'):
            conditions.append(InternationalShipmentModel.compliance_status == filters['compliance_status'])
        
        if filters.get('start_date'):
            conditions.append(InternationalShipmentModel.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            conditions.append(InternationalShipmentModel.created_at <= filters['end_date'])
        
        stmt = (
            select(InternationalShipmentModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(InternationalShipmentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        shipment_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in shipment_models]

    def _model_to_entity(self, model: InternationalShipmentModel) -> InternationalShipment:
        """Convertir modelo a entidad"""
        from src.domain.entities.international_shipping import CustomsStatus
        
        shipment = InternationalShipment(
            shipment_id=model.shipment_id,
            guide_id=GuideId(model.guide_id),
            customer_id=CustomerId(model.customer_id),
            destination_country=model.destination_country,
            declared_value=Money(model.declared_value_amount, model.declared_value_currency)
        )
        
        # Asignar propiedades adicionales
        shipment.created_at = model.created_at
        shipment.updated_at = model.updated_at
        shipment.customs_status = CustomsStatus(model.customs_status)
        shipment.customs_tracking_number = model.customs_tracking_number
        shipment.estimated_customs_clearance_date = model.estimated_customs_clearance_date
        shipment.actual_customs_clearance_date = model.actual_customs_clearance_date
        shipment.customs_fees = Money(model.customs_fees_amount, model.customs_fees_currency)
        shipment.insurance_amount = Money(model.insurance_amount_amount, model.insurance_amount_currency)
        shipment.compliance_status = model.compliance_status
        shipment.compliance_notes = model.compliance_notes
        
        # Cargar documentos relacionados
        if hasattr(model, 'documents') and model.documents:
            shipment.documents = [
                self._document_model_to_entity(doc) for doc in model.documents
            ]
        
        # Cargar declaración aduanera
        if hasattr(model, 'customs_declaration') and model.customs_declaration:
            shipment.customs_declaration = self._customs_model_to_entity(model.customs_declaration)
        
        return shipment

    def _kyc_model_to_entity(self, model: KYCValidationModel) -> KYCValidation:
        """Convertir modelo KYC a entidad"""
        from src.domain.entities.international_shipping import KYCStatus
        
        kyc_validation = KYCValidation(
            kyc_id=model.kyc_id,
            customer_id=CustomerId(model.customer_id),
            provider=model.provider
        )
        
        # Asignar propiedades
        kyc_validation.status = KYCStatus(model.status)
        kyc_validation.created_at = model.created_at
        kyc_validation.updated_at = model.updated_at
        kyc_validation.expiry_date = model.expiry_date
        kyc_validation.approval_date = model.approval_date
        kyc_validation.approved_by = model.approved_by
        kyc_validation.validation_score = model.validation_score
        kyc_validation.risk_level = model.risk_level
        
        # Parsear documentos enviados
        if model.submitted_documents:
            docs = {}
            for item in model.submitted_documents.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    docs[key] = value
            kyc_validation.submitted_documents = docs
        
        # Parsear razones de rechazo
        if model.rejection_reasons:
            kyc_validation.rejection_reasons = model.rejection_reasons.split(',')
        
        return kyc_validation

    def _document_model_to_entity(self, model: InternationalDocumentModel) -> InternationalDocument:
        """Convertir modelo de documento a entidad"""
        from src.domain.entities.international_shipping import DocumentType
        
        document = InternationalDocument(
            document_id=model.document_id,
            guide_id=GuideId(model.guide_id),
            document_type=DocumentType(model.document_type),
            customer_id=CustomerId(model.customer_id)
        )
        
        # Asignar propiedades
        document.created_at = model.created_at
        document.updated_at = model.updated_at
        document.file_url = model.file_url
        document.translated_file_url = model.translated_file_url
        document.is_translated = model.is_translated
        document.target_language = model.target_language
        document.validation_status = model.validation_status
        document.validation_notes = model.validation_notes
        document.validated_by = model.validated_by
        document.validated_at = model.validated_at
        
        # Parsear metadata
        if model.metadata:
            import json
            try:
                document.metadata = json.loads(model.metadata)
            except:
                document.metadata = {}
        
        return document

    def _customs_model_to_entity(self, model: CustomsDeclarationModel) -> CustomsDeclaration:
        """Convertir modelo de declaración aduanera a entidad"""
        return CustomsDeclaration(
            declaration_id=model.declaration_id,
            guide_id=GuideId(model.guide_id),
            declared_value=Money(model.declared_value_amount, model.declared_value_currency),
            product_description=model.product_description,
            product_category=model.product_category,
            quantity=model.quantity,
            weight_kg=model.weight_kg,
            country_of_origin=model.country_of_origin,
            hs_code=model.hs_code,
            purpose=model.purpose
        )