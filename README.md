# 🤖 Telegram MP3 → Black Background MP4 Bot

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/muhammedadnank/Telegram-MP3-to-MP4-Bot)

A professional Telegram bot built with **Pyrogram** and **MoviePy** that converts MP3 audio files into high-quality MP4 videos with a professional black background. Featuring a modern UI, real-time tracking, and administrative controls.

---

## 🌟 Key Features

- **🚀 Advanced UI**: Interactive menus with inline buttons for seamless navigation.
- **📊 Live Progress UI**: Box-formatted real-time status updates for Download, Conversion, and Upload.
- **🛑 Task Cancellation**: Safely abort ongoing conversions at any stage with an inline "Cancel" button.
- **👮 Admin Tools**: Broadcast messages to all users, monitor real-time stats, and track unique users.
- **💎 Black Background**: Standard 720x1280 vertical video layout, ideal for mobile sharing.
- **🛡️ Task Management**: Prevents multiple concurrent conversions per user for stability.
- **🧹 Auto-Cleanup**: Automated background task to clear temporary files and stale database entries.
- **🗄️ Database Integration**: Powered by PostgreSQL for reliable user tracking and logging.

---

## 🎮 Commands

### 👤 User Commands
- `/start` - Launch the interactive dashboard.
- `/help` - View detailed usage instructions and features.
- `/status` - Check current bot load and global stats.
- `/commands` - Display a quick list of all available commands.

### 👑 Admin Commands (Owner Only)
- `/users` - See total unique users in the database.
- `/broadcast` - Reply to any message to send it to all bot users.
- `/stats` - Detailed administrative dashboard with file counts and processing tasks.

---

## ⚙️ Configuration

### Environment Variables
Configure these in your `.env` or deployment dashboard:

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

1. **Fork/Push**: Push your code to your GitHub repo.
2. **Service Type**: Created as a **Web Service** (for health check support).
3. **Build Command**: `./build.sh`
4. **Start Command**: `python bot.py`
5. **Port**: The bot includes a health check server on port 8080 (auto-detected).

### VPS / Local Setup
1. **FFmpeg**: Ensure `ffmpeg` is installed on your system.
2. **Install**: `pip install -r requirements.txt`
3. **Run**: `chmod +x start.sh && ./start.sh`

---

## 📝 Technical Overview
- **Framework**: [Pyrogram V2](https://docs.pyrogram.org/)
- **Processing**: [MoviePy V2](https://zulko.github.io/moviepy/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Health Check**: Native HTTP server for cloud platform compatibility (Render/Koyeb).

---

## 📜 License
MIT License. Created by [Muhammed Adnan](https://github.com/muhammedadnank).
