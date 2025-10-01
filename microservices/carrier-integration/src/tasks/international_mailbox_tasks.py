"""
Async tasks for international mailbox operations
Handles Pasarex and Aeropost operations asynchronously
"""

from celery import Task, group
from ..celery_app import app
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from ..database import SessionLocal
from ..models import (
    InternationalMailbox, PackagePrealert, PackageConsolidation,
    CustomsDeclaration, ImportCostCalculation, CarrierType
)
from ..services.international_mailbox_service import InternationalMailboxService

logger = structlog.get_logger()


class MailboxTask(Task):
    """Base task for mailbox operations"""
    _db = None
    _service = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    @property
    def service(self):
        if self._service is None:
            self._service = InternationalMailboxService(self.db)
        return self._service
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._db is not None:
            self._db.close()
            self._db = None


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.assign_mailbox_async',
    max_retries=3
)
def assign_mailbox_async(self, customer_id: str, carrier: str, 
                         customer_data: Dict[str, Any], callback_url: Optional[str] = None):
    """
    Asynchronously assign a virtual mailbox to a customer
    
    Args:
        customer_id: Customer identifier
        carrier: PASAREX or AEROPOST
        customer_data: Customer information
        callback_url: Optional webhook URL for result
    
    Returns:
        Mailbox assignment details
    """
    try:
        logger.info("Assigning mailbox asynchronously",
                   task_id=self.request.id,
                   customer_id=customer_id,
                   carrier=carrier)
        
        # Run async operation
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.service.assign_mailbox(customer_id, carrier, customer_data)
            )
            
            logger.info("Mailbox assigned successfully",
                       task_id=self.request.id,
                       mailbox_id=result.get("mailbox_id"))
            
            # Send callback if provided
            if callback_url:
                send_mailbox_callback.delay(callback_url, result)
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Failed to assign mailbox",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.sync_prealerts',
    max_retries=3
)
def sync_prealerts(self, customer_id: str):
    """
    Synchronize pre-alerts for all customer mailboxes
    
    This task runs periodically to check for new packages
    
    Args:
        customer_id: Customer identifier
    
    Returns:
        Sync results
    """
    try:
        logger.info("Syncing pre-alerts",
                   task_id=self.request.id,
                   customer_id=customer_id)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            prealerts = loop.run_until_complete(
                self.service.get_prealerts(customer_id)
            )
            
            # Check for new packages and send notifications
            new_packages = [p for p in prealerts if p.get("status") == "new"]
            
            if new_packages:
                notify_new_packages.delay(customer_id, new_packages)
            
            return {
                "customer_id": customer_id,
                "total_prealerts": len(prealerts),
                "new_packages": len(new_packages),
                "synced_at": datetime.now().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Failed to sync pre-alerts",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=300)


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.consolidate_packages_async',
    max_retries=3
)
def consolidate_packages_async(self, customer_id: str, package_ids: List[str], 
                              carrier: str, callback_url: Optional[str] = None):
    """
    Asynchronously consolidate multiple packages
    
    Args:
        customer_id: Customer identifier
        package_ids: List of package IDs to consolidate
        carrier: PASAREX or AEROPOST
        callback_url: Optional webhook URL
    
    Returns:
        Consolidation details
    """
    try:
        logger.info("Processing package consolidation",
                   task_id=self.request.id,
                   customer_id=customer_id,
                   packages_count=len(package_ids))
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.service.consolidate_packages(customer_id, package_ids, carrier)
            )
            
            # Calculate estimated savings
            calculate_consolidation_savings.delay(
                result["consolidation_id"],
                package_ids,
                carrier
            )
            
            # Send callback if provided
            if callback_url:
                send_mailbox_callback.delay(callback_url, result)
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Failed to consolidate packages",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.calculate_import_costs_async',
    max_retries=2
)
def calculate_import_costs_async(self, package_data: Dict[str, Any], carrier: str):
    """
    Asynchronously calculate import costs
    
    Args:
        package_data: Package information
        carrier: PASAREX or AEROPOST
    
    Returns:
        Import cost breakdown
    """
    try:
        logger.info("Calculating import costs",
                   task_id=self.request.id,
                   value=package_data.get("value"),
                   weight=package_data.get("weight_lb"))
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            costs = loop.run_until_complete(
                self.service.calculate_import_costs(package_data, carrier)
            )
            
            # Check if costs exceed threshold
            if costs["total_cost"] > 5000000:  # > 5M COP
                send_high_value_alert.delay(package_data, costs)
            
            return costs
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Failed to calculate import costs",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.declare_content_async',
    max_retries=3
)
def declare_content_async(self, package_id: str, declaration: Dict[str, Any], 
                         carrier: str):
    """
    Asynchronously declare package content for customs
    
    Args:
        package_id: Package identifier
        declaration: Content declaration
        carrier: PASAREX or AEROPOST
    
    Returns:
        Declaration confirmation
    """
    try:
        logger.info("Declaring package content",
                   task_id=self.request.id,
                   package_id=package_id)
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.service.declare_content(package_id, declaration, carrier)
            )
            
            # Validate declaration for restricted items
            validate_customs_declaration.delay(
                result["declaration_id"],
                declaration["items"]
            )
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Failed to declare content",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    name='src.tasks.international_mailbox_tasks.notify_new_packages'
)
def notify_new_packages(customer_id: str, packages: List[Dict[str, Any]]):
    """
    Send notification about new packages in mailbox
    
    Args:
        customer_id: Customer identifier
        packages: List of new packages
    """
    logger.info("Notifying customer about new packages",
               customer_id=customer_id,
               packages_count=len(packages))
    
    # TODO: Implement actual notification
    # - Send email with package details
    # - Send SMS if enabled
    # - Push notification to mobile app
    # - Update customer dashboard
    
    notification = {
        "event": "new_packages_arrived",
        "customer_id": customer_id,
        "packages": packages,
        "timestamp": datetime.now().isoformat()
    }
    
    return notification


