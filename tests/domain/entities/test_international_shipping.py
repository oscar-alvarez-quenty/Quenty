import pytest
from datetime import datetime, timedelta
from src.domain.entities.international_shipping import (
    InternationalShipment, KYCValidation, CustomsDeclaration, InternationalDocument,
    ShippingRestriction, DocumentType, KYCStatus, CustomsStatus, RestrictionLevel
)
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class TestInternationalShipment:
    def test_create_international_shipment(self):
        """Test creating an international shipment"""
        shipment_id = "intl_001"
        guide_id = GuideId("guide_001")
        customer_id = CustomerId("customer_001")
        destination_country = "United States"
        declared_value = Money(100.0, "USD")
        product_description = "Electronics"
        product_category = "technology"
        weight_kg = 2.5
        
        shipment = InternationalShipment(
            shipment_id=shipment_id,
            guide_id=guide_id,
            customer_id=customer_id,
            destination_country=destination_country,
            declared_value=declared_value,
            product_description=product_description,
            product_category=product_category,
            weight_kg=weight_kg
        )
        
        assert shipment.shipment_id == shipment_id
        assert shipment.guide_id == guide_id
        assert shipment.customer_id == customer_id
        assert shipment.destination_country == destination_country
        assert shipment.declared_value == declared_value
        assert shipment.product_description == product_description
        assert shipment.product_category == product_category
        assert shipment.weight_kg == weight_kg
        assert shipment.customs_status == CustomsStatus.PENDING
        assert shipment.compliance_status == "pending"
        assert shipment.documents == []

    def test_add_required_document(self):
        """Test adding required document to shipment"""
        shipment = self._create_sample_shipment()
        document = InternationalDocument(
            document_id="doc_001",
            guide_id=shipment.guide_id,
            document_type=DocumentType.INVOICE,
            file_url="http://example.com/invoice.pdf"
        )
        
        shipment.add_required_document(document)
        
        assert len(shipment.documents) == 1
        assert shipment.documents[0] == document

    def test_set_customs_status(self):
        """Test setting customs status"""
        shipment = self._create_sample_shipment()
        
        shipment.set_customs_status(CustomsStatus.IN_PROCESS)
        assert shipment.customs_status == CustomsStatus.IN_PROCESS
        
        shipment.set_customs_status(CustomsStatus.CLEARED, estimated_clearance_date=datetime.now() + timedelta(days=3))
        assert shipment.customs_status == CustomsStatus.CLEARED
        assert shipment.estimated_customs_clearance_date is not None

    def test_update_compliance_status(self):
        """Test updating compliance status"""
        shipment = self._create_sample_shipment()
        
        shipment.update_compliance_status("approved")
        assert shipment.compliance_status == "approved"

    def test_get_missing_documents(self):
        """Test getting missing documents"""
        shipment = self._create_sample_shipment()
        
        # Initially all documents are missing
        missing = shipment.get_missing_documents()
        assert DocumentType.INVOICE in missing
        assert DocumentType.PACKING_LIST in missing
        assert DocumentType.CERTIFICATE_OF_ORIGIN in missing
        
        # Add invoice document
        invoice_doc = InternationalDocument(
            document_id="doc_001",
            guide_id=shipment.guide_id,
            document_type=DocumentType.INVOICE,
            file_url="http://example.com/invoice.pdf"
        )
        shipment.add_required_document(invoice_doc)
        
        missing_after = shipment.get_missing_documents()
        assert DocumentType.INVOICE not in missing_after
        assert DocumentType.PACKING_LIST in missing_after

    def test_is_ready_for_shipping(self):
        """Test checking if shipment is ready for shipping"""
        shipment = self._create_sample_shipment()
        
        # Not ready initially
        assert shipment.is_ready_for_shipping() == False
        
        # Add all required documents
        required_docs = [DocumentType.INVOICE, DocumentType.PACKING_LIST, DocumentType.CERTIFICATE_OF_ORIGIN]
        for i, doc_type in enumerate(required_docs):
            doc = InternationalDocument(
                document_id=f"doc_{i+1:03d}",
                guide_id=shipment.guide_id,
                document_type=doc_type,
                file_url=f"http://example.com/{doc_type.value}.pdf"
            )
            shipment.add_required_document(doc)
        
        # Set compliance and customs status
        shipment.update_compliance_status("approved")
        shipment.set_customs_status(CustomsStatus.CLEARED)
        
        # Now should be ready
        assert shipment.is_ready_for_shipping() == True

    def test_calculate_international_costs(self):
        """Test calculating international shipping costs"""
        shipment = self._create_sample_shipment()
        
        costs = shipment.calculate_international_costs()
        
        assert "customs_fees" in costs
        assert "insurance" in costs
        assert "total" in costs
        assert isinstance(costs["customs_fees"], Money)
        assert isinstance(costs["insurance"], Money)
        assert isinstance(costs["total"], Money)

    def _create_sample_shipment(self):
        """Helper method to create a sample international shipment"""
        return InternationalShipment(
            shipment_id="intl_001",
            guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            destination_country="United States",
            declared_value=Money(100.0, "USD"),
            product_description="Electronics",
            product_category="technology",
            weight_kg=2.5
        )


