from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.domain.entities.commission import Commission, CommissionRule, CommissionType, Liquidation
from src.domain.entities.order import Order
from src.domain.entities.customer import Customer
from src.domain.entities.franchise import Franchise
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.order_id import OrderId

class CommissionService:
    """Servicio de dominio para el cálculo y gestión de comisiones"""
    
    def __init__(self):
        self.commission_rules: List[CommissionRule] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Inicializa las reglas de comisión por defecto"""
        # Regla para envíos nacionales - clientes pequeños
        self.commission_rules.append(CommissionRule(
            name="National Small Customer",
            commission_type=CommissionType.SHIPMENT,
            customer_type="small",
            service_type="national",
            commission_rate=Decimal('0.05')  # 5%
        ))
        
        # Regla para envíos nacionales - clientes medianos
        self.commission_rules.append(CommissionRule(
            name="National Medium Customer",
            commission_type=CommissionType.SHIPMENT,
            customer_type="medium",
            service_type="national",
            commission_rate=Decimal('0.07')  # 7%
        ))
        
        # Regla para envíos internacionales
        self.commission_rules.append(CommissionRule(
            name="International Shipment",
            commission_type=CommissionType.SHIPMENT,
            customer_type="",  # Aplica a todos
            service_type="international",
            commission_rate=Decimal('0.10')  # 10%
        ))
        
        # Regla para franquicias
        self.commission_rules.append(CommissionRule(
            name="Franchise Fee",
            commission_type=CommissionType.FRANCHISE_FEE,
            customer_type="franchise",
            service_type="",
            commission_rate=Decimal('0.15')  # 15%
        ))
    
    def calculate_shipment_commission(self, order: Order, customer: Customer) -> Commission:
        """Calcula la comisión por envío"""
        
        # Determinar tipo de cliente y servicio
        customer_type = customer.customer_type.value
        service_type = order.service_type.value
        base_amount = order.quoted_price or Decimal('0.00')
        
        # Buscar regla aplicable
        applicable_rule = self._find_applicable_rule(
            CommissionType.SHIPMENT, 
            customer_type, 
            service_type, 
            base_amount
        )
        
        if not applicable_rule:
            raise ValueError(f"No commission rule found for {customer_type} {service_type} shipment")
        
        # Crear comisión
        commission = Commission(
            recipient_id=customer.id,
            order_id=order.id,
            commission_type=CommissionType.SHIPMENT,
            base_amount=base_amount,
            commission_rate=applicable_rule.commission_rate
        )
        
        # Calcular montos
        commission.calculate_commission()
        
        return commission
    
    def calculate_franchise_commission(self, franchise: Franchise, 
                                     gross_revenue: Decimal, period: str) -> Commission:
        """Calcula la comisión de franquicia"""
        
        applicable_rule = self._find_applicable_rule(
            CommissionType.FRANCHISE_FEE,
            "franchise",
            "",
            gross_revenue
        )
        
        if not applicable_rule:
            raise ValueError("No franchise commission rule found")
        
        commission = Commission(
            recipient_id=franchise.franchisee_id,
            franchise_id=franchise.id,
            commission_type=CommissionType.FRANCHISE_FEE,
            base_amount=gross_revenue,
            commission_rate=applicable_rule.commission_rate,
            reference_period=period
        )
        
        commission.calculate_commission()
        
        return commission
    
    def calculate_volume_bonus(self, customer_id: CustomerId, 
                             monthly_volume: Decimal, shipment_count: int) -> Commission:
        """Calcula bonos por volumen"""
        
        # Lógica de bonos por volumen
        bonus_rate = Decimal('0.00')
        
        if shipment_count >= 100:  # 100+ envíos
            bonus_rate = Decimal('0.02')  # 2% adicional
        elif shipment_count >= 50:   # 50+ envíos
            bonus_rate = Decimal('0.01')  # 1% adicional
        
        if bonus_rate > 0:
            commission = Commission(
                recipient_id=customer_id,
                commission_type=CommissionType.VOLUME_BONUS,
                base_amount=monthly_volume,
                commission_rate=bonus_rate
            )
            
            commission.calculate_commission()
            return commission
        
        return None
    
    def calculate_referral_commission(self, referrer_id: CustomerId, 
                                    referred_customer_id: CustomerId,
                                    first_order_amount: Decimal) -> Commission:
        """Calcula comisión por referido"""
        
        # Comisión fija por referido exitoso
        referral_rate = Decimal('0.03')  # 3% de la primera orden
        
        commission = Commission(
            recipient_id=referrer_id,
            commission_type=CommissionType.REFERRAL,
            base_amount=first_order_amount,
            commission_rate=referral_rate,
            notes=f"Referred customer: {referred_customer_id}"
        )
        
        commission.calculate_commission()
        
        return commission
    
    def create_monthly_liquidation(self, recipient_id: CustomerId, 
                                 period: str, commissions: List[Commission]) -> Liquidation:
        """Crea una liquidación mensual"""
        
        # Validar que todas las comisiones estén aprobadas
        approved_commissions = [c for c in commissions if c.status.value == "approved"]
        
        if not approved_commissions:
            raise ValueError("No approved commissions found for liquidation")
        
        liquidation = Liquidation(
            recipient_id=recipient_id,
            period=period
        )
        
        # Agregar comisiones a la liquidación
        for commission in approved_commissions:
            liquidation.add_commission(commission)
        
        return liquidation
    
    def apply_pyramid_structure(self, base_commission: Commission, 
                               agent_hierarchy: List[Dict[str, Any]]) -> List[Commission]:
        """Aplica estructura piramidal de comisiones"""
        
        pyramid_commissions = []
        base_amount = base_commission.commission_amount
        
        # Estructura piramidal: nivel 1 (40%), nivel 2 (30%), nivel 3 (20%), nivel 4 (10%)
        level_rates = [Decimal('0.40'), Decimal('0.30'), Decimal('0.20'), Decimal('0.10')]
        
        for i, agent_info in enumerate(agent_hierarchy[:4]):  # Máximo 4 niveles
            if i < len(level_rates):
                commission_amount = base_amount * level_rates[i]
                
                commission = Commission(
                    recipient_id=CustomerId.from_string(agent_info['agent_id']),
                    order_id=base_commission.order_id,
                    commission_type=CommissionType.SHIPMENT,
                    base_amount=base_amount,
                    commission_rate=level_rates[i],
                    notes=f"Pyramid level {i+1} from agent {agent_info['agent_id']}"
                )
                
                commission.calculate_commission()
                pyramid_commissions.append(commission)
        
        return pyramid_commissions
    
    def validate_commission_eligibility(self, recipient_id: CustomerId, 
                                      order: Order) -> Dict[str, Any]:
        """Valida elegibilidad para comisión"""
        
        validation_result = {
            "eligible": True,
            "reasons": []
        }
        
        # Aquí irían las validaciones de negocio:
        # - Cliente no tiene cartera vencida
        # - Orden está completamente entregada
        # - No hay disputas activas
        # - Cumple con políticas comerciales
        
        # Ejemplo de validaciones
        if order.status.value != "delivered":
            validation_result["eligible"] = False
            validation_result["reasons"].append("Order not delivered")
        
        # Agregar más validaciones según reglas de negocio
        
        return validation_result
    
    def _find_applicable_rule(self, commission_type: CommissionType, 
                            customer_type: str, service_type: str, 
                            amount: Decimal) -> CommissionRule:
        """Encuentra la regla de comisión aplicable"""
        
        for rule in self.commission_rules:
            if rule.is_applicable(amount, customer_type, service_type):
                if rule.commission_type == commission_type:
                    return rule
        
        return None
    
    def add_commission_rule(self, rule: CommissionRule) -> None:
        """Agrega una nueva regla de comisión"""
        self.commission_rules.append(rule)
    
    def get_active_rules(self) -> List[CommissionRule]:
        """Obtiene las reglas activas"""
        now = datetime.utcnow()
        return [rule for rule in self.commission_rules 
                if rule.is_active and rule.effective_from <= now and 
                (not rule.effective_until or rule.effective_until >= now)]