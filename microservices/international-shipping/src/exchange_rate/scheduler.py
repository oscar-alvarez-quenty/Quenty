"""
Exchange Rate Scheduler
Handles daily TRM fetching and automated updates
"""

import asyncio
from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

from .banrep import ExchangeRateService, ExchangeRate
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


class ExchangeRateScheduler:
    """Scheduler for automated exchange rate fetching"""
    
    def __init__(self, exchange_service: ExchangeRateService):
        self.exchange_service = exchange_service
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.update_time = time(9, 0)  # 9:00 AM daily update
        
    async def start(self):
        """Start the exchange rate scheduler"""
        if self._running:
            logger.warning("Exchange rate scheduler is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Exchange rate scheduler started")
    
    async def stop(self):
        """Stop the exchange rate scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Exchange rate scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                now = datetime.now()
                target_time = datetime.combine(date.today(), self.update_time)
                
                # If we've passed today's update time, schedule for tomorrow
                if now > target_time:
                    target_time = datetime.combine(date.today() + timedelta(days=1), self.update_time)
                
                # Calculate sleep time until next update
                sleep_seconds = (target_time - now).total_seconds()
                
                logger.info(f"Next TRM update scheduled for {target_time}")
                await asyncio.sleep(sleep_seconds)
                
                if self._running:  # Check if still running after sleep
                    await self._perform_daily_update()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Sleep for 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    async def _perform_daily_update(self):
        """Perform daily TRM update"""
        try:
            logger.info("Starting daily TRM update")
            
            # Get current TRM
            current_rate = await self.exchange_service.banrep_client.get_current_trm()
            
            if current_rate:
                # Store in database
                success = await self._store_exchange_rate(current_rate)
                
                if success:
                    logger.info(f"Daily TRM update successful: {current_rate.rate} COP/USD for {current_rate.date}")
                    
                    # Optionally fetch missing historical data
                    await self._fetch_missing_rates()
                else:
                    logger.error("Failed to store TRM in database")
            else:
                logger.error("Failed to fetch current TRM")
                
        except Exception as e:
            logger.error(f"Error in daily TRM update: {e}")
    
    async def _store_exchange_rate(self, rate: ExchangeRate) -> bool:
        """
        Store exchange rate in database
        
        Args:
            rate: ExchangeRate object to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with get_db() as db:
                # Use PostgreSQL UPSERT to handle duplicates
                stmt = pg_insert(ExchangeRateModel).values(
                    currency_from=rate.currency_from,
                    currency_to=rate.currency_to,
                    rate=rate.rate,
                    date=rate.date,
                    source=rate.source,
                    created_at=rate.created_at,
                    updated_at=datetime.utcnow()
                )
                
                # On conflict, update the rate and timestamp
                stmt = stmt.on_conflict_do_update(
                    index_elements=['currency_from', 'currency_to', 'date'],
                    set_=dict(
                        rate=stmt.excluded.rate,
                        source=stmt.excluded.source,
                        updated_at=datetime.utcnow()
                    )
                )
                
                await db.execute(stmt)
                await db.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing exchange rate: {e}")
            return False
    
    async def _fetch_missing_rates(self):
        """Fetch any missing exchange rates from the last 30 days"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            logger.info(f"Checking for missing TRM data from {start_date} to {end_date}")
            
            async with get_db() as db:
                # Find dates with missing data
                result = await db.execute(
                    select(ExchangeRateModel.date)
                    .where(
                        ExchangeRateModel.currency_from == "USD",
                        ExchangeRateModel.currency_to == "COP",
                        ExchangeRateModel.date >= start_date,
                        ExchangeRateModel.date <= end_date
                    )
                )
                
                existing_dates = {row.date for row in result.fetchall()}
                
                # Generate all business days in range
                all_dates = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                        all_dates.append(current_date)
                    current_date += timedelta(days=1)
                
                missing_dates = [d for d in all_dates if d not in existing_dates]
                
                if missing_dates:
                    logger.info(f"Found {len(missing_dates)} missing TRM dates, fetching...")
                    
                    # Fetch missing rates (with rate limiting)
                    for missing_date in missing_dates:
                        try:
                            rate = await self.exchange_service.banrep_client.get_trm_for_date(missing_date)
                            if rate:
                                await self._store_exchange_rate(rate)
                                logger.debug(f"Fetched missing TRM for {missing_date}: {rate.rate}")
                            
                            # Rate limiting - don't overwhelm the API
                            await asyncio.sleep(0.5)
                            
                        except Exception as e:
                            logger.error(f"Error fetching missing rate for {missing_date}: {e}")
                
                else:
                    logger.info("No missing TRM data found")
                    
        except Exception as e:
            logger.error(f"Error fetching missing rates: {e}")
    
    async def manual_update(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Manually trigger exchange rate update
        
        Args:
            target_date: Specific date to update, defaults to today
            
        Returns:
            Update result dictionary
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            logger.info(f"Manual TRM update requested for {target_date}")
            
            rate = await self.exchange_service.banrep_client.get_trm_for_date(target_date)
            
            if rate:
                success = await self._store_exchange_rate(rate)
                
                return {
                    "success": success,
                    "date": target_date.isoformat(),
                    "rate": rate.rate,
                    "source": rate.source,
                    "message": f"TRM updated: {rate.rate} COP/USD" if success else "Failed to store TRM"
                }
            else:
                return {
                    "success": False,
                    "date": target_date.isoformat(),
                    "message": "Failed to fetch TRM from Banco de la República"
                }
                
        except Exception as e:
            logger.error(f"Error in manual update: {e}")
            return {
                "success": False,
                "date": target_date.isoformat() if target_date else None,
                "error": str(e),
                "message": "Manual update failed"
            }


# Database model for storing exchange rates
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint
from ..models import Base


class ExchangeRateModel(Base):
    """Database model for exchange rates"""
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    currency_from = Column(String(3), nullable=False, index=True)
    currency_to = Column(String(3), nullable=False, index=True)
    rate = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True)
    source = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique combination of currencies and date
    __table_args__ = (
        UniqueConstraint('currency_from', 'currency_to', 'date', name='uq_exchange_rate_date'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.currency_from}/{self.currency_to}: {self.rate} on {self.date})>"


# Global scheduler instance
_scheduler: Optional[ExchangeRateScheduler] = None


async def get_scheduler() -> ExchangeRateScheduler:
    """Get or create exchange rate scheduler instance"""
    global _scheduler
    if _scheduler is None:
        exchange_service = ExchangeRateService()
        _scheduler = ExchangeRateScheduler(exchange_service)
    return _scheduler


@asynccontextmanager
async def lifespan_scheduler():
    """Context manager for scheduler lifecycle"""
    scheduler = await get_scheduler()
    try:
        await scheduler.start()
        yield scheduler
    finally:
        await scheduler.stop()