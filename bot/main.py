"""Main bot entry point."""
import asyncio
import sys
import os
from datetime import datetime

# CRITICAL: Print to stdout for Railway logs BEFORE any imports
print("=" * 60)
print("🚀 Starting UPC World Bot v3.0")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

# Print environment variables (masked sensitive data)
print("Environment variables:")
env_vars = [
    "BOT_TOKEN", "BOT_USERNAME", "DATABASE_URL", "REDIS_URL",
    "WEBSITE_URL", "LOG_LEVEL", "LOG_FORMAT"
]
for var in env_vars:
    value = os.getenv(var, "NOT SET")
    # Mask sensitive data
    if var in ["BOT_TOKEN", "DATABASE_URL", "REDIS_URL"] and value != "NOT SET":
        if "://" in value:
            # Show only protocol and host
            parts = value.split("://")
            if len(parts) > 1:
                protocol = parts[0]
                rest = parts[1].split("@")
                if len(rest) > 1:
                    host = rest[-1]
                    value = f"{protocol}://***@{host}"
                else:
                    value = f"{protocol}://***"
        else:
            value = value[:10] + "***" if len(value) > 10 else "***"
    print(f"  {var}: {value}")
print()

try:
    print("Loading configuration...")
    from bot.config import settings
    print("✅ Configuration loaded successfully")
    print(f"  Bot username: @{settings.bot_username}")
    print(f"  Admin IDs: {settings.admin_ids}")
    print(f"  Log level: {settings.log_level}")
    print()
except Exception as e:
    print("=" * 60)
    print("❌ CRITICAL ERROR: Failed to load configuration")
    print("=" * 60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    print("This usually means:")
    print("1. Required environment variables are missing")
    print("2. Invalid environment variable values")
    print("3. Check your Railway Variables settings")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.database.session import db_manager
from bot.database.base import Base
from bot.utils.logger import logger

# Import handlers
from bot.handlers.start import register_start_handlers
from bot.handlers.profile import register_profile_handlers
from bot.handlers.referral import register_referral_handlers
from bot.handlers.shop import register_shop_handlers
from bot.handlers.admin import register_admin_handlers
from bot.handlers.common import register_common_handlers


async def error_handler(update: object, context) -> None:
    """Handle errors."""
    logger.error(
        "exception_during_update",
        error=str(context.error),
        update=str(update) if update else None
    )
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "😔 Произошла ошибка при обработке вашего запроса.\n"
            "Попробуйте /start для перезапуска."
        )


async def help_command(update: Update, context) -> None:
    """Handle /help command."""
    text = (
        "ℹ️ *Помощь*\n\n"
        "*Основные команды:*\n"
        "/start \\- Запустить бота\n"
        "/profile \\- Ваш профиль\n"
        "/referral \\- Реферальная программа\n"
        "/daily \\- Ежедневный бонус\n"
        "/help \\- Эта справка\n\n"
        "*О клубе:*\n"
        "Under People Club \\- это молодёжное студенческое сообщество, "
        "организующее незабываемые вечеринки в Москве\\.\n\n"
        "*Поддержка:*\n"
        "Telegram: @underpeople\\_club\n"
        "Сайт: underpeople\\.club"
    )
    
    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2"
    )


async def about_command(update: Update, context) -> None:
    """Handle /about command."""
    text = (
        "🌑 *Under People Club*\n\n"
        "Мы \\- молодёжное студенческое сообщество, создающее "
        "атмосферу свободы и креатива на наших мероприятиях\\.\n\n"
        "*Что мы делаем:*\n"
        "• Организуем FreeBar вечеринки\n"
        "• Тематические мероприятия\n"
        "• Специальные события для студентов\n"
        "• Создаём пространство для знакомств\n\n"
        "*История:*\n"
        "Мы начали 5 лет назад в кругу студентов МГСУ, "
        "и с каждым разом наши мероприятия становятся всё лучше\\!\n\n"
        "*На наших вечеринках:*\n"
        "• DJ сеты\n"
        "• Кальяны\n"
        "• Конкурсы и развлечения\n"
        "• Профессиональная фото/видео съёмка\n"
        "• Стильные фотозоны\n\n"
        "Присоединяйся к нам\\!"
    )
    
    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2"
    )


async def post_init(application: Application) -> None:
    """Initialize database and other resources."""
    logger.info("initializing_bot")
    
    # Initialize database
    db_manager.init()
    
    # Create tables if they don't exist
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_tables_created")
    
    # Set bot commands
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("profile", "Мой профиль"),
        BotCommand("referral", "Реферальная программа"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("help", "Помощь"),
        BotCommand("about", "О клубе"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("bot_commands_set")


async def post_shutdown(application: Application) -> None:
    """Cleanup resources."""
    logger.info("shutting_down_bot")
    await db_manager.dispose()
    logger.info("bot_shutdown_complete")


def main() -> None:
    """Start the bot."""
    logger.info("starting_upc_world_bot", version="3.0")
    
    try:
        # Create application
        application = (
            Application.builder()
            .token(settings.bot_token)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Register command handlers
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # Register module handlers
        register_start_handlers(application)
        register_profile_handlers(application)
        register_referral_handlers(application)
        register_shop_handlers(application)
        register_admin_handlers(application)
        register_common_handlers(application)
        
        # Start bot
        logger.info("bot_started", mode="polling")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("bot_stopped_by_user")
    except Exception as e:
        logger.error("bot_startup_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
