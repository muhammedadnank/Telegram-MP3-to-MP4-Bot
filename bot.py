import os
import asyncio
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import proglog
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv
from database import init_db, add_task, remove_task, can_process, log_action, cleanup_old_data, get_stats, get_all_users, clear_all_tasks
from converter import convert_mp3_to_mp4
from utils import create_progress_box, CancelledError

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "1751433177")) # Default to a value or 0

# Initialize the Bot
app = Client(
    "mp3_to_mp4_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Ensure downloads directory exists
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Global dictionary to track cancellation events
ongoing_tasks = {}

# ADVANCED UI: BUTTONS
START_BUTTONS = InlineKeyboardMarkup([[
    InlineKeyboardButton("📖 Help", callback_data="help_ui"),
    InlineKeyboardButton("📊 Status", callback_data="status_ui")
], [
    InlineKeyboardButton("❌ Cancel Active", callback_data="cancel_task")
]])

BACK_BUTTON = InlineKeyboardMarkup([[
    InlineKeyboardButton("⬅️ Back", callback_data="start_ui")
]])

# HELPER FUNCTIONS FOR PROGRESS UI
async def progress_callback(current, total, status_msg, task_name, status_text, start_time, last_update, user_id):
    if user_id in ongoing_tasks and ongoing_tasks[user_id].is_set():
        raise CancelledError("Task cancelled by user.")
    
    # Update every 4 seconds to avoid flood
    now = time.time()
    if now - last_update[0] < 4:
        return
    
    last_update[0] = now
    box = create_progress_box(current, total, task_name, status_text, start_time)
    
    try:
        await status_msg.edit_text(
            f"<code>{box}</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Cancel ❌", callback_data="cancel_task")
            ]])
        )
    except Exception:
        pass

class TelegramLogger(proglog.ProgressBarLogger):
    def __init__(self, progress_dict, cancel_event):
        super().__init__()
        self.progress_dict = progress_dict
        self.cancel_event = cancel_event

    def callback(self, **changes):
        if self.cancel_event.is_set():
            raise CancelledError("Task cancelled during conversion.")
        
        # Log any bars that show up
        if 'bars' in changes:
            for bar_name, bar_data in changes['bars'].items():
                if bar_data['total'] > 1: # Ignore tiny bars
                    self.progress_dict['current'] = bar_data['index']
                    self.progress_dict['total'] = bar_data['total']
                    # Optional: print for server logs
                    if bar_data['index'] % 100 == 0:
                        print(f"DEBUG: Bar '{bar_name}' progress: {bar_data['index']}/{bar_data['total']}")
        
        if 'message' in changes:
            # Clean up MoviePy messages
            msg = changes['message'].replace("MoviePy - ", "")
            self.progress_dict['status'] = msg
            print(f"DEBUG: Status Update: {msg}")

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "cancel_task":
        if user_id in ongoing_tasks:
            ongoing_tasks[user_id].set()
            await callback_query.answer("Cancelling task... ⏳", show_alert=True)
        else:
            await callback_query.answer("No active task to cancel.", show_alert=True)
            try: await callback_query.message.delete()
            except: pass
            
    elif data == "start_ui":
        await callback_query.message.edit_text(
            "👋 <b>Welcome to MP3 to MP4 Bot!</b>\n\n"
            "I can convert your MP3 audio files into high-quality MP4 videos with a professional black background.\n\n"
            "⚡ <b>How to Use:</b>\n"
            "1. Send any MP3 audio file to me.\n"
            "2. Wait for the conversion to complete.\n"
            "3. Download your MP4 video!\n\n"
            "📖 Use the buttons below for more info.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=START_BUTTONS
        )
        
    elif data == "help_ui":
        help_text = (
            "❓ <b>Need Help?</b>\n\n"
            "This bot is designed to create black-background videos from audio files. Perfect for uploading music to platforms like YouTube or Telegram as video.\n\n"
            "🛠 <b>Available Commands:</b>\n"
            "• /start - Restart the bot\n"
            "• /status - Check bot load and stats\n"
            "• /help - Show this help message\n\n"
            "🛑 <b>Features:</b>\n"
            "- Real-time progress tracking\n"
            "- Reliable task cancellation\n"
            "- Automatic cleanup of temporary files"
        )
        await callback_query.message.edit_text(help_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)
        
    elif data == "status_ui":
        stats = get_stats()
        status_text = (
            "🤖 <b>Bot Status Report</b>\n\n"
            f"📊 <b>Total Processed:</b> {stats['total_conversions']}\n"
            f"👥 <b>Unique Users:</b> {stats['unique_users']}\n"
            f"⏳ <b>Current Load:</b> {stats['active_tasks']} active tasks\n\n"
            "✨ <i>Running smoothly on Render!</i>"
        )
        await callback_query.message.edit_text(status_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)

