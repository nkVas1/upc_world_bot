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


def logging_middleware(func: Callable) -> Callable:
    """
    Middleware decorator for comprehensive request/response logging.
    Logs handler execution time, user info, and action details.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        import time
        
        # Extract user information
        user = update.effective_user
        user_id = user.id if user else None
        username = user.username if user else "Unknown"
        
        # Determine message type
        message_type = None
        if update.message:
            message_type = "message"
            text = update.message.text or "[media]"
        elif update.callback_query:
            message_type = "callback_query"
            text = update.callback_query.data or "[no_data]"
        else:
            message_type = "unknown"
            text = "[unknown_update]"
        
        # Log request start
        logger.info(
            "handler_start",
            handler=func.__name__,
            user_id=user_id,
            username=username,
            message_type=message_type,
            text=text[:100]  # Limit text length
        )
        
        # Execute handler with timing
        start_time = time.time()
        
        try:
            result = await func(update, context)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.info(
                "handler_success",
                handler=func.__name__,
                user_id=user_id,
                execution_time=f"{execution_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            logger.error(
                "handler_error",
                handler=func.__name__,
                user_id=user_id,
                error=str(e),
                error_type=type(e).__name__,
                execution_time=f"{execution_time:.3f}s"
            )
            raise
    
    return wrapper


def auth_middleware(func: Callable) -> Callable:
    """
    Authentication middleware that ensures user exists in database.
    Automatically creates or updates user record, checks ban status,
    and loads user data into context.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from bot.database.session import db_manager
        from bot.services.user_service import UserService
        
        user = update.effective_user
        if not user:
            logger.warning("auth_middleware_no_user")
            return None
        
        user_id = user.id
        
        try:
            # Get or create user in database
            async with db_manager.session() as session:
                user_service = UserService(session)
                db_user = await user_service.get_or_create_user(user)
                
                # Check if user is banned
                if db_user.is_banned:
                    logger.warning(
                        "banned_user_attempt",
                        user_id=user_id,
                        ban_reason=db_user.ban_reason
                    )
                    
                    ban_message = (
                        "🚫 *Доступ заблокирован*\n\n"
                        f"Причина: {db_user.ban_reason or 'Нарушение правил'}\n\n"
                        "Для разблокировки обратитесь в поддержку: @underpeople"
                    )
                    
                    if update.message:
                        await update.message.reply_text(
                            ban_message,
                            parse_mode="Markdown"
                        )
                    elif update.callback_query:
                        await update.callback_query.answer(
                            "❌ Доступ заблокирован",
                            show_alert=True
                        )
                    
                    return None
                
                # Store user data in context for handler access
                context.user_data["db_user"] = db_user
                context.user_data["user_id"] = user_id
                context.user_data["is_member"] = db_user.is_member
                context.user_data["membership_level"] = db_user.membership_level
                context.user_data["up_coins"] = float(db_user.up_coins)
                
                # Execute handler
                return await func(update, context)
                
        except Exception as e:
            logger.error(
                "auth_middleware_error",
                user_id=user_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Send user-friendly error message
            error_message = (
                "😔 Произошла ошибка при проверке авторизации.\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            
            if update.message:
                await update.message.reply_text(error_message)
            elif update.callback_query:
                await update.callback_query.answer(
                    "❌ Ошибка авторизации",
                    show_alert=True
                )
            
            return None
    
    return wrapper


def rate_limit(max_calls: int = 5, period: int = 60):
    """
    Rate limiting decorator to prevent spam and abuse.
    
    Args:
        max_calls: Maximum number of calls allowed
        period: Time period in seconds
    """
    def decorator(func: Callable) -> Callable:
        # Store call timestamps per user
        call_history = {}
        
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            import time
            
            user = update.effective_user
            if not user:
                return await func(update, context)
            
            user_id = user.id
            current_time = time.time()
            
            # Initialize user history
            if user_id not in call_history:
                call_history[user_id] = []
            
            # Remove old calls outside the period
            call_history[user_id] = [
                timestamp for timestamp in call_history[user_id]
                if current_time - timestamp < period
            ]
            
            # Check rate limit
            if len(call_history[user_id]) >= max_calls:
                wait_time = int(period - (current_time - call_history[user_id][0]))
                
                logger.warning(
                    "rate_limit_exceeded",
                    user_id=user_id,
                    handler=func.__name__,
                    wait_time=wait_time
                )
                
                message = (
                    f"⏱️ Слишком много запросов!\n\n"
                    f"Подождите {wait_time} секунд перед следующей попыткой."
                )
                
                if update.message:
                    await update.message.reply_text(message)
                elif update.callback_query:
                    await update.callback_query.answer(
                        f"⏱️ Подождите {wait_time}с",
                        show_alert=True
                    )
                
                return None
            
            # Record this call
            call_history[user_id].append(current_time)
            
            # Execute handler
            return await func(update, context)
        
        return wrapper
    return decorator


def typing_action(func: Callable) -> Callable:
    """
    Decorator that shows 'typing...' indicator while processing.
    Enhances user experience by showing activity.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = None
        
        if update.message:
            chat_id = update.message.chat_id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat_id
        
        if chat_id:
            # Send typing action
            await context.bot.send_chat_action(
                chat_id=chat_id,
                action="typing"
            )
        
        return await func(update, context)
    
    return wrapper


def analytics_tracker(event_name: str):
    """
    Decorator for tracking user actions and analytics.
    
    Args:
        event_name: Name of the event to track
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            from datetime import datetime
            
            user = update.effective_user
            
            if user:
                # Log analytics event
                logger.info(
                    "analytics_event",
                    event=event_name,
                    user_id=user.id,
                    username=user.username,
                    handler=func.__name__
                )
                
                # Store in context for potential external analytics
                if "analytics_events" not in context.bot_data:
                    context.bot_data["analytics_events"] = []
                
                context.bot_data["analytics_events"].append({
                    "event": event_name,
                    "user_id": user.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "handler": func.__name__
                })
            
            return await func(update, context)
        
        return wrapper
    return decorator
