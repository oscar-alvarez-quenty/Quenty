from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from src.domain.entities.franchise import Franchise, LogisticPoint, LogisticOperator, FranchiseStatus
from src.domain.entities.token import CityToken, TokenDistribution, TokenHolder
from src.domain.entities.commission import Commission
from src.domain.value_objects.money import Money
from src.domain.events.franchise_events import (
    FranchiseCreated, FranchiseApproved, FranchiseActivated,
    LogisticPointAdded, OperatorAssigned, TokensIssued, UtilitiesDistributed
)


class FranchiseAggregate:
    def __init__(self, franchise: Franchise):
        self.franchise = franchise
        self.logistic_points: List[LogisticPoint] = []
        self.operators: List[LogisticOperator] = []
        self.city_tokens: List[CityToken] = []
        self.token_distributions: List[TokenDistribution] = []
        self.commission_history: List[Commission] = []
        self.performance_metrics: Dict[str, Any] = {}
        self._domain_events: List = []

    @classmethod
    def create_franchise(
        cls,
        franchise_id: str,
        business_name: str,
        owner_name: str,
        email: str,
        phone: str,
        city: str,
        zone_id: str,
        initial_investment: Money
    ) -> "FranchiseAggregate":
        """Crear nueva franquicia"""
        franchise = Franchise(
            franchise_id=franchise_id,
            business_name=business_name,
            owner_name=owner_name,
            email=email,
            phone=phone,
            city=city,
            zone_id=zone_id,
            initial_investment=initial_investment
        )
        
        aggregate = cls(franchise)
        aggregate._add_domain_event(
            FranchiseCreated(
                franchise_id=franchise_id,
                business_name=business_name,
                owner_name=owner_name,
                city=city,
                zone_id=zone_id,
                initial_investment=initial_investment.amount
            )
        )
        
        return aggregate

    def approve_franchise(
        self,
        approved_by: str,
        start_date: datetime,
        end_date: datetime,
        approved_investment: Money
    ) -> None:
        """Aprobar franquicia"""
        self.franchise.approve_franchise(start_date, end_date)
        self.franchise.investment_amount = approved_investment
        
        self._add_domain_event(
            FranchiseApproved(
                franchise_id=self.franchise.franchise_id,
                approved_by=approved_by,
                start_date=start_date,
                end_date=end_date,
                approved_investment=approved_investment.amount
            )
        )

    def activate_franchise(self, activation_fee_paid: Money) -> None:
        """Activar franquicia después de pago"""
        if self.franchise.status != FranchiseStatus.APPROVED:
            raise ValueError("Solo se pueden activar franquicias aprobadas")
        
        self.franchise.status = FranchiseStatus.ACTIVE
        self.franchise.is_active = True
        self.franchise.activation_date = datetime.now()
        
        # Inicializar métricas de rendimiento
        self.performance_metrics = {
            "total_orders": 0,
            "total_revenue": Money(0, "COP"),
            "monthly_targets": {},
            "customer_satisfaction": 0.0,
            "on_time_delivery_rate": 0.0
        }
        
        self._add_domain_event(
            FranchiseActivated(
                franchise_id=self.franchise.franchise_id,
                activation_date=datetime.now(),
                activation_fee=activation_fee_paid.amount
            )
        )

    def add_logistic_point(
        self,
        point_id: str,
        name: str,
        address: str,
        contact_phone: str,
        operating_hours: Dict[str, str],
        capacity: int
    ) -> LogisticPoint:
        """Agregar punto logístico a la franquicia"""
        if not self.franchise.is_active:
            raise ValueError("Solo franquicias activas pueden agregar puntos logísticos")
        
        point = LogisticPoint(
            point_id=point_id,
            franchise_id=self.franchise.franchise_id,
            name=name,
            address=address,
            contact_phone=contact_phone,
            operating_hours=operating_hours,
            capacity=capacity
        )
        
        self.logistic_points.append(point)
        
        self._add_domain_event(
            LogisticPointAdded(
                franchise_id=self.franchise.franchise_id,
                point_id=point_id,
                name=name,
                address=address,
                capacity=capacity
            )
        )
        
        return point

    def assign_operator(
        self,
        operator_id: str,
        name: str,
        email: str,
        phone: str,
        point_id: str
    ) -> LogisticOperator:
        """Asignar operador a un punto logístico"""
        # Verificar que el punto existe
        point = next((p for p in self.logistic_points if p.point_id == point_id), None)
        if not point:
            raise ValueError(f"Punto logístico {point_id} no encontrado")
        
        operator = LogisticOperator(
            operator_id=operator_id,
            franchise_id=self.franchise.franchise_id,
            name=name,
            email=email,
            phone=phone,
            assigned_point_id=point_id
        )
        
        self.operators.append(operator)
        
        self._add_domain_event(
            OperatorAssigned(
                franchise_id=self.franchise.franchise_id,
                operator_id=operator_id,
                name=name,
                point_id=point_id
            )
        )
        
        return operator

    def issue_city_tokens(
        self,
        token_id: str,
        total_supply: int,
        initial_distribution: Dict[str, int]  # holder_id -> amount
    ) -> CityToken:
        """Emitir tokens de ciudad para la franquicia"""
        if not self.franchise.is_active:
            raise ValueError("Solo franquicias activas pueden emitir tokens")
        
        city_token = CityToken(
            token_id=token_id,
            city=self.franchise.city,
            franchise_id=self.franchise.franchise_id,
            total_supply=total_supply
        )
        
        # Crear holders iniciales
        for holder_id, amount in initial_distribution.items():
            holder = TokenHolder(
                holder_id=holder_id,
                token_id=token_id,
                tokens_owned=amount,
                purchase_date=datetime.now(),
                purchase_price=Money(0, "COP")  # Distribución inicial gratuita
            )
            city_token.add_holder(holder)
        
        self.city_tokens.append(city_token)
        
        self._add_domain_event(
            TokensIssued(
                franchise_id=self.franchise.franchise_id,
                token_id=token_id,
                city=self.franchise.city,
                total_supply=total_supply,
                initial_holders=len(initial_distribution)
            )
        )
        
        return city_token

    def distribute_monthly_utilities(
        self,
        distribution_id: str,
        total_utilities: Money,
        distribution_date: datetime
    ) -> TokenDistribution:
        """Distribuir utilidades mensuales entre holders de tokens"""
        if not self.city_tokens:
            raise ValueError("No hay tokens emitidos para esta franquicia")
        
        # Usar el primer token de ciudad (podría haber múltiples)
        city_token = self.city_tokens[0]
        
        distribution = TokenDistribution(
            distribution_id=distribution_id,
            token_id=city_token.token_id,
            total_amount=total_utilities,
            distribution_date=distribution_date,
            distribution_type="monthly_utilities"
        )
        
        # Calcular distribución proporcional
        total_tokens = city_token.total_supply
        for holder in city_token.holders:
            holder_percentage = holder.tokens_owned / total_tokens
            holder_amount = Money(
                total_utilities.amount * holder_percentage,
                total_utilities.currency
            )
            
            distribution.add_recipient(holder.holder_id, holder_amount)
        
        city_token.add_distribution(distribution)
        self.token_distributions.append(distribution)
        
        self._add_domain_event(
            UtilitiesDistributed(
                franchise_id=self.franchise.franchise_id,
                distribution_id=distribution_id,
                total_amount=total_utilities.amount,
                recipients_count=len(city_token.holders),
                distribution_date=distribution_date
            )
        )
        
        return distribution

    def record_commission(self, commission: Commission) -> None:
        """Registrar comisión ganada por la franquicia"""
        self.commission_history.append(commission)
        
        # Actualizar métricas de rendimiento
        if commission.calculations:
            latest_calc = commission.calculations[-1]
            current_revenue = self.performance_metrics.get("total_revenue", Money(0, "COP"))
            self.performance_metrics["total_revenue"] = Money(
                current_revenue.amount + latest_calc.commission_amount.amount,
                current_revenue.currency
            )

    def update_performance_metrics(
        self,
        orders_processed: int,
        customer_satisfaction_score: float,
        on_time_delivery_rate: float
    ) -> None:
        """Actualizar métricas de rendimiento"""
        self.performance_metrics["total_orders"] += orders_processed
        self.performance_metrics["customer_satisfaction"] = customer_satisfaction_score
        self.performance_metrics["on_time_delivery_rate"] = on_time_delivery_rate
        
        # Calcular métricas adicionales
        current_month = datetime.now().strftime("%Y-%m")
        if current_month not in self.performance_metrics["monthly_targets"]:
            self.performance_metrics["monthly_targets"][current_month] = {
                "orders": 0,
                "revenue": Money(0, "COP"),
                "target_orders": 100,  # Meta mensual
                "target_revenue": Money(1000000, "COP")  # Meta mensual
            }
        
        self.performance_metrics["monthly_targets"][current_month]["orders"] += orders_processed

    def suspend_franchise(self, reason: str, suspended_by: str) -> None:
        """Suspender franquicia por incumplimiento"""
        if not self.franchise.is_active:
            raise ValueError("Solo se pueden suspender franquicias activas")
        
        self.franchise.status = FranchiseStatus.SUSPENDED
        self.franchise.is_active = False
        
        # Suspender todos los puntos logísticos
        for point in self.logistic_points:
            point.deactivate("Franquicia suspendida")
        
        self._add_domain_event(
            FranchiseSuspended(
                franchise_id=self.franchise.franchise_id,
                reason=reason,
                suspended_by=suspended_by,
                suspended_at=datetime.now()
            )
        )

    def reactivate_franchise(self, reactivated_by: str) -> None:
        """Reactivar franquicia suspendida"""
        if self.franchise.status != FranchiseStatus.SUSPENDED:
            raise ValueError("Solo se pueden reactivar franquicias suspendidas")
        
        self.franchise.status = FranchiseStatus.ACTIVE
        self.franchise.is_active = True
        
        # Reactivar puntos logísticos
        for point in self.logistic_points:
            if not point.is_active:
                point.activate()

    def get_financial_summary(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Obtener resumen financiero por período"""
        period_commissions = [
            c for c in self.commission_history
            if period_start <= c.created_at <= period_end
        ]
        
        total_revenue = Money(0, "COP")
        total_commissions = len(period_commissions)
        
        for commission in period_commissions:
            if commission.calculations:
                latest_calc = commission.calculations[-1]
                total_revenue = Money(
                    total_revenue.amount + latest_calc.commission_amount.amount,
                    total_revenue.currency
                )
        
        # Calcular ROI
        roi_percentage = 0.0
        if self.franchise.investment_amount and self.franchise.investment_amount.amount > 0:
            roi_percentage = (total_revenue.amount / self.franchise.investment_amount.amount) * 100
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_revenue": total_revenue,
            "total_commissions": total_commissions,
            "investment_amount": self.franchise.investment_amount,
            "roi_percentage": roi_percentage,
            "average_monthly_revenue": Money(
                total_revenue.amount / max(1, (period_end - period_start).days / 30),
                total_revenue.currency
            ),
            "active_points": len([p for p in self.logistic_points if p.is_active]),
            "total_operators": len(self.operators)
        }

    def get_token_performance(self) -> Dict[str, Any]:
        """Obtener rendimiento de tokens"""
        if not self.city_tokens:
            return {"has_tokens": False}
        
        city_token = self.city_tokens[0]
        total_distributed = Money(0, "COP")
        
        for distribution in self.token_distributions:
            total_distributed = Money(
                total_distributed.amount + distribution.total_amount.amount,
                total_distributed.currency
            )
        
        return {
            "has_tokens": True,
            "token_id": city_token.token_id,
            "total_supply": city_token.total_supply,
            "holders_count": len(city_token.holders),
            "total_distributed": total_distributed,
            "distributions_count": len(self.token_distributions),
            "last_distribution": self.token_distributions[-1].distribution_date if self.token_distributions else None
        }

    def get_operational_metrics(self) -> Dict[str, Any]:
        """Obtener métricas operacionales"""
        active_points = [p for p in self.logistic_points if p.is_active]
        total_capacity = sum(p.capacity for p in active_points)
        
        return {
            "franchise_status": self.franchise.status.value,
            "is_active": self.franchise.is_active,
            "total_points": len(self.logistic_points),
            "active_points": len(active_points),
            "total_operators": len(self.operators),
            "total_capacity": total_capacity,
            "performance_metrics": self.performance_metrics,
            "zone_coverage": self.franchise.zone_id,
            "city": self.franchise.city
        }

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()


# Evento de dominio adicional
from dataclasses import dataclass

@dataclass
class FranchiseSuspended:
    franchise_id: str
    reason: str
    suspended_by: str
    suspended_at: datetime