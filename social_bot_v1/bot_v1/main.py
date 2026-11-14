import asyncio
import logging
from threading import Thread

from flask import Flask
from telegram import Update
from telegram.ext import (ApplicationBuilder, ApplicationHandlerStop, CallbackQueryHandler,
                          CommandHandler, MessageHandler, TypeHandler, filters)

import config
from handlers import ai_connectors, menu, platforms, upload

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)   # টোকেন লগে না আসার জন্য
log = logging.getLogger("bot")

# ---- Render জাগিয়ে রাখার ওয়েব পেজ (UptimeRobot এখানে পিং করবে) ----
web = Flask(__name__)


@web.route("/")
def home():
    return "Bot is running!"


def run_web():
    web.run(host="0.0.0.0", port=config.PORT)


# ---- শুধু অনুমোদিত ইউজার ----
async def auth_gate(update: Update, context):
    user = update.effective_user
    if not user or user.id not in config.ALLOWED_IDS:
        if update.effective_message:
            await update.effective_message.reply_text(f"⛔ Access denied. (ID: {user.id if user else '?'})")
        raise ApplicationHandlerStop


async def on_error(update, context):
    log.error("Handler error", exc_info=context.error)


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env variable সেট করা নেই।")
    if not config.ALLOWED_IDS:
        log.warning("ALLOWED_IDS খালি! কেউ বট ব্যবহার করতে পারবে না।")

    Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(TypeHandler(Update, auth_gate), group=-1)

    # কথোপকথন (টেক্সট ইনপুট) আগে, তারপর বাটন, সবশেষে সাধারণ চ্যাট
    app.add_handler(upload.get_upload_handler())
    app.add_handler(platforms.conv)
    app.add_handler(ai_connectors.conv)
    app.add_handler(CommandHandler("start", menu.start))
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(platforms.platform_view, pattern=r"^acc:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.provider_view, pattern=r"^ai:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.set_active, pattern=r"^ai_active:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.test_ai, pattern=r"^ai_test:"))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, upload.on_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_connectors.chat))
    app.add_error_handler(on_error)

    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
