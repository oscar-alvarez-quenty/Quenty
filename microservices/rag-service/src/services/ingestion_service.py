import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..models import Document, DocumentChunk, IndexingJob
from ..database import microservice_connector
from .embedding_service import EmbeddingService
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting data from microservices into the vector database"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def ingest_from_microservice(
        self,
        db: AsyncSession,
        source: str,
        table_name: str,
        query: Optional[str] = None
    ) -> IndexingJob:
        """Ingest data from a specific microservice table"""
        
        # Create indexing job
        job = IndexingJob(
            source=source,
            status="running",
            started_at=datetime.utcnow(),
            metadata={"table": table_name}
        )
        db.add(job)
        await db.commit()
        
        try:
            # Execute query to fetch data
            if not query:
                query = f"SELECT * FROM {table_name}"
            
            rows = await microservice_connector.execute_query(source, query)
            job.total_records = len(rows)
            
            # Process each row
            for idx, row in enumerate(rows):
                await self._process_record(db, source, table_name, dict(row))
                job.processed_records = idx + 1
                
                # Commit every 100 records
                if (idx + 1) % 100 == 0:
                    await db.commit()
            
            # Final commit
            await db.commit()
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Successfully ingested {len(rows)} records from {source}.{table_name}")
            return job
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()
            logger.error(f"Failed to ingest from {source}.{table_name}: {e}")
            raise
    
    async def _process_record(
        self,
        db: AsyncSession,
        source: str,
        table_name: str,
        record: Dict[str, Any]
    ):
        """Process a single record and create document with chunks"""
        
        # Generate unique ID for the record
        source_id = record.get("id", hashlib.md5(json.dumps(record, sort_keys=True).encode()).hexdigest())
        
        # Check if document already exists
        existing_doc = await db.execute(
            select(Document).where(
                Document.source == source,
                Document.source_table == table_name,
                Document.source_id == str(source_id)
            )
        )
        existing_doc = existing_doc.scalar_one_or_none()
        
        # Delete existing document if it exists
        if existing_doc:
            await db.delete(existing_doc)
        
        # Create document content from record
        content = self._format_record_content(source, table_name, record)
        
        # Create document
        document = Document(
            source=source,
            source_table=table_name,
            source_id=str(source_id),
            document_type=self._get_document_type(table_name),
            content=content,
            metadata=record
        )
        db.add(document)
        await db.flush()
        
        # Create chunks with embeddings
        chunks = self.text_splitter.split_text(content)
        for idx, chunk_text in enumerate(chunks):
            embedding = await self.embedding_service.get_embedding(chunk_text)
            
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_text,
                embedding=embedding,
                metadata={"source": source, "table": table_name}
            )
            db.add(chunk)
    
    def _format_record_content(self, source: str, table_name: str, record: Dict[str, Any]) -> str:
        """Format record data into searchable text content"""
        
        # Service-specific formatting
        formatters = {
            "auth": self._format_auth_record,
            "customer": self._format_customer_record,
            "order": self._format_order_record,
            "carrier": self._format_carrier_record,
            "analytics": self._format_analytics_record,
            "franchise": self._format_franchise_record,
            "international": self._format_international_record,
            "microcredit": self._format_microcredit_record,
            "pickup": self._format_pickup_record,
            "reverse_logistics": self._format_reverse_logistics_record,
        }
        
        formatter = formatters.get(source, self._format_generic_record)
        return formatter(table_name, record)
    
    def _format_auth_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format auth service records"""
        if table_name == "users":
            return f"""
User Information:
- ID: {record.get('id')}
- Email: {record.get('email')}
- Name: {record.get('name', 'N/A')}
- Role: {record.get('role', 'N/A')}
- Status: {'Active' if record.get('is_active') else 'Inactive'}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_customer_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format customer service records"""
        if table_name == "customers":
            return f"""
