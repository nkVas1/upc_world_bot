"""
Unified launcher for Bot + API (Railway Production)
Runs Telegram bot polling and FastAPI server concurrently.
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


async def start_bot():
    """Start Telegram bot in polling mode."""
    try:
        print("[BOT] Loading bot modules...")
        
        # Import AFTER sys.path is set
        from bot.main import create_application, run_polling
        from bot.utils.logger import logger
        
        logger.info("bot_task_starting")
        
        # Create application
        app = await create_application()
        
        print("[BOT] ✅ Application created successfully")
        print("[BOT] 🤖 Starting Telegram Bot polling...")
        
        # Run polling (blocks forever)
        run_polling(app)
        
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
        
        # FIXED: Removed invalid shutdown_delay parameter
        # Only use parameters that exist in uvicorn.Config
        config = uvicorn.Config(
            app,  # Pass app object directly
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=75,  # For Railway proxy timeout
        )
        
        server = uvicorn.Server(config)
        
        print(f"[API] 🌐 API starting on {host}:{port}")
        print(f"[API] 📚 Docs: http://localhost:{port}/docs")
        print(f"[API] ✅ Health: http://localhost:{port}/api/health")
        
        logger.info("cors_configured")
        
        # Start server (blocks forever)
        await server.serve()
        
    except Exception as e:
        print(f"[API] ❌ API error: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Run bot and API concurrently."""
    try:
        print()
        print("=" * 70)
        print("Starting services in parallel mode...")
        print("=" * 70)
        print()
        
        # Create tasks
        bot_task = asyncio.create_task(start_bot(), name="bot")
        api_task = asyncio.create_task(start_api(), name="api")
        
        # Wait for both (they run forever)
        done, pending = await asyncio.wait(
            [bot_task, api_task],
            return_when=asyncio.FIRST_EXCEPTION  # Stop if one fails
        )
        
        # If we reach here, one task crashed
        for task in done:
            if task.exception():
                print(f"❌ Task '{task.get_name()}' failed:")
                print(f"   {task.exception()}")
                
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n[MAIN] ⚠️  Interrupt received, shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"[MAIN] ❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Signal handlers
    def handle_signal(sig, frame):
        print(f"\n[MAIN] Signal {sig} received, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Run
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Stopped")
