from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.events.base_event import DomainEvent


@dataclass
class TokensIssued(DomainEvent):
    token_id: str
    city: str
    franchise_id: str
    total_supply: int
    initial_price: float
    issued_at: datetime


@dataclass
class TokensTransferred(DomainEvent):
    token_id: str
    from_holder_id: str
    to_holder_id: str
    amount: int
    price_per_token: float
    transaction_type: str
    transaction_id: str


@dataclass
class UtilitiesDistributed(DomainEvent):
    token_id: str
    distribution_id: str
    total_amount: float
    recipients_count: int
    distribution_date: datetime
    period_start: datetime
    period_end: datetime


@dataclass
class TokenHolderAdded(DomainEvent):
    token_id: str
    holder_id: str
    initial_tokens: int
    purchase_price: float
    added_at: datetime


@dataclass
class TokenValueUpdated(DomainEvent):
    token_id: str
    old_price: float
    new_price: float
    updated_by: str
    reason: str
    updated_at: datetime


@dataclass
class TokenBurned(DomainEvent):
    token_id: str
    holder_id: str
    amount_burned: int
    burn_reason: str
    burned_at: datetime


@dataclass
class TokenMinted(DomainEvent):
    token_id: str
    amount_minted: int
    mint_reason: str
    minted_to: str
    minted_at: datetime


@dataclass
class TokenTradingStarted(DomainEvent):
    token_id: str
    exchange_name: str
    initial_trading_price: float
    trading_started_at: datetime


@dataclass
class TokenTradingSuspended(DomainEvent):
    token_id: str
    suspension_reason: str
    suspended_by: str
    suspended_at: datetime


@dataclass
class TokenVestingScheduleCreated(DomainEvent):
    token_id: str
    holder_id: str
    vesting_schedule_id: str
    total_tokens: int
    vesting_periods: list
    created_at: datetime


@dataclass
class TokensVested(DomainEvent):
    token_id: str
    holder_id: str
    vesting_schedule_id: str
    vested_amount: int
    vesting_date: datetime


@dataclass
class TokenStakingStarted(DomainEvent):
    token_id: str
    holder_id: str
    staked_amount: int
    staking_period_days: int
    expected_rewards: float
    staked_at: datetime


@dataclass
class TokenStakingRewardsClaimed(DomainEvent):
    token_id: str
    holder_id: str
    rewards_amount: float
    staking_period_completed: bool
    claimed_at: datetime


@dataclass
class TokenGovernanceProposalCreated(DomainEvent):
    token_id: str
    proposal_id: str
    proposer_id: str
    proposal_title: str
    proposal_description: str
    voting_start: datetime
    voting_end: datetime


@dataclass
class TokenGovernanceVoteCasted(DomainEvent):
    token_id: str
    proposal_id: str
    voter_id: str
    vote_weight: int
    vote_choice: str  # "yes", "no", "abstain"
    voted_at: datetime


@dataclass
class TokenGovernanceProposalExecuted(DomainEvent):
    token_id: str
    proposal_id: str
    execution_result: str
    executed_at: datetime
    executed_by: str


@dataclass
class TokenMetricsUpdated(DomainEvent):
    token_id: str
    market_cap: float
    trading_volume_24h: float
    price_change_24h: float
    holders_count: int
    updated_at: datetime


@dataclass
class TokenSmartContractDeployed(DomainEvent):
    token_id: str
    contract_address: str
    blockchain_network: str
    deployed_by: str
    deployed_at: datetime


@dataclass
class TokenAuditCompleted(DomainEvent):
    token_id: str
    audit_id: str
    auditor_name: str
    audit_score: float
    findings: list
    completed_at: datetime