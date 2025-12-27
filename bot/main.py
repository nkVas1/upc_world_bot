"""
UPC World Bot - Main Bot Logic
Handles Telegram bot initialization and startup for python-telegram-bot 20+.
Uses Application.builder() pattern (REQUIRED for v20+).
"""
import asyncio
import sys
import os
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from bot.config import settings
from bot.database.session import db_manager
from bot.database.base import Base
from bot.utils.logger import logger
from bot.utils.navigation import NavigationManager

# Import handlers
from bot.handlers.start import register_start_handlers
from bot.handlers.profile import register_profile_handlers
from bot.handlers.referral import register_referral_handlers
from bot.handlers.shop import register_shop_handlers
from bot.handlers.admin import register_admin_handlers
from bot.handlers.common import register_common_handlers

async def error_handler(update: object, context) -> None:
    """Handle errors during telegram updates."""
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


async def post_init(application: Application) -> None:
    """Initialize database and resources after Application.start()."""
    logger.info("initializing_bot")
    
    # Initialize database
    await db_manager.initialize()
    
    # Create tables if they don't exist
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("database_tables_created")
    
    # Set bot commands
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("login", "🔐 Вход на сайт"),
        BotCommand("profile", "👤 Мой профиль"),
        BotCommand("referral", "👥 Реферальная программа"),
        BotCommand("shop", "🛒 Магазин"),
        BotCommand("help", "❓ Помощь"),
        BotCommand("about", "ℹ️ О клубе"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("bot_commands_set")


async def post_shutdown(application: Application) -> None:
    """Cleanup resources after Application.stop()."""
    logger.info("shutting_down_bot")
    await db_manager.close()
    logger.info("bot_shutdown_complete")


async def create_application() -> Application:
    """
    Create and configure Telegram Application using builder pattern.
    REQUIRED for python-telegram-bot 20+.
    """
    try:
        logger.info("creating_application")
        
        # Build Application using builder pattern (REQUIRED for v20+)
        app = (
            Application.builder()
            .token(settings.bot_token)
            .concurrent_updates(True)
            .read_timeout(30)
            .write_timeout(30)
            .connect_timeout(30)
            .pool_timeout(30)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        
        logger.info("application_created")
        return app
        
    except Exception as e:
        logger.error("application_creation_error", error=str(e), exc_info=True)
        raise


def register_handlers(application: Application) -> None:
    """Register all command and message handlers."""
    logger.info("registering_handlers")
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Register module handlers
    register_start_handlers(application)
    register_profile_handlers(application)
    register_referral_handlers(application)
    register_shop_handlers(application)
    register_admin_handlers(application)
    register_common_handlers(application)
    
    logger.info("handlers_registered")


def run_polling(application: Application) -> None:
    """Run bot in polling mode."""
    try:
        logger.info("bot_starting_polling", mode="polling")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("bot_stopped_by_user")
    except Exception as e:
        logger.error(
            "polling_error", 
            error=str(e),
            exc_info=True
        )
        raise


def main() -> None:
    """Main entry point for the bot."""
    try:
        logger.info("starting_bot", version="3.0")
        
        # Create application
        app = asyncio.run(create_application())
        
        # Register handlers
        register_handlers(app)
        
        # Run polling
        run_polling(app)
        
    except Exception as e:
        # Critical error logging to stdout for Railway
        print("=" * 60)
        print("❌ BOT STARTUP ERROR")
        print("=" * 60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 60)
        
        logger.error(
            "bot_startup_error", 
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
