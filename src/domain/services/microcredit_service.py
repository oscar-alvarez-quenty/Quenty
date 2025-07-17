from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from src.domain.entities.microcredit import (
    MicrocreditApplication, Microcredit, CreditProfile, PaymentSchedule,
    MicrocreditPayment, ApplicationStatus, MicrocreditStatus, PaymentStatus
)
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.domain.events.microcredit_events import (
    MicrocreditApplicationSubmitted, CreditScoringStarted, CreditScoringCompleted,
    MicrocreditApproved, MicrocreditRejected, MicrocreditDisbursed,
    PaymentScheduleGenerated, MicrocreditPaymentReceived, CreditScoreUpdated
)


class CreditScoringEngine:
    """Motor de scoring crediticio"""
    
    def __init__(self):
        self.model_version = "v2.1"
        self.base_score = 500
        self.max_score = 850
        self.min_score = 300
    
    def calculate_credit_score(
        self,
        customer: Customer,
        application: MicrocreditApplication,
        credit_profile: Optional[CreditProfile] = None
    ) -> Dict[str, Any]:
        """Calcular score crediticio del cliente"""
        
        factors = {
            "payment_history": 35,      # Historial de pagos
            "credit_utilization": 30,   # Utilización de crédito
            "credit_length": 15,        # Longitud del historial
            "new_credit": 10,           # Nuevos créditos
            "credit_mix": 10            # Mix de tipos de crédito
        }
        
        # Scoring base
        score = self.base_score
        scoring_details = {}
        
        # Factor 1: Historial de pagos (35%)
        if credit_profile:
            payment_score = self._calculate_payment_history_score(credit_profile)
            score += int(payment_score * 0.35)
            scoring_details["payment_history"] = payment_score
        else:
            # Cliente nuevo - score neutro
            scoring_details["payment_history"] = 0
        
        # Factor 2: Utilización de crédito (30%)
        utilization_score = self._calculate_utilization_score(credit_profile, application)
        score += int(utilization_score * 0.30)
        scoring_details["credit_utilization"] = utilization_score
        
        # Factor 3: Longitud del historial (15%)
        length_score = self._calculate_credit_length_score(credit_profile)
        score += int(length_score * 0.15)
        scoring_details["credit_length"] = length_score
        
        # Factor 4: Nuevos créditos (10%)
        new_credit_score = self._calculate_new_credit_score(credit_profile)
        score += int(new_credit_score * 0.10)
        scoring_details["new_credit"] = new_credit_score
        
        # Factor 5: Mix de créditos (10%)
        mix_score = self._calculate_credit_mix_score(credit_profile)
        score += int(mix_score * 0.10)
        scoring_details["credit_mix"] = mix_score
        
        # Ajustes por datos específicos de la aplicación
        score += self._calculate_application_adjustments(application)
        
        # Mantener score en rango válido
        score = max(self.min_score, min(self.max_score, score))
        
        # Determinar nivel de riesgo
        risk_level = self._determine_risk_level(score)
        
        # Generar recomendación
        recommendation = self._generate_recommendation(score, risk_level, application)
        
        return {
            "credit_score": score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "scoring_factors": scoring_details,
            "model_version": self.model_version
        }
    
    def _calculate_payment_history_score(self, credit_profile: CreditProfile) -> float:
        """Calcular score basado en historial de pagos"""
        if not credit_profile.payment_history:
            return 0.0
        
        total_payments = len(credit_profile.payment_history)
        on_time_payments = sum(1 for p in credit_profile.payment_history if p["on_time"])
        
        if total_payments == 0:
            return 0.0
        
        on_time_rate = on_time_payments / total_payments
        
        # Score de 0 a 100 basado en porcentaje de pagos a tiempo
        if on_time_rate >= 0.95:
            return 100.0
        elif on_time_rate >= 0.90:
            return 80.0
        elif on_time_rate >= 0.80:
            return 60.0
        elif on_time_rate >= 0.70:
            return 40.0
        else:
            return 20.0
    
    def _calculate_utilization_score(
        self,
        credit_profile: Optional[CreditProfile],
        application: MicrocreditApplication
    ) -> float:
        """Calcular score basado en utilización de crédito"""
        if not credit_profile:
            return 50.0  # Score neutro para clientes nuevos
        
        if credit_profile.credit_limit.amount == 0:
            return 50.0
        
        # Incluir el monto solicitado en la utilización
        current_utilization = credit_profile.current_debt.amount
        requested_amount = application.requested_amount.amount
        total_utilization = (current_utilization + requested_amount) / credit_profile.credit_limit.amount
        
        # Score basado en utilización total
        if total_utilization <= 0.10:
            return 100.0
        elif total_utilization <= 0.30:
            return 80.0
        elif total_utilization <= 0.50:
            return 60.0
        elif total_utilization <= 0.70:
            return 40.0
        else:
            return 20.0
    
    def _calculate_credit_length_score(self, credit_profile: Optional[CreditProfile]) -> float:
        """Calcular score basado en longitud del historial crediticio"""
        if not credit_profile or not credit_profile.first_credit_date:
            return 0.0
        
        years_of_credit = (datetime.now() - credit_profile.first_credit_date).days / 365.25
        
        if years_of_credit >= 5:
            return 100.0
        elif years_of_credit >= 3:
            return 80.0
        elif years_of_credit >= 2:
            return 60.0
        elif years_of_credit >= 1:
            return 40.0
        else:
            return 20.0
    
    def _calculate_new_credit_score(self, credit_profile: Optional[CreditProfile]) -> float:
        """Calcular score basado en nuevos créditos recientes"""
        if not credit_profile:
            return 50.0
        
        # Contar aplicaciones en últimos 6 meses
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_applications = credit_profile.recent_applications_count(six_months_ago)
        
        if recent_applications == 0:
            return 100.0
        elif recent_applications == 1:
            return 80.0
        elif recent_applications == 2:
            return 60.0
        elif recent_applications == 3:
            return 40.0
        else:
            return 20.0
    
    def _calculate_credit_mix_score(self, credit_profile: Optional[CreditProfile]) -> float:
        """Calcular score basado en diversidad de tipos de crédito"""
        if not credit_profile:
            return 30.0  # Score bajo para clientes nuevos
        
        # En implementación real evaluaría tipos de crédito
        # Por ahora retorna score medio
        return 60.0
    
    def _calculate_application_adjustments(self, application: MicrocreditApplication) -> int:
        """Calcular ajustes basados en datos de la aplicación"""
        adjustments = 0
        
        # Ajuste por propósito del crédito
        purpose_adjustments = {
            "working_capital": 10,
            "inventory": 5,
            "equipment": 0,
            "personal": -5,
            "debt_consolidation": -10
        }
        adjustments += purpose_adjustments.get(application.purpose, 0)
        
        # Ajuste por monto solicitado vs ingresos declarados
        if application.monthly_income and application.monthly_income.amount > 0:
            debt_to_income = application.requested_amount.amount / application.monthly_income.amount
            if debt_to_income <= 0.3:
                adjustments += 10
            elif debt_to_income <= 0.5:
                adjustments += 0
            else:
                adjustments -= 15
        
        return adjustments
    
    def _determine_risk_level(self, score: int) -> str:
        """Determinar nivel de riesgo basado en score"""
        if score >= 750:
            return "very_low"
        elif score >= 650:
            return "low"
        elif score >= 550:
            return "medium"
        elif score >= 450:
            return "high"
        else:
            return "very_high"
    
    def _generate_recommendation(
        self,
        score: int,
        risk_level: str,
        application: MicrocreditApplication
    ) -> str:
        """Generar recomendación de aprobación/rechazo"""
        if score >= 650:
            return "approve"
        elif score >= 500:
            return "manual_review"
        else:
            return "reject"


