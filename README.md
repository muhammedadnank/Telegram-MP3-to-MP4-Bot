# Telegram MP3 → Black Background MP4 Bot

A simple yet powerful Telegram bot built with **Pyrogram** and **MoviePy** that converts MP3 audio files into MP4 videos with a full black background. Perfect for sharing audio on platforms that require video formats.

## 🚀 Features
- **Instant Conversion**: Converts MP3 to MP4 with a single message.
- **Black Background**: Clean 720x1280 vertical video layout.
- **Audio Preserved**: High-quality AAC audio encoding.
- **Task Management**: Prevents multiple concurrent conversions per user.
- **Auto Cleanup**: Automatically deletes temporary files and old database logs.
- **Supabase/PostgreSQL Integration**: Tracks usage and active tasks.

## 🛠 Tech Stack
- **Framework**: [Pyrogram](https://docs.pyrogram.org/)
- **Media Processing**: [MoviePy](https://zulko.github.io/moviepy/)
- **Database**: PostgreSQL (psycopg2)
- **Deployment**: Compatible with Render, VPS, and Docker.

---

## 💻 Local Setup

### 1. Prerequisites
- Python 3.9+
- FFmpeg installed on your system.

### 2. Clone and Install
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 4. Run the Bot
```bash
chmod +x start.sh
./start.sh
```

---

## ☁️ Deployment (Render.com)

1. **GitHub**: Push your code to a private or public repository.
2. **New Service**: Create a new **Background Worker** on Render.
3. **Connect**: Link your GitHub repo.
4. **Settings**:
   - **Build Command**: `./build.sh`
   - **Start Command**: `python bot.py`
5. **Environment Variables**: Add your `API_ID`, `API_HASH`, `BOT_TOKEN`, and `DATABASE_URL` in the Render dashboard.

---

## 📝 Database Schema
The bot automatically initializes two tables:
1. `tasks`: Tracks active conversions to prevent overload.
2. `usage_logs`: Logs user interactions for analytics.

---

## 📜 License
MIT License. Feel free to use and modify!
