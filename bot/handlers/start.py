"""Start command and main menu handler."""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.keyboards.inline import kb
from bot.database.session import db_manager
from bot.services.user_service import UserService
from bot.utils.decorators import handle_errors
from bot.utils.logger import logger
from bot.middlewares.auth import auth_middleware
from bot.middlewares.logging import logging_middleware
from bot.middlewares.throttling import throttling_middleware


@auth_middleware
@logging_middleware
@throttling_middleware()
@handle_errors
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    # Extract referral code from deep link
    referral_code = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
    
    async with db_manager.session() as session:
        user_service = UserService(session)
        db_user = await user_service.get_or_create_user(user, referral_code)
        
        # Check if user is new (created in last 5 seconds)
        is_new = (datetime.utcnow() - db_user.created_at).total_seconds() < 5 if db_user.created_at else False
    
    if is_new:
        welcome_text = (
            "🌑 *Добро пожаловать в Under People Club\\!*\n\n"
            "Мы рады видеть тебя в нашем мрачном, но удивительном сообществе\\.\n\n"
            "🎭 Здесь ты найдёшь:\n"
            "• Легендарные вечеринки в Москве\n"
            "• Систему наград и достижений\n"
            "• Карточную игру по миру UP\n"
            "• Эксклюзивный мерч и билеты\n\n"
            "💰 На твой счёт зачислено *100 UP Coins* в подарок\\!\n\n"
            "Используй меню ниже для навигации\\."
        )
    else:
        welcome_text = (
            f"🌑 С возвращением, *{user.first_name}*\\!\n\n"
            "Что будем делать сегодня?"
        )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=kb.main_menu(db_user.is_member),
        parse_mode="MarkdownV2"
    )
    
    logger.info("start_command", user_id=user.id, is_new=is_new)


@auth_middleware
@logging_middleware
@handle_errors
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back to main menu callback."""
    query = update.callback_query
    await query.answer()
    
    db_user = context.user_data.get("db_user")
    
    text = "🌑 *Главное меню*\n\nВыберите действие:"
    
    await query.edit_message_text(
        text,
        reply_markup=kb.main_menu(db_user.is_member if db_user else False),
        parse_mode="MarkdownV2"
    )


@handle_errors
async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle close button callback."""
    query = update.callback_query
    await query.answer()
    await query.message.delete()


# Register handlers
def register_start_handlers(application):
    """Register start-related handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(close_callback, pattern="^close$"))
