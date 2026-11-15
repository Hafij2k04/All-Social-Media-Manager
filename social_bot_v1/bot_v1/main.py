import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    AIConnectors,
    MenuHandlers,
    PlatformHandlers,
    UploadHandlers,
    CallbackQueryHandler,
    MessageHandler,
    TypeHandler,
    filters,
    ApplicationHandlerStop,
    ConversationHandler
)
import config
from lang import get_text  # নতুন ইমপোর্ট

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():
    web.run(host="0.0.0.0", port=config.PORT)

async def auth_gate(update: Update, context):
    user = update.effective_user
    if not user or user.id not in config.ALLOWED_IDS:
        await update.effective_message.reply_text("Access denied.")
        raise ApplicationHandlerStop

async def on_error(update, context):
    log.error(f"handler error", exc_info=context.error)

async def start(update: Update, context):
    await auth_gate(update, context)
    user = update.effective_user
    lang_code = config.DEFAULT_LANG  # অথবা ইউজার প্রোফাইল থেকে প্রাপ্ত ভাষা
    # get_text ব্যবহার করে মেসেজ পাঠানো
    welcome_text = get_text(lang_code, "welcome")
    await update.message.reply_text(welcome_text)

def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env variable সেটা কই")
    if not config.ALLOWED_IDS:
        log.warning("ALLOWED_IDS খালি! কোড বট ব্যবহার করতে পারবে না")
        return

    Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    app.add_handler(TypeHandler(auth_gate), group=-1)

    app.add_handler(CommandHandler("start", start))
    # অন্যান্য হ্যান্ডলারগুলো এখানে থাকবে...
    
    app.add_error_handler(on_error)
    
    loop = asyncio.get_event_loop()
    loop.create_task(app.initialize())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
