import os
import asyncio
import time
from telethon import events, Button
from telethon.tl.types import DocumentAttributeAudio

from bot.client import client, ongoing_tasks, OWNER_ID, DOWNLOAD_DIR
from bot.ui import progress_callback, TelegramLogger, create_progress_box
from database.manager import add_task, remove_task, can_process, log_action, get_stats, get_all_users, clear_all_tasks
from core.converter import convert_mp3_to_mp4, CancelledError

# BUTTONS
START_BUTTONS = [
    [
        Button.inline("📖 Help", data=b"help_ui"),
        Button.inline("📊 Status", data=b"status_ui")
    ],
    [
        Button.inline("❌ Cancel Active", data=b"cancel_task")
    ]
]

BACK_BUTTON = [[Button.inline("⬅️ Back", data=b"start_ui")]]

@client.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data
    user_id = event.sender_id
    
    if data == b"cancel_task":
        if user_id in ongoing_tasks:
            ongoing_tasks[user_id].set()
            await event.answer("Cancelling task... ⏳", alert=True)
        else:
            await event.answer("No active task to cancel.", alert=True)
            try: await event.delete()
            except: pass
            
    elif data == b"start_ui":
        await event.edit(
            "👋 <b>Welcome to MP3 to MP4 Bot!</b>\n\n"
            "I can convert your MP3 audio files into high-quality MP4 videos with a professional black background.\n\n"
            "⚡ <b>How to Use:</b>\n"
            "1. Send any MP3 audio file to me.\n"
            "2. Wait for the conversion to complete.\n"
            "3. Download your MP4 video!\n\n"
            "📖 Use the buttons below for more info.",
            parse_mode='html',
            buttons=START_BUTTONS
        )
        
    elif data == b"help_ui":
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
        await event.edit(help_text, parse_mode='html', buttons=BACK_BUTTON)
        
    elif data == b"status_ui":
        stats = get_stats()
        status_text = (
            "🤖 <b>Bot Status Report</b>\n\n"
            f"📊 <b>Total Processed:</b> {stats['total_conversions']}\n"
            f"👥 <b>Unique Users:</b> {stats['unique_users']}\n"
            f"⏳ <b>Current Load:</b> {stats['active_tasks']} active tasks\n\n"
            "✨ <i>Running smoothly on Render!</i>"
        )
        await event.edit(status_text, parse_mode='html', buttons=BACK_BUTTON)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply(
        "👋 <b>Welcome to MP3 to MP4 Bot!</b>\n\n"
        "I can convert your MP3 audio files into high-quality MP4 videos.\n\n"
        "📖 Use the buttons below for more info.",
        parse_mode='html',
        buttons=START_BUTTONS
    )

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    help_text = (
        "❓ <b>Need Help?</b>\n\n"
        "• /start - Restart the bot\n"
        "• /status - Check bot load and stats\n"
        "• /cancel - Cancel your active task\n"
        "• /help - Show this help message"
    )
    await event.reply(help_text, parse_mode='html', buttons=BACK_BUTTON)

@client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    stats = get_stats()
    status_text = (
        "🤖 <b>Bot Status Report</b>\n\n"
        f"📊 <b>Total Processed:</b> {stats['total_conversions']}\n"
        f"👥 <b>Unique Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Current Load:</b> {stats['active_tasks']} active tasks"
    )
    await event.reply(status_text, parse_mode='html', buttons=BACK_BUTTON)

@client.on(events.NewMessage(pattern='/cancel'))
async def cancel_command_handler(event):
    user_id = event.sender_id
    cancelled = False
    if user_id in ongoing_tasks:
        ongoing_tasks[user_id].set()
        cancelled = True
    if not can_process(user_id):
        remove_task(user_id)
        cancelled = True
        
    if cancelled:
        await event.reply("✅ <b>Tasks cleared.</b> You can send a new file now.", parse_mode='html')
    else:
        await event.reply("❌ <b>No active tasks.</b>", parse_mode='html')