class TestKYCValidation:
    def test_create_kyc_validation(self):
        """Test creating KYC validation"""
        kyc_id = "kyc_001"
        customer_id = CustomerId("customer_001")
        provider = "truora"
        
        kyc = KYCValidation(kyc_id, customer_id, provider)
        
        assert kyc.kyc_id == kyc_id
        assert kyc.customer_id == customer_id
        assert kyc.provider == provider
        assert kyc.status == KYCStatus.PENDING
        assert kyc.documents_submitted == []
        assert kyc.validation_score is None
        assert kyc.risk_level == "unknown"

    def test_submit_document(self):
        """Test submitting document for KYC"""
        kyc = self._create_sample_kyc()
        document_type = "passport"
        file_url = "http://example.com/passport.jpg"
        
        kyc.submit_document(document_type, file_url)
        
        assert len(kyc.documents_submitted) == 1
        submitted_doc = kyc.documents_submitted[0]
        assert submitted_doc["document_type"] == document_type
        assert submitted_doc["file_url"] == file_url
        assert "submitted_at" in submitted_doc

    def test_approve_kyc(self):
        """Test approving KYC validation"""
        kyc = self._create_sample_kyc()
        approved_by = "admin_001"
        validation_score = 85.0
        risk_level = "low"
        expiry_months = 12
        
        kyc.approve_kyc(approved_by, validation_score, risk_level, expiry_months)
        
        assert kyc.status == KYCStatus.APPROVED
        assert kyc.approved_by == approved_by
        assert kyc.validation_score == validation_score
        assert kyc.risk_level == risk_level
        assert kyc.approved_at is not None
        assert kyc.expiry_date is not None

    def test_reject_kyc(self):
        """Test rejecting KYC validation"""
        kyc = self._create_sample_kyc()
        rejection_reasons = ["Document quality poor", "Information mismatch"]
        
        kyc.reject_kyc(rejection_reasons)
        
        assert kyc.status == KYCStatus.REJECTED
        assert kyc.rejection_reasons == rejection_reasons
        assert kyc.rejected_at is not None

    def test_is_valid_for_international_shipping(self):
        """Test checking if KYC is valid for international shipping"""
        kyc = self._create_sample_kyc()
        
        # Not valid when pending
        assert kyc.is_valid_for_international_shipping() == False
        
        # Valid when approved and not expired
        kyc.approve_kyc("admin_001", 85.0, "low", 12)
        assert kyc.is_valid_for_international_shipping() == True
        
        # Not valid when rejected
        kyc.status = KYCStatus.REJECTED
        assert kyc.is_valid_for_international_shipping() == False

    def test_is_expired(self):
        """Test checking if KYC validation is expired"""
        kyc = self._create_sample_kyc()
        
        # Not expired when no expiry date
        assert kyc.is_expired() == False
        
        # Set expired date
        kyc.expiry_date = datetime.now() - timedelta(days=1)
        assert kyc.is_expired() == True
        
        # Set future expiry date
        kyc.expiry_date = datetime.now() + timedelta(days=30)
        assert kyc.is_expired() == False

    def _create_sample_kyc(self):
        """Helper method to create a sample KYC validation"""
        return KYCValidation(
            kyc_id="kyc_001",
            customer_id=CustomerId("customer_001"),
            provider="truora"
        )


