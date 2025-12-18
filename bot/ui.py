import time
import math
import proglog
from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.converter import CancelledError

def format_bytes(size):
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {units[i]}"

def get_eta(current, total, start_time):
    elapsed_time = time.time() - start_time
    if current <= 0:
        return "Calculating..."
    speed = current / elapsed_time
    eta_seconds = (total - current) / speed
    if eta_seconds < 0:
        return "0s"
    minutes, seconds = divmod(int(eta_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def create_progress_box(current, total, task_name, status, start_time, is_bytes=True):
    percentage = (current / total) * 100 if total > 0 else 0
    percentage = min(percentage, 100)
    filled_blocks = int(percentage / (100 / 15))
    bar = "▤" * filled_blocks + "□" * (15 - filled_blocks)
    eta = get_eta(current, total, start_time)
    if is_bytes:
        processed = format_bytes(current)
        total_size = format_bytes(total)
    else:
        processed = f"{int(current)}"
        total_size = f"{int(total)} (Frames)"
    
    return (
        f"┏ 🏷️ Name: {task_name}\n"
        f"┃ [{bar}] {percentage:.1f}%\n"
        f"┠ 🔄 Processed: {processed} of {total_size}\n"
        f"┠ ✨ Status: {status} | ETA: {eta}"
    )

async def progress_callback(current, total, status_msg, task_name, status_text, start_time, last_update, user_id, ongoing_tasks):
    if user_id in ongoing_tasks and ongoing_tasks[user_id].is_set():
        raise CancelledError("Task cancelled by user.")
    
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
    except:
        pass

class TelegramLogger(proglog.ProgressBarLogger):
    def __init__(self, progress_dict, cancel_event):
        super().__init__()
        self.progress_dict = progress_dict
        self.cancel_event = cancel_event

    def callback(self, **changes):
        if self.cancel_event.is_set():
            raise CancelledError("Task cancelled during conversion.")
        
        if 'bars' in changes:
            for bar_name, bar_data in changes['bars'].items():
                if bar_data['total'] > 1:
                    self.progress_dict['current'] = bar_data['index']
                    self.progress_dict['total'] = bar_data['total']
        
        if 'message' in changes:
            msg = changes['message'].replace("MoviePy - ", "")
            self.progress_dict['status'] = msg
            print(f"DEBUG: Status Update: {msg}")
