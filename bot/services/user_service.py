"""User service with business logic."""
from typing import Optional
from telegram import User as TelegramUser
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.user_repository import UserRepository
from bot.database.models import User
from bot.services.referral_service import ReferralService
from bot.services.qr_generator import QRCodeGenerator
from bot.services.website_sync import WebsiteSyncService
from bot.utils.logger import logger


class UserService:
    """High-level user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.referral_service = ReferralService(session)
        self.qr_generator = QRCodeGenerator()
        self.website_sync = WebsiteSyncService(session)
    
    async def get_or_create_user(
        self,
        telegram_user: TelegramUser,
        referral_code: Optional[str] = None
    ) -> User:
        """Get existing user or create new one."""
        user = await self.user_repo.get_by_id(telegram_user.id)
        
        if user:
            # Update user info if changed
            updates = {}
            if user.username != telegram_user.username:
                updates["username"] = telegram_user.username
            if user.first_name != telegram_user.first_name:
                updates["first_name"] = telegram_user.first_name
            if user.last_name != telegram_user.last_name:
                updates["last_name"] = telegram_user.last_name
            
            # Update photo if available
            if telegram_user.photo_id and not user.photo_url:
                updates["photo_url"] = f"tg://user/{telegram_user.id}"
            
            if updates:
                user = await self.user_repo.update(telegram_user.id, **updates)
            
            return user
        
        # Create new user
        ref_code = await self.referral_service.create_referral_code(telegram_user.id)
        
        # Get photo URL if available
        photo_url = None
        if telegram_user.photo_id:
            photo_url = f"tg://user/{telegram_user.id}"
        
        user = await self.user_repo.create({
            "id": telegram_user.id,
            "username": telegram_user.username,
            "first_name": telegram_user.first_name,
            "last_name": telegram_user.last_name,
            "referral_code": ref_code,
            "photo_url": photo_url,
        })
        
        # Process referral if provided
        if referral_code:
            await self.referral_service.process_referral(telegram_user.id, referral_code)
        
        # Give welcome bonus
        await self.user_repo.add_coins(
            telegram_user.id,
            Decimal("100"),
            "welcome",
            "Welcome to Under People Club! 🎉"
        )
        
        # Sync with website
        await self.website_sync.sync_user_to_website(user)
        
        logger.info("new_user_registered", user_id=telegram_user.id)
        
        return user
    
    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Get comprehensive user profile."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        referral_stats = await self.referral_service.get_referral_stats(user_id)
        
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "is_member": user.is_member,
            "membership_level": user.membership_level,
            "up_coins": float(user.up_coins),
            "daily_streak": user.daily_streak,
            "total_events_attended": user.total_events_attended,
            "joined_at": user.created_at.isoformat() if user.created_at else None,
            "referral": referral_stats,
            "is_synced": user.is_synced,
            "referral_code": user.referral_code,
        }
