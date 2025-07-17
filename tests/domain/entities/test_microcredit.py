import pytest
from datetime import datetime, timedelta
from src.domain.entities.microcredit import (
    MicrocreditApplication, Microcredit, MicrocreditPayment, CreditProfile,
    ApplicationStatus, MicrocreditStatus, PaymentStatus
)
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class TestMicrocreditApplication:
    def test_create_microcredit_application(self):
        """Test creating a microcredit application"""
        application_id = "app_001"
        customer_id = CustomerId("customer_001")
        requested_amount = Money(1000.0, "COP")
        purpose = "business_expansion"
        monthly_income = Money(2000.0, "COP")
        employment_type = "self_employed"
        
        application = MicrocreditApplication(
            application_id=application_id,
            customer_id=customer_id,
            requested_amount=requested_amount,
            purpose=purpose,
            monthly_income=monthly_income,
            employment_type=employment_type
        )
        
        assert application.application_id == application_id
        assert application.customer_id == customer_id
        assert application.requested_amount == requested_amount
        assert application.purpose == purpose
        assert application.monthly_income == monthly_income
        assert application.employment_type == employment_type
        assert application.status == ApplicationStatus.SUBMITTED
        assert application.credit_score is None
        assert application.risk_assessment is None

    def test_set_credit_score(self):
        """Test setting credit score"""
        application = self._create_sample_application()
        credit_score = 750
        risk_assessment = "low_risk"
        
        application.set_credit_score(credit_score, risk_assessment)
        
        assert application.credit_score == credit_score
        assert application.risk_assessment == risk_assessment

    def test_approve_application(self):
        """Test approving application"""
        application = self._create_sample_application()
        approved_amount = Money(800.0, "COP")
        interest_rate = 15.5
        term_months = 12
        approved_by = "underwriter_001"
        
        application.approve_application(approved_amount, interest_rate, term_months, approved_by)
        
        assert application.status == ApplicationStatus.APPROVED
        assert application.approved_amount == approved_amount
        assert application.interest_rate == interest_rate
        assert application.term_months == term_months
        assert application.approved_by == approved_by
        assert application.approved_at is not None

    def test_reject_application(self):
        """Test rejecting application"""
        application = self._create_sample_application()
        rejection_reasons = ["Insufficient income", "High debt ratio"]
        rejected_by = "underwriter_001"
        
        application.reject_application(rejection_reasons, rejected_by)
        
        assert application.status == ApplicationStatus.REJECTED
        assert application.rejection_reasons == rejection_reasons
        assert application.rejected_by == rejected_by
        assert application.rejected_at is not None

    def test_calculate_debt_to_income_ratio(self):
        """Test calculating debt-to-income ratio"""
        application = self._create_sample_application()
        current_debt = Money(500.0, "COP")
        
        ratio = application.calculate_debt_to_income_ratio(current_debt)
        
        # ratio = current_debt / monthly_income = 500 / 2000 = 0.25
        assert ratio == 0.25

    def test_is_eligible_for_approval(self):
        """Test checking eligibility for approval"""
        application = self._create_sample_application()
        
        # Without credit score, not eligible
        assert application.is_eligible_for_approval() == False
        
        # With good credit score, eligible
        application.set_credit_score(750, "low_risk")
        assert application.is_eligible_for_approval() == True
        
        # With poor credit score, not eligible
        application.set_credit_score(550, "high_risk")
        assert application.is_eligible_for_approval() == False

    def test_get_application_summary(self):
        """Test getting application summary"""
        application = self._create_sample_application()
        application.set_credit_score(750, "low_risk")
        
        summary = application.get_application_summary()
        
        assert summary["application_id"] == application.application_id
        assert summary["customer_id"] == application.customer_id.value
        assert summary["requested_amount"] == application.requested_amount.amount
        assert summary["status"] == application.status.value
        assert summary["credit_score"] == 750
        assert summary["risk_assessment"] == "low_risk"

    def _create_sample_application(self):
        """Helper method to create a sample microcredit application"""
        return MicrocreditApplication(
            application_id="app_001",
            customer_id=CustomerId("customer_001"),
            requested_amount=Money(1000.0, "COP"),
            purpose="business_expansion",
            monthly_income=Money(2000.0, "COP"),
            employment_type="self_employed"
        )


