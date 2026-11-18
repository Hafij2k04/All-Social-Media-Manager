import asyncio
import logging
from threading import Thread
from html import escape

from flask import Flask, redirect, request, send_from_directory
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


@web.route("/tiktokrGVe64pzSrLhisXxmYYk7E4ANAQ7SYWt.txt")
def tiktok_site_verification_file():
    return send_from_directory(__import__("os").path.dirname(__file__), "tiktokrGVe64pzSrLhisXxmYYk7E4ANAQ7SYWt.txt", mimetype="text/plain")


# ---- Public legal pages required for platform review ----
LEGAL_CONTACT_EMAIL = "rjtanjil2k04@gmail.com"

def _legal_page(title, body):
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + escape(title) + """ | All Social Media Manager</title>
<style>
body{font-family:Arial,sans-serif;line-height:1.65;color:#202124;max-width:850px;margin:36px auto;padding:0 20px}
h1,h2{line-height:1.25;color:#151923}h1{font-size:30px}h2{font-size:20px;margin-top:28px}
a{color:#1769aa}footer{border-top:1px solid #ddd;margin-top:36px;padding-top:18px;color:#555;font-size:14px}
</style>
</head>
<body>
<header><h1>""" + escape(title) + """</h1><p>All Social Media Manager</p></header>
<main>""" + body + """</main>
<footer>Questions or requests: <a href="mailto:""" + LEGAL_CONTACT_EMAIL + """">""" + LEGAL_CONTACT_EMAIL + """</a></footer>
</body></html>"""

@web.route("/privacy")
def privacy_policy():
    body = """
<p><strong>Effective date: November 18, 2026</strong></p>
<p>This Privacy Policy explains how All Social Media Manager (the "Service") handles information when you use the dashboard and connect social media or AI services.</p>
<h2>Information we handle</h2>
<ul>
<li><strong>Account and profile details:</strong> names, usernames, profile or channel identifiers, and links you provide for accounts you choose to manage.</li>
<li><strong>Connected-service credentials:</strong> authorization tokens and related details returned when you connect a supported platform. OAuth credentials saved through the supported OAuth flow are encrypted by the application before being stored. Older or manually entered credentials may be handled differently.</li>
<li><strong>Content and instructions:</strong> text, media, publishing instructions, and other information you submit to use the Service.</li>
<li><strong>AI integration details:</strong> API keys and provider settings that you choose to add for AI features.</li>
<li><strong>Technical information:</strong> basic request and error information may be processed by the hosting and service providers that operate the Service.</li>
</ul>
<h2>How information is used</h2>
<p>We use this information to operate the dashboard, connect the social accounts you select, carry out actions you request, provide AI-assisted features, troubleshoot errors, and protect the Service from misuse.</p>
<h2>Storage and service providers</h2>
<p>Application data is stored in the persistence system configured for the Service. This may be Firebase/Google Cloud Firestore when configured, or local application storage in other deployments. The Service may send relevant information to the social media, AI, hosting, and infrastructure providers needed to perform a feature you request. Those providers process information under their own terms and privacy policies.</p>
<p>We do not sell your personal information. We do not use your connected accounts to publish content unless you initiate or configure that action through the Service.</p>
<h2>Security</h2>
<p>We use technical safeguards available in the application, including encryption for OAuth credentials saved through the supported OAuth flow. No online service or storage method can be guaranteed to be completely secure. Keep your passwords and API keys private and do not share access with people you do not trust.</p>
<h2>Retention and deletion</h2>
<p>Information is retained while needed to provide the Service or maintain its operation. To request deletion of your account information, connected-account data, or stored credentials, email us from the address below. Include enough information for us to identify the relevant account, but never send passwords, access tokens, or API secrets. We may ask for reasonable verification before processing a request.</p>
<h2>Your choices</h2>
<p>You can stop using the Service and revoke its access from the relevant social platform's security or connected-app settings. Revoking access at a platform may not automatically delete information already stored by the Service; contact us to request deletion.</p>
<h2>Children</h2>
<p>The Service is not intended for children under 13, and we do not knowingly seek to collect their personal information.</p>
<h2>Changes to this policy</h2>
<p>We may update this policy as the Service changes. The effective date above will be revised when an update is made.</p>
<h2>Contact and data deletion requests</h2>
<p>For privacy questions or data deletion requests, contact <a href="mailto:rjtanjil2k04@gmail.com">rjtanjil2k04@gmail.com</a>.</p>
"""
    return _legal_page("Privacy Policy", body)

@web.route("/terms")
def terms_of_service():
    body = """
<p><strong>Effective date: November 18, 2026</strong></p>
<p>These Terms govern your use of All Social Media Manager (the "Service"). By using the Service, you agree to these Terms.</p>
<h2>Eligibility and account access</h2>
<p>You may connect only social media accounts that you own or are authorized to manage. You are responsible for keeping your login details, API keys, and connected accounts secure.</p>
<h2>Permitted use</h2>
<p>You agree to use the Service lawfully and in accordance with the terms, policies, and technical requirements of each connected platform and AI provider. You must not use the Service for spam, harassment, deceptive activity, unauthorized access, infringement, or any activity that violates applicable law or another service's rules.</p>
<h2>Your content and publishing activity</h2>
<p>You retain responsibility for the content you submit, schedule, upload, or publish. You must have all rights and permissions needed to use that content. You are responsible for reviewing publishing destinations, captions, media, and settings before authorizing an action.</p>
<h2>Third-party services</h2>
<p>The Service may connect to third-party platforms and providers. Their services are governed by their own terms and policies. We do not control their availability, decisions, API changes, or actions they take regarding your accounts.</p>
<h2>Availability and changes</h2>
<p>The Service is provided on an evolving basis. Features may change, be interrupted, or become unavailable, and we do not guarantee uninterrupted or error-free operation.</p>
<h2>Suspension and termination</h2>
<p>We may restrict or suspend access where we reasonably believe the Service is being misused, these Terms are being violated, or continued access creates a security or legal risk. You may stop using the Service and revoke connected-app permissions at any time.</p>
<h2>Disclaimer and limitation</h2>
<p>To the extent permitted by applicable law, the Service is provided without warranties of any kind. We are not responsible for losses caused by third-party platform outages, account restrictions, API changes, or content you choose to publish.</p>
<h2>Changes to these Terms</h2>
<p>We may update these Terms as the Service evolves. Continued use after updated Terms are posted means you accept the updated Terms, to the extent permitted by law.</p>
<h2>Contact</h2>
<p>For questions about these Terms, contact <a href="mailto:rjtanjil2k04@gmail.com">rjtanjil2k04@gmail.com</a>.</p>
"""
    return _legal_page("Terms of Service", body)


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



@web.route("/oauth/facebook/callback")
def facebook_oauth_callback_route():
    state = request.args.get("state", "")
    provider_error = request.args.get("error")
    payload = storage.consume_oauth_state(state) if state else None
    if not payload or payload.get("platform", "").lower() != "facebook":
        return "This Facebook authorization request is invalid, expired, or already used. Return to Telegram and try again.", 400
    if provider_error:
        detail = escape(str(request.args.get("error_description", "Facebook authorization was not completed.")))
        return f"<h2>Facebook connection was not completed</h2><p>{detail}</p><p>Return to Telegram and try again.</p>", 400
    code = request.args.get("code", "")
    if not code:
        return "Meta did not return an authorization code. Return to Telegram and try again.", 400

    account_name = str(payload.get("name", ""))
    platform = payload.get("platform", "Facebook")
    try:
        token_data = oauth.exchange_facebook_authorization_code(code)
        pages = oauth.fetch_facebook_pages(token_data["user_access_token"])
        accounts = storage.get_accounts().get(platform, {})
        account = accounts.get(account_name, {})
        target_id = str(account.get("channel_id", "")) if isinstance(account, dict) else ""
        selected = next((page for page in pages if target_id and str(page.get("id")) == target_id), None)
        if selected is None:
            selected = next((page for page in pages if str(page.get("name", "")).casefold() == account_name.casefold()), None)
        if selected is None and len(pages) == 1:
            selected = pages[0]
        if selected is None:
            available = ", ".join(
                f"{str(page.get('name', 'Page'))} (ID: {page.get('id', 'unknown')})"
                for page in pages[:20]
            ) or "No Pages were returned."
            raise RuntimeError(
                "Could not safely identify the intended Facebook Page. "
                "Set the correct Page ID in the Telegram account dashboard and connect again. "
                f"Pages available to this Facebook login: {available}"
            )
        storage.save_facebook_oauth(platform, account_name, {
            "page_access_token": selected.get("access_token", ""),
            "page_id": selected.get("id", ""),
            "page_name": selected.get("name", account_name),
            "user_expires_at": token_data.get("expires_at", 0),
            "scope": ",".join(oauth.META_SCOPES),
        })
    except Exception as exc:
        log.exception("Facebook OAuth callback failed")
        safe_error = escape(str(exc)[:700])
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Facebook connection</title></head>"
            "<body style='font-family:Arial,sans-serif;max-width:720px;margin:60px auto;padding:20px'>"
            "<h2>Facebook Page connection needs attention</h2>"
            f"<p>{safe_error}</p><p>Return to Telegram, correct the Page ID if needed, and try again.</p></body></html>"
        ), 400

    safe_name = escape(str(selected.get("name", account_name)))
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Facebook connected</title></head>"
        "<body style='font-family:Arial,sans-serif;max-width:620px;margin:60px auto;padding:20px'>"
        "<h2>Facebook Page connected successfully</h2>"
        f"<p><strong>{safe_name}</strong> is now connected.</p>"
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
