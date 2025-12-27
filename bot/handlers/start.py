"""Start command and main menu handler."""
from datetime import datetime
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.keyboards.inline import kb
from bot.keyboards.reply import main_keyboard
from bot.utils.formatters import fmt
from bot.utils.navigation import NavigationManager
from bot.utils.token_storage import TokenStorage
from bot.database.session import db_manager
from bot.services.user_service import UserService
from bot.utils.decorators import handle_errors
from bot.utils.logger import logger
from bot.middlewares.auth import auth_middleware
from bot.middlewares.logging import logging_middleware
from bot.middlewares.throttling import throttling_middleware
from bot.config import settings


@auth_middleware
@logging_middleware
@throttling_middleware()
@handle_errors
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional deep link parameter."""
    user = update.effective_user
    
    # Delete user's command message for cleaner chat
    await NavigationManager.delete_user_command(update)
    
    # Extract parameter from deep link (e.g., /start login, /start ref_code)
    param = None
    if context.args and len(context.args) > 0:
        param = context.args[0]
    
    # If user clicked /start login deep link, redirect to login_command
    if param == "login":
        await login_command(update, context)
        return
    
    # Otherwise treat as referral code
    referral_code = param
    
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


@auth_middleware
@logging_middleware
@handle_errors
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /login command - generates auth code and sends login link."""
    user = update.effective_user
    
    # Delete user's command message for cleaner chat
    await NavigationManager.delete_user_command(update)
    
    try:
        # Get user from database
        async with db_manager.session() as session:
            from bot.database.repositories.user_repository import UserRepository
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_id(user.id)
            
            if not db_user:
                await update.message.reply_text(
                    "❌ Пользователь не найден. Используйте /start для регистрации.",
                    parse_mode="HTML"
                )
                logger.warning("login_user_not_found", user_id=user.id)
                return
        
        # Generate auth code and store in TokenStorage (NOT in bot object)
        code = str(uuid4())
        TokenStorage.add_code(code, user.id)
        
        # Create login URL that returns user to website with auth code
        login_url = f"{settings.website_url}/auth/callback?code={code}"
        
        # Create inline keyboard with login button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Войти в Личный Кабинет",
                url=login_url
            )]
        ])
        
        # Send message with login button
        await update.message.reply_text(
            "🔐 <b>Вход в личный кабинет</b>\n\n"
            "Нажмите кнопку ниже, чтобы перейти на сайт. "
            "Вы будете авторизованы автоматически.\n\n"
            "<i>Ссылка действует 15 минут</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info("login_command_executed", user_id=user.id, code=code[:8] + "...")
        
    except Exception as e:
        logger.error("login_command_error", error=str(e), user_id=user.id)
        await update.message.reply_text(
            "❌ Ошибка при генерации ссылки входа. Попробуйте позже.",
            parse_mode="HTML"
        )


# Register handlers
def register_start_handlers(application):
    """Register start-related handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(close_callback, pattern="^close$"))
