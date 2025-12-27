"""Authentication service with code storage."""
import secrets
from datetime import datetime, timedelta
from typing import Optional
import json

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.config import settings
from bot.database.models import AuthCode, User
from bot.utils.logger import logger


class AuthCodeService:
    """Service for managing one-time authentication codes."""
    
    CODE_TTL = 600  # 10 minutes in seconds
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.redis = None
        self.use_redis = False
    
    async def initialize_redis(self) -> bool:
        """Initialize Redis connection if available."""
        try:
            self.redis = await aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_keepalive=True
            )
            # Test connection
            await self.redis.ping()
            self.use_redis = True
            logger.info("auth_service_redis_initialized")
            return True
        except Exception as e:
            logger.warning(
                "auth_service_redis_init_failed",
                error=str(e),
                fallback="using_database"
            )
            self.use_redis = False
            return False
    
    async def store_auth_code(self, user_id: int) -> str:
        """
        Generate and store auth code in Redis or Database.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Generated auth code (UUID-like string)
        """
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=self.CODE_TTL)
        
        if self.use_redis:
            try:
                # Store in Redis
                data = {
                    'user_id': user_id,
                    'created_at': datetime.utcnow().isoformat()
                }
                await self.redis.setex(
                    f"auth_code:{code}",
                    self.CODE_TTL,
                    json.dumps(data)
                )
                logger.info(
                    "auth_code_stored_redis",
                    user_id=user_id,
                    code=code[:8] + "...",
                    ttl=self.CODE_TTL
                )
                return code
            except Exception as e:
                logger.error("auth_code_redis_store_error", error=str(e))
                # Fallback to database
        
        # Store in database
        try:
            auth_code = AuthCode(
                code=code,
                user_id=user_id,
                expires_at=expires_at
            )
            self.session.add(auth_code)
            await self.session.flush()
            
            logger.info(
                "auth_code_stored_database",
                user_id=user_id,
                code=code[:8] + "...",
                ttl=self.CODE_TTL
            )
            return code
        except Exception as e:
            logger.error("auth_code_database_store_error", error=str(e))
            raise
    
    async def verify_auth_code(self, code: str) -> Optional[int]:
        """
        Verify auth code and return user_id if valid.
        Code is one-time use - deleted after verification.
        
        Args:
            code: Auth code to verify
            
        Returns:
            User ID if valid, None otherwise
        """
        if self.use_redis:
            try:
                # Try Redis first
                key = f"auth_code:{code}"
                data_str = await self.redis.get(key)
                
                if data_str:
                    data = json.loads(data_str)
                    user_id = data['user_id']
                    
                    # Delete code after use (one-time use)
                    await self.redis.delete(key)
                    
                    logger.info("auth_code_verified_redis", user_id=user_id)
                    return user_id
            except Exception as e:
                logger.error("auth_code_redis_verify_error", error=str(e))
                # Fallback to database
        
        # Verify in database
        try:
            result = await self.session.execute(
                select(AuthCode).where(AuthCode.code == code)
            )
            auth_code = result.scalar_one_or_none()
            
            if not auth_code:
                logger.warning("auth_code_not_found")
                return None
            
            if auth_code.is_expired():
                logger.warning("auth_code_expired", code=code[:8] + "...")
                # Clean up expired codes
                await self.session.delete(auth_code)
                await self.session.flush()
                return None
            
            if auth_code.used:
                logger.warning("auth_code_already_used", code=code[:8] + "...")
                return None
            
            user_id = auth_code.user_id
            
            # Mark as used
            auth_code.used = True
            auth_code.used_at = datetime.utcnow()
            await self.session.flush()
            
            logger.info("auth_code_verified_database", user_id=user_id)
            return user_id
            
        except Exception as e:
            logger.error("auth_code_database_verify_error", error=str(e))
            return None
    
    async def cleanup_expired_codes(self) -> int:
        """
        Clean up expired auth codes from database.
        
        Returns:
            Number of deleted codes
        """
        try:
            result = await self.session.execute(
                select(AuthCode).where(
                    AuthCode.expires_at < datetime.utcnow()
                )
            )
            expired_codes = result.scalars().all()
            count = len(expired_codes)
            
            for code in expired_codes:
                await self.session.delete(code)
            
            await self.session.flush()
            
            if count > 0:
                logger.info("auth_codes_cleanup", deleted_count=count)
            
            return count
        except Exception as e:
            logger.error("auth_codes_cleanup_error", error=str(e))
            return 0
    
    async def close(self):
        """Close Redis connection if open."""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("auth_service_redis_closed")
            except Exception as e:
                logger.error("auth_service_redis_close_error", error=str(e))