class TestMicrocredit:
    def test_create_microcredit(self):
        """Test creating a microcredit"""
        microcredit_id = "micro_001"
        customer_id = CustomerId("customer_001")
        principal_amount = Money(1000.0, "COP")
        interest_rate = 15.5
        term_months = 12
        
        microcredit = Microcredit(
            microcredit_id=microcredit_id,
            customer_id=customer_id,
            principal_amount=principal_amount,
            interest_rate=interest_rate,
            term_months=term_months
        )
        
        assert microcredit.microcredit_id == microcredit_id
        assert microcredit.customer_id == customer_id
        assert microcredit.principal_amount == principal_amount
        assert microcredit.interest_rate == interest_rate
        assert microcredit.term_months == term_months
        assert microcredit.status == MicrocreditStatus.APPROVED
        assert microcredit.outstanding_balance == principal_amount
        assert microcredit.total_paid == Money(0.0, "COP")
        assert microcredit.disbursement_date is None

    def test_disburse_microcredit(self):
        """Test disbursing microcredit"""
        microcredit = self._create_sample_microcredit()
        disbursement_method = "bank_transfer"
        reference_number = "TXN123456"
        
        microcredit.disburse_microcredit(disbursement_method, reference_number)
        
        assert microcredit.status == MicrocreditStatus.ACTIVE
        assert microcredit.disbursement_date is not None
        assert microcredit.disbursement_method == disbursement_method
        assert microcredit.disbursement_reference == reference_number

    def test_process_payment(self):
        """Test processing payment"""
        microcredit = self._create_sample_microcredit()
        microcredit.disburse_microcredit("bank_transfer", "TXN123")
        
        payment_amount = Money(200.0, "COP")
        payment_method = "bank_transfer"
        
        payment = microcredit.process_payment(payment_amount, payment_method)
        
        assert payment.microcredit_id == microcredit.microcredit_id
        assert payment.amount == payment_amount
        assert payment.payment_method == payment_method
        assert payment.status == PaymentStatus.COMPLETED
        assert len(microcredit.payments) == 1
        assert microcredit.total_paid == payment_amount
        assert microcredit.outstanding_balance == Money(800.0, "COP")

    def test_calculate_monthly_payment(self):
        """Test calculating monthly payment"""
        microcredit = self._create_sample_microcredit()
        
        monthly_payment = microcredit.calculate_monthly_payment()
        
        # Should calculate based on principal, interest rate, and term
        assert isinstance(monthly_payment, Money)
        assert monthly_payment.amount > 0

    def test_calculate_total_interest(self):
        """Test calculating total interest"""
        microcredit = self._create_sample_microcredit()
        
        total_interest = microcredit.calculate_total_interest()
        
        assert isinstance(total_interest, Money)
        assert total_interest.amount > 0

    def test_is_overdue(self):
        """Test checking if microcredit is overdue"""
        microcredit = self._create_sample_microcredit()
        
        # Not overdue when not disbursed
        assert microcredit.is_overdue() == False
        
        # Disburse and set old disbursement date
        microcredit.disburse_microcredit("bank_transfer", "TXN123")
        microcredit.disbursement_date = datetime.now() - timedelta(days=45)
        
        # Should be overdue if no payments made after 30 days
        assert microcredit.is_overdue() == True

    def test_calculate_late_fees(self):
        """Test calculating late fees"""
        microcredit = self._create_sample_microcredit()
        microcredit.disburse_microcredit("bank_transfer", "TXN123")
        microcredit.disbursement_date = datetime.now() - timedelta(days=45)
        
        late_fees = microcredit.calculate_late_fees()
        
        assert isinstance(late_fees, Money)
        # Should have late fees when overdue
        assert late_fees.amount > 0

    def test_get_payment_schedule(self):
        """Test getting payment schedule"""
        microcredit = self._create_sample_microcredit()
        microcredit.disburse_microcredit("bank_transfer", "TXN123")
        
        schedule = microcredit.get_payment_schedule()
        
        assert len(schedule) == microcredit.term_months
        for payment in schedule:
            assert "due_date" in payment
            assert "amount" in payment
            assert "principal" in payment
            assert "interest" in payment

    def test_mark_as_paid_off(self):
        """Test marking microcredit as paid off"""
        microcredit = self._create_sample_microcredit()
        microcredit.disburse_microcredit("bank_transfer", "TXN123")
        
        # Pay full amount
        microcredit.process_payment(Money(1000.0, "COP"), "bank_transfer")
        
        microcredit.mark_as_paid_off()
        
        assert microcredit.status == MicrocreditStatus.PAID_OFF
        assert microcredit.paid_off_at is not None

    def _create_sample_microcredit(self):
        """Helper method to create a sample microcredit"""
        return Microcredit(
            microcredit_id="micro_001",
            customer_id=CustomerId("customer_001"),
            principal_amount=Money(1000.0, "COP"),
            interest_rate=15.5,
            term_months=12
        )


class TestMicrocreditPayment:
    def test_create_microcredit_payment(self):
        """Test creating a microcredit payment"""
        payment_id = "pay_001"
        microcredit_id = "micro_001"
        amount = Money(200.0, "COP")
        payment_method = "bank_transfer"
        
        payment = MicrocreditPayment(
            payment_id=payment_id,
            microcredit_id=microcredit_id,
            amount=amount,
            payment_method=payment_method
        )
        
        assert payment.payment_id == payment_id
        assert payment.microcredit_id == microcredit_id
        assert payment.amount == amount
        assert payment.payment_method == payment_method
        assert payment.status == PaymentStatus.PENDING
        assert payment.is_late_payment == False
        assert payment.days_late == 0

    def test_confirm_payment(self):
        """Test confirming payment"""
        payment = self._create_sample_payment()
        transaction_reference = "TXN123456"
        
        payment.confirm_payment(transaction_reference)
        
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.transaction_reference == transaction_reference
        assert payment.confirmed_at is not None

    def test_fail_payment(self):
        """Test failing payment"""
        payment = self._create_sample_payment()
        failure_reason = "Insufficient funds"
        
        payment.fail_payment(failure_reason)
        
        assert payment.status == PaymentStatus.FAILED
        assert payment.failure_reason == failure_reason
        assert payment.failed_at is not None

    def test_mark_as_late(self):
        """Test marking payment as late"""
        payment = self._create_sample_payment()
        days_late = 5
        
        payment.mark_as_late(days_late)
        
        assert payment.is_late_payment == True
        assert payment.days_late == days_late

    def test_calculate_late_fee(self):
        """Test calculating late fee"""
        payment = self._create_sample_payment()
        payment.mark_as_late(10)
        
        late_fee = payment.calculate_late_fee()
        
        assert isinstance(late_fee, Money)
        assert late_fee.amount > 0

    def test_is_partial_payment(self):
        """Test checking if payment is partial"""
        payment = self._create_sample_payment()
        
        # Full monthly payment
        expected_amount = Money(200.0, "COP")
        assert payment.is_partial_payment(expected_amount) == False
        
        # Partial payment
        expected_amount = Money(300.0, "COP")
        assert payment.is_partial_payment(expected_amount) == True

    def _create_sample_payment(self):
        """Helper method to create a sample payment"""
        return MicrocreditPayment(
            payment_id="pay_001",
            microcredit_id="micro_001",
            amount=Money(200.0, "COP"),
            payment_method="bank_transfer"
        )


