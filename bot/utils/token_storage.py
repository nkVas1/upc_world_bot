"""Token storage for authentication codes - single source of truth."""
import time
from typing import Optional

from bot.utils.logger import logger


class TokenStorage:
    """
    Singleton for managing one-time auth codes.
    
    This is the single source of truth for all auth codes in the system.
    Both bot and API use this class to store/retrieve codes.
    
    Format: {code: {"user_id": int, "created_at": float, "used": bool}}
    """
    
    # Class-level storage (persistent across instances)
    _codes: dict = {}
    
    # Auth code TTL in seconds (15 minutes)
    CODE_TTL = 900

    @classmethod
    def add_code(cls, code: str, user_id: int) -> None:
        """
        Store a new auth code.
        
        Args:
            code: UUID code string
            user_id: Telegram user ID
        """
        cls._codes[code] = {
            "user_id": user_id,
            "created_at": time.time(),
            "used": False
        }
        logger.info(
            "auth_code_stored",
            code=code[:8] + "...",
            user_id=user_id,
            ttl_seconds=cls.CODE_TTL
        )

    @classmethod
    def get_user_id(cls, code: str) -> Optional[int]:
        """
        Exchange code for user_id (one-time use).
        
        Returns the user_id and IMMEDIATELY DELETES the code.
        This ensures one-time use and prevents replay attacks.
        
        Args:
            code: Auth code to exchange
            
        Returns:
            user_id if code is valid and not expired, None otherwise
        """
        # Clean old codes before checking
        cls._cleanup_expired()
        
        code_data = cls._codes.get(code)
        if not code_data:
            logger.warning("token_storage_code_not_found", code=code[:8] + "...")
            return None
        
        # Check if code is expired
        age_seconds = time.time() - code_data["created_at"]
        if age_seconds > cls.CODE_TTL:
            del cls._codes[code]
            logger.warning(
                "token_storage_code_expired",
                code=code[:8] + "...",
                age_seconds=age_seconds
            )
            return None
        
        # Check if already used
        if code_data["used"]:
            logger.warning("token_storage_code_reused", code=code[:8] + "...")
            return None
        
        user_id = code_data["user_id"]
        
        # Mark as used and delete immediately (one-time use)
        del cls._codes[code]
        
        logger.info(
            "token_storage_code_exchanged",
            code=code[:8] + "...",
            user_id=user_id
        )
        
        return user_id

    @classmethod
    def _cleanup_expired(cls) -> None:
        """Remove codes older than TTL."""
        current_time = time.time()
        expired_codes = [
            code for code, data in cls._codes.items()
            if current_time - data["created_at"] > cls.CODE_TTL
        ]
        
        for code in expired_codes:
            del cls._codes[code]
        
        if expired_codes:
            logger.info(
                "token_storage_cleanup",
                removed_count=len(expired_codes),
                remaining_count=len(cls._codes)
            )

    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all codes.
        Useful for testing or emergency reset.
        """
        cls._codes.clear()
        logger.warning("token_storage_cleared_all")

    @classmethod
    def get_stats(cls) -> dict:
        """Get storage statistics (useful for monitoring)."""
        cls._cleanup_expired()
        return {
            "total_codes": len(cls._codes),
            "ttl_seconds": cls.CODE_TTL
        }
