"""
UPC World Bot - Main Bot Logic
Handles Telegram bot initialization and startup for python-telegram-bot 20+.
"""
import asyncio
import sys
import signal
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
    """Initialize database and resources after Application starts."""
    try:
        logger.info("post_init_starting")
        
        # Initialize database
        await db_manager.initialize()
        logger.info("database_initialized")
        
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
        logger.info("post_init_complete")
        
    except Exception as e:
        logger.error("post_init_error", error=str(e), exc_info=True)
        raise


async def post_shutdown(application: Application) -> None:
    """Cleanup resources after Application stops."""
    try:
        logger.info("post_shutdown_starting")
        await db_manager.close()
        logger.info("post_shutdown_complete")
    except Exception as e:
        logger.error("post_shutdown_error", error=str(e))


def register_handlers(application: Application) -> None:
    """Register all command and message handlers."""
    try:
        logger.info("registering_handlers")
        
        # Add error handler first
        application.add_error_handler(error_handler)
        
        # Register module handlers
        register_start_handlers(application)
        register_profile_handlers(application)
        register_referral_handlers(application)
        register_shop_handlers(application)
        register_admin_handlers(application)
        register_common_handlers(application)
        
        logger.info("handlers_registered")
        
    except Exception as e:
        logger.error("handler_registration_error", error=str(e), exc_info=True)
        raise


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
        
        # Register handlers BEFORE starting
        register_handlers(app)
        
        logger.info("application_created")
        return app
        
    except Exception as e:
        logger.error("application_creation_error", error=str(e), exc_info=True)
        raise


async def run_bot_async(application: Application) -> None:
    """
    Run bot in polling mode ASYNCHRONOUSLY.
    This is the ASYNC version for use inside an existing event loop.
    CRITICAL: Does NOT create a new event loop.
    """
    try:
        logger.info("bot_starting", mode="async_polling")
        
        # Initialize the application
        await application.initialize()
        logger.info("application_initialized")
        
        # Start the application
        await application.start()
        logger.info("application_started")
        
        # Start polling
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("polling_started")
        
        # Keep running (this blocks forever)
        print("[BOT] ✅ Telegram Bot is now polling for updates")
        
        # This is a blocking wait, but it's async-safe
        stop_signals = (signal.SIGINT, signal.SIGTERM)
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        for sig in stop_signals:
            loop.add_signal_handler(sig, future.set_result, None)
        
        try:
            await future
        finally:
            for sig in stop_signals:
                loop.remove_signal_handler(sig)
        
    except asyncio.CancelledError:
        logger.info("bot_cancelled")
        raise
    except Exception as e:
        logger.error("bot_error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("bot_stopping")
        try:
            # Stop polling
            if application.updater and application.updater.running:
                await application.updater.stop()
            
            # Stop application
            await application.stop()
            
            # Shutdown application
            await application.shutdown()
            
            logger.info("bot_stopped")
        except Exception as e:
            logger.error("bot_cleanup_error", error=str(e))


# For direct standalone execution (NOT used in Railway with launcher.py)
def main_standalone() -> None:
    """Standalone entry point - creates its own event loop."""
    try:
        logger.info("starting_bot_standalone", version="3.0")
        
        async def run():
            app = await create_application()
            await run_bot_async(app)
        
        asyncio.run(run())
        
    except KeyboardInterrupt:
        logger.info("bot_stopped_by_user")
    except Exception as e:
        logger.error("bot_startup_error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Direct execution
    main_standalone()
