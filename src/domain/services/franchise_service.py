from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from src.domain.entities.franchise import Franchise, FranchiseStatus, LogisticZone, LogisticPoint
from src.domain.entities.token import CityToken, TokenHolder, UtilityDistribution
from src.domain.entities.commission import Commission, CommissionType
from src.domain.value_objects.customer_id import CustomerId
from src.domain.exceptions.base_exceptions import BusinessRuleViolationException, FranchiseException
from uuid import UUID

class FranchiseService:
    """Servicio de dominio para gestión de franquicias"""
    
    def __init__(self):
        self.minimum_investment = Decimal('5000000')  # 5M COP
        self.franchise_fee_percentage = Decimal('0.15')  # 15%
        self.monthly_fee_base = Decimal('500000')  # 500K COP
    
    def evaluate_franchise_application(self, franchisee_id: CustomerId, 
                                     investment_amount: Decimal,
                                     business_plan: Dict[str, Any],
                                     zone_id: UUID) -> Dict[str, Any]:
        """Evalúa una solicitud de franquicia"""
        
        evaluation_result = {
            "approved": False,
            "score": 0,
            "requirements_met": [],
            "requirements_missing": [],
            "recommendations": []
        }
        
        score = 0
        
        # Criterio 1: Inversión mínima (30 puntos)
        if investment_amount >= self.minimum_investment:
            score += 30
            evaluation_result["requirements_met"].append("Minimum investment requirement")
        else:
            evaluation_result["requirements_missing"].append(
                f"Investment below minimum: {investment_amount} < {self.minimum_investment}"
            )
        
        # Criterio 2: Experiencia en logística (25 puntos)
        logistics_experience = business_plan.get("logistics_experience_years", 0)
        if logistics_experience >= 2:
            score += 25
        elif logistics_experience >= 1:
            score += 15
        else:
            evaluation_result["recommendations"].append("Consider gaining logistics experience")
        
        # Criterio 3: Plan de negocio (25 puntos)
        business_plan_score = self._evaluate_business_plan(business_plan)
        score += business_plan_score
        
        if business_plan_score < 15:
            evaluation_result["recommendations"].append("Improve business plan completeness")
        
        # Criterio 4: Disponibilidad de zona (20 puntos)
        zone_available = self._is_zone_available(zone_id)
        if zone_available:
            score += 20
            evaluation_result["requirements_met"].append("Zone available for franchise")
        else:
            evaluation_result["requirements_missing"].append("Requested zone not available")
        
        evaluation_result["score"] = score
        evaluation_result["approved"] = score >= 70  # 70% mínimo para aprobación
        
        return evaluation_result
    
    def create_franchise(self, franchisee_id: CustomerId, zone_id: UUID,
                        business_name: str, investment_amount: Decimal) -> Franchise:
        """Crea una nueva franquicia"""
        
        # Validar que la zona esté disponible
        if not self._is_zone_available(zone_id):
            raise FranchiseException(
                franchise_id="",
                operation="create",
                error_message="Zone not available for franchise"
            )
        
        # Validar inversión mínima
        if investment_amount < self.minimum_investment:
            raise BusinessRuleViolationException(
                f"Investment amount {investment_amount} below minimum {self.minimum_investment}",
                "INSUFFICIENT_INVESTMENT"
            )
        
        # Calcular cuotas
        franchise_fee = investment_amount * self.franchise_fee_percentage
        monthly_fee = self._calculate_monthly_fee(zone_id)
        
        franchise = Franchise(
            franchisee_id=franchisee_id,
            zone_id=zone_id,
            business_name=business_name,
            investment_amount=investment_amount,
            franchise_fee=franchise_fee,
            monthly_fee=monthly_fee,
            status=FranchiseStatus.PENDING
        )
        
        return franchise
    
    def approve_franchise(self, franchise: Franchise, contract_months: int = 24) -> None:
        """Aprueba una franquicia"""
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=contract_months * 30)
        
        franchise.approve_franchise(start_date, end_date)
        
        # Calcular asignación inicial de tokens
        token_allocation = self._calculate_initial_token_allocation(franchise.investment_amount)
        franchise.token_allocation = token_allocation
    
    def calculate_franchise_performance(self, franchise: Franchise, 
                                      monthly_revenue: Decimal,
                                      shipment_count: int,
                                      customer_satisfaction: Decimal) -> Dict[str, Any]:
        """Calcula el rendimiento de una franquicia"""
        
        performance = {
            "revenue_score": 0,
            "volume_score": 0,
            "satisfaction_score": 0,
            "overall_score": 0,
            "performance_level": "Poor"
        }
        
        # Score por ingresos (40%)
        revenue_target = Decimal('10000000')  # 10M COP mensual
        revenue_ratio = min(monthly_revenue / revenue_target, Decimal('1.5'))
        performance["revenue_score"] = int(revenue_ratio * 40)
        
        # Score por volumen (35%)
        volume_target = 500  # 500 envíos mensuales
        volume_ratio = min(shipment_count / volume_target, 1.5)
        performance["volume_score"] = int(volume_ratio * 35)
        
        # Score por satisfacción (25%)
        satisfaction_ratio = min(customer_satisfaction / Decimal('5.0'), Decimal('1.0'))
        performance["satisfaction_score"] = int(satisfaction_ratio * 25)
        
        # Score total
        total_score = (performance["revenue_score"] + 
                      performance["volume_score"] + 
                      performance["satisfaction_score"])
        performance["overall_score"] = total_score
        
        # Nivel de rendimiento
        if total_score >= 90:
            performance["performance_level"] = "Excellent"
        elif total_score >= 75:
            performance["performance_level"] = "Good"
        elif total_score >= 60:
            performance["performance_level"] = "Average"
        elif total_score >= 40:
            performance["performance_level"] = "Below Average"
        else:
            performance["performance_level"] = "Poor"
        
        return performance
    
    def calculate_monthly_franchise_fee(self, franchise: Franchise, 
                                      gross_revenue: Decimal) -> Decimal:
        """Calcula la cuota mensual de franquicia"""
        
        # Cuota base + porcentaje de ingresos
        percentage_fee = gross_revenue * franchise.commission_rate
        total_fee = franchise.monthly_fee + percentage_fee
        
        return total_fee
    
    def process_token_distribution(self, franchise: Franchise, 
                                 city_token: CityToken,
                                 monthly_utilities: Decimal) -> UtilityDistribution:
        """Procesa la distribución de utilidades en tokens"""
        
        if not franchise.can_allocate_tokens():
            raise FranchiseException(
                franchise_id=str(franchise.id),
                operation="token_distribution",
                error_message="Franchise not eligible for token distribution"
            )
        
        # Crear distribución
        distribution = UtilityDistribution(
            city_token_id=city_token.id,
            period=datetime.utcnow().strftime("%Y-%m"),
            total_utility_amount=monthly_utilities
        )
        
        # Calcular distribución para esta franquicia
        franchise_tokens = franchise.token_allocation
        total_participating_tokens = city_token.circulating_supply
        
        if total_participating_tokens > 0:
            distribution.calculate_distribution_rate(total_participating_tokens)
            distribution.add_holder_distribution(franchise.id, franchise_tokens)
        
        return distribution
    
    def create_logistic_point(self, franchise: Franchise, point_data: Dict[str, Any]) -> LogisticPoint:
        """Crea un punto logístico para la franquicia"""
        
        if franchise.status != FranchiseStatus.ACTIVE:
            raise FranchiseException(
                franchise_id=str(franchise.id),
                operation="create_logistic_point",
                error_message="Only active franchises can create logistic points"
            )
        
        point = LogisticPoint(
            name=point_data["name"],
            address=point_data["address"],
            city=point_data["city"],
            phone=point_data["phone"],
            email=point_data["email"],
            zone_id=franchise.zone_id,
            operating_hours=point_data.get("operating_hours", "8:00-18:00")
        )
        
        return point
    
    def evaluate_franchise_renewal(self, franchise: Franchise, 
                                 performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evalúa la renovación de una franquicia"""
        
        renewal_evaluation = {
            "eligible": False,
            "renewal_terms": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        if not performance_history:
            renewal_evaluation["recommendations"].append("No performance history available")
            return renewal_evaluation
        
        # Calcular promedios de rendimiento
        avg_revenue_score = sum(p["revenue_score"] for p in performance_history) / len(performance_history)
        avg_volume_score = sum(p["volume_score"] for p in performance_history) / len(performance_history)
        avg_satisfaction_score = sum(p["satisfaction_score"] for p in performance_history) / len(performance_history)
        avg_overall_score = (avg_revenue_score + avg_volume_score + avg_satisfaction_score)
        
        renewal_evaluation["performance_summary"] = {
            "average_revenue_score": avg_revenue_score,
            "average_volume_score": avg_volume_score,
            "average_satisfaction_score": avg_satisfaction_score,
            "average_overall_score": avg_overall_score
        }
        
        # Criterios de renovación
        if avg_overall_score >= 70:
            renewal_evaluation["eligible"] = True
            
            # Términos mejorados para buen rendimiento
            if avg_overall_score >= 85:
                renewal_evaluation["renewal_terms"] = {
                    "commission_rate": franchise.commission_rate * Decimal('0.95'),  # 5% descuento
                    "contract_months": 36,
                    "additional_benefits": ["Priority support", "Marketing assistance"]
                }
            else:
                renewal_evaluation["renewal_terms"] = {
                    "commission_rate": franchise.commission_rate,
                    "contract_months": 24,
                    "additional_benefits": []
                }
        else:
            renewal_evaluation["recommendations"].append("Improve performance before renewal")
            if avg_revenue_score < 30:
                renewal_evaluation["recommendations"].append("Focus on revenue generation")
            if avg_volume_score < 30:
                renewal_evaluation["recommendations"].append("Increase shipment volume")
            if avg_satisfaction_score < 20:
                renewal_evaluation["recommendations"].append("Improve customer satisfaction")
        
        return renewal_evaluation
    
    def _evaluate_business_plan(self, business_plan: Dict[str, Any]) -> int:
        """Evalúa la calidad del plan de negocio"""
        
        score = 0
        required_sections = [
            "market_analysis", "financial_projections", "marketing_strategy",
            "operational_plan", "logistics_experience", "target_customers"
        ]
        
        # 4 puntos por cada sección completa
        for section in required_sections:
            if section in business_plan and business_plan[section]:
                score += 4
        
        # Punto extra por proyecciones realistas
        if "financial_projections" in business_plan:
            projections = business_plan["financial_projections"]
            if (isinstance(projections, dict) and 
                "monthly_revenue" in projections and
                projections["monthly_revenue"] > 0):
                score += 1
        
        return min(score, 25)  # Máximo 25 puntos
    
    def _is_zone_available(self, zone_id: UUID) -> bool:
        """Verifica si una zona está disponible para franquicia"""
        # En una implementación real, esto consultaría la base de datos
        # Por ahora simulamos que está disponible
        return True
    
    def _calculate_monthly_fee(self, zone_id: UUID) -> Decimal:
        """Calcula la cuota mensual base según la zona"""
        # En una implementación real, esto variaría según la zona
        return self.monthly_fee_base
    
    def _calculate_initial_token_allocation(self, investment_amount: Decimal) -> Decimal:
        """Calcula la asignación inicial de tokens según la inversión"""
        # 1 token por cada 10,000 COP de inversión
        return investment_amount / Decimal('10000')