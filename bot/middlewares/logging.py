"""Logging middleware for handlers."""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import logger


def logging_middleware(func):
    """
    Middleware decorator for logging requests.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        # Log incoming update
        logger.info(
            "incoming_update",
            handler=func.__name__,
            user_id=user_id,
            chat_id=chat_id,
            update_type=update.update_id
        )
        
        try:
            result = await func(update, context, *args, **kwargs)
            
            logger.info(
                "update_processed",
                handler=func.__name__,
                user_id=user_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "update_error",
                handler=func.__name__,
                user_id=user_id,
                error=str(e)
            )
            raise
    
    return wrapper
