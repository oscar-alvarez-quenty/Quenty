import pytest
from datetime import datetime, timedelta
from src.domain.entities.pickup import (
    PickupRequest, PickupRoute, PickupStatus, PickupType, PickupTimeSlot
)
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId


class TestPickupRequest:
    def test_create_pickup_request(self):
        """Test creating a pickup request"""
        pickup_id = "pickup_001"
        guide_id = GuideId("guide_001")
        customer_id = CustomerId("customer_001")
        pickup_type = PickupType.DIRECT_PICKUP
        pickup_address = "Calle 123, Bogotá"
        contact_name = "Juan Pérez"
        contact_phone = "3001234567"
        
        pickup_request = PickupRequest(
            pickup_id=pickup_id,
            guide_id=guide_id,
            customer_id=customer_id,
            pickup_type=pickup_type,
            pickup_address=pickup_address,
            contact_name=contact_name,
            contact_phone=contact_phone
        )
        
        assert pickup_request.pickup_id == pickup_id
        assert pickup_request.guide_id == guide_id
        assert pickup_request.customer_id == customer_id
        assert pickup_request.pickup_type == pickup_type
        assert pickup_request.pickup_address == pickup_address
        assert pickup_request.contact_name == contact_name
        assert pickup_request.contact_phone == contact_phone
        assert pickup_request.status == PickupStatus.SCHEDULED
        assert pickup_request.priority == "normal"
        assert pickup_request.estimated_packages == 1
        assert pickup_request.max_attempts == 3

    def test_schedule_pickup_success(self):
        """Test successful pickup scheduling"""
        pickup_request = self._create_sample_pickup_request()
        scheduled_date = datetime.now() + timedelta(days=1)
        time_slot = PickupTimeSlot(
            start_time=scheduled_date.replace(hour=9, minute=0),
            end_time=scheduled_date.replace(hour=11, minute=0),
            is_available=True,
            max_pickups=10,
            current_pickups=0
        )
        operator_id = "op_001"
        
        pickup_request.schedule_pickup(scheduled_date, time_slot, operator_id)
        
        assert pickup_request.status == PickupStatus.CONFIRMED
        assert pickup_request.scheduled_date == scheduled_date
        assert pickup_request.time_slot == time_slot
        assert pickup_request.assigned_operator_id == operator_id
        assert time_slot.current_pickups == 1

    def test_schedule_pickup_unavailable_slot(self):
        """Test scheduling pickup with unavailable time slot"""
        pickup_request = self._create_sample_pickup_request()
        scheduled_date = datetime.now() + timedelta(days=1)
        time_slot = PickupTimeSlot(
            start_time=scheduled_date.replace(hour=9, minute=0),
            end_time=scheduled_date.replace(hour=11, minute=0),
            is_available=False
        )
        
        with pytest.raises(ValueError, match="Slot de tiempo no disponible"):
            pickup_request.schedule_pickup(scheduled_date, time_slot, "op_001")

    def test_schedule_pickup_full_slot(self):
        """Test scheduling pickup with full time slot"""
        pickup_request = self._create_sample_pickup_request()
        scheduled_date = datetime.now() + timedelta(days=1)
        time_slot = PickupTimeSlot(
            start_time=scheduled_date.replace(hour=9, minute=0),
            end_time=scheduled_date.replace(hour=11, minute=0),
            is_available=True,
            max_pickups=2,
            current_pickups=2
        )
        
        with pytest.raises(ValueError, match="Slot de tiempo completo"):
            pickup_request.schedule_pickup(scheduled_date, time_slot, "op_001")

    def test_assign_to_point(self):
        """Test assigning pickup to logistic point"""
        pickup_request = PickupRequest(
            pickup_id="pickup_001",
            guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            pickup_type=PickupType.POINT_DELIVERY,
            pickup_address="Calle 123",
            contact_name="Juan",
            contact_phone="3001234567"
        )
        
        point_id = "point_001"
        pickup_request.assign_to_point(point_id)
        
        assert pickup_request.assigned_point_id == point_id
        assert pickup_request.status == PickupStatus.CONFIRMED

    def test_assign_to_point_wrong_type(self):
        """Test assigning direct pickup to point (should fail)"""
        pickup_request = self._create_sample_pickup_request()
        
        with pytest.raises(ValueError, match="Solo las entregas en punto pueden ser asignadas"):
            pickup_request.assign_to_point("point_001")

    def test_complete_pickup_success(self):
        """Test successful pickup completion"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.IN_PROGRESS
        
        operator_id = "op_001"
        completion_notes = "Pickup completed successfully"
        evidence_urls = ["http://example.com/evidence1.jpg"]
        
        attempt = pickup_request.complete_pickup(operator_id, completion_notes, evidence_urls)
        
        assert pickup_request.status == PickupStatus.COMPLETED
        assert pickup_request.completed_at is not None
        assert attempt.status == "success"
        assert attempt.attempted_by == operator_id
        assert attempt.notes == completion_notes
        assert attempt.evidence_urls == evidence_urls

    def test_fail_pickup(self):
        """Test pickup failure"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.IN_PROGRESS
        
        operator_id = "op_001"
        failure_reason = "customer_not_available"
        notes = "Customer was not at the location"
        
        attempt = pickup_request.fail_pickup(operator_id, failure_reason, notes)
        
        assert pickup_request.status == PickupStatus.RESCHEDULED
        assert attempt.status == "failed"
        assert attempt.failure_reason == failure_reason
        assert len(pickup_request.pickup_attempts) == 1

    def test_fail_pickup_max_attempts(self):
        """Test pickup failure with max attempts reached"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.IN_PROGRESS
        pickup_request.max_attempts = 1
        
        # First attempt - should fail and mark as rescheduled
        pickup_request.fail_pickup("op_001", "customer_not_available", "Not available")
        
        # Simulate another attempt
        pickup_request.status = PickupStatus.IN_PROGRESS
        pickup_request.fail_pickup("op_001", "customer_not_available", "Still not available")
        
        assert pickup_request.status == PickupStatus.FAILED
        assert len(pickup_request.pickup_attempts) == 2

    def test_reschedule_pickup(self):
        """Test pickup rescheduling"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.CONFIRMED
        
        old_time_slot = PickupTimeSlot(
            start_time=datetime.now().replace(hour=9),
            end_time=datetime.now().replace(hour=11),
            current_pickups=1
        )
        pickup_request.time_slot = old_time_slot
        
        new_date = datetime.now() + timedelta(days=2)
        new_time_slot = PickupTimeSlot(
            start_time=new_date.replace(hour=14),
            end_time=new_date.replace(hour=16)
        )
        reschedule_reason = "Customer requested different time"
        
        pickup_request.reschedule_pickup(new_date, new_time_slot, reschedule_reason)
        
        assert pickup_request.status == PickupStatus.RESCHEDULED
        assert pickup_request.scheduled_date == new_date
        assert pickup_request.time_slot == new_time_slot
        assert old_time_slot.current_pickups == 0
        assert new_time_slot.current_pickups == 1

    def test_cancel_pickup(self):
        """Test pickup cancellation"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.CONFIRMED
        
        time_slot = PickupTimeSlot(
            start_time=datetime.now().replace(hour=9),
            end_time=datetime.now().replace(hour=11),
            current_pickups=1
        )
        pickup_request.time_slot = time_slot
        
        cancellation_reason = "Customer cancelled order"
        pickup_request.cancel_pickup(cancellation_reason, "customer")
        
        assert pickup_request.status == PickupStatus.CANCELLED
        assert time_slot.current_pickups == 0

    def test_set_priority(self):
        """Test setting pickup priority"""
        pickup_request = self._create_sample_pickup_request()
        
        pickup_request.set_priority("high")
        assert pickup_request.priority == "high"
        
        with pytest.raises(ValueError, match="Prioridad debe ser una de"):
            pickup_request.set_priority("invalid")

    def test_set_package_details(self):
        """Test setting package details"""
        pickup_request = self._create_sample_pickup_request()
        
        estimated_packages = 5
        total_weight_kg = 10.5
        
        pickup_request.set_package_details(estimated_packages, total_weight_kg)
        
        assert pickup_request.estimated_packages == estimated_packages
        assert pickup_request.total_weight_kg == total_weight_kg

    def test_set_package_details_invalid(self):
        """Test setting invalid package details"""
        pickup_request = self._create_sample_pickup_request()
        
        with pytest.raises(ValueError, match="Número de paquetes debe ser mayor a 0"):
            pickup_request.set_package_details(0, 10.0)
        
        with pytest.raises(ValueError, match="Peso total debe ser mayor a 0"):
            pickup_request.set_package_details(5, 0)

    def test_can_be_rescheduled(self):
        """Test checking if pickup can be rescheduled"""
        pickup_request = self._create_sample_pickup_request()
        
        # Should be reschedulable when not completed/cancelled and under max attempts
        assert pickup_request.can_be_rescheduled() == True
        
        # Completed pickup should not be reschedulable
        pickup_request.status = PickupStatus.COMPLETED
        assert pickup_request.can_be_rescheduled() == False
        
        # Reset status and add max attempts
        pickup_request.status = PickupStatus.CONFIRMED
        pickup_request.pickup_attempts = ["attempt1", "attempt2", "attempt3"]
        pickup_request.max_attempts = 3
        assert pickup_request.can_be_rescheduled() == False

    def test_is_overdue(self):
        """Test checking if pickup is overdue"""
        pickup_request = self._create_sample_pickup_request()
        
        # No scheduled date
        assert pickup_request.is_overdue() == False
        
        # Scheduled in future
        pickup_request.scheduled_date = datetime.now() + timedelta(hours=1)
        assert pickup_request.is_overdue() == False
        
        # Scheduled in past (more than 2 hours ago)
        pickup_request.scheduled_date = datetime.now() - timedelta(hours=3)
        assert pickup_request.is_overdue() == True

    def test_get_pickup_summary(self):
        """Test getting pickup summary"""
        pickup_request = self._create_sample_pickup_request()
        pickup_request.set_priority("high")
        pickup_request.add_special_instructions("Handle with care")
        
        summary = pickup_request.get_pickup_summary()
        
        assert summary["pickup_id"] == pickup_request.pickup_id
        assert summary["guide_id"] == pickup_request.guide_id.value
        assert summary["status"] == pickup_request.status.value
        assert summary["priority"] == "high"
        assert summary["special_instructions"] == "Handle with care"
        assert "is_overdue" in summary
        assert "can_be_rescheduled" in summary

    def _create_sample_pickup_request(self):
        """Helper method to create a sample pickup request"""
        return PickupRequest(
            pickup_id="pickup_001",
            guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            pickup_type=PickupType.DIRECT_PICKUP,
            pickup_address="Calle 123, Bogotá",
            contact_name="Juan Pérez",
            contact_phone="3001234567"
        )


class TestPickupRoute:
    def test_create_pickup_route(self):
        """Test creating a pickup route"""
        route_id = "route_001"
        operator_id = "op_001"
        scheduled_date = datetime.now() + timedelta(days=1)
        
        pickup_route = PickupRoute(route_id, operator_id, scheduled_date)
        
        assert pickup_route.route_id == route_id
        assert pickup_route.operator_id == operator_id
        assert pickup_route.scheduled_date == scheduled_date
        assert pickup_route.status == "planned"
        assert pickup_route.pickup_requests == []

    def test_add_pickup_to_route(self):
        """Test adding pickup to route"""
        pickup_route = self._create_sample_route()
        pickup_request = self._create_sample_pickup_request()
        pickup_request.assigned_operator_id = pickup_route.operator_id
        pickup_request.scheduled_date = pickup_route.scheduled_date
        
        pickup_route.add_pickup(pickup_request)
        
        assert len(pickup_route.pickup_requests) == 1
        assert pickup_route.pickup_requests[0] == pickup_request

    def test_add_pickup_wrong_operator(self):
        """Test adding pickup with wrong operator"""
        pickup_route = self._create_sample_route()
        pickup_request = self._create_sample_pickup_request()
        pickup_request.assigned_operator_id = "different_operator"
        
        with pytest.raises(ValueError, match="La recolección debe estar asignada al mismo operador"):
            pickup_route.add_pickup(pickup_request)

    def test_add_pickup_wrong_date(self):
        """Test adding pickup with wrong date"""
        pickup_route = self._create_sample_route()
        pickup_request = self._create_sample_pickup_request()
        pickup_request.assigned_operator_id = pickup_route.operator_id
        pickup_request.scheduled_date = pickup_route.scheduled_date + timedelta(days=1)
        
        with pytest.raises(ValueError, match="La recolección debe ser del mismo día"):
            pickup_route.add_pickup(pickup_request)

    def test_optimize_route(self):
        """Test route optimization"""
        pickup_route = self._create_sample_route()
        
        # Create pickups with different priorities
        pickup1 = self._create_sample_pickup_request()
        pickup1.pickup_id = "pickup_1"
        pickup1.priority = "urgent"
        pickup1.pickup_address = "Address A"
        pickup1.assigned_operator_id = pickup_route.operator_id
        pickup1.scheduled_date = pickup_route.scheduled_date
        
        pickup2 = self._create_sample_pickup_request()
        pickup2.pickup_id = "pickup_2"
        pickup2.priority = "normal"
        pickup2.pickup_address = "Address B"
        pickup2.assigned_operator_id = pickup_route.operator_id
        pickup2.scheduled_date = pickup_route.scheduled_date
        
        pickup_route.add_pickup(pickup2)  # Add normal priority first
        pickup_route.add_pickup(pickup1)  # Add urgent priority second
        
        pickup_route.optimize_route()
        
        # Urgent should come first after optimization
        assert pickup_route.pickup_requests[0].priority == "urgent"
        assert pickup_route.pickup_requests[1].priority == "normal"

    def test_start_route(self):
        """Test starting a route"""
        pickup_route = self._create_sample_route()
        
        pickup_route.start_route()
        
        assert pickup_route.status == "in_progress"
        assert pickup_route.started_at is not None

    def test_start_route_wrong_status(self):
        """Test starting route with wrong status"""
        pickup_route = self._create_sample_route()
        pickup_route.status = "completed"
        
        with pytest.raises(ValueError, match="Solo se pueden iniciar rutas planificadas"):
            pickup_route.start_route()

    def test_complete_route(self):
        """Test completing a route"""
        pickup_route = self._create_sample_route()
        pickup_route.status = "in_progress"
        
        # Add completed pickup
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.COMPLETED
        pickup_request.assigned_operator_id = pickup_route.operator_id
        pickup_request.scheduled_date = pickup_route.scheduled_date
        pickup_route.add_pickup(pickup_request)
        
        pickup_route.complete_route()
        
        assert pickup_route.status == "completed"
        assert pickup_route.completed_at is not None

    def test_complete_route_with_pending_pickups(self):
        """Test completing route with pending pickups"""
        pickup_route = self._create_sample_route()
        pickup_route.status = "in_progress"
        
        # Add pending pickup
        pickup_request = self._create_sample_pickup_request()
        pickup_request.status = PickupStatus.CONFIRMED
        pickup_request.assigned_operator_id = pickup_route.operator_id
        pickup_request.scheduled_date = pickup_route.scheduled_date
        pickup_route.add_pickup(pickup_request)
        
        with pytest.raises(ValueError, match="Hay recolecciones pendientes en la ruta"):
            pickup_route.complete_route()

    def test_get_route_summary(self):
        """Test getting route summary"""
        pickup_route = self._create_sample_route()
        
        # Add completed and failed pickups
        completed_pickup = self._create_sample_pickup_request()
        completed_pickup.pickup_id = "completed"
        completed_pickup.status = PickupStatus.COMPLETED
        completed_pickup.assigned_operator_id = pickup_route.operator_id
        completed_pickup.scheduled_date = pickup_route.scheduled_date
        
        failed_pickup = self._create_sample_pickup_request()
        failed_pickup.pickup_id = "failed"
        failed_pickup.status = PickupStatus.FAILED
        failed_pickup.assigned_operator_id = pickup_route.operator_id
        failed_pickup.scheduled_date = pickup_route.scheduled_date
        
        pickup_route.add_pickup(completed_pickup)
        pickup_route.add_pickup(failed_pickup)
        
        summary = pickup_route.get_route_summary()
        
        assert summary["route_id"] == pickup_route.route_id
        assert summary["operator_id"] == pickup_route.operator_id
        assert summary["total_pickups"] == 2
        assert summary["completed_pickups"] == 1
        assert summary["failed_pickups"] == 1
        assert summary["success_rate"] == 0.5

    def _create_sample_route(self):
        """Helper method to create a sample pickup route"""
        return PickupRoute(
            route_id="route_001",
            operator_id="op_001",
            scheduled_date=datetime.now() + timedelta(days=1)
        )

    def _create_sample_pickup_request(self):
        """Helper method to create a sample pickup request"""
        return PickupRequest(
            pickup_id="pickup_001",
            guide_id=GuideId("guide_001"),
            customer_id=CustomerId("customer_001"),
            pickup_type=PickupType.DIRECT_PICKUP,
            pickup_address="Calle 123, Bogotá",
            contact_name="Juan Pérez",
            contact_phone="3001234567"
        )