@app.task(
    name='src.tasks.international_mailbox_tasks.calculate_consolidation_savings'
)
def calculate_consolidation_savings(consolidation_id: str, package_ids: List[str], 
                                   carrier: str):
    """
    Calculate savings from package consolidation
    
    Args:
        consolidation_id: Consolidation identifier
        package_ids: List of consolidated packages
        carrier: Carrier name
    """
    try:
        # This would calculate the difference between:
        # - Individual shipping costs for each package
        # - Consolidated shipping cost
        
        estimated_savings = len(package_ids) * 15.00  # USD per package (example)
        
        logger.info("Consolidation savings calculated",
                   consolidation_id=consolidation_id,
                   savings_usd=estimated_savings)
        
        return {
            "consolidation_id": consolidation_id,
            "packages_consolidated": len(package_ids),
            "estimated_savings_usd": estimated_savings
        }
        
    except Exception as e:
        logger.error("Failed to calculate savings", error=str(e))
        return None


@app.task(
    name='src.tasks.international_mailbox_tasks.send_high_value_alert'
)
def send_high_value_alert(package_data: Dict[str, Any], costs: Dict[str, Any]):
    """
    Send alert for high-value packages
    
    Args:
        package_data: Package information
        costs: Import cost breakdown
    """
    logger.warning("High value package detected",
                  value=package_data.get("value"),
                  total_cost_cop=costs["total_cost"])
    
    # TODO: Implement alerting
    # - Notify customer about high import costs
    # - Suggest insurance options
    # - Provide cost breakdown details
    
    alert = {
        "event": "high_value_package",
        "package_value_usd": package_data.get("value"),
        "total_cost_cop": costs["total_cost"],
        "breakdown": costs["breakdown"],
        "timestamp": datetime.now().isoformat()
    }
    
    return alert


@app.task(
    name='src.tasks.international_mailbox_tasks.validate_customs_declaration'
)
def validate_customs_declaration(declaration_id: str, items: List[Dict[str, Any]]):
    """
    Validate customs declaration for restricted items
    
    Args:
        declaration_id: Declaration identifier
        items: List of declared items
    """
    restricted_keywords = [
        "weapon", "drug", "explosive", "ammunition",
        "tobacco", "alcohol", "medicine", "pharmaceutical"
    ]
    
    flagged_items = []
    
    for item in items:
        description = item.get("description", "").lower()
        for keyword in restricted_keywords:
            if keyword in description:
                flagged_items.append({
                    "item": item["description"],
                    "reason": f"Contains restricted keyword: {keyword}"
                })
    
    if flagged_items:
        logger.warning("Customs declaration flagged",
                      declaration_id=declaration_id,
                      flagged_items=flagged_items)
        
        # TODO: Create review task for operations team
        
    return {
        "declaration_id": declaration_id,
        "validated": len(flagged_items) == 0,
        "flagged_items": flagged_items
    }


