import pytest
from datetime import datetime, timedelta
from src.domain.entities.reverse_logistics import (
    ReturnRequest, ReturnItem, InspectionReport, LogisticsCenter, ReturnPolicy,
    ReturnStatus, ReturnReason, InspectionResult, RefundMethod
)
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class TestReturnRequest:
    def test_create_return_request(self):
        """Test creating a return request"""
        return_id = "return_001"
        original_guide_id = GuideId("guide_001")
        customer_id = CustomerId("customer_001")
        return_reason = ReturnReason.DEFECTIVE_PRODUCT
        customer_comments = "Product arrived damaged"
        contact_info = {"phone": "123456789", "email": "customer@test.com"}
        
        return_request = ReturnRequest(
            return_id=return_id,
            original_guide_id=original_guide_id,
            customer_id=customer_id,
            return_reason=return_reason,
            customer_comments=customer_comments,
            contact_info=contact_info
        )
        
        assert return_request.return_id == return_id
        assert return_request.original_guide_id == original_guide_id
        assert return_request.customer_id == customer_id
        assert return_request.return_reason == return_reason
        assert return_request.customer_comments == customer_comments
        assert return_request.contact_info == contact_info
        assert return_request.status == ReturnStatus.PENDING
        assert return_request.return_items == []
        assert return_request.expected_return_value == Money(0.0, "COP")

    def test_add_item(self):
        """Test adding item to return request"""
        return_request = self._create_sample_return_request()
        item = ReturnItem(
            item_id="item_001",
            product_id="prod_001",
            product_name="Test Product",
            quantity_returned=1,
            unit_price=Money(100.0, "COP"),
            return_reason=ReturnReason.DEFECTIVE_PRODUCT,
            condition_description="Damaged packaging"
        )
        
        return_request.add_item(item)
        
        assert len(return_request.return_items) == 1
        assert return_request.return_items[0] == item
        assert return_request.expected_return_value == Money(100.0, "COP")

    def test_approve_return(self):
        """Test approving return request"""
        return_request = self._create_sample_return_request()
        approved_by = "manager_001"
        pickup_date = datetime.now() + timedelta(days=2)
        
        return_request.approve_return(approved_by, pickup_date)
        
        assert return_request.status == ReturnStatus.APPROVED
        assert return_request.approved_by == approved_by
        assert return_request.approved_at is not None
        assert return_request.pickup_date == pickup_date

    def test_reject_return(self):
        """Test rejecting return request"""
        return_request = self._create_sample_return_request()
        rejection_reason = "Outside return window"
        rejected_by = "manager_001"
        
        return_request.reject_return(rejection_reason, rejected_by)
        
        assert return_request.status == ReturnStatus.REJECTED
        assert return_request.rejection_reason == rejection_reason
        assert return_request.rejected_by == rejected_by
        assert return_request.rejected_at is not None

    def test_receive_return(self):
        """Test receiving return at logistics center"""
        return_request = self._create_sample_return_request()
        return_request.approve_return("manager_001", datetime.now() + timedelta(days=1))
        
        center_id = "center_001"
        received_by = "operator_001"
        packages_count = 2
        initial_condition = "good"
        
        return_request.receive_return(center_id, received_by, packages_count, initial_condition)
        
        assert return_request.status == ReturnStatus.RECEIVED
        assert return_request.received_at_center == center_id
        assert return_request.received_by == received_by
        assert return_request.packages_received == packages_count
        assert return_request.received_at is not None

    def test_complete_inspection(self):
        """Test completing inspection"""
        return_request = self._create_sample_return_request()
        return_request.status = ReturnStatus.RECEIVED
        
        inspection_report = InspectionReport(
            inspection_id="insp_001",
            inspector_id="inspector_001",
            overall_result=InspectionResult.APPROVED,
            refund_amount=Money(80.0, "COP")
        )
        
        return_request.complete_inspection(inspection_report)
        
        assert return_request.status == ReturnStatus.INSPECTED
        assert return_request.inspection_report == inspection_report
        assert return_request.inspected_at is not None

    def test_process_refund(self):
        """Test processing refund"""
        return_request = self._create_sample_return_request()
        return_request.status = ReturnStatus.INSPECTED
        
        transaction_reference = "TXN123456"
        refund_method = RefundMethod.ORIGINAL_PAYMENT
        processed_by = "finance_001"
        
        return_request.process_refund(transaction_reference, refund_method, processed_by)
        
        assert return_request.status == ReturnStatus.REFUNDED
        assert return_request.refund_transaction_reference == transaction_reference
        assert return_request.refund_method == refund_method
        assert return_request.refund_processed_by == processed_by
        assert return_request.refund_processed_at is not None

    def test_is_within_deadline(self):
        """Test checking if return is within deadline"""
        return_request = self._create_sample_return_request()
        
        # Recent return request should be within deadline
        assert return_request.is_within_deadline() == True
        
        # Old return request should be outside deadline
        return_request.created_at = datetime.now() - timedelta(days=35)
        assert return_request.is_within_deadline() == False

    def test_calculate_refund_amount(self):
        """Test calculating refund amount"""
        return_request = self._create_sample_return_request()
        
        # Add items
        item1 = ReturnItem(
            item_id="item_001",
            product_id="prod_001",
            product_name="Product 1",
            quantity_returned=1,
            unit_price=Money(100.0, "COP"),
            return_reason=ReturnReason.DEFECTIVE_PRODUCT,
            condition_description="Good condition"
        )
        item2 = ReturnItem(
            item_id="item_002",
            product_id="prod_002",
            product_name="Product 2",
            quantity_returned=2,
            unit_price=Money(50.0, "COP"),
            return_reason=ReturnReason.NOT_AS_DESCRIBED,
            condition_description="Good condition"
        )
        
        return_request.add_item(item1)
        return_request.add_item(item2)
        
        refund_amount = return_request.calculate_refund_amount()
        
        # 1 * 100 + 2 * 50 = 200
        assert refund_amount == Money(200.0, "COP")

    def test_get_return_summary(self):
        """Test getting return summary"""
        return_request = self._create_sample_return_request()
        
        summary = return_request.get_return_summary()
        
        assert summary["return_id"] == return_request.return_id
        assert summary["original_guide_id"] == return_request.original_guide_id.value
        assert summary["customer_id"] == return_request.customer_id.value
        assert summary["status"] == return_request.status.value
        assert summary["return_reason"] == return_request.return_reason.value
        assert summary["items_count"] == len(return_request.return_items)

    def _create_sample_return_request(self):
        """Helper method to create a sample return request"""
        return ReturnRequest(
            return_id="return_001",
            original_guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            return_reason=ReturnReason.DEFECTIVE_PRODUCT,
            customer_comments="Product arrived damaged",
            contact_info={"phone": "123456789", "email": "customer@test.com"}
        )


