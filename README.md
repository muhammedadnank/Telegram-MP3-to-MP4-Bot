# 🤖 Telegram MP3 → Black Background MP4 Bot

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/muhammedadnank/Telegram-MP3-to-MP4-Bot)

A professional Telegram bot built with **Telethon** and **MoviePy** that converts MP3 audio files into high-quality MP4 videos with a professional black background. Featuring a modular architecture, real-time tracking, and administrative controls.

---

## 🌟 Key Features

- **🚀 Advanced UI**: Interactive menus with inline buttons for seamless navigation using Telethon events.
- **📊 Live Progress UI**: Box-formatted real-time status updates for Download, Conversion, and Upload.
- **🛑 Task Cancellation**: Safely abort ongoing conversions at any stage with an inline "Cancel" button.
- **👮 Admin Tools**: Broadcast messages to all users, monitor real-time stats, and track unique users.
- **💎 Optimized Encoding**: Ultra-fast conversion using 2 FPS and "Still Image" tuning for minimal resource usage.
- **🛡️ Task Management**: Prevents multiple concurrent conversions per user for stability.
- **🧹 Auto-Cleanup**: Automated background task to clear temporary files and stale database entries.
- **🗄️ Database Integration**: Powered by PostgreSQL for reliable user tracking and logging.

---

## 🏗️ Project Structure
This bot uses a professional modular package structure:
```text
.
├── bot/                # Telegram client, handlers, and UI logic
├── core/               # Media conversion engine (FFmpeg/MoviePy)
├── database/           # PostgreSQL management logic
├── web/                # Health check server for cloud deployments
├── main.py             # Application entry point
└── requirements.txt    # Project dependencies
```

---

## 🎮 Commands

### 👤 User Commands
- `/start` - Launch the interactive dashboard.
- `/help` - View detailed usage instructions and features.
- `/status` - Check current bot load and global stats.
- `/cancel` - Abort your active processing task immediately.

### 👑 Admin Commands (Owner Only)
- `/users` - See total unique users in the database.
- `/broadcast` - Reply to any message to send it to all bot users.
- `/stats` - Detailed administrative dashboard.
- `/clearall` - Emergency: Clear all active tasks from DB/Memory.

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description |
| :--- | :--- |
| `API_ID` | Your Telegram API ID from my.telegram.org |
| `API_HASH` | Your Telegram API Hash from my.telegram.org |
| `BOT_TOKEN` | Your Bot Token from @BotFather |
| `DATABASE_URL` | Your PostgreSQL connection string |
| `OWNER_ID` | Your Telegram User ID (for Admin access) |

---

## ☁️ Deployment

### Render.com (Recommended)
This bot is pre-configured for Render using `render.yaml`.

1. **Service Type**: Created as a **Web Service**.
2. **Build Command**: `./build.sh`
3. **Start Command**: `python3 main.py`
4. **Port**: 8080 (auto-detected).

### VPS / Local Setup
1. **FFmpeg**: Ensure `ffmpeg` is installed.
2. **Install**: `pip install -r requirements.txt`
3. **Run**: `python3 main.py`

---

## 📝 Technical Overview
- **Framework**: [Telethon](https://docs.telethon.dev/)
- **Processing**: [MoviePy](https://zulko.github.io/moviepy/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Health Check**: Native HTTP server for cloud platform compatibility (Render/Railway/Koyeb).

---

## 📜 License
MIT License. Created by [Muhammed Adnan](https://github.com/muhammedadnank).
