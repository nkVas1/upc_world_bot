"""Authentication middleware for handlers."""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from bot.database.session import db_manager
from bot.database.repositories.user_repository import UserRepository
from bot.utils.logger import logger


def auth_middleware(func):
    """
    Middleware decorator for authenticating users.
    Fetches user from database and adds to context.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return await func(update, context, *args, **kwargs)
        
        user_id = update.effective_user.id
        
        try:
            # Get or create user in database
            async with db_manager.session() as session:
                user_repo = UserRepository(session)
                db_user = await user_repo.get_by_id(user_id)
                
                # Store in context for handlers
                context.user_data["db_user"] = db_user
                context.user_data["user_id"] = user_id
        except Exception as e:
            logger.error(
                "auth_middleware_error",
                user_id=user_id,
                error=str(e)
            )
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper
