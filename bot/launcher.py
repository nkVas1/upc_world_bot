"""
Unified entry point for running Bot and API server together.
This is used in production (Railway) to start both services.
"""
import asyncio
import os
import sys
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Critical startup logging BEFORE any imports
print("=" * 70)
print("🚀 Starting UPC World Bot v3.0 with API Server")
print("=" * 70)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

import uvicorn
from bot.config import settings
from bot.utils.logger import logger


async def run_bot():
    """Start Telegram bot in polling mode."""
    try:
        print("[BOT] Loading bot modules...")
        from bot.main import Application
        
        app = Application()
        await app.initialize()
        
        print("[BOT] ✅ Bot initialized")
        print("[BOT] Starting polling...")
        
        await app.start()
        print("[BOT] 🤖 Telegram Bot polling started")
        
        # Keep bot running
        await app.updater.start_polling()
        print("[BOT] Waiting for updates...")
        
    except Exception as e:
        logger.error("bot_startup_error", error=str(e))
        print(f"[BOT] ❌ Bot error: {e}")
        raise


async def run_api():
    """Start FastAPI server."""
    try:
        print("[API] Starting FastAPI server...")
        
        # Get port from environment (Railway sets $PORT dynamically)
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        config = uvicorn.Config(
            "bot.api_server:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=75,  # Keep-alive timeout for Railway proxy
            timeout_notify=30,       # Graceful shutdown timeout
        )
        
        server = uvicorn.Server(config)
        
        print(f"[API] 🌐 FastAPI server starting on {host}:{port}")
        print(f"[API] 📚 API Documentation: http://localhost:{port}/docs")
        print(f"[API] ✅ Health check: http://localhost:{port}/api/health")
        
        await server.serve()
        
    except Exception as e:
        logger.error("api_startup_error", error=str(e))
        print(f"[API] ❌ API error: {e}")
        raise


async def main():
    """Run both bot and API server concurrently."""
    try:
        print("\n" + "=" * 70)
        print("Starting services in parallel mode...")
        print("=" * 70 + "\n")
        
        # Create tasks for bot and API
        # Note: In this implementation, we run API in the main event loop
        # and bot will use polling
        
        # Run both concurrently
        tasks = [
            asyncio.create_task(run_api()),
            asyncio.create_task(run_bot()),
        ]
        
        # Wait for both tasks (they should run indefinitely)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # If any task fails, log and exit
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Task {i} failed: {result}")
                
    except KeyboardInterrupt:
        print("\n[MAIN] ⚠️  Received interrupt signal")
        print("[MAIN] Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error("main_error", error=str(e))
        print(f"[MAIN] ❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            print("\n[MAIN] Received signal, shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run main
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n[MAIN] Bot and API stopped")
        sys.exit(0)
