"""Utility decorators for handlers."""
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.utils.logger import logger


def admin_only(func: Callable) -> Callable:
    """Decorator to restrict handler to admin users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        
        if not user_id or not settings.is_admin(user_id):
            logger.warning("unauthorized_admin_access", user_id=user_id)
            
            if update.message:
                await update.message.reply_text(
                    "❌ У вас нет прав для выполнения этой команды."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "❌ Доступ запрещен",
                    show_alert=True
                )
            
            return None
        
        return await func(update, context)
    
    return wrapper


def member_only(func: Callable) -> Callable:
    """Decorator to restrict handler to club members only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_user = context.user_data.get("db_user")
        
        if not db_user or not db_user.is_member:
            if update.message:
                await update.message.reply_text(
                    "🔒 Эта функция доступна только членам клуба.\n"
                    "Посетите наш сайт для регистрации!"
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "🔒 Только для членов клуба",
                    show_alert=True
                )
            
            return None
        
        return await func(update, context)
    
    return wrapper


def with_db_session(func: Callable) -> Callable:
    """Decorator to provide database session to handler."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from bot.database.session import db_manager
        
        async with db_manager.session() as session:
            context.user_data["db_session"] = session
            result = await func(update, context)
            del context.user_data["db_session"]
            return result
    
    return wrapper


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors gracefully."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.error(
                "handler_error",
                handler=func.__name__,
                error=str(e),
                user_id=update.effective_user.id if update.effective_user else None
            )
            
            error_message = (
                "😔 Произошла ошибка при обработке вашего запроса.\n"
                "Наша команда уже работает над решением проблемы.\n\n"
                "Попробуйте /start для перезапуска бота."
            )
            
            if update.message:
                await update.message.reply_text(error_message)
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message)
                await update.callback_query.answer()
    
    return wrapper
