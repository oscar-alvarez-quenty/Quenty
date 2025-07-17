from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.domain.entities.microcredit import (
    MicrocreditApplication, Microcredit, CreditProfile, 
    PaymentSchedule, MicrocreditPayment
)
from src.infrastructure.models.microcredit_models import (
    MicrocreditApplicationModel, MicrocreditModel, CreditProfileModel,
    PaymentScheduleModel, MicrocreditPaymentModel
)
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class MicrocreditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_application(self, application: MicrocreditApplication) -> MicrocreditApplication:
        """Crear nueva solicitud de microcrédito"""
        app_model = MicrocreditApplicationModel(
            application_id=application.application_id,
            customer_id=application.customer_id.value,
            requested_amount_amount=application.requested_amount.amount,
            requested_amount_currency=application.requested_amount.currency,
            purpose=application.purpose,
            status=application.status.value,
            created_at=application.created_at,
            updated_at=application.updated_at,
            submitted_at=application.submitted_at,
            reviewed_at=application.reviewed_at,
            approved_at=application.approved_at,
            rejected_at=application.rejected_at,
            credit_score=application.credit_score,
            risk_assessment=application.risk_assessment,
            rejection_reasons=",".join(application.rejection_reasons) if application.rejection_reasons else None,
            monthly_income_amount=application.monthly_income.amount if application.monthly_income else None,
            monthly_income_currency=application.monthly_income.currency if application.monthly_income else None,
            employment_type=application.employment_type,
            business_description=application.business_description,
            collateral_description=application.collateral_description,
            guarantor_info=str(application.guarantor_info) if application.guarantor_info else None
        )
        
        self.session.add(app_model)
        await self.session.commit()
        await self.session.refresh(app_model)
        
        return application

    async def get_application(self, application_id: str) -> Optional[MicrocreditApplication]:
        """Obtener solicitud por ID"""
        stmt = select(MicrocreditApplicationModel).where(
            MicrocreditApplicationModel.application_id == application_id
        )
        result = await self.session.execute(stmt)
        app_model = result.scalar_one_or_none()
        
        if app_model:
            return self._application_model_to_entity(app_model)
        return None

    async def update_application(self, application: MicrocreditApplication) -> MicrocreditApplication:
        """Actualizar solicitud de microcrédito"""
        stmt = (
            update(MicrocreditApplicationModel)
            .where(MicrocreditApplicationModel.application_id == application.application_id)
            .values(
                status=application.status.value,
                updated_at=application.updated_at,
                reviewed_at=application.reviewed_at,
                approved_at=application.approved_at,
                rejected_at=application.rejected_at,
                credit_score=application.credit_score,
                risk_assessment=application.risk_assessment,
                rejection_reasons=",".join(application.rejection_reasons) if application.rejection_reasons else None,
                monthly_income_amount=application.monthly_income.amount if application.monthly_income else None,
                monthly_income_currency=application.monthly_income.currency if application.monthly_income else None,
                employment_type=application.employment_type,
                business_description=application.business_description,
                collateral_description=application.collateral_description,
                guarantor_info=str(application.guarantor_info) if application.guarantor_info else None
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return application

    async def get_applications_by_customer(self, customer_id: CustomerId) -> List[MicrocreditApplication]:
        """Obtener solicitudes por cliente"""
        stmt = (
            select(MicrocreditApplicationModel)
            .where(MicrocreditApplicationModel.customer_id == customer_id.value)
            .order_by(MicrocreditApplicationModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        app_models = result.scalars().all()
        
        return [self._application_model_to_entity(model) for model in app_models]

    async def get_applications_by_status(self, status: str) -> List[MicrocreditApplication]:
        """Obtener solicitudes por estado"""
        stmt = (
            select(MicrocreditApplicationModel)
            .where(MicrocreditApplicationModel.status == status)
            .order_by(MicrocreditApplicationModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        app_models = result.scalars().all()
        
        return [self._application_model_to_entity(model) for model in app_models]

    # Microcredit methods
    async def create_microcredit(self, microcredit: Microcredit) -> Microcredit:
        """Crear nuevo microcrédito"""
        microcredit_model = MicrocreditModel(
            microcredit_id=microcredit.microcredit_id,
            customer_id=microcredit.customer_id.value,
            principal_amount_amount=microcredit.principal_amount.amount,
            principal_amount_currency=microcredit.principal_amount.currency,
            interest_rate=microcredit.interest_rate,
            term_months=microcredit.term_months,
            status=microcredit.status.value,
            created_at=microcredit.created_at,
            updated_at=microcredit.updated_at,
            disbursement_date=microcredit.disbursement_date,
            first_payment_date=microcredit.first_payment_date,
            final_payment_date=microcredit.final_payment_date,
            total_amount_amount=microcredit.total_amount.amount,
            total_amount_currency=microcredit.total_amount.currency,
            outstanding_balance_amount=microcredit.outstanding_balance.amount,
            outstanding_balance_currency=microcredit.outstanding_balance.currency,
            total_paid_amount=microcredit.total_paid.amount,
            total_paid_currency=microcredit.total_paid.currency,
            late_fees_amount=microcredit.late_fees.amount,
            late_fees_currency=microcredit.late_fees.currency,
            default_date=microcredit.default_date,
            fully_paid_date=microcredit.fully_paid_date
        )
        
        self.session.add(microcredit_model)
        await self.session.commit()
        await self.session.refresh(microcredit_model)
        
        return microcredit

    async def get_microcredit(self, microcredit_id: str) -> Optional[Microcredit]:
        """Obtener microcrédito por ID"""
        stmt = (
            select(MicrocreditModel)
            .options(
                selectinload(MicrocreditModel.payments),
                selectinload(MicrocreditModel.payment_schedule)
            )
            .where(MicrocreditModel.microcredit_id == microcredit_id)
        )
        
        result = await self.session.execute(stmt)
        microcredit_model = result.scalar_one_or_none()
        
        if microcredit_model:
            return self._microcredit_model_to_entity(microcredit_model)
        return None

    async def update_microcredit(self, microcredit: Microcredit) -> Microcredit:
        """Actualizar microcrédito"""
        stmt = (
            update(MicrocreditModel)
            .where(MicrocreditModel.microcredit_id == microcredit.microcredit_id)
            .values(
                status=microcredit.status.value,
                updated_at=microcredit.updated_at,
                disbursement_date=microcredit.disbursement_date,
                first_payment_date=microcredit.first_payment_date,
                final_payment_date=microcredit.final_payment_date,
                outstanding_balance_amount=microcredit.outstanding_balance.amount,
                outstanding_balance_currency=microcredit.outstanding_balance.currency,
                total_paid_amount=microcredit.total_paid.amount,
                total_paid_currency=microcredit.total_paid.currency,
                late_fees_amount=microcredit.late_fees.amount,
                late_fees_currency=microcredit.late_fees.currency,
                default_date=microcredit.default_date,
                fully_paid_date=microcredit.fully_paid_date
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return microcredit

    async def get_microcredits_by_customer(self, customer_id: CustomerId) -> List[Microcredit]:
        """Obtener microcréditos por cliente"""
        stmt = (
            select(MicrocreditModel)
            .options(selectinload(MicrocreditModel.payments))
            .where(MicrocreditModel.customer_id == customer_id.value)
            .order_by(MicrocreditModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        microcredit_models = result.scalars().all()
        
        return [self._microcredit_model_to_entity(model) for model in microcredit_models]

    async def get_microcredits_by_status(self, status: str) -> List[Microcredit]:
        """Obtener microcréditos por estado"""
        stmt = (
            select(MicrocreditModel)
            .where(MicrocreditModel.status == status)
            .order_by(MicrocreditModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        microcredit_models = result.scalars().all()
        
        return [self._microcredit_model_to_entity(model) for model in microcredit_models]

    async def get_overdue_microcredits(self) -> List[Microcredit]:
        """Obtener microcréditos vencidos"""
        now = datetime.now()
        
        stmt = (
            select(MicrocreditModel)
            .where(
                and_(
                    MicrocreditModel.status.in_(['active', 'late']),
                    MicrocreditModel.final_payment_date < now,
                    MicrocreditModel.outstanding_balance_amount > 0
                )
            )
        )
        
        result = await self.session.execute(stmt)
        microcredit_models = result.scalars().all()
        
        return [self._microcredit_model_to_entity(model) for model in microcredit_models]

    # Payment methods
    async def create_payment(self, payment: MicrocreditPayment) -> MicrocreditPayment:
        """Crear nuevo pago de microcrédito"""
        payment_model = MicrocreditPaymentModel(
            payment_id=payment.payment_id,
            microcredit_id=payment.microcredit_id,
            amount_amount=payment.amount.amount,
            amount_currency=payment.amount.currency,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            status=payment.status.value,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            reference_number=payment.reference_number,
            principal_portion=payment.principal_portion,
            interest_portion=payment.interest_portion,
            late_fee_portion=payment.late_fee_portion,
            is_late_payment=payment.is_late_payment,
            days_late=payment.days_late,
            payment_notes=payment.payment_notes
        )
        
        self.session.add(payment_model)
        await self.session.commit()
        await self.session.refresh(payment_model)
        
        return payment

    async def get_payments_by_microcredit(self, microcredit_id: str) -> List[MicrocreditPayment]:
        """Obtener pagos por microcrédito"""
        stmt = (
            select(MicrocreditPaymentModel)
            .where(MicrocreditPaymentModel.microcredit_id == microcredit_id)
            .order_by(MicrocreditPaymentModel.payment_date)
        )
        
        result = await self.session.execute(stmt)
        payment_models = result.scalars().all()
        
        return [self._payment_model_to_entity(model) for model in payment_models]

    # Credit Profile methods
    async def create_credit_profile(self, profile: CreditProfile) -> CreditProfile:
        """Crear perfil crediticio"""
        profile_model = CreditProfileModel(
            customer_id=profile.customer_id.value,
            credit_score=profile.credit_score,
            credit_limit_amount=profile.credit_limit.amount,
            credit_limit_currency=profile.credit_limit.currency,
            current_debt_amount=profile.current_debt.amount,
            current_debt_currency=profile.current_debt.currency,
            payment_history_score=profile.payment_history_score,
            default_history_count=profile.default_history_count,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_updated_score=profile.last_updated_score,
            first_credit_date=profile.first_credit_date,
            risk_category=profile.risk_category
        )
        
        self.session.add(profile_model)
        await self.session.commit()
        await self.session.refresh(profile_model)
        
        return profile

    async def get_credit_profile(self, customer_id: CustomerId) -> Optional[CreditProfile]:
        """Obtener perfil crediticio por cliente"""
        stmt = select(CreditProfileModel).where(
            CreditProfileModel.customer_id == customer_id.value
        )
        result = await self.session.execute(stmt)
        profile_model = result.scalar_one_or_none()
        
        if profile_model:
            return self._credit_profile_model_to_entity(profile_model)
        return None

    async def update_credit_profile(self, profile: CreditProfile) -> CreditProfile:
        """Actualizar perfil crediticio"""
        stmt = (
            update(CreditProfileModel)
            .where(CreditProfileModel.customer_id == profile.customer_id.value)
            .values(
                credit_score=profile.credit_score,
                credit_limit_amount=profile.credit_limit.amount,
                credit_limit_currency=profile.credit_limit.currency,
                current_debt_amount=profile.current_debt.amount,
                current_debt_currency=profile.current_debt.currency,
                payment_history_score=profile.payment_history_score,
                default_history_count=profile.default_history_count,
                updated_at=profile.updated_at,
                last_updated_score=profile.last_updated_score,
                risk_category=profile.risk_category
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return profile

    async def search_microcredits(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[Microcredit]:
        """Buscar microcréditos con filtros"""
        conditions = []
        
        if filters.get('customer_id'):
            conditions.append(MicrocreditModel.customer_id == filters['customer_id'])
        
        if filters.get('status'):
            conditions.append(MicrocreditModel.status == filters['status'])
        
        if filters.get('start_date'):
            conditions.append(MicrocreditModel.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            conditions.append(MicrocreditModel.created_at <= filters['end_date'])
        
        if filters.get('min_amount'):
            conditions.append(MicrocreditModel.principal_amount_amount >= filters['min_amount'])
        
        if filters.get('max_amount'):
            conditions.append(MicrocreditModel.principal_amount_amount <= filters['max_amount'])
        
        stmt = (
            select(MicrocreditModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(MicrocreditModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        microcredit_models = result.scalars().all()
        
        return [self._microcredit_model_to_entity(model) for model in microcredit_models]

    def _application_model_to_entity(self, model: MicrocreditApplicationModel) -> MicrocreditApplication:
        """Convertir modelo de solicitud a entidad"""
        from src.domain.entities.microcredit import ApplicationStatus
        
        application = MicrocreditApplication(
            application_id=model.application_id,
            customer_id=CustomerId(model.customer_id),
            requested_amount=Money(model.requested_amount_amount, model.requested_amount_currency),
            purpose=model.purpose
        )
        
        # Asignar propiedades adicionales
        application.status = ApplicationStatus(model.status)
        application.created_at = model.created_at
        application.updated_at = model.updated_at
        application.submitted_at = model.submitted_at
        application.reviewed_at = model.reviewed_at
        application.approved_at = model.approved_at
        application.rejected_at = model.rejected_at
        application.credit_score = model.credit_score
        application.risk_assessment = model.risk_assessment
        application.employment_type = model.employment_type
        application.business_description = model.business_description
        application.collateral_description = model.collateral_description
        
        if model.monthly_income_amount and model.monthly_income_currency:
            application.monthly_income = Money(model.monthly_income_amount, model.monthly_income_currency)
        
        if model.rejection_reasons:
            application.rejection_reasons = model.rejection_reasons.split(',')
        
        if model.guarantor_info:
            import json
            try:
                application.guarantor_info = json.loads(model.guarantor_info)
            except:
                application.guarantor_info = {}
        
        return application

    def _microcredit_model_to_entity(self, model: MicrocreditModel) -> Microcredit:
        """Convertir modelo de microcrédito a entidad"""
        from src.domain.entities.microcredit import MicrocreditStatus
        
        microcredit = Microcredit(
            microcredit_id=model.microcredit_id,
            customer_id=CustomerId(model.customer_id),
            approved_amount=Money(model.principal_amount_amount, model.principal_amount_currency),
            interest_rate=model.interest_rate,
            term_months=model.term_months
        )
        
        # Asignar propiedades adicionales
        microcredit.status = MicrocreditStatus(model.status)
        microcredit.created_at = model.created_at
        microcredit.updated_at = model.updated_at
        microcredit.disbursement_date = model.disbursement_date
        microcredit.first_payment_date = model.first_payment_date
        microcredit.final_payment_date = model.final_payment_date
        microcredit.total_amount = Money(model.total_amount_amount, model.total_amount_currency)
        microcredit.outstanding_balance = Money(model.outstanding_balance_amount, model.outstanding_balance_currency)
        microcredit.total_paid = Money(model.total_paid_amount, model.total_paid_currency)
        microcredit.late_fees = Money(model.late_fees_amount, model.late_fees_currency)
        microcredit.default_date = model.default_date
        microcredit.fully_paid_date = model.fully_paid_date
        
        # Cargar pagos relacionados
        if hasattr(model, 'payments') and model.payments:
            microcredit.payments = [
                self._payment_model_to_entity(payment) for payment in model.payments
            ]
        
        return microcredit

    def _payment_model_to_entity(self, model: MicrocreditPaymentModel) -> MicrocreditPayment:
        """Convertir modelo de pago a entidad"""
        from src.domain.entities.microcredit import PaymentStatus
        
        payment = MicrocreditPayment(
            payment_id=model.payment_id,
            microcredit_id=model.microcredit_id,
            amount=Money(model.amount_amount, model.amount_currency),
            payment_date=model.payment_date,
            payment_method=model.payment_method
        )
        
        # Asignar propiedades adicionales
        payment.status = PaymentStatus(model.status)
        payment.created_at = model.created_at
        payment.updated_at = model.updated_at
        payment.reference_number = model.reference_number
        payment.principal_portion = model.principal_portion
        payment.interest_portion = model.interest_portion
        payment.late_fee_portion = model.late_fee_portion
        payment.is_late_payment = model.is_late_payment
        payment.days_late = model.days_late
        payment.payment_notes = model.payment_notes
        
        return payment

    def _credit_profile_model_to_entity(self, model: CreditProfileModel) -> CreditProfile:
        """Convertir modelo de perfil crediticio a entidad"""
        profile = CreditProfile(CustomerId(model.customer_id))
        
        # Asignar propiedades
        profile.credit_score = model.credit_score
        profile.credit_limit = Money(model.credit_limit_amount, model.credit_limit_currency)
        profile.current_debt = Money(model.current_debt_amount, model.current_debt_currency)
        profile.payment_history_score = model.payment_history_score
        profile.default_history_count = model.default_history_count
        profile.created_at = model.created_at
        profile.updated_at = model.updated_at
        profile.last_updated_score = model.last_updated_score
        profile.first_credit_date = model.first_credit_date
        profile.risk_category = model.risk_category
        
        return profile