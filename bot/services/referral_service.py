"""Referral system service."""
import string
import random
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.user_repository import UserRepository
from bot.database.models import User
from bot.utils.logger import logger


class ReferralService:
    """Manages referral system logic."""
    
    # Referral rewards configuration
    REFERRAL_REWARDS = {
        1: {"coins": Decimal("50"), "description": "First referral bonus"},
        3: {"coins": Decimal("100"), "discount": 0.30, "description": "3 referrals - 30% discount"},
        5: {"coins": Decimal("200"), "discount": 0.50, "vip_cocktail": True, "description": "5 referrals - 50% discount + VIP cocktail"},
        8: {"free_vip_ticket": True, "description": "8 referrals - Free VIP ticket"},
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
    
    @staticmethod
    def generate_referral_code(length: int = 8) -> str:
        """Generate unique referral code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))
    
    async def create_referral_code(self, user_id: int) -> str:
        """Create unique referral code for user."""
        # Try up to 10 times to generate unique code
        for _ in range(10):
            code = self.generate_referral_code()
            existing = await self.user_repo.get_by_referral_code(code)
            if not existing:
                await self.user_repo.update(user_id, referral_code=code)
                logger.info("referral_code_created", user_id=user_id, code=code)
                return code
        
        # Fallback to user_id based code
        code = f"UP{user_id}"
        await self.user_repo.update(user_id, referral_code=code)
        return code
    
    async def process_referral(
        self,
        referred_user_id: int,
        referral_code: str
    ) -> tuple[bool, Optional[str]]:
        """Process new user registration with referral code."""
        # Get referrer
        referrer = await self.user_repo.get_by_referral_code(referral_code)
        if not referrer:
            return False, "Invalid referral code"
        
        if referrer.id == referred_user_id:
            return False, "Cannot use your own referral code"
        
        # Check if user already has a referrer
        referred_user = await self.user_repo.get_by_id(referred_user_id)
        if referred_user and referred_user.referred_by_id:
            return False, "You already used a referral code"
        
        # Update referred user
        await self.user_repo.update(
            referred_user_id,
            referred_by_id=referrer.id
        )
        
        # Increment referrer's count
        await self.user_repo.increment_referral_count(referrer.id)
        
        # Give bonus to referrer
        new_count = referrer.referral_count + 1
        reward = self._calculate_referral_reward(new_count)
        
        if reward:
            await self.user_repo.add_coins(
                referrer.id,
                reward["coins"],
                "referral",
                f"Referral bonus for {new_count} referrals",
                {"referred_user_id": referred_user_id, "referral_count": new_count}
            )
        
        # Give welcome bonus to new user
        await self.user_repo.add_coins(
            referred_user_id,
            Decimal("25"),
            "referral_welcome",
            "Welcome bonus for using referral code",
            {"referrer_id": referrer.id}
        )
        
        logger.info(
            "referral_processed",
            referrer_id=referrer.id,
            referred_user_id=referred_user_id,
            new_count=new_count
        )
        
        return True, f"You've been referred by {referrer.first_name or referrer.username}! +25 UP Coins"
    
    def _calculate_referral_reward(self, count: int) -> Optional[dict]:
        """Calculate referral reward based on count."""
        if count in self.REFERRAL_REWARDS:
            reward = self.REFERRAL_REWARDS[count].copy()
            if "coins" not in reward:
                reward["coins"] = Decimal("0")
            return reward
        return None
    
    async def get_referral_benefits(self, user: User) -> dict:
        """Get current referral benefits for user."""
        benefits = {
            "referral_count": user.referral_count,
            "referral_earnings": float(user.referral_earnings),
            "current_discount": 0,
            "next_milestone": None,
            "perks": []
        }
        
        # Calculate current discount
        if user.referral_count >= 5:
            benefits["current_discount"] = 50
            benefits["perks"].append("50% discount on tickets")
            benefits["perks"].append("Free VIP cocktail")
        elif user.referral_count >= 3:
            benefits["current_discount"] = 30
            benefits["perks"].append("30% discount on tickets")
        
        # Free VIP ticket
        if user.referral_count >= 8:
            benefits["perks"].append("Free VIP ticket to next event")
        
        # Next milestone
        if user.referral_count < 3:
            benefits["next_milestone"] = {
                "count": 3,
                "reward": "30% discount"
            }
        elif user.referral_count < 5:
            benefits["next_milestone"] = {
                "count": 5,
                "reward": "50% discount + VIP cocktail"
            }
        elif user.referral_count < 8:
            benefits["next_milestone"] = {
                "count": 8,
                "reward": "Free VIP ticket"
            }
        
        return benefits
    
    async def get_referral_stats(self, user_id: int) -> dict:
        """Get referral statistics for user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {}
        
        # CRITICAL FIX: Handle None referrals
        referral_details = []
        if user.referrals is not None:
            for referral in user.referrals[:10]:  # Limit to recent 10
                referral_details.append({
                    "name": referral.first_name or referral.username or "Anonymous",
                    "joined_at": referral.created_at.isoformat() if referral.created_at else None,
                    "is_member": referral.is_member
                })
        
        return {
            "total_referrals": user.referral_count,
            "referral_code": user.referral_code,
            "referral_earnings": float(user.referral_earnings),
            "recent_referrals": referral_details,
            "benefits": await self.get_referral_benefits(user)
        }
