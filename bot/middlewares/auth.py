"""Authentication middleware."""
from typing import Callable, Dict, Any, Awaitable

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.session import db_manager
from bot.services.user_service import UserService
from bot.utils.logger import logger


class AuthMiddleware:
    """Middleware for user authentication and registration."""
    
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]
    ) -> Any:
        """Process update through middleware."""
        if not update.effective_user:
            return await handler(update, context)
        
        async with db_manager.session() as session:
            user_service = UserService(session)
            
            # Get or create user
            user = await user_service.get_or_create_user(update.effective_user)
            
            # Store user in context for handlers
            context.user_data["db_user"] = user
            context.user_data["user_id"] = user.id
            
            logger.info(
                "user_authenticated",
                user_id=user.id,
                username=user.username,
                handler=handler.__name__ if hasattr(handler, "__name__") else "unknown"
            )
        
        return await handler(update, context)
