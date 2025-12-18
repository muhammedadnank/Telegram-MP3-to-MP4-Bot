import os
import asyncio
import time
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.client import app, ongoing_tasks, OWNER_ID, DOWNLOAD_DIR
from bot.ui import progress_callback, TelegramLogger, create_progress_box
from database.manager import add_task, remove_task, can_process, log_action, get_stats, get_all_users, clear_all_tasks
from core.converter import convert_mp3_to_mp4, CancelledError

# BUTTONS
START_BUTTONS = InlineKeyboardMarkup([[
    InlineKeyboardButton("📖 Help", callback_data="help_ui"),
    InlineKeyboardButton("📊 Status", callback_data="status_ui")
], [
    InlineKeyboardButton("❌ Cancel Active", callback_data="cancel_task")
]])

BACK_BUTTON = InlineKeyboardMarkup([[
    InlineKeyboardButton("⬅️ Back", callback_data="start_ui")
]])

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
            "This bot is designed to create black-background videos from audio files.\n\n"
            "🛠 <b>Available Commands:</b>\n"
            "• /start - Restart the bot\n"
            "• /status - Check bot load and stats\n"
            "• /help - Show this help message\n\n"
            "🛑 <b>Features:</b>\n"
            "- Real-time progress tracking\n"
            "- Reliable task cancellation\n"
            "- Automatic cleanup"
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

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "👋 <b>Welcome to MP3 to MP4 Bot!</b>\n\n"
        "I can convert your MP3 audio files into high-quality MP4 videos.\n\n"
        "📖 Use the buttons below for more info.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=START_BUTTONS
    )

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    help_text = (
        "❓ <b>Need Help?</b>\n\n"
        "• /start - Restart the bot\n"
        "• /status - Check bot load and stats\n"
        "• /cancel - Cancel your active task\n"
        "• /help - Show this help message"
    )
    await message.reply_text(help_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)

@app.on_message(filters.command("status"))
async def status_handler(client, message: Message):
    stats = get_stats()
    status_text = (
        "🤖 <b>Bot Status Report</b>\n\n"
        f"📊 <b>Total Processed:</b> {stats['total_conversions']}\n"
        f"👥 <b>Unique Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Current Load:</b> {stats['active_tasks']} active tasks"
    )
    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML, reply_markup=BACK_BUTTON)

@app.on_message(filters.command("cancel"))
async def cancel_command_handler(client, message: Message):
    user_id = message.from_user.id
    cancelled = False
    if user_id in ongoing_tasks:
        ongoing_tasks[user_id].set()
        cancelled = True
    if not can_process(user_id):
        remove_task(user_id)
        cancelled = True
        
    if cancelled:
        await message.reply_text("✅ <b>Tasks cleared.</b> You can send a new file now.", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("❌ <b>No active tasks.</b>", parse_mode=enums.ParseMode.HTML)

# ADMIN COMMANDS
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
            await asyncio.sleep(0.05)
        except: pass
    await status_msg.edit_text(f"✅ <b>Broadcast Complete!</b> Sent to {count} users.", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def admin_stats_handler(client, message: Message):
    stats = get_stats()
    admin_text = (
        "👑 <b>Admin Dashboard</b>\n\n"
        f"✅ <b>Conversions:</b> {stats['total_conversions']}\n"
        f"👥 <b>Total Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Active Tasks:</b> {stats['active_tasks']}"
    )
    await message.reply_text(admin_text, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("clearall") & filters.user(OWNER_ID))
async def clear_all_handler(client, message: Message):
    clear_all_tasks()
    ongoing_tasks.clear()
    await message.reply_text("🚨 <b>Emergency Reset Complete.</b>", parse_mode=enums.ParseMode.HTML)

# AUDIO HANDLER
@app.on_message(filters.audio)
async def audio_handler(client, message: Message):
    user_id = message.from_user.id
    if not can_process(user_id):
        await message.reply_text("⏳ <b>Already processing.</b> Use /cancel if stuck.")
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
    
    initial_box = create_progress_box(0, message.audio.file_size, task_name, "Downloading Audio...", start_time)
    status_msg = await message.reply_text(
        f"<code>{initial_box}</code>", 
        parse_mode=enums.ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    file_path = None
    output_file = None
    try:
        file_path = await message.download(
            file_name=os.path.join(DOWNLOAD_DIR, f"{message.audio.file_id}.mp3"),
            progress=progress_callback,
            progress_args=(status_msg, task_name, "Downloading Audio...", start_time, last_update, user_id, ongoing_tasks)
        )
        
        output_file = file_path.replace(".mp3", ".mp4")
        conv_current_total = {'current': 0, 'total': 0}
        logger = TelegramLogger(conv_current_total, ongoing_tasks[user_id])
        conv_done = asyncio.Event()

        async def update_conv_ui():
            while not conv_done.is_set():
                if ongoing_tasks[user_id].is_set(): break
                status_text = conv_current_total.get('status', "Processing Video...")
                if conv_current_total['total'] > 0:
                    box = create_progress_box(conv_current_total['current'], conv_current_total['total'], task_name, status_text, start_time, is_bytes=False)
                else:
                    box = create_progress_box(0, 100, task_name, status_text, start_time, is_bytes=False)
                try: 
                    await status_msg.edit_text(f"<code>{box}</code>", parse_mode=enums.ParseMode.HTML, reply_markup=reply_markup)
                except: pass
                await asyncio.sleep(4)

        ui_task = asyncio.create_task(update_conv_ui())
        loop = asyncio.get_event_loop()
        try:
            success = await loop.run_in_executor(None, convert_mp3_to_mp4, file_path, output_file, logger)
            if ongoing_tasks[user_id].is_set():
                raise CancelledError("Task cancelled.")
        finally:
            conv_done.set()
            await ui_task
        
        if success:
            last_update[0] = 0
            await message.reply_video(
                video=output_file,
                caption="✅ Here is your MP4 video!",
                duration=message.audio.duration,
                progress=progress_callback,
                progress_args=(status_msg, task_name, "Uploading Result...", start_time, last_update, user_id, ongoing_tasks)
            )
            await status_msg.delete()
            log_action(user_id, "CONVERSION_SUCCESS")
        else:
            await status_msg.edit_text("❌ Conversion failed.")
            log_action(user_id, "CONVERSION_FAILED")

    except CancelledError:
        try: await status_msg.edit_text("⚠️ Task cancelled.")
        except: pass
        log_action(user_id, "CONVERSION_CANCELLED")
    except Exception as e:
        print(f"Error: {e}")
        try: await message.reply_text(f"❌ Error: {str(e)}")
        except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)
        if output_file and os.path.exists(output_file): os.remove(output_file)
        remove_task(user_id)
        if user_id in ongoing_tasks: del ongoing_tasks[user_id]
