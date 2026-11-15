import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ApplicationHandlerStop
)
import config
from lang import get_text

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger("bot")

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running!"

def run_web():
    web.run(host="0.0.0.0", port=config.PORT)

async def auth_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.id not in config.ALLOWED_IDS:
        if update.effective_message:
            await update.effective_message.reply_text("Access denied.")
        raise ApplicationHandlerStop

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error(f"Handler error: {context.error}", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang_code = getattr(config, 'DEFAULT_LANG', 'en')
    welcome_text = get_text(lang_code, "welcome")
    await update.message.reply_text(welcome_text)

def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN Not Found")
    if not config.ALLOWED_IDS:
        log.warning("ALLOWED_IDS is empty!")

    Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(on_error)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
