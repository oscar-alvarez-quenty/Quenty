from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

from src.domain.value_objects.money import Money


class CampaignType(Enum):
    DISCOUNT = "discount"
    VOLUME_BONUS = "volume_bonus"
    CASHBACK = "cashback"
    FREE_SHIPPING = "free_shipping"
    COMMISSION_BOOST = "commission_boost"
    REFERRAL = "referral"


class CampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TargetType(Enum):
    ALL_CUSTOMERS = "all_customers"
    CUSTOMER_TYPE = "customer_type"  # pequeño, mediano, grande
    SPECIFIC_CUSTOMERS = "specific_customers"
    GEOGRAPHIC = "geographic"
    FRANCHISE = "franchise"
    NEW_CUSTOMERS = "new_customers"
    VOLUME_BASED = "volume_based"


class DiscountType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    TIERED = "tiered"


@dataclass
class CampaignRule:
    rule_id: str
    condition: str  # JSON condition string
    action: str  # Action to apply
    parameters: Dict[str, Any]
    is_active: bool = True


@dataclass
class CampaignReward:
    reward_type: str  # "discount", "cashback", "commission_boost"
    value: Union[float, Money]
    max_redemptions: Optional[int] = None
    per_user_limit: Optional[int] = None


@dataclass
class CampaignUsage:
    customer_id: str
    usage_date: datetime
    order_id: Optional[str] = None
    reward_applied: Optional[CampaignReward] = None
    amount_saved: Optional[Money] = None