# BASIC COMMANDS
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "👋 <b>Welcome to MP3 to MP4 Bot!</b>\n\n"
        "I can convert your MP3 audio files into high-quality MP4 videos with a professional black background.\n\n"
        "⚡ <b>How to Use:</b>\n"
        "1. Send any MP3 audio file to me.\n"
        "2. Wait for the conversion to complete.\n"
        "3. Download your MP4 video!\n\n"
        "📖 Use the buttons below for more info.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=START_BUTTONS
    )

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await help_ui_message(message)

async def help_ui_message(message: Message):
    help_text = (
        "❓ <b>Need Help?</b>\n\n"
        "This bot is designed to create black-background videos from audio files. Perfect for uploading music to platforms like YouTube or Telegram as video.\n\n"
        "🛠 <b>Available Commands:</b>\n"
        "• /start - Restart the bot\n"
        "• /status - Check bot load and stats\n"
        "• /cancel - Cancel your active task\n"
        "• /help - Show this help message\n\n"
        "🛑 <b>Features:</b>\n"
        "- Real-time progress tracking\n"
        "- Reliable task cancellation\n"
        "- Automatic cleanup of temporary files"
    )
    await message.reply_text(help_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)


@app.on_message(filters.command("status"))
async def status_handler(client, message: Message):
    stats = get_stats()
    status_text = (
        "🤖 <b>Bot Status Report</b>\n\n"
        f"📊 <b>Total Processed:</b> {stats['total_conversions']}\n"
        f"👥 <b>Unique Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Current Load:</b> {stats['active_tasks']} active tasks\n\n"
        "✨ <i>Running smoothly on Render!</i>"
    )
    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)

