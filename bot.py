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
    r"https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+"
)

def find_tiktok_urls(text: str) -> list[str]:
    """Find all TikTok URLs in a message."""
    return TIKTOK_URL_PATTERN.findall(text)

def download_tiktok_video(url: str, output_dir: str) -> str:
    """Download a TikTok video using yt-dlp. Returns the path to the MP4 file."""
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"tiktok": {"embed_metadata": False}},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not filename.endswith(".mp4"):
            base = os.path.splitext(filename)[0]
            filename = base + ".mp4"
        return filename


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Send me one or multiple TikTok links and I'll download them and send them back as MP4 videos.\n\n"
        "You can send several links in the same message — I'll handle them all!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    urls = find_tiktok_urls(text)

    if not urls:
        await update.message.reply_text(
            "That doesn't look like a TikTok link. Please send a valid TikTok URL!"
        )
        return

    # Let the user know how many links were found
    count = len(urls)
    if count == 1:
        status_msg = await update.message.reply_text("⏳ Downloading your TikTok video...")
    else:
        status_msg = await update.message.reply_text(f"⏳ Found {count} links! Downloading them one by one...")

    success = 0
    failed = 0

    for i, url in enumerate(urls, start=1):
        # Update status for multiple links so user knows progress
        if count > 1:
            await status_msg.edit_text(f"⏳ Downloading video {i} of {count}...")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                video_path = download_tiktok_video(url, tmp_dir)

                if not os.path.exists(video_path):
                    await update.message.reply_text(
                        f"❌ Video {i}: Could not find the file. The link might be private or unavailable.\n🔗 {url}"
                    )
                    failed += 1
                    continue

                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                if file_size_mb > 50:
                    await update.message.reply_text(
                        f"❌ Video {i} is too large ({file_size_mb:.1f} MB). Telegram bots can only send files up to 50 MB.\n🔗 {url}"
                    )
                    failed += 1
                    continue

                if count > 1:
                    await status_msg.edit_text(f"📤 Uploading video {i} of {count}...")

                with open(video_path, "rb") as video_file:
                    caption = f"🎵 Video {i}/{count}" if count > 1 else "Here's your TikTok video! 🎵"
                    await update.message.reply_video(
                        video=video_file,
                        caption=caption,
                        supports_streaming=True,
                    )
                success += 1

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
            await update.message.reply_text(
                f"❌ Video {i}: Failed to download. It might be private, deleted, or region-locked.\n🔗 {url}"
            )
            failed += 1
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            await update.message.reply_text(f"❌ Video {i}: Something went wrong. Please try again.\n🔗 {url}")
            failed += 1

    # Final summary for multiple links
    if count > 1:
        if failed == 0:
            await status_msg.edit_text(f"✅ All {count} videos sent successfully!")
        elif success == 0:
            await status_msg.edit_text(f"❌ All {count} downloads failed.")
        else:
            await status_msg.edit_text(f"✅ Done! {success} succeeded, {failed} failed.")
    else:
        await status_msg.delete()


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
