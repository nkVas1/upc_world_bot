"""User data caching middleware to reduce API calls."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio

from bot.utils.logger import logger


class UserCacheManager:
    """
    Manages caching of user data to reduce API calls.
    
    This prevents excessive /api/users/me requests by caching user data
    with a configurable TTL. Reduces load on API server significantly.
    """
    
    DEFAULT_TTL = 300  # 5 minutes in seconds
    MAX_CACHE_SIZE = 10000  # Maximum cached users
    
    def __init__(self, ttl: int = DEFAULT_TTL):
        self.ttl = ttl
        self.cache: Dict[int, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[int, datetime] = {}
        self.lock = asyncio.Lock()
    
    async def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached user data if not expired.
        
        Args:
            user_id: User ID to fetch from cache
            
        Returns:
            Cached user data if found and valid, None otherwise
        """
        async with self.lock:
            if user_id not in self.cache:
                return None
            
            # Check if expired
            if self._is_expired(user_id):
                del self.cache[user_id]
                del self.cache_timestamps[user_id]
                return None
            
            logger.debug("cache_hit", user_id=user_id)
            return self.cache[user_id]
    
    async def set(self, user_id: int, data: Dict[str, Any]) -> None:
        """
        Store user data in cache with TTL.
        
        Args:
            user_id: User ID
            data: User data to cache
        """
        async with self.lock:
            # Evict oldest entry if cache is full
            if len(self.cache) >= self.MAX_CACHE_SIZE:
                oldest_user = min(
                    self.cache_timestamps,
                    key=self.cache_timestamps.get
                )
                del self.cache[oldest_user]
                del self.cache_timestamps[oldest_user]
                logger.debug("cache_evicted", user_id=oldest_user)
            
            self.cache[user_id] = data
            self.cache_timestamps[user_id] = datetime.utcnow()
            logger.debug("cache_stored", user_id=user_id, ttl=self.ttl)
    
    async def invalidate(self, user_id: int) -> None:
        """
        Manually invalidate cache for a user (e.g., after profile update).
        
        Args:
            user_id: User ID to invalidate
        """
        async with self.lock:
            if user_id in self.cache:
                del self.cache[user_id]
                del self.cache_timestamps[user_id]
                logger.debug("cache_invalidated", user_id=user_id)
    
    async def clear(self) -> None:
        """Clear entire cache."""
        async with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.cache_timestamps.clear()
            if count > 0:
                logger.info("cache_cleared", entries=count)
    
    async def cleanup_expired(self) -> int:
        """
        Clean up all expired entries.
        
        Returns:
            Number of expired entries removed
        """
        async with self.lock:
            expired_users = [
                user_id for user_id in self.cache_timestamps
                if self._is_expired(user_id)
            ]
            
            for user_id in expired_users:
                del self.cache[user_id]
                del self.cache_timestamps[user_id]
            
            if expired_users:
                logger.debug("cache_cleanup", expired_count=len(expired_users))
            
            return len(expired_users)
    
    def _is_expired(self, user_id: int) -> bool:
        """Check if cache entry has expired."""
        if user_id not in self.cache_timestamps:
            return True
        
        timestamp = self.cache_timestamps[user_id]
        return datetime.utcnow() > timestamp + timedelta(seconds=self.ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cached_users': len(self.cache),
            'max_size': self.MAX_CACHE_SIZE,
            'ttl_seconds': self.ttl,
            'utilization_percent': round(
                (len(self.cache) / self.MAX_CACHE_SIZE) * 100, 2
            )
        }


# Global cache manager instance
user_cache = UserCacheManager(ttl=300)  # 5 minutes TTL