class MicrocreditService:
    def __init__(self):
        self.applications: Dict[str, MicrocreditApplication] = {}
        self.microcredits: Dict[str, Microcredit] = {}
        self.credit_profiles: Dict[str, CreditProfile] = {}
        self.scoring_engine = CreditScoringEngine()
        self._domain_events: List = []

    def submit_application(
        self,
        customer: Customer,
        requested_amount: Money,
        purpose: str,
        monthly_income: Optional[Money] = None,
        employment_type: str = "self_employed",
        business_description: Optional[str] = None
    ) -> MicrocreditApplication:
        """Enviar solicitud de microcrédito"""
        application_id = str(uuid.uuid4())
        
        application = MicrocreditApplication(
            application_id=application_id,
            customer_id=customer.customer_id,
            requested_amount=requested_amount,
            purpose=purpose
        )
        
        if monthly_income:
            application.monthly_income = monthly_income
        
        application.employment_type = employment_type
        application.business_description = business_description
        
        self.applications[application_id] = application
        
        self._add_domain_event(
            MicrocreditApplicationSubmitted(
                application_id=application_id,
                customer_id=customer.customer_id.value,
                requested_amount={
                    "amount": requested_amount.amount,
                    "currency": requested_amount.currency
                },
                purpose=purpose,
                submitted_at=datetime.now()
            )
        )
        
        return application

    def evaluate_application(
        self,
        application_id: str,
        customer: Customer
    ) -> Dict[str, Any]:
        """Evaluar solicitud de microcrédito"""
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Solicitud {application_id} no encontrada")
        
        # Iniciar scoring
        self._add_domain_event(
            CreditScoringStarted(
                application_id=application_id,
                customer_id=customer.customer_id.value,
                scoring_model_version=self.scoring_engine.model_version,
                data_sources=["internal_history", "payment_behavior", "application_data"],
                started_at=datetime.now()
            )
        )
        
        # Obtener perfil crediticio del cliente
        credit_profile = self.credit_profiles.get(customer.customer_id.value)
        
        # Calcular score crediticio
        scoring_result = self.scoring_engine.calculate_credit_score(
            customer, application, credit_profile
        )
        
        # Actualizar aplicación con resultado
        application.credit_score = scoring_result["credit_score"]
        application.risk_assessment = scoring_result["risk_level"]
        
        self._add_domain_event(
            CreditScoringCompleted(
                application_id=application_id,
                customer_id=customer.customer_id.value,
                credit_score=scoring_result["credit_score"],
                risk_level=scoring_result["risk_level"],
                scoring_factors=scoring_result["scoring_factors"],
                recommendation=scoring_result["recommendation"],
                completed_at=datetime.now()
            )
        )
        
        return scoring_result

    def approve_application(
        self,
        application_id: str,
        approved_amount: Money,
        interest_rate: float,
        term_months: int,
        approved_by: str
    ) -> Microcredit:
        """Aprobar solicitud de microcrédito"""
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Solicitud {application_id} no encontrada")
        
        if application.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden aprobar solicitudes en revisión")
        
        # Crear microcrédito
        microcredit_id = str(uuid.uuid4())
        microcredit = Microcredit(
            microcredit_id=microcredit_id,
            customer_id=application.customer_id,
            approved_amount=approved_amount,
            interest_rate=interest_rate,
            term_months=term_months
        )
        
        # Aprobar aplicación
        application.approve(approved_amount, interest_rate, term_months)
        
        self.microcredits[microcredit_id] = microcredit
        
        self._add_domain_event(
            MicrocreditApproved(
                microcredit_id=microcredit_id,
                application_id=application_id,
                customer_id=application.customer_id.value,
                approved_amount={
                    "amount": approved_amount.amount,
                    "currency": approved_amount.currency
                },
                interest_rate=interest_rate,
                term_months=term_months,
                approved_by=approved_by,
                approved_at=datetime.now()
            )
        )
        
        return microcredit

    def reject_application(
        self,
        application_id: str,
        rejection_reasons: List[str],
        rejected_by: str
    ) -> None:
        """Rechazar solicitud de microcrédito"""
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Solicitud {application_id} no encontrada")
        
        application.reject(rejection_reasons)
        
        self._add_domain_event(
            MicrocreditRejected(
                application_id=application_id,
                customer_id=application.customer_id.value,
                rejection_reasons=rejection_reasons,
                rejection_code="CREDIT_SCORE_LOW",
                rejected_by=rejected_by,
                rejected_at=datetime.now()
            )
        )

    def disburse_microcredit(
        self,
        microcredit_id: str,
        disbursement_method: str = "wallet"
    ) -> str:
        """Desembolsar microcrédito"""
        microcredit = self.microcredits.get(microcredit_id)
        if not microcredit:
            raise ValueError(f"Microcrédito {microcredit_id} no encontrado")
        
        if microcredit.status != MicrocreditStatus.APPROVED:
            raise ValueError("Solo se pueden desembolsar microcréditos aprobados")
        
        reference_number = f"DISB_{microcredit_id[:8]}"
        microcredit.disburse()
        
        # Generar cronograma de pagos
        self._generate_payment_schedule(microcredit)
        
        self._add_domain_event(
            MicrocreditDisbursed(
                microcredit_id=microcredit_id,
                customer_id=microcredit.customer_id.value,
                disbursed_amount={
                    "amount": microcredit.principal_amount.amount,
                    "currency": microcredit.principal_amount.currency
                },
                disbursement_method=disbursement_method,
                reference_number=reference_number,
                disbursed_at=datetime.now()
            )
        )
        
        return reference_number

    def process_payment(
        self,
        microcredit_id: str,
        payment_amount: Money,
        payment_method: str,
        reference_number: Optional[str] = None
    ) -> MicrocreditPayment:
        """Procesar pago de microcrédito"""
        microcredit = self.microcredits.get(microcredit_id)
        if not microcredit:
            raise ValueError(f"Microcrédito {microcredit_id} no encontrado")
        
        payment_id = str(uuid.uuid4())
        payment = microcredit.process_payment(
            payment_id=payment_id,
            amount=payment_amount,
            payment_method=payment_method,
            reference_number=reference_number
        )
        
        # Verificar si el pago está a tiempo
        is_on_time = True
        days_late = 0
        
        if microcredit.payment_schedule:
            next_due = microcredit.payment_schedule.get_next_due_payment()
            if next_due and datetime.now().date() > next_due["due_date"]:
                is_on_time = False
                days_late = (datetime.now().date() - next_due["due_date"]).days
        
        self._add_domain_event(
            MicrocreditPaymentReceived(
                payment_id=payment_id,
                microcredit_id=microcredit_id,
                customer_id=microcredit.customer_id.value,
                payment_amount={
                    "amount": payment_amount.amount,
                    "currency": payment_amount.currency
                },
                payment_method=payment_method,
                payment_date=datetime.now(),
                is_on_time=is_on_time,
                days_late=days_late
            )
        )
        
        # Actualizar perfil crediticio
        self._update_credit_profile(microcredit.customer_id, payment, is_on_time)
        
        return payment

    def get_customer_credit_profile(
        self,
        customer_id: CustomerId
    ) -> Optional[CreditProfile]:
        """Obtener perfil crediticio del cliente"""
        return self.credit_profiles.get(customer_id.value)

    def update_credit_limit(
        self,
        customer_id: CustomerId,
        new_limit: Money,
        reason: str,
        approved_by: str
    ) -> None:
        """Actualizar límite de crédito del cliente"""
        profile = self.credit_profiles.get(customer_id.value)
        if not profile:
            # Crear nuevo perfil si no existe
            profile = CreditProfile(customer_id)
            self.credit_profiles[customer_id.value] = profile
        
        old_limit = profile.credit_limit
        profile.update_credit_limit(new_limit)
        
        # Aquí iría el evento de actualización de límite
        # self._add_domain_event(CreditLimitUpdated(...))

    def _generate_payment_schedule(self, microcredit: Microcredit) -> PaymentSchedule:
        """Generar cronograma de pagos"""
        schedule = PaymentSchedule(
            microcredit_id=microcredit.microcredit_id,
            total_amount=microcredit.total_amount,
            term_months=microcredit.term_months,
            payment_frequency="monthly"
        )
        
        schedule.generate_schedule(microcredit.disbursement_date or datetime.now())
        microcredit.payment_schedule = schedule
        
        self._add_domain_event(
            PaymentScheduleGenerated(
                microcredit_id=microcredit.microcredit_id,
                customer_id=microcredit.customer_id.value,
                total_payments=len(schedule.payments),
                payment_frequency="monthly",
                first_payment_date=schedule.payments[0]["due_date"],
                total_amount={
                    "amount": microcredit.total_amount.amount,
                    "currency": microcredit.total_amount.currency
                },
                generated_at=datetime.now()
            )
        )
        
        return schedule

    def _update_credit_profile(
        self,
        customer_id: CustomerId,
        payment: MicrocreditPayment,
        is_on_time: bool
    ) -> None:
        """Actualizar perfil crediticio con información de pago"""
        profile = self.credit_profiles.get(customer_id.value)
        if not profile:
            profile = CreditProfile(customer_id)
            self.credit_profiles[customer_id.value] = profile
        
        # Agregar pago al historial
        payment_record = {
            "payment_id": payment.payment_id,
            "amount": payment.amount.amount,
            "date": payment.payment_date,
            "on_time": is_on_time
        }
        
        profile.add_payment_record(payment_record)
        
        # Recalcular score crediticio si hay cambios significativos
        old_score = profile.credit_score
        # En implementación real recalcularía el score
        new_score = old_score + (5 if is_on_time else -10)
        new_score = max(300, min(850, new_score))
        
        if abs(new_score - old_score) >= 10:
            profile.credit_score = new_score
            
            self._add_domain_event(
                CreditScoreUpdated(
                    customer_id=customer_id.value,
                    old_score=old_score,
                    new_score=new_score,
                    score_change=new_score - old_score,
                    update_triggers=["payment_received"],
                    updated_at=datetime.now()
                )
            )

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()