"""User repository with business logic."""
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import User, Transaction
from bot.utils.logger import logger


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID with referrals loaded."""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.referrals))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        # CRITICAL FIX: Ensure referrals is never None
        if user and user.referrals is None:
            user.referrals = []
        
        return user
    
    async def get_by_referral_code(self, code: str) -> Optional[User]:
        """Get user by referral code."""
        result = await self.session.execute(
            select(User).where(User.referral_code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_website_id(self, website_user_id: int) -> Optional[User]:
        """Get user by website user ID."""
        result = await self.session.execute(
            select(User).where(User.website_user_id == website_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: dict) -> User:
        """Create new user."""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        
        logger.info("user_created", user_id=user.id, username=user.username)
        return user
    
    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs, updated_at=datetime.utcnow())
        )
        return await self.get_by_id(user_id)
    
    async def add_coins(
        self,
        user_id: int,
        amount: Decimal,
        transaction_type: str,
        description: str,
        metadata: Optional[dict] = None
    ) -> tuple[User, Transaction]:
        """Add UP Coins to user balance with transaction record."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        user.up_coins += amount
        user.total_earned += amount
        
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            balance_after=user.up_coins,
            description=description,
            extra_metadata=metadata or {}
        )
        self.session.add(transaction)
        await self.session.flush()
        
        logger.info(
            "coins_added",
            user_id=user_id,
            amount=float(amount),
            new_balance=float(user.up_coins)
        )
        
        return user, transaction
    
    async def deduct_coins(
        self,
        user_id: int,
        amount: Decimal,
        transaction_type: str,
        description: str,
        metadata: Optional[dict] = None
    ) -> tuple[User, Transaction]:
        """Deduct UP Coins from user balance."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if user.up_coins < amount:
            raise ValueError("Insufficient balance")
        
        user.up_coins -= amount
        user.total_spent += amount
        
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            amount=-amount,
            balance_after=user.up_coins,
            description=description,
            extra_metadata=metadata or {}
        )
        self.session.add(transaction)
        await self.session.flush()
        
        logger.info(
            "coins_deducted",
            user_id=user_id,
            amount=float(amount),
            new_balance=float(user.up_coins)
        )
        
        return user, transaction
    
    async def claim_daily_bonus(self, user_id: int) -> tuple[bool, Optional[Decimal]]:
        """Claim daily bonus and update streak."""
        user = await self.get_by_id(user_id)
        if not user:
            return False, None
        
        now = datetime.utcnow()
        
        # Check if already claimed today
        if user.last_daily_claim:
            time_since_claim = now - user.last_daily_claim
            if time_since_claim < timedelta(hours=20):
                return False, None
        
        # Update streak
        if user.last_daily_claim:
            time_diff = now - user.last_daily_claim
            if time_diff < timedelta(hours=48):
                user.daily_streak += 1
            else:
                user.daily_streak = 1
        else:
            user.daily_streak = 1
        
        # Calculate bonus based on streak
        base_bonus = Decimal("10")
        streak_bonus = Decimal(min(user.daily_streak, 7)) * Decimal("5")
        total_bonus = base_bonus + streak_bonus
        
        user.last_daily_claim = now
        await self.add_coins(
            user_id,
            total_bonus,
            "daily_bonus",
            f"Daily bonus (Streak: {user.daily_streak})",
            {"streak": user.daily_streak}
        )
        
        return True, total_bonus
    
    async def increment_referral_count(self, user_id: int) -> User:
        """Increment referral count."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(referral_count=User.referral_count + 1)
        )
        return await self.get_by_id(user_id)
    
    async def get_top_referrers(self, limit: int = 10) -> list[User]:
        """Get top users by referral count."""
        result = await self.session.execute(
            select(User)
            .where(User.referral_count > 0)
            .order_by(User.referral_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_statistics(self) -> dict:
        """Get overall user statistics."""
        total_users = await self.session.scalar(select(func.count(User.id)))
        total_members = await self.session.scalar(
            select(func.count(User.id)).where(User.is_member == True)
        )
        active_users = await self.session.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        
        return {
            "total_users": total_users,
            "total_members": total_members,
            "active_users": active_users,
        }