class TestCustomsDeclaration:
    def test_create_customs_declaration(self):
        """Test creating customs declaration"""
        declaration_id = "customs_001"
        guide_id = GuideId("guide_001")
        declared_value = Money(100.0, "USD")
        product_description = "Electronics"
        product_category = "technology"
        quantity = 2
        weight_kg = 1.5
        country_of_origin = "Colombia"
        
        declaration = CustomsDeclaration(
            declaration_id=declaration_id,
            guide_id=guide_id,
            declared_value=declared_value,
            product_description=product_description,
            product_category=product_category,
            quantity=quantity,
            weight_kg=weight_kg,
            country_of_origin=country_of_origin
        )
        
        assert declaration.declaration_id == declaration_id
        assert declaration.guide_id == guide_id
        assert declaration.declared_value == declared_value
        assert declaration.product_description == product_description
        assert declaration.product_category == product_category
        assert declaration.quantity == quantity
        assert declaration.weight_kg == weight_kg
        assert declaration.country_of_origin == country_of_origin
        assert declaration.hs_code is None

    def test_set_hs_code(self):
        """Test setting HS code"""
        declaration = self._create_sample_declaration()
        hs_code = "8517.12.00"
        
        declaration.set_hs_code(hs_code)
        assert declaration.hs_code == hs_code

    def test_calculate_customs_duties(self):
        """Test calculating customs duties"""
        declaration = self._create_sample_declaration()
        
        duties = declaration.calculate_customs_duties()
        
        assert isinstance(duties, Money)
        assert duties.amount >= 0

    def test_validate_declaration(self):
        """Test validating customs declaration"""
        declaration = self._create_sample_declaration()
        
        # Should be valid initially
        is_valid, errors = declaration.validate_declaration()
        assert is_valid == True
        assert len(errors) == 0
        
        # Test with invalid quantity
        declaration.quantity = 0
        is_valid, errors = declaration.validate_declaration()
        assert is_valid == False
        assert "Cantidad debe ser mayor a 0" in errors

    def _create_sample_declaration(self):
        """Helper method to create a sample customs declaration"""
        return CustomsDeclaration(
            declaration_id="customs_001",
            guide_id=GuideId("guide_001"),
            declared_value=Money(100.0, "USD"),
            product_description="Electronics",
            product_category="technology",
            quantity=2,
            weight_kg=1.5,
            country_of_origin="Colombia"
        )


class TestInternationalDocument:
    def test_create_international_document(self):
        """Test creating international document"""
        document_id = "doc_001"
        guide_id = GuideId("guide_001")
        document_type = DocumentType.INVOICE
        file_url = "http://example.com/invoice.pdf"
        
        document = InternationalDocument(
            document_id=document_id,
            guide_id=guide_id,
            document_type=document_type,
            file_url=file_url
        )
        
        assert document.document_id == document_id
        assert document.guide_id == guide_id
        assert document.document_type == document_type
        assert document.file_url == file_url
        assert document.is_translated == False
        assert document.validation_status == "pending"
        assert document.requires_translation() == False

    def test_set_validation_status(self):
        """Test setting validation status"""
        document = self._create_sample_document()
        
        document.set_validation_status("approved")
        assert document.validation_status == "approved"

    def test_mark_as_translated(self):
        """Test marking document as translated"""
        document = self._create_sample_document()
        translated_url = "http://example.com/invoice_translated.pdf"
        
        document.mark_as_translated(translated_url)
        
        assert document.is_translated == True
        assert document.translated_file_url == translated_url

    def test_requires_translation(self):
        """Test checking if document requires translation"""
        document = self._create_sample_document()
        
        # Set destination to country requiring translation
        document.destination_language = "en"
        document.source_language = "es"
        
        assert document.requires_translation() == True
        
        # Same language
        document.source_language = "en"
        assert document.requires_translation() == False

    def test_validate_document_format(self):
        """Test validating document format"""
        document = self._create_sample_document()
        
        # Valid PDF format
        is_valid, error = document.validate_document_format()
        assert is_valid == True
        assert error is None
        
        # Invalid format
        document.file_url = "http://example.com/invoice.txt"
        is_valid, error = document.validate_document_format()
        assert is_valid == False
        assert "Formato de documento no válido" in error

    def _create_sample_document(self):
        """Helper method to create a sample international document"""
        return InternationalDocument(
            document_id="doc_001",
            guide_id=GuideId("guide_001"),
            document_type=DocumentType.INVOICE,
            file_url="http://example.com/invoice.pdf"
        )


