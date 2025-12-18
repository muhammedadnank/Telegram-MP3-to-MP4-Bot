import os
import asyncio
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import proglog
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from database import init_db, add_task, remove_task, can_process, log_action, cleanup_old_data
from converter import convert_mp3_to_mp4

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize the Bot
app = Client(
    "mp3_to_mp4_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Ensure downloads directory exists
DOWNLOAD_DIR = "downloads"

import time
import proglog
from utils import create_progress_box

class TelegramLogger(proglog.ProgressBarLogger):
    """Custom logger for MoviePy to capture progress."""
    def __init__(self, data):
        super().__init__()
        self.data = data

    def callback(self, **kwargs):
        bar = self.bars.get('chunk') or self.bars.get('tqdm') or self.bars.get('index')
        if bar:
            self.data['current'] = bar['index']
            self.data['total'] = bar['total']

async def progress_callback(current, total, status_msg, task_name, status, start_time, last_update):
    """Callback for Pyrogram to update progress UI."""
    now = time.time()
    # Update every 3 seconds to avoid rate matching
    if (now - last_update[0]) < 3 and current < total:
        return
    
    last_update[0] = now
    box = create_progress_box(current, total, task_name, status, start_time)
    try:
        await status_msg.edit_text(f"<code>{box}</code>", parse_mode="html")
    except Exception:
        pass

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "👋 Hello! Send me an MP3 file, and I'll convert it into an MP4 video with a black background for you."
    )

@app.on_message(filters.audio)
async def audio_handler(client, message: Message):
    user_id = message.from_user.id
    
    if not can_process(user_id):
        await message.reply_text("⏳ Please wait! I am already processing a file for you.")
        return

    log_action(user_id, "UPLOAD_MP3")
    add_task(user_id)
    
    start_time = time.time()
    last_update = [0]
    task_name = "MP3 to MP4 Conversion"
    
    # 1. Start with Download
    initial_box = create_progress_box(0, message.audio.file_size, task_name, "Downloading Audio...", start_time)
    status_msg = await message.reply_text(f"<code>{initial_box}</code>", parse_mode="html")
    
    try:
        # Step 1: Download
        file_path = await message.download(
            file_name=os.path.join(DOWNLOAD_DIR, f"{message.audio.file_id}.mp3"),
            progress=progress_callback,
            progress_args=(status_msg, task_name, "Downloading Audio...", start_time, last_update)
        )
        
        # Step 2: Conversion
        output_file = file_path.replace(".mp3", ".mp4")
        conv_current_total = {'current': 0, 'total': 100}
        logger = TelegramLogger(conv_current_total)
        conv_done = asyncio.Event()

        async def update_conv_ui():
            while not conv_done.is_set():
                if conv_current_total['total'] > 0:
                    box = create_progress_box(
                        conv_current_total['current'], 
                        conv_current_total['total'], 
                        task_name, "Processing Video...", start_time,
                        is_bytes=False
                    )
                    try: await status_msg.edit_text(f"<code>{box}</code>", parse_mode="html")
                    except: pass
                await asyncio.sleep(4)

        ui_task = asyncio.create_task(update_conv_ui())
        loop = asyncio.get_event_loop()
        try:
            success = await loop.run_in_executor(None, convert_mp3_to_mp4, file_path, output_file, logger)
        finally:
            conv_done.set()
            await ui_task
        
        if success:
            # Step 3: Upload
            last_update[0] = 0 # Reset for upload
            file_size = os.path.getsize(output_file)
            await message.reply_video(
                video=output_file,
                caption="✅ Here is your MP4 video!",
                duration=message.audio.duration,
                progress=progress_callback,
                progress_args=(status_msg, task_name, "Uploading Result...", start_time, last_update)
            )
            await status_msg.delete()
            log_action(user_id, "CONVERSION_SUCCESS")
        else:
            await status_msg.edit_text("❌ Failed to convert the file.")
            log_action(user_id, "CONVERSION_FAILED")

        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(output_file): os.remove(output_file)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")
    finally:
        remove_task(user_id)

async def periodic_cleanup():
    """Run database and file cleanup periodically."""
    while True:
        try:
            cleanup_old_data()
            print("Database cleanup completed.")
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(3600)  # Run every hour

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server started on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # Initialize DB
    init_db()
    
    # Start health check server in a separate thread for Render
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Start the bot
    print("Bot is starting...")
    
    # Create background cleanup task
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_cleanup())
    
    app.run()
