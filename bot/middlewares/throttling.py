"""Rate limiting middleware."""
from typing import Callable, Any, Awaitable
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.utils.logger import logger


class ThrottlingMiddleware:
    """Middleware for rate limiting."""
    
    def __init__(self):
        self.user_requests: dict[int, list[datetime]] = defaultdict(list)
        self.rate_limit = settings.rate_limit_requests
        self.period = settings.rate_limit_period
    
    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.period)
        
        # Remove old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.user_requests[user_id]) >= self.rate_limit:
            return True
        
        # Add current request
        self.user_requests[user_id].append(now)
        return False
    
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]
    ) -> Any:
        """Process update through middleware."""
        if not update.effective_user:
            return await handler(update, context)
        
        user_id = update.effective_user.id
        
        # Skip rate limiting for admins
        if settings.is_admin(user_id):
            return await handler(update, context)
        
        if self._is_rate_limited(user_id):
            logger.warning("rate_limit_exceeded", user_id=user_id)
            
            if update.message:
                await update.message.reply_text(
                    "⏱ Вы отправляете сообщения слишком часто. "
                    "Пожалуйста, подождите немного."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "⏱ Слишком много запросов. Подождите немного.",
                    show_alert=True
                )
            
            return None
        
        return await handler(update, context)