# ADMIN COMMANDS
@client.on(events.NewMessage(pattern='/users', from_users=OWNER_ID))
async def users_handler(event):
    stats = get_stats()
    await event.reply(f"👥 <b>Total Unique Users:</b> {stats['unique_users']}", parse_mode='html')

@client.on(events.NewMessage(pattern='/broadcast', from_users=OWNER_ID))
async def broadcast_handler(event):
    if not event.is_reply:
        await event.reply("❌ Please reply to a message to broadcast it.")
        return
    reply_msg = await event.get_reply_message()
    users = get_all_users()
    count = 0
    status_msg = await event.reply(f"📣 <b>Broadcasting to {len(users)} users...</b>", parse_mode='html')
    for user_id in users:
        try:
            await client.send_message(user_id, reply_msg)
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await status_msg.edit(f"✅ <b>Broadcast Complete!</b> Sent to {count} users.", parse_mode='html')

@client.on(events.NewMessage(pattern='/stats', from_users=OWNER_ID))
async def admin_stats_handler(event):
    stats = get_stats()
    admin_text = (
        "👑 <b>Admin Dashboard</b>\n\n"
        f"✅ <b>Conversions:</b> {stats['total_conversions']}\n"
        f"👥 <b>Total Users:</b> {stats['unique_users']}\n"
        f"⏳ <b>Active Tasks:</b> {stats['active_tasks']}"
    )
    await event.reply(admin_text, parse_mode='html')

@client.on(events.NewMessage(pattern='/clearall', from_users=OWNER_ID))
async def clear_all_handler(event):
    clear_all_tasks()
    ongoing_tasks.clear()
    await event.reply("🚨 <b>Emergency Reset Complete.</b>", parse_mode='html')

# AUDIO HANDLER
@client.on(events.NewMessage(func=lambda e: e.message.file and e.message.file.mime_type.startswith('audio/')))
async def audio_handler(event):
    user_id = event.sender_id
    if not can_process(user_id):
        await event.reply("⏳ <b>Already processing.</b> Use /cancel if stuck.")
        return

    log_action(user_id, "UPLOAD_MP3")
    add_task(user_id)
    ongoing_tasks[user_id] = asyncio.Event()
    start_time = time.time()
    last_update = [0]
    task_name = "MP3 to MP4 Conversion"
    
    file_size = event.file.size
    file_id = event.file.id
    
    initial_box = create_progress_box(0, file_size, task_name, "Downloading Audio...", start_time)
    status_msg = await event.reply(
        f"<code>{initial_box}</code>", 
        parse_mode='html',
        buttons=[[Button.inline("Cancel ❌", data=b"cancel_task")]]
    )
    
    file_path = None
    output_file = None
    try:
        # Step 1: Download
        file_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")
        await client.download_media(
            event.message,
            file=file_path,
            progress_callback=lambda c, t: progress_callback(c, t, status_msg, task_name, "Downloading Audio...", start_time, last_update, user_id, ongoing_tasks)
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
                    await status_msg.edit(f"<code>{box}</code>", parse_mode='html', buttons=[[Button.inline("Cancel ❌", data=b"cancel_task")]])
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
            # Step 3: Upload
            await client.send_file(
                event.chat_id,
                output_file,
                caption="✅ Here is your MP4 video!",
                progress_callback=lambda c, t: progress_callback(c, t, status_msg, task_name, "Uploading Result...", start_time, last_update, user_id, ongoing_tasks)
            )
            await status_msg.delete()
            log_action(user_id, "CONVERSION_SUCCESS")
        else:
            await status_msg.edit("❌ Conversion failed.")
            log_action(user_id, "CONVERSION_FAILED")

    except CancelledError:
        try: await status_msg.edit("⚠️ Task cancelled.")
        except: pass
        log_action(user_id, "CONVERSION_CANCELLED")
    except Exception as e:
        print(f"Error: {e}")
        try: await event.reply(f"❌ Error: {str(e)}")
        except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)
        if output_file and os.path.exists(output_file): os.remove(output_file)
        remove_task(user_id)
        if user_id in ongoing_tasks: del ongoing_tasks[user_id]
