"""
Unified launcher for Bot + API (Railway Production)
Runs Telegram bot polling and FastAPI server concurrently in single event loop.
"""
import asyncio
import os
import sys
import signal
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("🚀 Starting UPC World Bot v3.0 with API Server")
print("=" * 70)
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print()


async def initialize_database():
    """
    Initialize database ONCE before starting both bot and API.
    CRITICAL: Both bot and API need database access, so initialize FIRST.
    """
    try:
        print("[DB] Initializing database...")
        
        from bot.database.session import db_manager
        from bot.database.base import Base
        from bot.utils.logger import logger
        
        # Initialize database manager (creates engine and session factory)
        db_manager.init()
        logger.info("database_manager_initialized")
        
        # Create tables if they don't exist
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("database_tables_created")
        print("[DB] ✅ Database initialized successfully")
        
    except Exception as e:
        print(f"[DB] ❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def start_bot():
    """Start Telegram bot in ASYNC polling mode."""
    try:
        print("[BOT] Loading bot modules...")
        
        # Import AFTER sys.path is set
        from bot.main import create_application, run_bot_async
        from bot.utils.logger import logger
        
        logger.info("bot_task_starting")
        
        # Create application (without post_init database initialization)
        app = await create_application()
        
        print("[BOT] ✅ Application created successfully")
        print("[BOT] 🤖 Starting Telegram Bot polling...")
        
        # Run polling ASYNC
        await run_bot_async(app)
        
    except asyncio.CancelledError:
        print("[BOT] ⚠️  Bot task cancelled")
        raise
    except Exception as e:
        print(f"[BOT] ❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
        raise


async def start_api():
    """Start FastAPI server."""
    try:
        print("[API] Starting FastAPI server...")
        
        import uvicorn
        from bot.api_server import app
        from bot.utils.logger import logger
        
        logger.info("api_task_starting")
        
        # Get port from environment (Railway sets PORT dynamically)
        port = int(os.getenv("PORT", "8000"))
        host = "0.0.0.0"  # Listen on all interfaces for Railway
        
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=75,
        )
        
        server = uvicorn.Server(config)
        
        print(f"[API] 🌐 API starting on {host}:{port}")
        print(f"[API] 📚 Docs: http://localhost:{port}/docs")
        print(f"[API] ✅ Health: http://localhost:{port}/api/health")
        
        logger.info("api_server_starting")
        
        # Start server (blocks forever)
        await server.serve()
        
    except asyncio.CancelledError:
        print("[API] ⚠️  API task cancelled")
        raise
    except Exception as e:
        print(f"[API] ❌ API error: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Run bot and API concurrently in single event loop."""
    try:
        print()
        print("=" * 70)
        print("Initializing services...")
        print("=" * 70)
        print()
        
        # CRITICAL FIX: Initialize database FIRST before starting services
        await initialize_database()
        
        print()
        print("=" * 70)
        print("Starting services in parallel mode...")
        print("=" * 70)
        print()
        
        # Create tasks for both services
        bot_task = asyncio.create_task(start_bot(), name="telegram_bot")
        api_task = asyncio.create_task(start_api(), name="fastapi_server")
        
        # Wait for both tasks to complete (they should run forever)
        # If any task raises an exception, both will be cancelled
        try:
            await asyncio.gather(bot_task, api_task)
        except Exception as e:
            print(f"\n[MAIN] ❌ Exception in main loop: {e}")
            
            # Cancel both tasks
            bot_task.cancel()
            api_task.cancel()
            
            # Wait for cancellation
            await asyncio.gather(bot_task, api_task, return_exceptions=True)
            
            raise
        
    except KeyboardInterrupt:
        print("\n[MAIN] ⚠️  Keyboard interrupt received")
    except Exception as e:
        print(f"\n[MAIN] ❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("[MAIN] Shutting down...")
        
        # Cleanup database
        try:
            from bot.database.session import db_manager
            await db_manager.dispose()
            print("[DB] ✅ Database disposed")
        except Exception as e:
            print(f"[DB] ⚠️  Database cleanup error: {e}")


if __name__ == "__main__":
    # Setup signal handlers
    def handle_signal(sig, frame):
        print(f"\n[MAIN] Signal {sig} received, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Run main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Stopped by user")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n[MAIN] Unexpected error: {e}")
        sys.exit(1)