Customer Profile:
- Customer ID: {record.get('id')}
- Name: {record.get('first_name')} {record.get('last_name')}
- Email: {record.get('email')}
- Phone: {record.get('phone')}
- Address: {record.get('address')}
- City: {record.get('city')}
- Country: {record.get('country')}
- Registration Date: {record.get('created_at')}
- Status: {record.get('status', 'Active')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_order_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format order service records"""
        if table_name == "orders":
            return f"""
Order Details:
- Order ID: {record.get('id')}
- Customer ID: {record.get('customer_id')}
- Order Number: {record.get('order_number')}
- Total Amount: ${record.get('total_amount', 0)}
- Status: {record.get('status')}
- Payment Method: {record.get('payment_method')}
- Shipping Address: {record.get('shipping_address')}
- Items: {record.get('items', [])}
- Created: {record.get('created_at')}
- Updated: {record.get('updated_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_carrier_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format carrier integration records"""
        if table_name == "shipments":
            return f"""
Shipment Information:
- Shipment ID: {record.get('id')}
- Tracking Number: {record.get('tracking_number')}
- Carrier: {record.get('carrier')}
- Service Type: {record.get('service_type')}
- Status: {record.get('status')}
- Origin: {record.get('origin_address')}
- Destination: {record.get('destination_address')}
- Weight: {record.get('weight')} {record.get('weight_unit')}
- Cost: ${record.get('cost')}
- Created: {record.get('created_at')}
"""
        elif table_name == "international_mailboxes":
            return f"""
International Mailbox:
- Mailbox ID: {record.get('id')}
- Customer ID: {record.get('customer_id')}
- Provider: {record.get('provider')}
- Mailbox Number: {record.get('mailbox_number')}
- Address: {record.get('address')}
- Status: {record.get('status')}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_analytics_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format analytics service records"""
        if table_name == "metrics":
            return f"""
Analytics Metric:
- Metric ID: {record.get('id')}
- Type: {record.get('metric_type')}
- Value: {record.get('value')}
- Period: {record.get('period')}
- Dimensions: {record.get('dimensions')}
- Timestamp: {record.get('timestamp')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_franchise_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format franchise service records"""
        if table_name == "franchises":
            return f"""
Franchise Information:
- Franchise ID: {record.get('id')}
- Name: {record.get('name')}
- Owner: {record.get('owner_name')}
- Location: {record.get('location')}
- Status: {record.get('status')}
- Revenue: ${record.get('revenue', 0)}
- Employees: {record.get('employee_count')}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_international_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format international shipping records"""
        if table_name == "international_shipments":
            return f"""
International Shipment:
- Shipment ID: {record.get('id')}
- Tracking: {record.get('tracking_number')}
- Origin Country: {record.get('origin_country')}
- Destination Country: {record.get('destination_country')}
- Customs Value: ${record.get('customs_value')}
- Status: {record.get('status')}
- Carrier: {record.get('carrier')}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_microcredit_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format microcredit service records"""
        if table_name == "credit_applications":
            return f"""
Credit Application:
- Application ID: {record.get('id')}
- Customer ID: {record.get('customer_id')}
- Amount Requested: ${record.get('amount_requested')}
- Amount Approved: ${record.get('amount_approved')}
- Status: {record.get('status')}
- Interest Rate: {record.get('interest_rate')}%
- Term: {record.get('term_months')} months
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_pickup_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format pickup service records"""
        if table_name == "pickups":
            return f"""
Pickup Request:
- Pickup ID: {record.get('id')}
- Customer ID: {record.get('customer_id')}
- Address: {record.get('pickup_address')}
- Scheduled Date: {record.get('scheduled_date')}
- Time Window: {record.get('time_window')}
- Status: {record.get('status')}
- Items Count: {record.get('items_count')}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_reverse_logistics_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Format reverse logistics records"""
        if table_name == "returns":
            return f"""
Return Request:
- Return ID: {record.get('id')}
- Order ID: {record.get('order_id')}
- Customer ID: {record.get('customer_id')}
- Reason: {record.get('reason')}
- Status: {record.get('status')}
- Refund Amount: ${record.get('refund_amount')}
- Items: {record.get('items')}
- Created: {record.get('created_at')}
"""
        return self._format_generic_record(table_name, record)
    
    def _format_generic_record(self, table_name: str, record: Dict[str, Any]) -> str:
        """Generic record formatting"""
        content = f"Table: {table_name}\n"
        for key, value in record.items():
            if value is not None:
                content += f"- {key.replace('_', ' ').title()}: {value}\n"
        return content
    
    def _get_document_type(self, table_name: str) -> str:
        """Determine document type from table name"""
        type_mapping = {
            "users": "user",
            "customers": "customer",
            "orders": "order",
            "shipments": "shipment",
            "franchises": "franchise",
            "pickups": "pickup",
            "returns": "return",
            "credit_applications": "credit",
            "international_shipments": "international_shipment",
            "international_mailboxes": "mailbox",
            "metrics": "analytics"
        }
        return type_mapping.get(table_name, table_name)
    
    async def ingest_all_microservices(self, db: AsyncSession):
        """Ingest data from all microservices"""
        
        # Define ingestion tasks for each microservice
        tasks = [
            ("auth", "users"),
            ("customer", "customers"),
            ("order", "orders"),
            ("carrier", "shipments"),
            ("carrier", "international_mailboxes"),
            ("analytics", "metrics"),
            ("franchise", "franchises"),
            ("international", "international_shipments"),
            ("microcredit", "credit_applications"),
            ("pickup", "pickups"),
            ("reverse_logistics", "returns"),
        ]
        
        results = []
        for source, table in tasks:
            try:
                job = await self.ingest_from_microservice(db, source, table)
                results.append({"source": source, "table": table, "status": job.status})
            except Exception as e:
                logger.error(f"Failed to ingest {source}.{table}: {e}")
                results.append({"source": source, "table": table, "status": "failed", "error": str(e)})
        
        return results