# TikTok Downloader Telegram Bot

A Telegram bot that receives TikTok links and replies with the video as an MP4 file.

---

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **API token** you receive

### 2. Install dependencies

Make sure you have Python 3.11+ installed, then:

```bash
pip install -r requirements.txt
```

### 3. Set your bot token

**Linux / macOS:**
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
```

**Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=your_token_here
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_token_here"
```

### 4. Run the bot

```bash
python bot.py
```

---

## Usage

1. Open your bot in Telegram
2. Send `/start` to get a welcome message
3. Paste any TikTok URL (e.g. `https://vm.tiktok.com/xxxxx`)
4. The bot will download and send the video as an MP4

---

## Notes

- Videos must be under **50 MB** (Telegram bot upload limit)
- Private or deleted TikTok videos cannot be downloaded
- The bot runs in **polling mode** — keep the terminal open while using it
- For 24/7 hosting, deploy to a VPS, Railway, Fly.io, or similar

---

## Project Structure

```
tiktok_bot/
├── bot.py            # Main bot code
├── requirements.txt  # Python dependencies
└── README.md         # This file
```
