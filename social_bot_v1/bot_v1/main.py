from telegram import Update
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    TypeHandler,
    filters,
    ApplicationHandlerStop,
    ConversationHandler
)
import config
from lang import get_text  # ল্যাঙ্গুয়েজ ফাংশন ইমপোর্ট

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():
    web.run(host="0.0.0.0", port=config.PORT)

# --- অনুমোদিত ইউজার ---
async def auth_gate(update: Update, context):
    user = update.effective_user
    if not user or user.id not in config.ALLOWED_IDS:
        if update.effective_message:
            await update.effective_message.reply_text("Access denied.")
        raise ApplicationHandlerStop

async def on_error(update, context):
    log.error(f"Handler error", exc_info=context.error)

# আপডেট করা স্টার্ট ফাংশন
async def start(update: Update, context):
    await auth_gate(update, context)
    user = update.effective_user
    lang_code = getattr(config, 'DEFAULT_LANG', 'en') # কনফিগ থেকে ভাষা নেওয়া
    welcome_text = get_text(lang_code, "welcome")
    await update.message.reply_text(welcome_text)

def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env variable সেটা কই")
    if not config.ALLOWED_IDS:
        log.warning("ALLOWED_IDS খালি! কোড বট ব্যবহার করতে পারবে না")

    Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    TypeHandler(callback=auth_gate)

    # আপনার আগের সব হ্যান্ডলার এখানে অক্ষত আছে
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^m"))
    app.add_handler(upload.get_upload_handler())
    app.add_handler(platforms.conv)
    app.add_handler(ai_connectors.conv)
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^menu_start"))
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^menu_ref"))
    app.add_handler(CallbackQueryHandler(platforms.platform_view, pattern=r"^platform_edit"))
    app.add_handler(CallbackQueryHandler(ai_connectors.provider_view, pattern=r"^provider_edit"))
    app.add_handler(CallbackQueryHandler(ai_connectors.set_active, pattern=r"^set_active"))
    app.add_handler(CallbackQueryHandler(ai_connectors.test_ai, pattern=r"^test_ai"))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, upload.upload_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_connectors.handle_ai_input))
    
    app.add_error_handler(on_error)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
