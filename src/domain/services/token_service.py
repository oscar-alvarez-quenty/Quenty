from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass

from src.domain.entities.token import CityToken, TokenDistribution, TokenHolder, TokenTransaction
from src.domain.entities.franchise import Franchise
from src.domain.value_objects.money import Money
from src.domain.events.token_events import (
    TokensIssued, TokensTransferred, UtilitiesDistributed,
    TokenHolderAdded, TokenValueUpdated
)


@dataclass
class TokenIssuanceRequest:
    city: str
    franchise_id: str
    total_supply: int
    initial_price: Money
    vesting_periods: List[Dict[str, Any]]  # Períodos de vesting
    utility_distribution_frequency: str  # "monthly", "quarterly"


@dataclass
class UtilityCalculation:
    period_start: datetime
    period_end: datetime
    total_revenue: Money
    operating_expenses: Money
    net_utilities: Money
    distribution_percentage: float  # % de utilidades a distribuir


@dataclass
class TokenPerformanceMetrics:
    token_id: str
    current_price: Money
    price_change_24h: float
    total_volume_24h: Money
    market_cap: Money
    holders_count: int
    avg_holding_period_days: float
    total_distributed_utilities: Money


class TokenService:
    def __init__(self):
        self.city_tokens: Dict[str, CityToken] = {}
        self.token_holders: Dict[str, List[TokenHolder]] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.utility_calculations: Dict[str, List[UtilityCalculation]] = {}
        self._domain_events: List = []

    def issue_city_tokens(
        self,
        issuance_request: TokenIssuanceRequest,
        franchise: Franchise
    ) -> CityToken:
        """Emitir tokens de ciudad para una franquicia"""
        if not franchise.is_active:
            raise ValueError("Solo franquicias activas pueden emitir tokens")
        
        # Validar que no existan tokens para esta ciudad/franquicia
        existing_token = next(
            (token for token in self.city_tokens.values() 
             if token.city == issuance_request.city and token.franchise_id == issuance_request.franchise_id),
            None
        )
        
        if existing_token:
            raise ValueError(f"Ya existen tokens para la ciudad {issuance_request.city}")
        
        # Crear token de ciudad
        token_id = f"QUENTY_{issuance_request.city.upper()}_{datetime.now().strftime('%Y%m%d')}"
        
        city_token = CityToken(
            token_id=token_id,
            city=issuance_request.city,
            franchise_id=issuance_request.franchise_id,
            total_supply=issuance_request.total_supply
        )
        
        # Configurar precio inicial
        city_token.current_price = issuance_request.initial_price
        
        # Crear holder inicial (franquicia)
        franchise_holder = TokenHolder(
            holder_id=f"franchise_{franchise.franchise_id}",
            token_id=token_id,
            tokens_owned=issuance_request.total_supply,  # Inicialmente la franquicia tiene todos
            purchase_date=datetime.now(),
            purchase_price=issuance_request.initial_price
        )
        
        city_token.add_holder(franchise_holder)
        
        # Guardar token
        self.city_tokens[token_id] = city_token
        self.token_holders[token_id] = [franchise_holder]
        self.price_history[token_id] = [{
            "date": datetime.now(),
            "price": issuance_request.initial_price.amount,
            "volume": 0
        }]
        
        self._add_domain_event(
            TokensIssued(
                token_id=token_id,
                city=issuance_request.city,
                franchise_id=issuance_request.franchise_id,
                total_supply=issuance_request.total_supply,
                initial_price=issuance_request.initial_price.amount,
                issued_at=datetime.now()
            )
        )
        
        return city_token

    def transfer_tokens(
        self,
        token_id: str,
        from_holder_id: str,
        to_holder_id: str,
        amount: int,
        transfer_price: Money,
        transfer_type: str = "sale"  # "sale", "gift", "utility_distribution"
    ) -> TokenTransaction:
        """Transferir tokens entre holders"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            raise ValueError(f"Token {token_id} no encontrado")
        
        # Validar que el holder origen tenga suficientes tokens
        from_holder = next(
            (h for h in city_token.holders if h.holder_id == from_holder_id),
            None
        )
        
        if not from_holder:
            raise ValueError(f"Holder {from_holder_id} no encontrado")
        
        if from_holder.tokens_owned < amount:
            raise ValueError("Tokens insuficientes para la transferencia")
        
        # Crear o actualizar holder destino
        to_holder = next(
            (h for h in city_token.holders if h.holder_id == to_holder_id),
            None
        )
        
        if not to_holder:
            to_holder = TokenHolder(
                holder_id=to_holder_id,
                token_id=token_id,
                tokens_owned=0,
                purchase_date=datetime.now(),
                purchase_price=transfer_price
            )
            city_token.add_holder(to_holder)
        
        # Crear transacción
        transaction = TokenTransaction(
            transaction_id=f"tx_{datetime.now().timestamp()}",
            token_id=token_id,
            from_holder_id=from_holder_id,
            to_holder_id=to_holder_id,
            amount=amount,
            price_per_token=transfer_price,
            transaction_type=transfer_type,
            timestamp=datetime.now()
        )
        
        # Ejecutar transferencia
        from_holder.tokens_owned -= amount
        to_holder.tokens_owned += amount
        
        # Registrar transacción
        city_token.add_transaction(transaction)
        
        # Actualizar precio del token si es una venta
        if transfer_type == "sale":
            city_token.current_price = transfer_price
            self._update_price_history(token_id, transfer_price, amount)
        
        self._add_domain_event(
            TokensTransferred(
                token_id=token_id,
                from_holder_id=from_holder_id,
                to_holder_id=to_holder_id,
                amount=amount,
                price_per_token=transfer_price.amount,
                transaction_type=transfer_type,
                transaction_id=transaction.transaction_id
            )
        )
        
        return transaction

    def calculate_monthly_utilities(
        self,
        franchise_id: str,
        period_start: datetime,
        period_end: datetime,
        total_revenue: Money,
        operating_expenses: Money,
        distribution_percentage: float = 0.3  # 30% de utilidades a distribuir
    ) -> UtilityCalculation:
        """Calcular utilidades mensuales para distribución"""
        net_utilities = Money(
            total_revenue.amount - operating_expenses.amount,
            total_revenue.currency
        )
        
        if net_utilities.amount <= 0:
            raise ValueError("No hay utilidades positivas para distribuir")
        
        calculation = UtilityCalculation(
            period_start=period_start,
            period_end=period_end,
            total_revenue=total_revenue,
            operating_expenses=operating_expenses,
            net_utilities=net_utilities,
            distribution_percentage=distribution_percentage
        )
        
        # Guardar cálculo
        if franchise_id not in self.utility_calculations:
            self.utility_calculations[franchise_id] = []
        
        self.utility_calculations[franchise_id].append(calculation)
        
        return calculation

    def distribute_utilities(
        self,
        token_id: str,
        utility_calculation: UtilityCalculation,
        distribution_id: str
    ) -> TokenDistribution:
        """Distribuir utilidades entre holders de tokens"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            raise ValueError(f"Token {token_id} no encontrado")
        
        # Calcular monto a distribuir
        distribution_amount = Money(
            utility_calculation.net_utilities.amount * utility_calculation.distribution_percentage,
            utility_calculation.net_utilities.currency
        )
        
        # Crear distribución
        distribution = TokenDistribution(
            distribution_id=distribution_id,
            token_id=token_id,
            total_amount=distribution_amount,
            distribution_date=datetime.now(),
            distribution_type="monthly_utilities"
        )
        
        # Calcular distribución proporcional
        total_tokens = sum(holder.tokens_owned for holder in city_token.holders)
        
        if total_tokens == 0:
            raise ValueError("No hay tokens en circulación")
        
        for holder in city_token.holders:
            if holder.tokens_owned > 0:
                holder_percentage = holder.tokens_owned / total_tokens
                holder_amount = Money(
                    distribution_amount.amount * holder_percentage,
                    distribution_amount.currency
                )
                
                distribution.add_recipient(holder.holder_id, holder_amount)
                
                # Crear transacción de distribución
                distribution_transaction = TokenTransaction(
                    transaction_id=f"dist_{distribution_id}_{holder.holder_id}",
                    token_id=token_id,
                    from_holder_id="system",
                    to_holder_id=holder.holder_id,
                    amount=0,  # No es transferencia de tokens, sino de utilidades
                    price_per_token=Money(0, distribution_amount.currency),
                    transaction_type="utility_distribution",
                    timestamp=datetime.now(),
                    metadata={"utility_amount": holder_amount.amount}
                )
                
                city_token.add_transaction(distribution_transaction)
        
        # Agregar distribución al token
        city_token.add_distribution(distribution)
        
        self._add_domain_event(
            UtilitiesDistributed(
                token_id=token_id,
                distribution_id=distribution_id,
                total_amount=distribution_amount.amount,
                recipients_count=len(distribution.recipients),
                distribution_date=datetime.now(),
                period_start=utility_calculation.period_start,
                period_end=utility_calculation.period_end
            )
        )
        
        return distribution

    def add_token_holder(
        self,
        token_id: str,
        holder_id: str,
        initial_tokens: int,
        purchase_price: Money
    ) -> TokenHolder:
        """Agregar nuevo holder de tokens"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            raise ValueError(f"Token {token_id} no encontrado")
        
        # Verificar que no existe el holder
        existing_holder = next(
            (h for h in city_token.holders if h.holder_id == holder_id),
            None
        )
        
        if existing_holder:
            raise ValueError(f"Holder {holder_id} ya existe")
        
        # Crear nuevo holder
        holder = TokenHolder(
            holder_id=holder_id,
            token_id=token_id,
            tokens_owned=initial_tokens,
            purchase_date=datetime.now(),
            purchase_price=purchase_price
        )
        
        city_token.add_holder(holder)
        
        self._add_domain_event(
            TokenHolderAdded(
                token_id=token_id,
                holder_id=holder_id,
                initial_tokens=initial_tokens,
                purchase_price=purchase_price.amount,
                added_at=datetime.now()
            )
        )
        
        return holder

    def update_token_price(
        self,
        token_id: str,
        new_price: Money,
        updated_by: str,
        reason: str
    ) -> None:
        """Actualizar precio del token manualmente"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            raise ValueError(f"Token {token_id} no encontrado")
        
        old_price = city_token.current_price
        city_token.current_price = new_price
        
        # Registrar en historial
        self._update_price_history(token_id, new_price, 0)
        
        self._add_domain_event(
            TokenValueUpdated(
                token_id=token_id,
                old_price=old_price.amount if old_price else 0,
                new_price=new_price.amount,
                updated_by=updated_by,
                reason=reason,
                updated_at=datetime.now()
            )
        )

    def get_token_performance(self, token_id: str) -> TokenPerformanceMetrics:
        """Obtener métricas de rendimiento del token"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            raise ValueError(f"Token {token_id} no encontrado")
        
        # Calcular cambio de precio 24h
        price_change_24h = self._calculate_price_change_24h(token_id)
        
        # Calcular volumen 24h
        volume_24h = self._calculate_volume_24h(token_id)
        
        # Calcular market cap
        market_cap = Money(
            city_token.current_price.amount * city_token.total_supply,
            city_token.current_price.currency
        )
        
        # Calcular período promedio de tenencia
        avg_holding_period = self._calculate_avg_holding_period(token_id)
        
        # Calcular total distribuido
        total_distributed = Money(0, city_token.current_price.currency)
        for distribution in city_token.distributions:
            total_distributed = Money(
                total_distributed.amount + distribution.total_amount.amount,
                total_distributed.currency
            )
        
        return TokenPerformanceMetrics(
            token_id=token_id,
            current_price=city_token.current_price,
            price_change_24h=price_change_24h,
            total_volume_24h=volume_24h,
            market_cap=market_cap,
            holders_count=len(city_token.holders),
            avg_holding_period_days=avg_holding_period,
            total_distributed_utilities=total_distributed
        )

    def get_holder_portfolio(self, holder_id: str) -> Dict[str, Any]:
        """Obtener portafolio de un holder"""
        holder_tokens = []
        total_value = Money(0, "COP")
        
        for token_id, city_token in self.city_tokens.items():
            holder = next(
                (h for h in city_token.holders if h.holder_id == holder_id),
                None
            )
            
            if holder and holder.tokens_owned > 0:
                token_value = Money(
                    holder.tokens_owned * city_token.current_price.amount,
                    city_token.current_price.currency
                )
                
                # Calcular utilidades recibidas
                received_utilities = Money(0, city_token.current_price.currency)
                for distribution in city_token.distributions:
                    if holder_id in distribution.recipients:
                        received_utilities = Money(
                            received_utilities.amount + distribution.recipients[holder_id].amount,
                            received_utilities.currency
                        )
                
                holder_tokens.append({
                    "token_id": token_id,
                    "city": city_token.city,
                    "tokens_owned": holder.tokens_owned,
                    "current_value": token_value,
                    "purchase_price": holder.purchase_price,
                    "purchase_date": holder.purchase_date,
                    "received_utilities": received_utilities,
                    "roi_percentage": self._calculate_roi(holder, city_token, received_utilities)
                })
                
                total_value = Money(
                    total_value.amount + token_value.amount,
                    total_value.currency
                )
        
        return {
            "holder_id": holder_id,
            "total_portfolio_value": total_value,
            "tokens_count": len(holder_tokens),
            "tokens": holder_tokens,
            "total_received_utilities": sum(
                token["received_utilities"].amount for token in holder_tokens
            )
        }

    def _update_price_history(self, token_id: str, price: Money, volume: int) -> None:
        """Actualizar historial de precios"""
        if token_id not in self.price_history:
            self.price_history[token_id] = []
        
        self.price_history[token_id].append({
            "date": datetime.now(),
            "price": price.amount,
            "volume": volume
        })
        
        # Mantener solo últimos 365 días
        cutoff_date = datetime.now() - timedelta(days=365)
        self.price_history[token_id] = [
            entry for entry in self.price_history[token_id]
            if entry["date"] >= cutoff_date
        ]

    def _calculate_price_change_24h(self, token_id: str) -> float:
        """Calcular cambio de precio en 24h"""
        history = self.price_history.get(token_id, [])
        if len(history) < 2:
            return 0.0
        
        current_price = history[-1]["price"]
        price_24h_ago = history[-2]["price"] if len(history) >= 2 else current_price
        
        if price_24h_ago == 0:
            return 0.0
        
        return ((current_price - price_24h_ago) / price_24h_ago) * 100

    def _calculate_volume_24h(self, token_id: str) -> Money:
        """Calcular volumen de transacciones en 24h"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            return Money(0, "COP")
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        volume = 0
        
        for transaction in city_token.transactions:
            if (transaction.timestamp >= cutoff_time and 
                transaction.transaction_type == "sale"):
                volume += transaction.amount * transaction.price_per_token.amount
        
        return Money(volume, city_token.current_price.currency)

    def _calculate_avg_holding_period(self, token_id: str) -> float:
        """Calcular período promedio de tenencia en días"""
        city_token = self.city_tokens.get(token_id)
        if not city_token:
            return 0.0
        
        total_days = 0
        holders_count = 0
        
        for holder in city_token.holders:
            if holder.tokens_owned > 0:
                holding_days = (datetime.now() - holder.purchase_date).days
                total_days += holding_days
                holders_count += 1
        
        return total_days / holders_count if holders_count > 0 else 0.0

    def _calculate_roi(
        self, 
        holder: TokenHolder, 
        city_token: CityToken, 
        received_utilities: Money
    ) -> float:
        """Calcular ROI del holder"""
        initial_investment = holder.tokens_owned * holder.purchase_price.amount
        current_value = holder.tokens_owned * city_token.current_price.amount
        total_return = current_value + received_utilities.amount
        
        if initial_investment == 0:
            return 0.0
        
        return ((total_return - initial_investment) / initial_investment) * 100

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()