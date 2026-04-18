import os
import re
import logging
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

import yt_dlp

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helpers ---

TIKTOK_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?(vm\.tiktok\.com|tiktok\.com|vt\.tiktok\.com)"
    r"(/[^\s]*)?"
)

def is_tiktok_url(text: str) -> bool:
    return bool(TIKTOK_URL_PATTERN.search(text))

def extract_tiktok_url(text: str) -> str | None:
    match = TIKTOK_URL_PATTERN.search(text)
    if match:
        return match.group(0)
    return None

def download_tiktok_video(url: str, output_dir: str) -> str:
    """Download a TikTok video using yt-dlp. Returns the path to the MP4 file."""
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        # Remove TikTok watermark when possible
        "extractor_args": {"tiktok": {"embed_metadata": False}},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Ensure .mp4 extension
        if not filename.endswith(".mp4"):
            base = os.path.splitext(filename)[0]
            filename = base + ".mp4"
        return filename


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Send me any TikTok link and I'll download it and send it back as an MP4.\n\n"
        "Just paste a TikTok URL in the chat!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if not is_tiktok_url(text):
        await update.message.reply_text(
            "That doesn't look like a TikTok link. Please send a valid TikTok URL!"
        )
        return

    url = extract_tiktok_url(text)
    status_msg = await update.message.reply_text("⏳ Downloading your TikTok video...")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = download_tiktok_video(url, tmp_dir)

            if not os.path.exists(video_path):
                await status_msg.edit_text("❌ Could not find the downloaded file. The link might be private or unavailable.")
                return

            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if file_size_mb > 50:
                await status_msg.edit_text(
                    f"❌ The video is too large ({file_size_mb:.1f} MB). "
                    "Telegram bots can only send files up to 50 MB."
                )
                return

            await status_msg.edit_text("📤 Uploading video...")

            with open(video_path, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption="Here's your TikTok video! 🎵",
                    supports_streaming=True,
                )

            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp download error: {e}")
        await status_msg.edit_text(
            "❌ Failed to download the video. It might be private, deleted, or region-locked."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await status_msg.edit_text("❌ Something went wrong. Please try again.")


# --- Main ---

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
