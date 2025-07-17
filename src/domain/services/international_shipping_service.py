from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from src.domain.entities.international_shipping import (
    InternationalShipment, KYCValidation, InternationalDocument, 
    CustomsDeclaration, CountryRestriction, KYCStatus, DocumentType,
    CustomsStatus, ShippingRestrictionLevel
)
from src.domain.entities.customer import Customer
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.domain.events.international_shipping_events import (
    KYCValidationStarted, InternationalShipmentCreated, CustomsDeclarationCreated,
    CountryRestrictionsValidated, InternationalShipmentReadyForShipping,
    CustomsClearanceStarted, InternationalCostsCalculated, HSCodeAssigned
)


class InternationalShippingService:
    def __init__(self):
        self.shipments: Dict[str, InternationalShipment] = {}
        self.kyc_validations: Dict[str, KYCValidation] = {}
        self.country_restrictions: List[CountryRestriction] = []
        self.hs_codes_database: Dict[str, str] = {}  # product_category -> hs_code
        self._domain_events: List = []
        
        # Inicializar restricciones de países
        self._initialize_country_restrictions()
        self._initialize_hs_codes()

    def create_international_shipment(
        self,
        guide_id: GuideId,
        customer: Customer,
        destination_country: str,
        declared_value: Money,
        product_description: str,
        product_category: str,
        weight_kg: float
    ) -> InternationalShipment:
        """Crear envío internacional"""
        shipment_id = str(uuid.uuid4())
        
        shipment = InternationalShipment(
            shipment_id=shipment_id,
            guide_id=guide_id,
            customer_id=customer.customer_id,
            destination_country=destination_country,
            declared_value=declared_value
        )
        
        # Validar restricciones del país
        applicable_restrictions = [
            r for r in self.country_restrictions
            if r.country_code == destination_country
        ]
        
        compliance_status = shipment.validate_country_restrictions(applicable_restrictions)
        
        self.shipments[shipment_id] = shipment
        
        self._add_domain_event(
            InternationalShipmentCreated(
                shipment_id=shipment_id,
                guide_id=guide_id.value,
                customer_id=customer.customer_id.value,
                destination_country=destination_country,
                declared_value={
                    "amount": declared_value.amount,
                    "currency": declared_value.currency
                },
                created_at=datetime.now()
            )
        )
        
        self._add_domain_event(
            CountryRestrictionsValidated(
                shipment_id=shipment_id,
                destination_country=destination_country,
                compliance_status=shipment.compliance_status,
                restrictions_checked=len(applicable_restrictions),
                compliance_issues=[shipment.compliance_notes] if shipment.compliance_notes else [],
                validated_at=datetime.now()
            )
        )
        
        return shipment

    def start_kyc_validation(
        self,
        customer_id: CustomerId,
        provider: str = "truora"
    ) -> KYCValidation:
        """Iniciar validación KYC para cliente"""
        kyc_id = str(uuid.uuid4())
        
        kyc_validation = KYCValidation(
            kyc_id=kyc_id,
            customer_id=customer_id,
            provider=provider
        )
        
        self.kyc_validations[kyc_id] = kyc_validation
        
        self._add_domain_event(
            KYCValidationStarted(
                kyc_id=kyc_id,
                customer_id=customer_id.value,
                provider=provider,
                validation_type="international_shipping"
            )
        )
        
        return kyc_validation

    def create_customs_declaration(
        self,
        shipment_id: str,
        product_description: str,
        product_category: str,
        quantity: int,
        weight_kg: float,
        country_of_origin: str
    ) -> CustomsDeclaration:
        """Crear declaración aduanera"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        declaration_id = str(uuid.uuid4())
        
        # Asignar código HS automáticamente
        hs_code = self._auto_assign_hs_code(product_category, product_description)
        
        declaration = shipment.create_customs_declaration(
            declaration_id=declaration_id,
            product_description=product_description,
            product_category=product_category,
            quantity=quantity,
            weight_kg=weight_kg,
            country_of_origin=country_of_origin,
            hs_code=hs_code
        )
        
        self._add_domain_event(
            CustomsDeclarationCreated(
                declaration_id=declaration_id,
                shipment_id=shipment_id,
                guide_id=shipment.guide_id.value,
                declared_value={
                    "amount": shipment.declared_value.amount,
                    "currency": shipment.declared_value.currency
                },
                product_description=product_description,
                product_category=product_category,
                hs_code=hs_code,
                created_at=datetime.now()
            )
        )
        
        if hs_code:
            self._add_domain_event(
                HSCodeAssigned(
                    declaration_id=declaration_id,
                    shipment_id=shipment_id,
                    product_description=product_description,
                    assigned_hs_code=hs_code,
                    assigned_by="system_auto",
                    confidence_score=0.85,
                    assigned_at=datetime.now()
                )
            )
        
        return declaration

    def add_required_document(
        self,
        shipment_id: str,
        document_type: DocumentType,
        file_url: str,
        metadata: Dict[str, Any] = None
    ) -> InternationalDocument:
        """Agregar documento requerido"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        document_id = str(uuid.uuid4())
        
        document = InternationalDocument(
            document_id=document_id,
            guide_id=shipment.guide_id,
            document_type=document_type,
            customer_id=shipment.customer_id
        )
        
        document.upload_document(file_url, metadata or {})
        
        # Verificar si requiere traducción
        if document.requires_translation(shipment.destination_country):
            # En implementación real, se enviaría a servicio de traducción
            pass
        
        shipment.add_document(document)
        
        return document

    def start_customs_clearance(
        self,
        shipment_id: str
    ) -> bool:
        """Iniciar proceso de liberación aduanera"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        if not shipment.is_ready_for_shipping():
            return False
        
        customs_tracking = f"CUS_{shipment_id[:8]}"
        shipment.start_customs_clearance(customs_tracking)
        
        self._add_domain_event(
            CustomsClearanceStarted(
                shipment_id=shipment_id,
                guide_id=shipment.guide_id.value,
                customs_tracking_number=customs_tracking,
                estimated_clearance_date=shipment.estimated_customs_clearance_date,
                started_at=datetime.now()
            )
        )
        
        return True

    def check_shipment_readiness(
        self,
        shipment_id: str
    ) -> Dict[str, Any]:
        """Verificar si envío está listo para ser enviado"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        readiness_status = {
            "is_ready": shipment.is_ready_for_shipping(),
            "kyc_valid": bool(shipment.kyc_validation and 
                            shipment.kyc_validation.is_valid_for_international_shipping()),
            "customs_declaration": bool(shipment.customs_declaration),
            "documents_complete": len(shipment.get_missing_documents()) == 0,
            "compliance_verified": shipment.compliance_status == "compliant",
            "missing_documents": [doc.value for doc in shipment.get_missing_documents()],
            "compliance_issues": shipment.compliance_notes
        }
        
        if readiness_status["is_ready"]:
            self._add_domain_event(
                InternationalShipmentReadyForShipping(
                    shipment_id=shipment_id,
                    guide_id=shipment.guide_id.value,
                    kyc_status=shipment.kyc_validation.status.value if shipment.kyc_validation else "not_submitted",
                    documents_complete=readiness_status["documents_complete"],
                    customs_ready=readiness_status["customs_declaration"],
                    compliance_verified=readiness_status["compliance_verified"],
                    ready_at=datetime.now()
                )
            )
        
        return readiness_status

    def calculate_international_costs(
        self,
        shipment_id: str
    ) -> Dict[str, Money]:
        """Calcular costos internacionales totales"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        # Calcular seguro (2% del valor declarado)
        insurance_amount = Money(
            shipment.declared_value.amount * 0.02,
            shipment.declared_value.currency
        )
        shipment.insurance_amount = insurance_amount
        
        # Estimar tarifas aduaneras (5% del valor declarado)
        estimated_customs_fees = Money(
            shipment.declared_value.amount * 0.05,
            shipment.declared_value.currency
        )
        
        total_costs = shipment.calculate_total_international_costs()
        
        costs = {
            "customs_fees": shipment.customs_fees,
            "insurance": insurance_amount,
            "total": total_costs
        }
        
        self._add_domain_event(
            InternationalCostsCalculated(
                shipment_id=shipment_id,
                guide_id=shipment.guide_id.value,
                customs_fees={
                    "amount": shipment.customs_fees.amount,
                    "currency": shipment.customs_fees.currency
                },
                insurance_amount={
                    "amount": insurance_amount.amount,
                    "currency": insurance_amount.currency
                },
                total_international_costs={
                    "amount": total_costs.amount,
                    "currency": total_costs.currency
                },
                calculated_at=datetime.now()
            )
        )
        
        return costs

    def get_shipping_restrictions(
        self,
        destination_country: str,
        product_category: str
    ) -> List[CountryRestriction]:
        """Obtener restricciones de envío para país y categoría"""
        return [
            r for r in self.country_restrictions
            if r.country_code == destination_country and 
               (r.product_category == product_category or r.product_category == "all")
        ]

    def validate_kyc_documents(
        self,
        kyc_id: str,
        validation_results: Dict[str, Any]
    ) -> bool:
        """Validar documentos KYC"""
        kyc_validation = self.kyc_validations.get(kyc_id)
        if not kyc_validation:
            raise ValueError(f"Validación KYC {kyc_id} no encontrada")
        
        if validation_results.get("approved", False):
            kyc_validation.approve_kyc(
                approved_by=validation_results["approved_by"],
                validation_score=validation_results["score"],
                risk_level=validation_results["risk_level"]
            )
            return True
        else:
            kyc_validation.reject_kyc(validation_results.get("rejection_reasons", []))
            return False

    def get_shipment_status_summary(
        self,
        shipment_id: str
    ) -> Dict[str, Any]:
        """Obtener resumen completo del estado del envío"""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Envío {shipment_id} no encontrado")
        
        return shipment.get_shipment_status_summary()

    def _auto_assign_hs_code(
        self,
        product_category: str,
        product_description: str
    ) -> Optional[str]:
        """Asignar código HS automáticamente"""
        # Buscar en base de datos de códigos HS
        hs_code = self.hs_codes_database.get(product_category.lower())
        
        # En implementación real, usaría ML para clasificación más precisa
        if not hs_code and "electronics" in product_description.lower():
            hs_code = "8517.12.00"
        elif not hs_code and "clothing" in product_description.lower():
            hs_code = "6109.10.00"
        elif not hs_code and "books" in product_description.lower():
            hs_code = "4901.99.00"
        
        return hs_code

    def _initialize_country_restrictions(self) -> None:
        """Inicializar restricciones por país"""
        # Restricciones para Estados Unidos
        self.country_restrictions.extend([
            CountryRestriction(
                country_code="US",
                product_category="electronics",
                restriction_level=ShippingRestrictionLevel.DOCUMENTATION,
                required_documents=[DocumentType.COMMERCIAL_INVOICE, DocumentType.CERTIFICATE_OF_ORIGIN],
                max_value=Money(800, "USD"),
                estimated_customs_days=5
            ),
            CountryRestriction(
                country_code="US",
                product_category="food",
                restriction_level=ShippingRestrictionLevel.PROHIBITED,
                required_documents=[],
                estimated_customs_days=7
            ),
            # Restricciones para Europa
            CountryRestriction(
                country_code="DE",
                product_category="all",
                restriction_level=ShippingRestrictionLevel.DOCUMENTATION,
                required_documents=[DocumentType.COMMERCIAL_INVOICE, DocumentType.PACKING_LIST],
                max_value=Money(150, "EUR"),
                estimated_customs_days=3
            ),
            # Restricciones para Reino Unido
            CountryRestriction(
                country_code="GB",
                product_category="all",
                restriction_level=ShippingRestrictionLevel.DOCUMENTATION,
                required_documents=[DocumentType.COMMERCIAL_INVOICE, DocumentType.CUSTOMS_DECLARATION],
                max_value=Money(135, "GBP"),
                estimated_customs_days=4
            )
        ])

    def _initialize_hs_codes(self) -> None:
        """Inicializar base de datos de códigos HS"""
        self.hs_codes_database = {
            "electronics": "8517.12.00",
            "clothing": "6109.10.00", 
            "books": "4901.99.00",
            "toys": "9503.00.00",
            "jewelry": "7113.11.00",
            "cosmetics": "3304.99.00",
            "shoes": "6403.99.00",
            "bags": "4202.92.00"
        }

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()