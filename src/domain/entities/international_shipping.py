"""Entidades de dominio para envíos internacionales.

Este módulo contiene las entidades para manejar envíos internacionales,
incluyendo validación KYC, documentación aduanera, restricciones por país
y cumplimiento regulatorio.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class KYCStatus(Enum):
    """Estados de validación KYC para envíos internacionales.
    
    Attributes:
        PENDING: Validación pendiente de inicio
        IN_REVIEW: En proceso de revisión
        APPROVED: Validación aprobada
        REJECTED: Validación rechazada
        EXPIRED: Validación expirada
        REQUIRES_UPDATE: Requiere actualización de datos
    """
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_UPDATE = "requires_update"


class DocumentType(Enum):
    """Tipos de documentos requeridos para envíos internacionales.
    
    Attributes:
        COMMERCIAL_INVOICE: Factura comercial
        RESPONSIBILITY_LETTER: Carta de responsabilidad
        EXPORT_PERMIT: Permiso de exportación
        CERTIFICATE_OF_ORIGIN: Certificado de origen
        PACKING_LIST: Lista de empaque
        CUSTOMS_DECLARATION: Declaración aduanera
        INSURANCE_CERTIFICATE: Certificado de seguro
    """
    COMMERCIAL_INVOICE = "commercial_invoice"
    RESPONSIBILITY_LETTER = "responsibility_letter"
    EXPORT_PERMIT = "export_permit"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    PACKING_LIST = "packing_list"
    CUSTOMS_DECLARATION = "customs_declaration"
    INSURANCE_CERTIFICATE = "insurance_certificate"


class CustomsStatus(Enum):
    """Estados del proceso aduanero.
    
    Attributes:
        PENDING: Pendiente de procesamiento aduanero
        IN_PROCESS: En proceso aduanero
        CLEARED: Liberado por aduana
        DETAINED: Detenido por aduana
        REJECTED: Rechazado por aduana
        REQUIRES_ADDITIONAL_INFO: Requiere información adicional
    """
    PENDING = "pending"
    IN_PROCESS = "in_process"
    CLEARED = "cleared"
    DETAINED = "detained"
    REJECTED = "rejected"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"


class ShippingRestrictionLevel(Enum):
    """Niveles de restricción para envíos por país.
    
    Attributes:
        NONE: Sin restricciones
        DOCUMENTATION: Requiere documentación adicional
        PROHIBITED: Completamente prohibido
        RESTRICTED: Restringido con condiciones especiales
    """
    NONE = "none"
    DOCUMENTATION = "documentation"
    PROHIBITED = "prohibited"
    RESTRICTED = "restricted"


@dataclass
class CountryRestriction:
    """Restricción de envío para un país específico.
    
    Define las limitaciones y requisitos especiales
    para envíos a un país particular.
    
    Attributes:
        country_code: Código ISO del país
        product_category: Categoría de producto afectada
        restriction_level: Nivel de restricción aplicable
    """
    country_code: str
    product_category: str
    restriction_level: ShippingRestrictionLevel
    required_documents: List[DocumentType]
    max_value: Optional[Money] = None
    max_weight_kg: Optional[float] = None
    special_requirements: List[str] = None
    estimated_customs_days: int = 3


@dataclass
class CustomsDeclaration:
    declaration_id: str
    guide_id: GuideId
    declared_value: Money
    product_description: str
    product_category: str
    quantity: int
    weight_kg: float
    country_of_origin: str
    hs_code: Optional[str] = None  # Harmonized System Code
    purpose: str = "commercial"  # commercial, gift, sample, return


class KYCValidation:
    def __init__(
        self,
        kyc_id: str,
        customer_id: CustomerId,
        provider: str = "truora"
    ):
        self.kyc_id = kyc_id
        self.customer_id = customer_id
        self.provider = provider
        self.status = KYCStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.submitted_documents: Dict[str, str] = {}  # document_type -> file_url
        self.validation_results: Dict[str, Any] = {}
        self.expiry_date: Optional[datetime] = None
        self.rejection_reasons: List[str] = []
        self.approval_date: Optional[datetime] = None
        self.approved_by: Optional[str] = None
        self.validation_score: Optional[float] = None
        self.risk_level: str = "unknown"  # low, medium, high, unknown

    def submit_document(self, document_type: str, file_url: str) -> None:
        """Enviar documento para validación"""
        if self.status in [KYCStatus.APPROVED, KYCStatus.REJECTED]:
            raise ValueError("No se pueden agregar documentos a un KYC finalizado")
        
        self.submitted_documents[document_type] = file_url
        self.updated_at = datetime.now()
        
        if self.status == KYCStatus.PENDING:
            self.status = KYCStatus.IN_REVIEW

    def approve_kyc(
        self,
        approved_by: str,
        validation_score: float,
        risk_level: str,
        expiry_months: int = 12
    ) -> None:
        """Aprobar validación KYC"""
        if self.status != KYCStatus.IN_REVIEW:
            raise ValueError("Solo se pueden aprobar KYCs en revisión")
        
        self.status = KYCStatus.APPROVED
        self.approved_by = approved_by
        self.approval_date = datetime.now()
        self.validation_score = validation_score
        self.risk_level = risk_level
        self.expiry_date = datetime.now().replace(month=(datetime.now().month + expiry_months) % 12)
        self.updated_at = datetime.now()

    def reject_kyc(self, rejection_reasons: List[str]) -> None:
        """Rechazar validación KYC"""
        if self.status not in [KYCStatus.IN_REVIEW, KYCStatus.PENDING]:
            raise ValueError("Solo se pueden rechazar KYCs en revisión o pendientes")
        
        self.status = KYCStatus.REJECTED
        self.rejection_reasons = rejection_reasons
        self.updated_at = datetime.now()

    def is_valid_for_international_shipping(self) -> bool:
        """Verificar si el KYC es válido para envíos internacionales"""
        return (self.status == KYCStatus.APPROVED and
                self.expiry_date and 
                self.expiry_date > datetime.now())

    def requires_renewal(self, days_before_expiry: int = 30) -> bool:
        """Verificar si requiere renovación"""
        if not self.expiry_date:
            return False
        
        renewal_date = self.expiry_date - timedelta(days=days_before_expiry)
        return datetime.now() >= renewal_date


class InternationalDocument:
    def __init__(
        self,
        document_id: str,
        guide_id: GuideId,
        document_type: DocumentType,
        customer_id: CustomerId
    ):
        self.document_id = document_id
        self.guide_id = guide_id
        self.document_type = document_type
        self.customer_id = customer_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.file_url: Optional[str] = None
        self.translated_file_url: Optional[str] = None
        self.is_translated = False
        self.target_language: Optional[str] = None
        self.validation_status = "pending"  # pending, valid, invalid, expired
        self.validation_notes: Optional[str] = None
        self.validated_by: Optional[str] = None
        self.validated_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    def upload_document(self, file_url: str, metadata: Dict[str, Any] = None) -> None:
        """Cargar documento"""
        self.file_url = file_url
        if metadata:
            self.metadata.update(metadata)
        self.updated_at = datetime.now()

    def add_translation(self, translated_file_url: str, target_language: str) -> None:
        """Agregar traducción del documento"""
        self.translated_file_url = translated_file_url
        self.target_language = target_language
        self.is_translated = True
        self.updated_at = datetime.now()

    def validate_document(
        self,
        is_valid: bool,
        validated_by: str,
        notes: Optional[str] = None
    ) -> None:
        """Validar documento"""
        self.validation_status = "valid" if is_valid else "invalid"
        self.validated_by = validated_by
        self.validated_at = datetime.now()
        if notes:
            self.validation_notes = notes
        self.updated_at = datetime.now()

    def requires_translation(self, destination_country: str) -> bool:
        """Verificar si requiere traducción"""
        # Países que requieren documentos en inglés
        english_required_countries = ["US", "GB", "CA", "AU", "NZ"]
        # Países hispanos que aceptan español
        spanish_countries = ["ES", "MX", "AR", "CL", "PE", "CO", "VE", "EC", "UY", "PY", "BO"]
        
        if destination_country in spanish_countries:
            return False
        
        return destination_country in english_required_countries


class InternationalShipment:
    def __init__(
        self,
        shipment_id: str,
        guide_id: GuideId,
        customer_id: CustomerId,
        destination_country: str,
        declared_value: Money
    ):
        self.shipment_id = shipment_id
        self.guide_id = guide_id
        self.customer_id = customer_id
        self.destination_country = destination_country
        self.declared_value = declared_value
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.kyc_validation: Optional[KYCValidation] = None
        self.documents: List[InternationalDocument] = []
        self.customs_declaration: Optional[CustomsDeclaration] = None
        self.customs_status = CustomsStatus.PENDING
        self.customs_tracking_number: Optional[str] = None
        self.estimated_customs_clearance_date: Optional[datetime] = None
        self.actual_customs_clearance_date: Optional[datetime] = None
        self.customs_fees: Money = Money(0, declared_value.currency)
        self.insurance_amount: Money = Money(0, declared_value.currency)
        self.country_restrictions: List[CountryRestriction] = []
        self.compliance_status = "pending"  # pending, compliant, non_compliant
        self.compliance_notes: Optional[str] = None

    def set_kyc_validation(self, kyc_validation: KYCValidation) -> None:
        """Establecer validación KYC"""
        if not kyc_validation.is_valid_for_international_shipping():
            raise ValueError("KYC no es válido para envíos internacionales")
        
        self.kyc_validation = kyc_validation
        self.updated_at = datetime.now()

    def add_document(self, document: InternationalDocument) -> None:
        """Agregar documento requerido"""
        if document.guide_id != self.guide_id:
            raise ValueError("El documento debe corresponder al mismo guide_id")
        
        # Verificar que no existe otro documento del mismo tipo
        existing = next(
            (d for d in self.documents if d.document_type == document.document_type),
            None
        )
        
        if existing:
            raise ValueError(f"Ya existe un documento de tipo {document.document_type.value}")
        
        self.documents.append(document)
        self.updated_at = datetime.now()

    def create_customs_declaration(
        self,
        declaration_id: str,
        product_description: str,
        product_category: str,
        quantity: int,
        weight_kg: float,
        country_of_origin: str,
        hs_code: Optional[str] = None
    ) -> CustomsDeclaration:
        """Crear declaración aduanera"""
        if self.customs_declaration:
            raise ValueError("Ya existe una declaración aduanera para este envío")
        
        self.customs_declaration = CustomsDeclaration(
            declaration_id=declaration_id,
            guide_id=self.guide_id,
            declared_value=self.declared_value,
            product_description=product_description,
            product_category=product_category,
            quantity=quantity,
            weight_kg=weight_kg,
            country_of_origin=country_of_origin,
            hs_code=hs_code
        )
        
        self.updated_at = datetime.now()
        return self.customs_declaration

    def validate_country_restrictions(self, restrictions: List[CountryRestriction]) -> bool:
        """Validar restricciones del país destino"""
        self.country_restrictions = [
            r for r in restrictions 
            if r.country_code == self.destination_country
        ]
        
        compliance_issues = []
        
        for restriction in self.country_restrictions:
            # Verificar valor máximo
            if restriction.max_value and self.declared_value.amount > restriction.max_value.amount:
                compliance_issues.append(f"Valor declarado excede máximo permitido")
            
            # Verificar peso máximo
            if restriction.max_weight_kg and self.customs_declaration:
                if self.customs_declaration.weight_kg > restriction.max_weight_kg:
                    compliance_issues.append(f"Peso excede máximo permitido")
            
            # Verificar documentos requeridos
            required_doc_types = set(restriction.required_documents)
            available_doc_types = set(d.document_type for d in self.documents)
            missing_docs = required_doc_types - available_doc_types
            
            if missing_docs:
                missing_names = [doc.value for doc in missing_docs]
                compliance_issues.append(f"Documentos faltantes: {', '.join(missing_names)}")
            
            # Verificar prohibiciones
            if restriction.restriction_level == ShippingRestrictionLevel.PROHIBITED:
                compliance_issues.append(f"Producto prohibido para {self.destination_country}")
        
        if compliance_issues:
            self.compliance_status = "non_compliant"
            self.compliance_notes = "; ".join(compliance_issues)
            return False
        else:
            self.compliance_status = "compliant"
            self.compliance_notes = "Cumple con todas las restricciones"
            return True

    def start_customs_clearance(self, tracking_number: str) -> None:
        """Iniciar proceso aduanero"""
        if not self.customs_declaration:
            raise ValueError("Se requiere declaración aduanera")
        
        if self.compliance_status != "compliant":
            raise ValueError("El envío debe cumplir con las restricciones antes del proceso aduanero")
        
        self.customs_status = CustomsStatus.IN_PROCESS
        self.customs_tracking_number = tracking_number
        
        # Estimar fecha de liberación aduanera
        base_days = 3  # días base para aduanas
        if self.country_restrictions:
            additional_days = max(r.estimated_customs_days for r in self.country_restrictions)
            base_days = max(base_days, additional_days)
        
        self.estimated_customs_clearance_date = datetime.now() + timedelta(days=base_days)
        self.updated_at = datetime.now()

    def complete_customs_clearance(self, customs_fees: Money) -> None:
        """Completar liberación aduanera"""
        if self.customs_status != CustomsStatus.IN_PROCESS:
            raise ValueError("El proceso aduanero debe estar en progreso")
        
        self.customs_status = CustomsStatus.CLEARED
        self.customs_fees = customs_fees
        self.actual_customs_clearance_date = datetime.now()
        self.updated_at = datetime.now()

    def detain_at_customs(self, reason: str) -> None:
        """Detener en aduanas"""
        self.customs_status = CustomsStatus.DETAINED
        self.compliance_notes = reason
        self.updated_at = datetime.now()

    def calculate_total_international_costs(self) -> Money:
        """Calcular costos totales internacionales"""
        total = Money(0, self.declared_value.currency)
        
        # Agregar fees aduaneros
        total = Money(total.amount + self.customs_fees.amount, total.currency)
        
        # Agregar seguro
        total = Money(total.amount + self.insurance_amount.amount, total.currency)
        
        return total

    def get_required_documents(self) -> List[DocumentType]:
        """Obtener documentos requeridos según destino"""
        required_docs = set()
        
        # Documentos base para envíos internacionales
        required_docs.add(DocumentType.COMMERCIAL_INVOICE)
        required_docs.add(DocumentType.RESPONSIBILITY_LETTER)
        
        # Documentos adicionales según restricciones del país
        for restriction in self.country_restrictions:
            required_docs.update(restriction.required_documents)
        
        return list(required_docs)

    def get_missing_documents(self) -> List[DocumentType]:
        """Obtener documentos faltantes"""
        required = set(self.get_required_documents())
        available = set(d.document_type for d in self.documents)
        return list(required - available)

    def is_ready_for_shipping(self) -> bool:
        """Verificar si está listo para envío"""
        return (
            self.kyc_validation and
            self.kyc_validation.is_valid_for_international_shipping() and
            self.customs_declaration and
            len(self.get_missing_documents()) == 0 and
            self.compliance_status == "compliant"
        )

    def get_shipment_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado del envío"""
        return {
            "shipment_id": self.shipment_id,
            "guide_id": self.guide_id.value,
            "destination_country": self.destination_country,
            "declared_value": {
                "amount": self.declared_value.amount,
                "currency": self.declared_value.currency
            },
            "kyc_status": self.kyc_validation.status.value if self.kyc_validation else "not_submitted",
            "customs_status": self.customs_status.value,
            "compliance_status": self.compliance_status,
            "documents_submitted": len(self.documents),
            "documents_required": len(self.get_required_documents()),
            "missing_documents": [doc.value for doc in self.get_missing_documents()],
            "ready_for_shipping": self.is_ready_for_shipping(),
            "estimated_customs_clearance": self.estimated_customs_clearance_date,
            "total_international_costs": {
                "amount": self.calculate_total_international_costs().amount,
                "currency": self.calculate_total_international_costs().currency
            }
        }