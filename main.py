import asyncio
import threading
import time
from pyrogram.errors import FloodWait

# Import modular components
from bot.client import app
from bot.handlers import * # Ensures handlers are registered
from database.manager import init_db, cleanup_old_data
from web.health import run_health_check

async def periodic_cleanup():
    """Run database and file cleanup periodically."""
    while True:
        try:
            cleanup_old_data()
            print("Database cleanup completed.")
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(3600)  # Run every hour

def start_bot():
    """Start the Pyrogram bot with retry logic."""
    print("Bot is starting...")
    while True:
        try:
            app.run()
            break
        except FloodWait as e:
            print(f"Telegram FloodWait: Must wait for {e.value} seconds.")
            time.sleep(e.value + 5)
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Initialize Database
    init_db()
    
    # 2. Start Health Check Server in a background thread
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # 3. Setup cleanup task in the event loop
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_cleanup())
    
    # 4. Start the Bot
    start_bot()