class TestReturnItem:
    def test_create_return_item(self):
        """Test creating a return item"""
        item_id = "item_001"
        product_id = "prod_001"
        product_name = "Test Product"
        quantity_returned = 2
        unit_price = Money(50.0, "COP")
        return_reason = ReturnReason.DEFECTIVE_PRODUCT
        condition_description = "Damaged packaging"
        
        item = ReturnItem(
            item_id=item_id,
            product_id=product_id,
            product_name=product_name,
            quantity_returned=quantity_returned,
            unit_price=unit_price,
            return_reason=return_reason,
            condition_description=condition_description
        )
        
        assert item.item_id == item_id
        assert item.product_id == product_id
        assert item.product_name == product_name
        assert item.quantity_returned == quantity_returned
        assert item.unit_price == unit_price
        assert item.return_reason == return_reason
        assert item.condition_description == condition_description
        assert item.photos_urls == []
        assert item.disposition_action is None

    def test_add_photo(self):
        """Test adding photo to return item"""
        item = self._create_sample_item()
        photo_url = "http://example.com/photo1.jpg"
        
        item.add_photo(photo_url)
        
        assert len(item.photos_urls) == 1
        assert item.photos_urls[0] == photo_url

    def test_set_disposition_action(self):
        """Test setting disposition action"""
        item = self._create_sample_item()
        action = "restock"
        
        item.set_disposition_action(action)
        
        assert item.disposition_action == action

    def test_calculate_total_value(self):
        """Test calculating total value of item"""
        item = self._create_sample_item()
        
        total_value = item.calculate_total_value()
        
        # quantity (2) * unit_price (50) = 100
        assert total_value == Money(100.0, "COP")

    def test_update_condition_description(self):
        """Test updating condition description"""
        item = self._create_sample_item()
        new_description = "Minor scratches observed"
        
        item.update_condition_description(new_description)
        
        assert item.condition_description == new_description

    def test_is_eligible_for_resale(self):
        """Test checking if item is eligible for resale"""
        item = self._create_sample_item()
        
        # Default condition should not be eligible
        assert item.is_eligible_for_resale() == False
        
        # Good condition should be eligible
        item.condition_description = "excellent condition"
        assert item.is_eligible_for_resale() == True

    def _create_sample_item(self):
        """Helper method to create a sample return item"""
        return ReturnItem(
            item_id="item_001",
            product_id="prod_001",
            product_name="Test Product",
            quantity_returned=2,
            unit_price=Money(50.0, "COP"),
            return_reason=ReturnReason.DEFECTIVE_PRODUCT,
            condition_description="Damaged packaging"
        )


