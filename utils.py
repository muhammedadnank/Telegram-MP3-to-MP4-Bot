import time
import math

class CancelledError(Exception):
    """Custom exception to handle task cancellation."""
    pass

def format_bytes(size):
    """Formats bytes into a human-readable string."""
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {units[i]}"

def get_eta(current, total, start_time):
    """Calculates the estimated time remaining."""
    elapsed_time = time.time() - start_time
    if current <= 0:
        return "Calculating..."
    
    # Speed = current / elapsed
    # Remaining = (total - current) / speed
    speed = current / elapsed_time
    eta_seconds = (total - current) / speed
    
    if eta_seconds < 0:
        return "0s"
    
    # Format ETA
    minutes, seconds = divmod(int(eta_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def create_progress_box(current, total, task_name, status, start_time, is_bytes=True):
    """Generates the specialized live progress box format."""
    percentage = (current / total) * 100 if total > 0 else 0
    percentage = min(percentage, 100) # Cap at 100%
    
    # Progress bar: 15 blocks
    filled_blocks = int(percentage / (100 / 15))
    bar = "▤" * filled_blocks + "□" * (15 - filled_blocks)
    
    eta = get_eta(current, total, start_time)
    
    if is_bytes:
        processed = format_bytes(current)
        total_size = format_bytes(total)
    else:
        processed = f"{int(current)}"
        total_size = f"{int(total)} (Frames)"
    
    box = (
        f"┏ 🏷️ Name: {task_name}\n"
        f"┃ [{bar}] {percentage:.1f}%\n"
        f"┠ 🔄 Processed: {processed} of {total_size}\n"
        f"┠ ✨ Status: {status} | ETA: {eta}"
    )
    return box
