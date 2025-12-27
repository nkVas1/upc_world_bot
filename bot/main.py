"""
UPC World Bot - Main Bot Logic
Handles Telegram bot initialization and startup for python-telegram-bot 20+.
"""
import asyncio
import sys
import signal
from telegram import Update, BotCommand
from telegram.error import TelegramError, NetworkError, TimedOut
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
    """Initialize resources after Application starts."""
    try:
        logger.info("post_init_starting")
        
        # ✅ Database is now initialized in launcher.py before starting services
        # No need to initialize it here again
        
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
    Run bot in polling mode ASYNCHRONOUSLY with production-grade retry mechanism.
    This is the ASYNC version for use inside an existing event loop.
    CRITICAL: Does NOT create a new event loop.
    
    Implements infinite loop with exponential backoff for maximum reliability.
    Never stops unless explicitly signaled (SIGINT/SIGTERM).
    """
    base_backoff = 5  # Start with 5 seconds
    max_backoff = 300  # Cap at 5 minutes
    consecutive_errors = 0
    max_consecutive = 5  # Reset after success
    
    try:
        logger.info("bot_starting", mode="async_polling_with_retry")
        
        # Initialize the application
        await application.initialize()
        logger.info("application_initialized")
        
        # Start the application
        await application.start()
        logger.info("application_started")
        
        # INFINITE LOOP: Production systems never exit polling
        while True:
            try:
                logger.info(
                    "polling_attempt",
                    consecutive_errors=consecutive_errors,
                    max_retries=max_consecutive
                )
                
                await application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=False,  # Don't drop pending updates
                    poll_interval=0.0,  # No delay between polls
                    timeout=30,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30,
                )
                logger.info("polling_started_successfully")
                
                # Keep running (this blocks forever or until signal)
                print("[BOT] ✅ Telegram Bot is now polling for updates")
                
                # This is a blocking wait for graceful shutdown
                stop_signals = (signal.SIGINT, signal.SIGTERM)
                loop = asyncio.get_event_loop()
                future = loop.create_future()
                
                for sig in stop_signals:
                    loop.add_signal_handler(sig, future.set_result, None)
                
                try:
                    await future
                    logger.info("polling_shutdown_signal_received")
                    break  # Graceful shutdown
                finally:
                    for sig in stop_signals:
                        loop.remove_signal_handler(sig)
                    
            except (NetworkError, TimedOut) as e:
                consecutive_errors += 1
                
                # Calculate backoff with exponential growth
                backoff = min(base_backoff * (2 ** (consecutive_errors - 1)), max_backoff)
                
                logger.warning(
                    "polling_network_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    consecutive_errors=consecutive_errors,
                    max_retries=max_consecutive,
                    backoff_seconds=backoff
                )
                
                # Don't give up - just retry with backoff
                if consecutive_errors >= max_consecutive:
                    logger.warning(
                        "polling_max_consecutive_errors",
                        consecutive_errors=consecutive_errors,
                        cooling_down_seconds=60
                    )
                    backoff = 60  # Cool down for 1 minute
                
                logger.info(
                    "polling_retry_scheduled",
                    retry_in=backoff,
                    next_attempt=consecutive_errors + 1
                )
                await asyncio.sleep(backoff)
                    
            except TelegramError as e:
                consecutive_errors += 1
                backoff = min(base_backoff * (2 ** (consecutive_errors - 1)), max_backoff)
                
                logger.warning(
                    "polling_telegram_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    consecutive_errors=consecutive_errors,
                    backoff_seconds=backoff
                )
                
                await asyncio.sleep(backoff)
                    
            except asyncio.CancelledError:
                logger.info("polling_cancelled")
                raise
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    "polling_unexpected_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    consecutive_errors=consecutive_errors,
                    exc_info=True
                )
                
                # Use longer backoff for unexpected errors
                await asyncio.sleep(60)
        
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
