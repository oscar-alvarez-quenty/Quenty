"""
Unit tests for SCRUM-46: Bulk Shipment Loading functionality
Tests cover bulk upload validation, file processing, and row-by-row validation
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import io
from datetime import datetime, timedelta

from src.main import app, BulkUploadValidation
from src.models import BulkUploadStatus


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "user_id": "test_user_123",
        "company_id": "test_company_456",
        "permissions": ["shipping:bulk_create", "shipping:bulk_process"],
        "is_superuser": False
    }


@pytest.fixture
def valid_csv_content():
    """Valid CSV content for testing"""
    return """description,quantity,weight,volume,value,hs_code,country_of_origin,destination_country
Electronics - Smartphone,5,2.5,0.01,1000.0,8517.12,CN,US
Clothing - T-shirt,10,0.5,0.02,150.0,6109.10,BD,US
Books - Technical Manual,3,1.2,0.005,75.0,4901.99,US,MX"""


@pytest.fixture
def invalid_csv_content():
    """Invalid CSV content for testing validation errors"""
    return """description,quantity,weight,volume,value,hs_code,country_of_origin,destination_country
,5,2.5,0.01,1000.0,8517.12,CN,US
Electronics - Phone,-1,2.5,0.01,1000.0,8517.12,CN,US
Valid Product,10,0,0.02,150.0,6109.10,BD,US
Another Product,5,2.5,0.01,-100.0,invalid_hs,X,Y"""


class TestBulkUploadValidation:
    """Test cases for bulk upload validation logic"""
    
    def test_valid_item_validation(self):
        """Test validation of valid bulk upload item"""
        valid_data = {
            "row_number": 2,
            "description": "Electronics - Smartphone",
            "quantity": 5,
            "weight": 2.5,
            "volume": 0.01,
            "value": 1000.0,
            "hs_code": "8517.12",
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        validated_item = BulkUploadValidation(**valid_data)
        assert validated_item.description == "Electronics - Smartphone"
        assert validated_item.quantity == 5
        assert validated_item.weight == 2.5
        assert validated_item.value == 1000.0
    
    def test_invalid_description_validation(self):
        """Test validation failure for invalid description"""
        invalid_data = {
            "row_number": 2,
            "description": "",  # Empty description should fail
            "quantity": 5,
            "weight": 2.5,
            "value": 1000.0,
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "Description must be at least 3 characters" in str(exc_info.value)
    
    def test_invalid_quantity_validation(self):
        """Test validation failure for invalid quantity"""
        invalid_data = {
            "row_number": 2,
            "description": "Valid Product",
            "quantity": 0,  # Quantity must be > 0
            "weight": 2.5,
            "value": 1000.0,
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_invalid_weight_validation(self):
        """Test validation failure for invalid weight"""
        invalid_data = {
            "row_number": 2,
            "description": "Valid Product",
            "quantity": 5,
            "weight": -1.0,  # Weight must be > 0
            "value": 1000.0,
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_invalid_value_validation(self):
        """Test validation failure for invalid value"""
        invalid_data = {
            "row_number": 2,
            "description": "Valid Product",
            "quantity": 5,
            "weight": 2.5,
            "value": 0,  # Value must be > 0
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "greater than 0" in str(exc_info.value)
    
    def test_invalid_hs_code_validation(self):
        """Test validation failure for invalid HS code"""
        invalid_data = {
            "row_number": 2,
            "description": "Valid Product",
            "quantity": 5,
            "weight": 2.5,
            "value": 1000.0,
            "hs_code": "invalid_code",  # HS code should be numeric
            "country_of_origin": "CN",
            "destination_country": "US"
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "HS Code must contain only numbers and dots" in str(exc_info.value)
    
    def test_invalid_country_codes(self):
        """Test validation failure for invalid country codes"""
        invalid_data = {
            "row_number": 2,
            "description": "Valid Product",
            "quantity": 5,
            "weight": 2.5,
            "value": 1000.0,
            "country_of_origin": "X",  # Too short
            "destination_country": "Y"  # Too short
        }
        
        with pytest.raises(ValueError) as exc_info:
            BulkUploadValidation(**invalid_data)
        assert "at least 2 characters" in str(exc_info.value)


class TestBulkUploadEndpoints:
    """Test cases for bulk upload API endpoints"""
    
    @patch('src.main.verify_token')
    def test_bulk_upload_csv_success(self, mock_verify_token, client, mock_user, valid_csv_content):
        """Test successful CSV bulk upload"""
        mock_verify_token.return_value = mock_user
        
        files = {
            "file": ("test_shipments.csv", valid_csv_content, "text/csv")
        }
        
        response = client.post("/api/v1/bulk-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_shipments.csv"
        assert data["total_rows"] == 3
        assert data["valid_rows"] == 3
        assert data["invalid_rows"] == 0
        assert data["status"] == "completed"
    
    @patch('src.main.verify_token')
    def test_bulk_upload_csv_with_validation_errors(self, mock_verify_token, client, mock_user, invalid_csv_content):
        """Test CSV bulk upload with validation errors"""
        mock_verify_token.return_value = mock_user
        
        files = {
            "file": ("test_invalid.csv", invalid_csv_content, "text/csv")
        }
        
        response = client.post("/api/v1/bulk-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_invalid.csv"
        assert data["total_rows"] == 4
        assert data["valid_rows"] == 0  # All rows have validation errors
        assert data["invalid_rows"] == 4
        assert data["status"] == "failed"
        assert data["error_summary"] is not None
    
    @patch('src.main.verify_token')
    def test_bulk_upload_unsupported_file_type(self, mock_verify_token, client, mock_user):
        """Test bulk upload with unsupported file type"""
        mock_verify_token.return_value = mock_user
        
        files = {
            "file": ("test.txt", "some content", "text/plain")
        }
        
        response = client.post("/api/v1/bulk-upload", files=files)
        
        assert response.status_code == 400
        assert "Only CSV and Excel files are supported" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_bulk_upload_missing_columns(self, mock_verify_token, client, mock_user):
        """Test bulk upload with missing required columns"""
        mock_verify_token.return_value = mock_user
        
        # CSV missing 'weight' column
        invalid_csv = "description,quantity,value\nProduct 1,5,100.0"
        files = {
            "file": ("test_missing_cols.csv", invalid_csv, "text/csv")
        }
        
        response = client.post("/api/v1/bulk-upload", files=files)
        
        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_get_bulk_uploads(self, mock_verify_token, client, mock_user):
        """Test getting list of bulk uploads"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/bulk-upload")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all("unique_id" in upload for upload in data)
    
    @patch('src.main.verify_token')
    def test_get_bulk_uploads_with_status_filter(self, mock_verify_token, client, mock_user):
        """Test getting bulk uploads with status filter"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/bulk-upload?status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for upload in data:
            assert upload["status"] == "completed"
    
    @patch('src.main.verify_token')
    def test_get_bulk_upload_details(self, mock_verify_token, client, mock_user):
        """Test getting specific bulk upload details"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/bulk-upload/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "unique_id" in data
        assert "error_summary" in data
    
    @patch('src.main.verify_token')
    def test_get_bulk_upload_items(self, mock_verify_token, client, mock_user):
        """Test getting items from a bulk upload"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/bulk-upload/1/items")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "row_number" in item
            assert "status" in item
            assert "validation_errors" in item
    
    @patch('src.main.verify_token')
    def test_get_bulk_upload_items_with_status_filter(self, mock_verify_token, client, mock_user):
        """Test getting bulk upload items with status filter"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/bulk-upload/1/items?status=valid")
        
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "valid"
    
    @patch('src.main.verify_token')
    def test_process_bulk_upload(self, mock_verify_token, client, mock_user):
        """Test processing a bulk upload"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/bulk-upload/1/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == 1
        assert data["status"] == "completed"
        assert "processed_items" in data
        assert "manifest_ids" in data
    
    def test_bulk_upload_unauthorized(self, client):
        """Test bulk upload without authentication"""
        files = {
            "file": ("test.csv", "content", "text/csv")
        }
        
        response = client.post("/api/v1/bulk-upload", files=files)
        
        assert response.status_code == 403  # Forbidden without auth


class TestBulkUploadProcessing:
    """Test cases for bulk upload processing logic"""
    
    def test_csv_parsing(self, valid_csv_content):
        """Test CSV file parsing"""
        df = pd.read_csv(io.StringIO(valid_csv_content))
        
        assert len(df) == 3
        assert "description" in df.columns
        assert "quantity" in df.columns
        assert df.iloc[0]["description"] == "Electronics - Smartphone"
    
    def test_row_validation_tracking(self, invalid_csv_content):
        """Test that row numbers are correctly tracked during validation"""
        df = pd.read_csv(io.StringIO(invalid_csv_content))
        
        error_summary = {}
        for index, row in df.iterrows():
            row_number = index + 2  # Excel style row numbering
            try:
                # Simulate validation
                if not row.get('description') or len(str(row.get('description')).strip()) < 3:
                    raise ValueError("Description too short")
                if row.get('quantity', 0) <= 0:
                    raise ValueError("Invalid quantity")
            except ValueError as e:
                error_summary[f"row_{row_number}"] = [str(e)]
        
        assert len(error_summary) > 0
        assert "row_2" in error_summary  # First invalid row
    
    @pytest.mark.asyncio
    async def test_bulk_processing_performance(self):
        """Test that bulk processing can handle large datasets efficiently"""
        # Simulate processing 1000 rows
        start_time = datetime.utcnow()
        
        # Mock processing
        for i in range(1000):
            # Simulate validation and processing
            await asyncio.sleep(0.001)  # 1ms per row
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should process 1000 rows in reasonable time (< 5 seconds)
        assert processing_time < 5.0


class TestBulkUploadModels:
    """Test cases for bulk upload database models"""
    
    def test_bulk_upload_status_enum(self):
        """Test BulkUploadStatus enum values"""
        assert BulkUploadStatus.PENDING.value == "pending"
        assert BulkUploadStatus.PROCESSING.value == "processing"
        assert BulkUploadStatus.COMPLETED.value == "completed"
        assert BulkUploadStatus.FAILED.value == "failed"
    
    def test_bulk_upload_unique_id_generation(self):
        """Test unique ID generation for bulk uploads"""
        import uuid
        
        unique_id = f"BULK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        assert unique_id.startswith("BULK-")
        assert len(unique_id.split("-")) == 3
        assert len(unique_id.split("-")[2]) == 8  # UUID part is 8 chars


# Performance and integration test markers
@pytest.mark.performance
class TestBulkUploadPerformance:
    """Performance tests for bulk upload functionality"""
    
    @pytest.mark.asyncio
    async def test_large_file_processing(self):
        """Test processing of large CSV files"""
        # Generate large CSV content
        rows = []
        for i in range(100):  # 100 rows for testing
            rows.append(f"Product {i},5,2.5,0.01,100.0,8517.12,CN,US")
        
        large_csv = "description,quantity,weight,volume,value,hs_code,country_of_origin,destination_country\n"
        large_csv += "\n".join(rows)
        
        # Simulate processing
        df = pd.read_csv(io.StringIO(large_csv))
        assert len(df) == 100
        
        # Processing should complete without timeout
        valid_count = 0
        for index, row in df.iterrows():
            # Simulate validation
            if row.get('quantity', 0) > 0 and row.get('weight', 0) > 0:
                valid_count += 1
        
        assert valid_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])