class TestInspectionReport:
    def test_create_inspection_report(self):
        """Test creating an inspection report"""
        inspection_id = "insp_001"
        inspector_id = "inspector_001"
        overall_result = InspectionResult.APPROVED
        refund_amount = Money(150.0, "COP")
        
        report = InspectionReport(
            inspection_id=inspection_id,
            inspector_id=inspector_id,
            overall_result=overall_result,
            refund_amount=refund_amount
        )
        
        assert report.inspection_id == inspection_id
        assert report.inspector_id == inspector_id
        assert report.overall_result == overall_result
        assert report.refund_amount == refund_amount
        assert report.items_inspected == []
        assert report.notes is None

    def test_add_item_inspection(self):
        """Test adding item inspection"""
        report = self._create_sample_report()
        item_inspection = {
            "item_id": "item_001",
            "result": "approved",
            "condition": "good",
            "disposition": "restock",
            "refund_eligible": True
        }
        
        report.add_item_inspection(item_inspection)
        
        assert len(report.items_inspected) == 1
        assert report.items_inspected[0] == item_inspection

    def test_set_notes(self):
        """Test setting inspection notes"""
        report = self._create_sample_report()
        notes = "Items received in good condition overall"
        
        report.set_notes(notes)
        
        assert report.notes == notes

    def test_calculate_approval_rate(self):
        """Test calculating approval rate"""
        report = self._create_sample_report()
        
        # Add mixed inspection results
        report.add_item_inspection({"item_id": "item_001", "result": "approved"})
        report.add_item_inspection({"item_id": "item_002", "result": "approved"})
        report.add_item_inspection({"item_id": "item_003", "result": "rejected"})
        
        approval_rate = report.calculate_approval_rate()
        
        # 2 approved out of 3 total = 66.67%
        assert abs(approval_rate - 66.67) < 0.01

    def test_get_approved_items_count(self):
        """Test getting approved items count"""
        report = self._create_sample_report()
        
        report.add_item_inspection({"item_id": "item_001", "result": "approved"})
        report.add_item_inspection({"item_id": "item_002", "result": "rejected"})
        report.add_item_inspection({"item_id": "item_003", "result": "approved"})
        
        approved_count = report.get_approved_items_count()
        
        assert approved_count == 2

    def test_get_rejected_items_count(self):
        """Test getting rejected items count"""
        report = self._create_sample_report()
        
        report.add_item_inspection({"item_id": "item_001", "result": "approved"})
        report.add_item_inspection({"item_id": "item_002", "result": "rejected"})
        report.add_item_inspection({"item_id": "item_003", "result": "rejected"})
        
        rejected_count = report.get_rejected_items_count()
        
        assert rejected_count == 2

    def _create_sample_report(self):
        """Helper method to create a sample inspection report"""
        return InspectionReport(
            inspection_id="insp_001",
            inspector_id="inspector_001",
            overall_result=InspectionResult.APPROVED,
            refund_amount=Money(150.0, "COP")
        )


