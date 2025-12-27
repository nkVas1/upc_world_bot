"""Service for synchronizing bot data with website."""
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.database.repositories.user_repository import UserRepository
from bot.utils.logger import logger


class WebsiteSyncService:
    """Handles synchronization between bot and website."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.base_url = settings.website_url
        self.api_key = settings.website_api_key
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Bot-Version": "3.0"
        }
    
    def verify_telegram_auth(self, auth_data: Dict[str, Any]) -> bool:
        """Verify Telegram Login Widget data."""
        check_hash = auth_data.pop("hash", None)
        if not check_hash:
            return False
        
        # Sort keys and create data_check_string
        data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
        data_check_string = "\n".join(data_check_arr)
        
        # Calculate hash
        secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == check_hash
    
    async def sync_user_from_website(self, telegram_id: int) -> Optional[User]:
        """Sync user data from website to bot."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/telegram/{telegram_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 404:
                    logger.info("user_not_found_on_website", telegram_id=telegram_id)
                    return None
                
                response.raise_for_status()
                website_data = response.json()
                
                # Update or create user in bot DB
                user = await self.user_repo.get_by_id(telegram_id)
                
                if user:
                    await self.user_repo.update(
                        telegram_id,
                        website_user_id=website_data["id"],
                        up_coins=website_data.get("up_coins", 0),
                        is_member=website_data.get("is_member", False),
                        membership_level=website_data.get("membership_level", "guest"),
                        referral_code=website_data.get("referral_code"),
                        is_synced=True,
                        last_sync_at=datetime.utcnow()
                    )
                else:
                    user = await self.user_repo.create({
                        "id": telegram_id,
                        "username": website_data.get("telegram_username"),
                        "first_name": website_data.get("first_name"),
                        "website_user_id": website_data["id"],
                        "up_coins": website_data.get("up_coins", 0),
                        "is_member": website_data.get("is_member", False),
                        "membership_level": website_data.get("membership_level", "guest"),
                        "referral_code": website_data.get("referral_code"),
                        "is_synced": True,
                        "last_sync_at": datetime.utcnow()
                    })
                
                logger.info(
                    "user_synced_from_website",
                    telegram_id=telegram_id,
                    website_id=website_data["id"]
                )
                
                return user
                
        except httpx.HTTPError as e:
            logger.error("website_sync_error", error=str(e), telegram_id=telegram_id)
            return None
    
    async def sync_user_to_website(self, user: User) -> bool:
        """Sync user data from bot to website."""
        try:
            payload = {
                "telegram_id": user.id,
                "telegram_username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "up_coins": float(user.up_coins),
                "referral_code": user.referral_code,
                "daily_streak": user.daily_streak,
                "total_events_attended": user.total_events_attended,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/users/sync",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Update website_user_id if returned
                if "id" in result:
                    await self.user_repo.update(
                        user.id,
                        website_user_id=result["id"],
                        is_synced=True,
                        last_sync_at=datetime.utcnow()
                    )
                
                logger.info("user_synced_to_website", telegram_id=user.id)
                return True
                
        except httpx.HTTPError as e:
            logger.error("website_sync_error", error=str(e), user_id=user.id)
            return False
    
    async def sync_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: float,
        description: str
    ) -> bool:
        """Sync transaction to website."""
        try:
            payload = {
                "telegram_user_id": user_id,
                "type": transaction_type,
                "amount": amount,
                "description": description,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/transactions/sync",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                
                logger.info("transaction_synced", user_id=user_id, type=transaction_type)
                return True
                
        except httpx.HTTPError as e:
            logger.error("transaction_sync_error", error=str(e), user_id=user_id)
            return False
    
    async def get_user_tickets(self, telegram_id: int) -> list[Dict[str, Any]]:
        """Get user's tickets from website."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tickets/user/{telegram_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error("tickets_fetch_error", error=str(e), telegram_id=telegram_id)
            return []
    
    async def get_upcoming_events(self, limit: int = 5) -> list[Dict[str, Any]]:
        """Get upcoming events from website with fallback for missing endpoint."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/events/upcoming?limit={limit}",
                    headers=self._get_headers()
                )
                
                # Handle 404 gracefully - endpoint may not be implemented yet
                if response.status_code == 404:
                    logger.warning(
                        "events_endpoint_not_found",
                        url=f"{self.base_url}/api/v1/events/upcoming",
                        status_code=404
                    )
                    return []
                
                response.raise_for_status()
                data = response.json()
                
                # Handle both single list and nested "events" key
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "events" in data:
                    return data["events"]
                else:
                    logger.warning("unexpected_events_response_format", data=data)
                    return []
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "events_fetch_http_error",
                error=str(e),
                status_code=e.response.status_code
            )
            return []
        except httpx.TimeoutException as e:
            logger.error("events_fetch_timeout", error=str(e))
            return []
        except httpx.HTTPError as e:
            logger.error("events_fetch_error", error=str(e))
            return []
        except Exception as e:
            logger.error("events_fetch_unexpected_error", error=str(e), exc_info=True)
            return []
    
    async def validate_qr_code(self, qr_code: str) -> Optional[Dict[str, Any]]:
        """Validate QR code with website."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/tickets/validate",
                    headers=self._get_headers(),
                    json={"qr_code": qr_code}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error("qr_validation_error", error=str(e))
            return None