@app.task(
    name='src.tasks.international_mailbox_tasks.send_mailbox_callback'
)
def send_mailbox_callback(callback_url: str, data: Dict[str, Any]):
    """
    Send callback to webhook URL
    
    Args:
        callback_url: Webhook URL
        data: Data to send
    """
    import httpx
    
    try:
        with httpx.Client() as client:
            response = client.post(
                callback_url,
                json=data,
                timeout=10.0
            )
            response.raise_for_status()
            
        logger.info("Mailbox callback sent successfully", url=callback_url)
        
    except Exception as e:
        logger.error("Failed to send mailbox callback",
                    url=callback_url,
                    error=str(e))


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.sync_all_customer_mailboxes'
)
def sync_all_customer_mailboxes(self):
    """
    Sync all active customer mailboxes
    
    This is a periodic task that runs every hour
    """
    try:
        logger.info("Starting mailbox sync for all customers",
                   task_id=self.request.id)
        
        # Get all active mailboxes
        mailboxes = self.db.query(InternationalMailbox).filter(
            InternationalMailbox.status == "active"
        ).all()
        
        # Group by customer
        customers = {}
        for mailbox in mailboxes:
            if mailbox.customer_id not in customers:
                customers[mailbox.customer_id] = []
            customers[mailbox.customer_id].append(mailbox)
        
        # Sync each customer's mailboxes
        for customer_id in customers:
            sync_prealerts.delay(customer_id)
        
        logger.info("Mailbox sync scheduled for all customers",
                   task_id=self.request.id,
                   customer_count=len(customers))
        
        return {
            "customers_synced": len(customers),
            "mailboxes_processed": len(mailboxes)
        }
        
    except Exception as e:
        logger.error("Failed to sync customer mailboxes",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    base=MailboxTask,
    name='src.tasks.international_mailbox_tasks.process_arrived_packages'
)
def process_arrived_packages(self):
    """
    Process packages that have arrived at origin warehouse
    
    This task runs daily to check for packages ready to ship
    """
    try:
        logger.info("Processing arrived packages",
                   task_id=self.request.id)
        
        # Get packages that arrived but not yet shipped
        arrived_packages = self.db.query(PackagePrealert).filter(
            PackagePrealert.status == "arrived",
            PackagePrealert.arrived_at.isnot(None)
        ).all()
        
        # Group by customer for consolidation opportunities
        by_customer = {}
        for package in arrived_packages:
            mailbox = self.db.query(InternationalMailbox).filter(
                InternationalMailbox.mailbox_id == package.mailbox_id
            ).first()
            
            if mailbox:
                customer_id = mailbox.customer_id
                if customer_id not in by_customer:
                    by_customer[customer_id] = []
                by_customer[customer_id].append(package)
        
        # Check consolidation opportunities
        consolidation_suggestions = []
        for customer_id, packages in by_customer.items():
            if len(packages) >= 2:
                consolidation_suggestions.append({
                    "customer_id": customer_id,
                    "packages": len(packages),
                    "potential_savings": len(packages) * 15.00  # USD
                })
                
                # Send consolidation suggestion
                suggest_consolidation.delay(customer_id, 
                                          [p.tracking_number for p in packages])
        
        return {
            "arrived_packages": len(arrived_packages),
            "consolidation_suggestions": len(consolidation_suggestions),
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to process arrived packages",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    name='src.tasks.international_mailbox_tasks.suggest_consolidation'
)
def suggest_consolidation(customer_id: str, package_ids: List[str]):
    """
    Send consolidation suggestion to customer
    
    Args:
        customer_id: Customer identifier
        package_ids: List of packages that can be consolidated
    """
    logger.info("Sending consolidation suggestion",
               customer_id=customer_id,
               packages_count=len(package_ids))
    
    # TODO: Implement notification
    # - Send email with consolidation benefits
    # - Show in customer dashboard
    # - Calculate exact savings
    
    return {
        "customer_id": customer_id,
        "packages_suggested": len(package_ids),
        "estimated_savings_usd": len(package_ids) * 15.00
    }