class TestLogisticsCenter:
    def test_create_logistics_center(self):
        """Test creating a logistics center"""
        center_id = "center_001"
        name = "Main Distribution Center"
        address = "Calle 123, Bogotá"
        capacity = 1000
        
        center = LogisticsCenter(
            center_id=center_id,
            name=name,
            address=address,
            capacity=capacity
        )
        
        assert center.center_id == center_id
        assert center.name == name
        assert center.address == address
        assert center.capacity == capacity
        assert center.current_inventory == {}
        assert center.processing_queue == []
        assert center.is_active == True

    def test_add_to_inventory(self):
        """Test adding items to inventory"""
        center = self._create_sample_center()
        product_id = "prod_001"
        quantity = 10
        
        center.add_to_inventory(product_id, quantity)
        
        assert center.current_inventory[product_id] == quantity

    def test_remove_from_inventory(self):
        """Test removing items from inventory"""
        center = self._create_sample_center()
        product_id = "prod_001"
        center.add_to_inventory(product_id, 10)
        
        success = center.remove_from_inventory(product_id, 5)
        
        assert success == True
        assert center.current_inventory[product_id] == 5

    def test_remove_from_inventory_insufficient_stock(self):
        """Test removing more items than available"""
        center = self._create_sample_center()
        product_id = "prod_001"
        center.add_to_inventory(product_id, 3)
        
        success = center.remove_from_inventory(product_id, 5)
        
        assert success == False
        assert center.current_inventory[product_id] == 3

    def test_add_to_processing_queue(self):
        """Test adding return to processing queue"""
        center = self._create_sample_center()
        return_id = "return_001"
        
        center.add_to_processing_queue(return_id)
        
        assert len(center.processing_queue) == 1
        assert center.processing_queue[0] == return_id

    def test_remove_from_processing_queue(self):
        """Test removing return from processing queue"""
        center = self._create_sample_center()
        return_id = "return_001"
        center.add_to_processing_queue(return_id)
        
        center.remove_from_processing_queue(return_id)
        
        assert len(center.processing_queue) == 0

    def test_get_capacity_utilization(self):
        """Test getting capacity utilization"""
        center = self._create_sample_center()
        
        center.add_to_inventory("prod_001", 200)
        center.add_to_inventory("prod_002", 300)
        
        utilization = center.get_capacity_utilization()
        
        # (200 + 300) / 1000 = 0.5 = 50%
        assert utilization == 50.0

    def test_is_at_capacity(self):
        """Test checking if center is at capacity"""
        center = self._create_sample_center()
        
        assert center.is_at_capacity() == False
        
        center.add_to_inventory("prod_001", 1000)
        assert center.is_at_capacity() == True

    def test_activate_deactivate_center(self):
        """Test activating and deactivating center"""
        center = self._create_sample_center()
        
        center.deactivate_center()
        assert center.is_active == False
        
        center.activate_center()
        assert center.is_active == True

    def test_get_center_summary(self):
        """Test getting center summary"""
        center = self._create_sample_center()
        center.add_to_inventory("prod_001", 100)
        center.add_to_processing_queue("return_001")
        
        summary = center.get_center_summary()
        
        assert summary["center_id"] == center.center_id
        assert summary["name"] == center.name
        assert summary["capacity"] == center.capacity
        assert summary["current_inventory_count"] == 100
        assert summary["processing_queue_size"] == 1
        assert summary["capacity_utilization"] == 10.0
        assert summary["is_active"] == center.is_active

    def _create_sample_center(self):
        """Helper method to create a sample logistics center"""
        return LogisticsCenter(
            center_id="center_001",
            name="Main Distribution Center",
            address="Calle 123, Bogotá",
            capacity=1000
        )


