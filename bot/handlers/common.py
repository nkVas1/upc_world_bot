"""Common handlers for menu buttons - App-like navigation."""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler

from bot.utils.decorators import handle_errors
from bot.utils.logger import logger
from bot.utils.navigation import NavigationManager
from bot.middlewares.logging import logging_middleware

# Brand constants - properly escaped for MarkdownV2
TELEGRAM_CHANNEL = "https://t\\.me/underpeople\\_club"
WEBSITE_URL = "https://under\\-people\\-club\\.vercel\\.app/"


@logging_middleware
@handle_errors
async def events_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle events button - Хроники событий."""
    # Delete user's command for cleaner chat
    await NavigationManager.delete_user_command(update)
    
    text = (
        "📅 *ХРОНИКИ СОБЫТИЙ*\n\n"
        "🌑 *Under People Club* организует легендарные рейды в Москве\\!\n\n"
        "*Ближайшие события:*\n"
        "Следите за анонсами в нашем канале\\.\n\n"
        f"📱 Telegram: {TELEGRAM_CHANNEL}\n"
        f"🌐 Сайт: {WEBSITE_URL}"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=None
    )


@logging_middleware
@handle_errors
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help button - Система помощи."""
    # Delete user's command for cleaner chat
    await NavigationManager.delete_user_command(update)
    
    text = (
        "❓ *СИСТЕМА ПОМОЩИ*\n\n"
        "*Основные команды:*\n"
        "• `/start` \\- Запустить терминал\n"
        "• `/profile` \\- Убежище \\(профиль\\)\n"
        "• `/referral` \\- Связь \\(рефералы\\)\n"
        "• `/daily` \\- Ежедневный ресурс\n\n"
        "*Навигация:*\n"
        "Используйте кнопки меню для быстрого доступа\\.\n\n"
        "*Поддержка:*\n"
        f"📱 Telegram: {TELEGRAM_CHANNEL}\n"
        f"🌐 Сайт: {WEBSITE_URL}"
    )
    
    await NavigationManager.send_or_edit(
        update,
        context,
        text,
        reply_markup=None
    )


def register_common_handlers(application) -> None:
    """Register common message handlers for menu buttons."""
    # События
    application.add_handler(MessageHandler(
        filters.Regex(r"^📅 События$"), events_handler
    ))
    
    # Помощь
    application.add_handler(MessageHandler(
        filters.Regex(r"^❓ Помощь$"), help_handler
    ))
    
    # Help command
    application.add_handler(CommandHandler("help", help_handler))
    
    logger.info("common_handlers_registered", count=3)
