"""Common handlers for menu buttons - Unified UX with brand consistency."""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler

from bot.utils.decorators import handle_errors, logging_middleware
from bot.utils.logger import logger

# Brand constants - properly escaped for MarkdownV2
TELEGRAM_CHANNEL = "https://t\\.me/underpeople\\_club"
WEBSITE_URL = "https://under\\-people\\-club\\.vercel\\.app/"


@logging_middleware
@handle_errors
async def events_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle events button - Хроники событий."""
    try:
        text = (
            "📅 *ХРОНИКИ СОБЫТИЙ*\n\n"
            "🌑 *Under People Club* организует легендарные вечеринки в Москве\\!\n\n"
            "*Ближайшие события:*\n"
            "Следите за анонсами в нашей группе\\.\n\n"
            f"📱 Telegram: {TELEGRAM_CHANNEL}\n"
            f"🌐 Сайт: {WEBSITE_URL}"
        )
        
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=False
        )
    except Exception as e:
        logger.error("events_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка\\. Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


@logging_middleware
@handle_errors
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help button - Система помощи."""
    try:
        text = (
            "❓ *СИСТЕМА ПОМОЩИ*\n\n"
            "*Основные команды:*\n"
            "• `/start` \\- Запустить терминал\n"
            "• `/profile` \\- Убежище \\(профиль\\)\n"
            "• `/referral` \\- Связь \\(рефералы\\)\n"
            "• `/daily` \\- Ежедневный ресурс\n\n"
            "*Навигация:*\n"
            "Используйте кнопки меню для быстрого доступа к функциям\\.\n\n"
            "*Поддержка:*\n"
            f"📱 Telegram: {TELEGRAM_CHANNEL}\n"
            f"🌐 Сайт: {WEBSITE_URL}"
        )
        
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=False
        )
    except Exception as e:
        logger.error("help_handler_error", error=str(e), user_id=update.effective_user.id)
        await update.message.reply_text(
            "😔 Произошла ошибка\\. Попробуйте позже\\.",
            parse_mode="MarkdownV2"
        )


def register_common_handlers(application) -> None:
    """Register common message handlers for menu buttons.
    
    Args:
        application: Telegram Application instance
    """
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