class TestReturnPolicy:
    def test_create_return_policy(self):
        """Test creating a return policy"""
        policy_id = "policy_001"
        name = "Standard Return Policy"
        description = "30-day return policy for most products"
        return_window_days = 30
        eligible_reasons = [ReturnReason.DEFECTIVE_PRODUCT, ReturnReason.NOT_AS_DESCRIBED]
        excluded_categories = ["electronics", "perishables"]
        
        policy = ReturnPolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            return_window_days=return_window_days,
            eligible_reasons=eligible_reasons,
            excluded_categories=excluded_categories
        )
        
        assert policy.policy_id == policy_id
        assert policy.name == name
        assert policy.description == description
        assert policy.return_window_days == return_window_days
        assert policy.eligible_reasons == eligible_reasons
        assert policy.excluded_categories == excluded_categories
        assert policy.is_active == True
        assert policy.restocking_fee_percentage == 0.0

    def test_is_return_eligible(self):
        """Test checking if return is eligible"""
        policy = self._create_sample_policy()
        
        # Eligible return - within window and valid reason
        order_date = datetime.now() - timedelta(days=15)
        delivery_date = datetime.now() - timedelta(days=10)
        product_categories = ["clothing"]
        return_reason = ReturnReason.DEFECTIVE_PRODUCT
        
        is_eligible, reason = policy.is_return_eligible(
            order_date, delivery_date, product_categories, return_reason
        )
        
        assert is_eligible == True
        assert reason is None

    def test_is_return_eligible_outside_window(self):
        """Test return outside time window"""
        policy = self._create_sample_policy()
        
        # Outside window
        order_date = datetime.now() - timedelta(days=50)
        delivery_date = datetime.now() - timedelta(days=45)
        product_categories = ["clothing"]
        return_reason = ReturnReason.DEFECTIVE_PRODUCT
        
        is_eligible, reason = policy.is_return_eligible(
            order_date, delivery_date, product_categories, return_reason
        )
        
        assert is_eligible == False
        assert "outside the return window" in reason

    def test_is_return_eligible_excluded_category(self):
        """Test return for excluded category"""
        policy = self._create_sample_policy()
        
        # Excluded category
        order_date = datetime.now() - timedelta(days=15)
        delivery_date = datetime.now() - timedelta(days=10)
        product_categories = ["electronics"]
        return_reason = ReturnReason.DEFECTIVE_PRODUCT
        
        is_eligible, reason = policy.is_return_eligible(
            order_date, delivery_date, product_categories, return_reason
        )
        
        assert is_eligible == False
        assert "category is excluded" in reason

    def test_is_return_eligible_invalid_reason(self):
        """Test return with invalid reason"""
        policy = self._create_sample_policy()
        
        # Invalid reason
        order_date = datetime.now() - timedelta(days=15)
        delivery_date = datetime.now() - timedelta(days=10)
        product_categories = ["clothing"]
        return_reason = ReturnReason.CHANGED_MIND
        
        is_eligible, reason = policy.is_return_eligible(
            order_date, delivery_date, product_categories, return_reason
        )
        
        assert is_eligible == False
        assert "reason is not eligible" in reason

    def test_calculate_restocking_fee(self):
        """Test calculating restocking fee"""
        policy = self._create_sample_policy()
        policy.restocking_fee_percentage = 10.0
        
        item_value = Money(100.0, "COP")
        fee = policy.calculate_restocking_fee(item_value)
        
        assert fee == Money(10.0, "COP")

    def test_update_return_window(self):
        """Test updating return window"""
        policy = self._create_sample_policy()
        new_window = 45
        
        policy.update_return_window(new_window)
        
        assert policy.return_window_days == new_window

    def test_add_eligible_reason(self):
        """Test adding eligible reason"""
        policy = self._create_sample_policy()
        new_reason = ReturnReason.CHANGED_MIND
        
        policy.add_eligible_reason(new_reason)
        
        assert new_reason in policy.eligible_reasons

    def test_remove_eligible_reason(self):
        """Test removing eligible reason"""
        policy = self._create_sample_policy()
        reason_to_remove = ReturnReason.DEFECTIVE_PRODUCT
        
        policy.remove_eligible_reason(reason_to_remove)
        
        assert reason_to_remove not in policy.eligible_reasons

    def test_add_excluded_category(self):
        """Test adding excluded category"""
        policy = self._create_sample_policy()
        new_category = "books"
        
        policy.add_excluded_category(new_category)
        
        assert new_category in policy.excluded_categories

    def test_remove_excluded_category(self):
        """Test removing excluded category"""
        policy = self._create_sample_policy()
        category_to_remove = "electronics"
        
        policy.remove_excluded_category(category_to_remove)
        
        assert category_to_remove not in policy.excluded_categories

    def test_activate_deactivate_policy(self):
        """Test activating and deactivating policy"""
        policy = self._create_sample_policy()
        
        policy.deactivate_policy()
        assert policy.is_active == False
        
        policy.activate_policy()
        assert policy.is_active == True

    def _create_sample_policy(self):
        """Helper method to create a sample return policy"""
        return ReturnPolicy(
            policy_id="policy_001",
            name="Standard Return Policy",
            description="30-day return policy for most products",
            return_window_days=30,
            eligible_reasons=[ReturnReason.DEFECTIVE_PRODUCT, ReturnReason.NOT_AS_DESCRIBED],
            excluded_categories=["electronics", "perishables"]
        )