"""Start command and main menu handler."""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.keyboards.inline import kb
from bot.keyboards.reply import main_keyboard
from bot.utils.formatters import fmt
from bot.utils.navigation import NavigationManager
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
    
    # Delete user's command message for cleaner chat
    await NavigationManager.delete_user_command(update)
    
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
            "🌑 *ДОБРО ПОЖАЛОВАТЬ В UNDER PEOPLE CLUB*\n\n"
            "Терминал активирован\\. Система загружена\\.\n\n"
            "🎯 *Доступные модули:*\n"
            "• 👤 Убежище \\- твой профиль\n"
            "• 🎟️ Арсенал \\- билеты на рейды\n"
            "• 🏪 Снабжение \\- мерч и артефакты\n"
            "• 🔗 Связь \\- реферальная сеть\n"
            "• 📅 Хроники \\- архив событий\n\n"
            "💰 *Стартовый капитал:* 100 UP Coins\n\n"
            "Используй меню для навигации\\.\n\n"
            "📱 Канал: https://t\\.me/underpeople\\_club\n"
            "🌐 База: https://under\\-people\\-club\\.vercel\\.app/"
        )
    else:
        welcome_text = (
            f"🌑 *Терминал активирован*\n\n"
            f"С возвращением, *{fmt.escape_markdown(user.first_name)}*\\!\n\n"
            f"Система готова к работе\\."
        )
    
    # Use reply_text with main_keyboard since this is a Reply keyboard, not Inline
    # NavigationManager is for inline messages
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_keyboard(db_user.is_member),
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
