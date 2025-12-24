"""Throttling middleware for rate limiting."""
from functools import wraps
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import logger


# In-memory storage for throttling (можно заменить на Redis в production)
_throttle_storage = {}


def throttling_middleware(rate: int = 3, per: int = 60):
    """
    Middleware decorator for rate limiting.
    
    Args:
        rate: Number of allowed requests
        per: Time period in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not update.effective_user:
                return await func(update, context, *args, **kwargs)
            
            user_id = update.effective_user.id
            key = f"throttle:{user_id}:{func.__name__}"
            
            now = datetime.now()
            
            # Check if user is throttled
            if key in _throttle_storage:
                requests, reset_time = _throttle_storage[key]
                
                if now < reset_time:
                    if requests >= rate:
                        logger.warning(
                            "rate_limit_exceeded",
                            user_id=user_id,
                            handler=func.__name__
                        )
                        if update.message:
                            await update.message.reply_text(
                                "⏱ Слишком много запросов. Подождите немного."
                            )
                        return
                    else:
                        _throttle_storage[key] = (requests + 1, reset_time)
                else:
                    # Reset throttle window
                    _throttle_storage[key] = (1, now + timedelta(seconds=per))
            else:
                # First request
                _throttle_storage[key] = (1, now + timedelta(seconds=per))
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator
