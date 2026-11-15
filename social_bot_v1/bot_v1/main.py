import asyncio
import logging
from threading import Thread
from html import escape

from flask import Flask, redirect, request
from telegram import Update
from telegram.ext import (ApplicationBuilder, ApplicationHandlerStop, CallbackQueryHandler,
                          CommandHandler, MessageHandler, TypeHandler, filters)

import config
import oauth
import storage
from handlers import ai_connectors, automation, menu, platforms, upload

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)   # টোকেন লগে না আসার জন্য
log = logging.getLogger("bot")

# ---- Render জাগিয়ে রাখার ওয়েব পেজ (UptimeRobot এখানে পিং করবে) ----
web = Flask(__name__)


@web.route("/")
def home():
    return "Bot is running!"


@web.route("/oauth/youtube/start")
def youtube_oauth_start_route():
    state = request.args.get("state", "")
    payload = storage.get_oauth_state(state) if state else None
    if not payload:
        return "This Google connection link is invalid or expired. Return to Telegram and try again.", 400
    try:
        return redirect(oauth.build_authorization_url(state))
    except Exception:
        log.exception("Could not start YouTube OAuth")
        return "YouTube OAuth is not configured correctly. Check the Render environment variables.", 500


@web.route("/oauth/youtube/callback")
def youtube_oauth_callback_route():
    state = request.args.get("state", "")
    provider_error = request.args.get("error")
    payload = storage.consume_oauth_state(state) if state else None
    if not payload:
        return "The authorization request is invalid, expired, or already used. Return to Telegram and try again.", 400
    if provider_error:
        return "Google authorization was not completed. Return to Telegram and try again.", 400
    code = request.args.get("code", "")
    if not code:
        return "Google did not return an authorization code.", 400
    try:
        token_data = oauth.exchange_authorization_code(code)
        channel_data = oauth.fetch_authorized_youtube_channel(token_data["access_token"])
        token_data.update(channel_data)
        storage.save_youtube_oauth(payload["platform"], payload["name"], token_data)
    except Exception:
        log.exception("YouTube OAuth callback failed")
        return "Could not save the YouTube connection. Check server configuration and try again.", 500
    account_name = escape(str(payload.get("name", "YouTube account")))
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>YouTube connected</title></head>"
        "<body style='font-family:Arial,sans-serif;max-width:620px;margin:60px auto;padding:20px'>"
        "<h2>YouTube account connected successfully</h2>"
        f"<p><strong>{account_name}</strong> is now authorized.</p>"
        "<p>You can close this page and return to Telegram.</p></body></html>"
    )


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
    app.add_handler(CallbackQueryHandler(automation.analysis_callback, pattern=r"^an:"))
    app.add_handler(CallbackQueryHandler(menu.menu_router, pattern=r"^(menu:|lang:)"))
    app.add_handler(CallbackQueryHandler(platforms.platform_view, pattern=r"^acc:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.provider_view, pattern=r"^ai:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.set_active, pattern=r"^ai_active:"))
    app.add_handler(CallbackQueryHandler(ai_connectors.test_ai, pattern=r"^ai_test:"))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, upload.receive_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_connectors.chat))
    app.add_error_handler(on_error)

    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