class TestCreditProfile:
    def test_create_credit_profile(self):
        """Test creating a credit profile"""
        customer_id = CustomerId("customer_001")
        credit_score = 750
        credit_limit = Money(5000.0, "COP")
        payment_history_score = 85.5
        
        profile = CreditProfile(
            customer_id=customer_id,
            credit_score=credit_score,
            credit_limit=credit_limit,
            payment_history_score=payment_history_score
        )
        
        assert profile.customer_id == customer_id
        assert profile.credit_score == credit_score
        assert profile.credit_limit == credit_limit
        assert profile.payment_history_score == payment_history_score
        assert profile.current_debt == Money(0.0, "COP")
        assert profile.risk_category == "low"

    def test_update_credit_score(self):
        """Test updating credit score"""
        profile = self._create_sample_profile()
        new_score = 800
        
        profile.update_credit_score(new_score)
        
        assert profile.credit_score == new_score
        assert profile.last_updated_score is not None

    def test_update_credit_limit(self):
        """Test updating credit limit"""
        profile = self._create_sample_profile()
        new_limit = Money(10000.0, "COP")
        reason = "Income increase"
        approved_by = "manager_001"
        
        profile.update_credit_limit(new_limit, reason, approved_by)
        
        assert profile.credit_limit == new_limit
        assert len(profile.credit_limit_history) == 1
        history_entry = profile.credit_limit_history[0]
        assert history_entry["new_limit"] == new_limit.amount
        assert history_entry["reason"] == reason
        assert history_entry["approved_by"] == approved_by

    def test_add_debt(self):
        """Test adding debt"""
        profile = self._create_sample_profile()
        debt_amount = Money(1000.0, "COP")
        
        profile.add_debt(debt_amount)
        
        assert profile.current_debt == debt_amount

    def test_reduce_debt(self):
        """Test reducing debt"""
        profile = self._create_sample_profile()
        profile.add_debt(Money(1000.0, "COP"))
        
        payment = Money(300.0, "COP")
        profile.reduce_debt(payment)
        
        assert profile.current_debt == Money(700.0, "COP")

    def test_calculate_available_credit(self):
        """Test calculating available credit"""
        profile = self._create_sample_profile()
        profile.add_debt(Money(2000.0, "COP"))
        
        available = profile.calculate_available_credit()
        
        # credit_limit (5000) - current_debt (2000) = 3000
        assert available == Money(3000.0, "COP")

    def test_calculate_utilization_ratio(self):
        """Test calculating credit utilization ratio"""
        profile = self._create_sample_profile()
        profile.add_debt(Money(2500.0, "COP"))
        
        ratio = profile.calculate_utilization_ratio()
        
        # current_debt (2500) / credit_limit (5000) = 0.5
        assert ratio == 0.5

    def test_is_eligible_for_new_credit(self):
        """Test checking eligibility for new credit"""
        profile = self._create_sample_profile()
        requested_amount = Money(1000.0, "COP")
        
        # With low utilization, should be eligible
        is_eligible, reason = profile.is_eligible_for_new_credit(requested_amount)
        assert is_eligible == True
        assert reason is None
        
        # Add debt to exceed limit
        profile.add_debt(Money(4500.0, "COP"))
        is_eligible, reason = profile.is_eligible_for_new_credit(requested_amount)
        assert is_eligible == False
        assert "Límite de crédito insuficiente" in reason

    def test_determine_risk_category(self):
        """Test determining risk category"""
        profile = self._create_sample_profile()
        
        # Good credit score = low risk
        profile.credit_score = 800
        category = profile.determine_risk_category()
        assert category == "low"
        
        # Poor credit score = high risk
        profile.credit_score = 500
        category = profile.determine_risk_category()
        assert category == "high"

    def test_get_credit_summary(self):
        """Test getting credit summary"""
        profile = self._create_sample_profile()
        profile.add_debt(Money(1000.0, "COP"))
        
        summary = profile.get_credit_summary()
        
        assert summary["customer_id"] == profile.customer_id.value
        assert summary["credit_score"] == profile.credit_score
        assert summary["credit_limit"] == profile.credit_limit.amount
        assert summary["current_debt"] == profile.current_debt.amount
        assert summary["available_credit"] == 4000.0  # 5000 - 1000
        assert summary["utilization_ratio"] == 0.2  # 1000 / 5000

    def _create_sample_profile(self):
        """Helper method to create a sample credit profile"""
        return CreditProfile(
            customer_id=CustomerId("customer_001"),
            credit_score=750,
            credit_limit=Money(5000.0, "COP"),
            payment_history_score=85.5
        )