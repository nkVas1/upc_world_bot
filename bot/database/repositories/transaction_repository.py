"""Transaction repository."""
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Transaction


class TransactionRepository:
    """Repository for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[Transaction]:
        """Get user's transaction history."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_transactions_by_type(
        self,
        user_id: int,
        transaction_type: str,
        limit: int = 50
    ) -> list[Transaction]:
        """Get transactions by type."""
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.type == transaction_type
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_user_total_earned(self, user_id: int) -> Decimal:
        """Get total earned by user."""
        result = await self.session.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == user_id,
                Transaction.amount > 0
            )
        )
        total = result.scalar()
        return Decimal(total) if total else Decimal(0)
    
    async def get_user_total_spent(self, user_id: int) -> Decimal:
        """Get total spent by user."""
        result = await self.session.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == user_id,
                Transaction.amount < 0
            )
        )
        total = result.scalar()
        return abs(Decimal(total)) if total else Decimal(0)
    
    async def get_recent_transactions(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> list[Transaction]:
        """Get recent transactions."""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.created_at >= since)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
