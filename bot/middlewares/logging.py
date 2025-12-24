"""Logging middleware."""
from typing import Callable, Any, Awaitable
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.logger import logger


class LoggingMiddleware:
    """Middleware for logging all interactions."""
    
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]
    ) -> Any:
        """Process update through middleware."""
        start_time = datetime.utcnow()
        
        # Extract update info
        user_id = update.effective_user.id if update.effective_user else None
        username = update.effective_user.username if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        update_type = None
        update_data = None
        
        if update.message:
            update_type = "message"
            update_data = update.message.text or "[media]"
        elif update.callback_query:
            update_type = "callback_query"
            update_data = update.callback_query.data
        elif update.inline_query:
            update_type = "inline_query"
            update_data = update.inline_query.query
        
        logger.info(
            "update_received",
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            update_type=update_type,
            data=update_data
        )
        
        try:
            result = await handler(update, context)
            
            # Log success
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "update_processed",
                user_id=user_id,
                update_type=update_type,
                duration=duration,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Log error
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "update_error",
                user_id=user_id,
                update_type=update_type,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