class CommercialCampaign:
    def __init__(
        self,
        campaign_id: str,
        name: str,
        campaign_type: CampaignType,
        target_type: TargetType
    ):
        self.campaign_id = campaign_id
        self.name = name
        self.description = ""
        self.campaign_type = campaign_type
        self.target_type = target_type
        self.status = CampaignStatus.DRAFT
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.budget: Optional[Money] = None
        self.spent_amount = Money(0, "COP")
        self.rules: List[CampaignRule] = []
        self.rewards: List[CampaignReward] = []
        self.target_criteria: Dict[str, Any] = {}
        self.usage_history: List[CampaignUsage] = []
        self.max_total_redemptions: Optional[int] = None
        self.current_redemptions = 0
        self.created_by: str = ""
        self.priority = 1  # 1 = lowest, 10 = highest

    def set_schedule(self, start_date: datetime, end_date: datetime) -> None:
        """Programar fechas de inicio y fin de la campaña"""
        if start_date >= end_date:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        self.start_date = start_date
        self.end_date = end_date
        self.updated_at = datetime.now()
        
        # Actualizar status según fechas
        now = datetime.now()
        if now < start_date:
            self.status = CampaignStatus.SCHEDULED
        elif start_date <= now <= end_date:
            self.status = CampaignStatus.ACTIVE

    def set_budget(self, budget: Money) -> None:
        """Establecer presupuesto de la campaña"""
        if budget.amount <= 0:
            raise ValueError("El presupuesto debe ser mayor a cero")
        
        self.budget = budget
        self.updated_at = datetime.now()

    def add_rule(self, rule: CampaignRule) -> None:
        """Agregar regla a la campaña"""
        if any(r.rule_id == rule.rule_id for r in self.rules):
            raise ValueError(f"Ya existe una regla con ID {rule.rule_id}")
        
        self.rules.append(rule)
        self.updated_at = datetime.now()

    def add_reward(self, reward: CampaignReward) -> None:
        """Agregar recompensa a la campaña"""
        self.rewards.append(reward)
        self.updated_at = datetime.now()

    def set_target_criteria(self, criteria: Dict[str, Any]) -> None:
        """Establecer criterios de targeting"""
        self.target_criteria = criteria
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activar campaña"""
        if self.status != CampaignStatus.DRAFT and self.status != CampaignStatus.SCHEDULED:
            raise ValueError("Solo se pueden activar campañas en borrador o programadas")
        
        if not self.start_date or not self.end_date:
            raise ValueError("Se requieren fechas de inicio y fin")
        
        if not self.rewards:
            raise ValueError("Se requiere al menos una recompensa")
        
        now = datetime.now()
        if now < self.start_date:
            self.status = CampaignStatus.SCHEDULED
        elif now <= self.end_date:
            self.status = CampaignStatus.ACTIVE
        else:
            raise ValueError("No se puede activar una campaña cuya fecha de fin ya pasó")
        
        self.updated_at = datetime.now()

    def pause(self) -> None:
        """Pausar campaña activa"""
        if self.status != CampaignStatus.ACTIVE:
            raise ValueError("Solo se pueden pausar campañas activas")
        
        self.status = CampaignStatus.PAUSED
        self.updated_at = datetime.now()

    def resume(self) -> None:
        """Reanudar campaña pausada"""
        if self.status != CampaignStatus.PAUSED:
            raise ValueError("Solo se pueden reanudar campañas pausadas")
        
        now = datetime.now()
        if self.end_date and now > self.end_date:
            self.status = CampaignStatus.COMPLETED
        else:
            self.status = CampaignStatus.ACTIVE
        
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """Cancelar campaña"""
        if self.status in [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED]:
            raise ValueError("No se puede cancelar una campaña completada o ya cancelada")
        
        self.status = CampaignStatus.CANCELLED
        self.updated_at = datetime.now()

    def is_applicable_to_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> bool:
        """Verificar si la campaña es aplicable a un cliente"""
        if not self.is_active():
            return False
        
        if self.has_reached_redemption_limit():
            return False
        
        if self.has_exceeded_budget():
            return False
        
        # Verificar límite por usuario
        user_usage_count = len([u for u in self.usage_history if u.customer_id == customer_id])
        for reward in self.rewards:
            if reward.per_user_limit and user_usage_count >= reward.per_user_limit:
                return False
        
        # Verificar criterios de targeting
        return self._evaluate_target_criteria(customer_data)

    def apply_to_order(self, customer_id: str, order_data: Dict[str, Any]) -> Optional[CampaignUsage]:
        """Aplicar campaña a una orden"""
        if not self.is_applicable_to_customer(customer_id, order_data.get("customer_data", {})):
            return None
        
        # Evaluar reglas para determinar recompensa
        applicable_reward = self._evaluate_rules(order_data)
        if not applicable_reward:
            return None
        
        # Crear uso de campaña
        usage = CampaignUsage(
            customer_id=customer_id,
            usage_date=datetime.now(),
            order_id=order_data.get("order_id"),
            reward_applied=applicable_reward
        )
        
        # Calcular ahorro
        if applicable_reward.reward_type == "discount":
            if isinstance(applicable_reward.value, Money):
                usage.amount_saved = applicable_reward.value
            else:  # percentage
                order_amount = order_data.get("amount", Money(0, "COP"))
                usage.amount_saved = Money(
                    order_amount.amount * (applicable_reward.value / 100),
                    order_amount.currency
                )
        
        self.usage_history.append(usage)
        self.current_redemptions += 1
        
        if usage.amount_saved:
            self.spent_amount = Money(
                self.spent_amount.amount + usage.amount_saved.amount,
                self.spent_amount.currency
            )
        
        self.updated_at = datetime.now()
        return usage

    def is_active(self) -> bool:
        """Verificar si la campaña está activa"""
        if self.status != CampaignStatus.ACTIVE:
            return False
        
        now = datetime.now()
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            self.status = CampaignStatus.COMPLETED
            return False
        
        return True

    def has_reached_redemption_limit(self) -> bool:
        """Verificar si se alcanzó el límite de redenciones"""
        return (self.max_total_redemptions is not None and 
                self.current_redemptions >= self.max_total_redemptions)

    def has_exceeded_budget(self) -> bool:
        """Verificar si se excedió el presupuesto"""
        return (self.budget is not None and 
                self.spent_amount.amount >= self.budget.amount)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento de la campaña"""
        total_savings = sum(u.amount_saved.amount for u in self.usage_history if u.amount_saved)
        unique_customers = len(set(u.customer_id for u in self.usage_history))
        
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "status": self.status.value,
            "total_redemptions": self.current_redemptions,
            "max_redemptions": self.max_total_redemptions,
            "unique_customers": unique_customers,
            "total_savings": Money(total_savings, self.spent_amount.currency),
            "budget": self.budget,
            "spent_amount": self.spent_amount,
            "budget_utilization": (self.spent_amount.amount / self.budget.amount * 100) if self.budget else 0,
            "average_savings_per_redemption": total_savings / self.current_redemptions if self.current_redemptions > 0 else 0,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days_remaining": (self.end_date - datetime.now()).days if self.end_date else None
        }

    def _evaluate_target_criteria(self, customer_data: Dict[str, Any]) -> bool:
        """Evaluar criterios de targeting"""
        if self.target_type == TargetType.ALL_CUSTOMERS:
            return True
        
        if self.target_type == TargetType.CUSTOMER_TYPE:
            required_type = self.target_criteria.get("customer_type")
            return customer_data.get("customer_type") == required_type
        
        if self.target_type == TargetType.SPECIFIC_CUSTOMERS:
            target_customers = self.target_criteria.get("customer_ids", [])
            return customer_data.get("customer_id") in target_customers
        
        if self.target_type == TargetType.NEW_CUSTOMERS:
            registration_date = customer_data.get("registration_date")
            if registration_date:
                days_since_registration = (datetime.now() - registration_date).days
                max_days = self.target_criteria.get("max_days_since_registration", 30)
                return days_since_registration <= max_days
        
        # Implementar otros tipos de targeting según necesidades
        return False

    def _evaluate_rules(self, order_data: Dict[str, Any]) -> Optional[CampaignReward]:
        """Evaluar reglas para determinar recompensa aplicable"""
        # Ordenar reglas activas por prioridad
        active_rules = [r for r in self.rules if r.is_active]
        
        # Por simplicidad, devolvemos la primera recompensa disponible
        # En una implementación real, evaluaríamos las condiciones JSON
        if self.rewards and active_rules:
            return self.rewards[0]
        
        return None

    def __str__(self) -> str:
        return f"CommercialCampaign({self.name}, {self.campaign_type.value}, {self.status.value})"