class TestShippingRestriction:
    def test_create_shipping_restriction(self):
        """Test creating shipping restriction"""
        restriction_id = "restr_001"
        destination_country = "United States"
        product_category = "technology"
        restriction_level = RestrictionLevel.MODERATE
        required_documents = [DocumentType.INVOICE, DocumentType.CERTIFICATE_OF_ORIGIN]
        max_value = Money(1000.0, "USD")
        max_weight_kg = 10.0
        estimated_customs_days = 5
        
        restriction = ShippingRestriction(
            restriction_id=restriction_id,
            destination_country=destination_country,
            product_category=product_category,
            restriction_level=restriction_level,
            required_documents=required_documents,
            max_value=max_value,
            max_weight_kg=max_weight_kg,
            estimated_customs_days=estimated_customs_days
        )
        
        assert restriction.restriction_id == restriction_id
        assert restriction.destination_country == destination_country
        assert restriction.product_category == product_category
        assert restriction.restriction_level == restriction_level
        assert restriction.required_documents == required_documents
        assert restriction.max_value == max_value
        assert restriction.max_weight_kg == max_weight_kg
        assert restriction.estimated_customs_days == estimated_customs_days

    def test_is_shipment_allowed(self):
        """Test checking if shipment is allowed under restriction"""
        restriction = self._create_sample_restriction()
        shipment = self._create_sample_shipment()
        
        # Should be allowed within limits
        is_allowed, reason = restriction.is_shipment_allowed(shipment)
        assert is_allowed == True
        assert reason is None
        
        # Test value limit
        shipment.declared_value = Money(2000.0, "USD")  # Exceeds max
        is_allowed, reason = restriction.is_shipment_allowed(shipment)
        assert is_allowed == False
        assert "valor excede el máximo permitido" in reason
        
        # Test weight limit
        shipment.declared_value = Money(500.0, "USD")  # Reset value
        shipment.weight_kg = 15.0  # Exceeds max weight
        is_allowed, reason = restriction.is_shipment_allowed(shipment)
        assert is_allowed == False
        assert "peso excede el máximo permitido" in reason

    def test_get_missing_documents_for_shipment(self):
        """Test getting missing documents for shipment"""
        restriction = self._create_sample_restriction()
        shipment = self._create_sample_shipment()
        
        # Add one required document
        invoice_doc = InternationalDocument(
            document_id="doc_001",
            guide_id=shipment.guide_id,
            document_type=DocumentType.INVOICE,
            file_url="http://example.com/invoice.pdf"
        )
        shipment.add_required_document(invoice_doc)
        
        missing = restriction.get_missing_documents_for_shipment(shipment)
        
        assert DocumentType.INVOICE not in missing
        assert DocumentType.CERTIFICATE_OF_ORIGIN in missing

    def test_estimate_processing_time(self):
        """Test estimating processing time"""
        restriction = self._create_sample_restriction()
        
        estimated_days = restriction.estimate_processing_time()
        assert estimated_days == restriction.estimated_customs_days

    def _create_sample_restriction(self):
        """Helper method to create a sample shipping restriction"""
        return ShippingRestriction(
            restriction_id="restr_001",
            destination_country="United States",
            product_category="technology",
            restriction_level=RestrictionLevel.MODERATE,
            required_documents=[DocumentType.INVOICE, DocumentType.CERTIFICATE_OF_ORIGIN],
            max_value=Money(1000.0, "USD"),
            max_weight_kg=10.0,
            estimated_customs_days=5
        )

    def _create_sample_shipment(self):
        """Helper method to create a sample shipment for testing"""
        return InternationalShipment(
            shipment_id="intl_001",
            guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            destination_country="United States",
            declared_value=Money(500.0, "USD"),
            product_description="Electronics",
            product_category="technology",
            weight_kg=2.5
        )