@app.on_message(filters.command("cancel"))
async def cancel_command_handler(client, message: Message):
    user_id = message.from_user.id
    cancelled = False
    
    # Check memory first
    if user_id in ongoing_tasks:
        ongoing_tasks[user_id].set()
        cancelled = True
    
    # Always check/clear DB just in case of ghost tasks
    if not can_process(user_id):
        remove_task(user_id)
        cancelled = True
        
    if cancelled:
        await message.reply_text("✅ <b>Any active or stuck tasks have been cleared.</b> You can send a new file now.", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("❌ <b>You have no active tasks to cancel.</b>", parse_mode=enums.ParseMode.HTML)

# ADMIN TOOLS
@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def users_handler(client, message: Message):
    stats = get_stats()
    await message.reply_text(f"👥 <b>Total Unique Users:</b> {stats['unique_users']}", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a message to broadcast it.")
        return
    
    users = get_all_users()
    count = 0
    status_msg = await message.reply_text(f"📣 <b>Broadcasting to {len(users)} users...</b>", parse_mode=enums.ParseMode.HTML)
    
    for user_id in users:
        try:
            await message.reply_to_message.copy(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05) # Rate limit
        except:
            pass
            
    await status_msg.edit_text(f"✅ <b>Broadcast Complete!</b>\nSuccessfully sent to {count} users.", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def admin_stats_handler(client, message: Message):
    stats = get_stats()
    admin_text = (
        "👑 <b>Admin Dashboard - Stats</b>\n\n"
        f"✅ <b>Successful Conversions:</b> {stats['total_conversions']}\n"
        f"👥 <b>Total Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Current Processing Tasks:</b> {stats['active_tasks']}\n"
        f"📁 <b>Temporary Dir Files:</b> {len(os.listdir(DOWNLOAD_DIR))}\n\n"
        "<i>Use /clearall if tasks are stuck globally.</i>"
    )
    await message.reply_text(admin_text, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("clearall") & filters.user(OWNER_ID))
async def clear_all_handler(client, message: Message):
    clear_all_tasks()
    ongoing_tasks.clear()
    await message.reply_text("🚨 <b>Emergency Reset Complete:</b> All tasks cleared from DB and memory.", parse_mode=enums.ParseMode.HTML)

# CORE AUDIO HANDLER
@app.on_message(filters.audio)
async def audio_handler(client, message: Message):
    user_id = message.from_user.id
    
    if not can_process(user_id):
        await message.reply_text("⏳ <b>I am already processing a file for you.</b>\n\nIf you think this is a mistake or the bot is stuck, use /cancel to clear it.")
        return

    log_action(user_id, "UPLOAD_MP3")
    add_task(user_id)
    ongoing_tasks[user_id] = asyncio.Event()
    
    start_time = time.time()
    last_update = [0]
    task_name = "MP3 to MP4 Conversion"
    
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Cancel ❌", callback_data="cancel_task")
    ]])
    
    # 1. Start with Download
    initial_box = create_progress_box(0, message.audio.file_size, task_name, "Downloading Audio...", start_time)
    status_msg = await message.reply_text(
        f"<code>{initial_box}</code>", 
        parse_mode=enums.ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    file_path = None
    output_file = None
    
    try:
        # Step 1: Download
        file_path = await message.download(
            file_name=os.path.join(DOWNLOAD_DIR, f"{message.audio.file_id}.mp3"),
            progress=progress_callback,
            progress_args=(status_msg, task_name, "Downloading Audio...", start_time, last_update, user_id)
        )
        
        # Step 2: Conversion
        output_file = file_path.replace(".mp3", ".mp4")
        conv_current_total = {'current': 0, 'total': 0}
        logger = TelegramLogger(conv_current_total, ongoing_tasks[user_id])
        conv_done = asyncio.Event()

        async def update_conv_ui():
            while not conv_done.is_set():
                if ongoing_tasks[user_id].is_set():
                    break
                status_text = conv_current_total.get('status', "Processing Video...")
                if conv_current_total['total'] > 0:
                    box = create_progress_box(
                        conv_current_total['current'], 
                        conv_current_total['total'], 
                        task_name, status_text, start_time,
                        is_bytes=False
                    )
                else:
                    box = create_progress_box(
                        0, 100, 
                        task_name, status_text, start_time,
                        is_bytes=False
                    )
                try: 
                    await status_msg.edit_text(
                        f"<code>{box}</code>", 
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                except:
                    pass
                await asyncio.sleep(4)

        ui_task = asyncio.create_task(update_conv_ui())
        loop = asyncio.get_event_loop()
        try:
            success = await loop.run_in_executor(None, convert_mp3_to_mp4, file_path, output_file, logger)
            if ongoing_tasks[user_id].is_set():
                raise CancelledError("Task cancelled during conversion.")
        finally:
            conv_done.set()
            await ui_task
        
        if success:
            # Step 3: Upload
            last_update[0] = 0 # Reset for upload
            await message.reply_video(
                video=output_file,
                caption="✅ Here is your MP4 video!",
                duration=message.audio.duration,
                progress=progress_callback,
                progress_args=(status_msg, task_name, "Uploading Result...", start_time, last_update, user_id)
            )
            await status_msg.delete()
            log_action(user_id, "CONVERSION_SUCCESS")
        else:
            await status_msg.edit_text("❌ Failed to convert the file.")
            log_action(user_id, "CONVERSION_FAILED")

    except CancelledError:
        try: await status_msg.edit_text("⚠️ Task cancelled by user.")
        except: pass
        log_action(user_id, "CONVERSION_CANCELLED")
    except Exception as e:
        print(f"Error: {e}")
        try: await message.reply_text(f"❌ Error: {str(e)}")
        except: pass
    finally:
        # Cleanup files
        if file_path and os.path.exists(file_path): os.remove(file_path)
        if output_file and os.path.exists(output_file): os.remove(output_file)
        
        # Remove task references
        remove_task(user_id)
        if user_id in ongoing_tasks:
            del ongoing_tasks[user_id]

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

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server started on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_health_check, daemon=True).start()
    print("Bot is starting...")
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_cleanup())
    
    while True:
        try:
            app.run()
            break # Exit loop if bot stops normally
        except FloodWait as e:
            print(f"Telegram FloodWait: Must wait for {e.value} seconds.")
            time.sleep(e.value + 5) # Adding a buffer
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(10) # Brief pause before restart
