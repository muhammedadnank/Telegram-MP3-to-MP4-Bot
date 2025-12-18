import os
import asyncio
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
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "👋 Hello! Send me an MP3 file, and I'll convert it into an MP4 video with a black background for you."
    )

@app.on_message(filters.audio)
async def audio_handler(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is already processing a file
    if not can_process(user_id):
        await message.reply_text("⏳ Please wait! I am already processing a file for you.")
        return

    # Log action
    log_action(user_id, "UPLOAD_MP3")
    
    # Add task to database
    add_task(user_id)
    
    status_msg = await message.reply_text("Downloading... ⏳")
    
    try:
        # Download the file
        file_path = await message.download(file_name=os.path.join(DOWNLOAD_DIR, f"{message.audio.file_id}.mp3"))
        
        await status_msg.edit_text("Converting to MP4... 🎬 This may take a moment.")
        
        output_file = file_path.replace(".mp3", ".mp4")
        
        # Convert MP3 to MP4
        # Running in a thread to prevent blocking the event loop
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, convert_mp3_to_mp4, file_path, output_file)
        
        if success:
            await status_msg.edit_text("Uploading... ⬆️")
            await message.reply_video(
                video=output_file,
                caption="✅ Here is your MP4 video!",
                duration=message.audio.duration
            )
            await status_msg.delete()
            log_action(user_id, "CONVERSION_SUCCESS")
        else:
            await status_msg.edit_text("❌ Failed to convert the file.")
            log_action(user_id, "CONVERSION_FAILED")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_file):
            os.remove(output_file)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("❌ An unexpected error occurred during processing.")
    finally:
        # Remove task from database
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

if __name__ == "__main__":
    # Initialize DB
    init_db()
    
    # Start the bot
    print("Bot is starting...")
    
    # Create background cleanup task
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_cleanup())
    
    app.run()
