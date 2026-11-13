from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

import config
import storage
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup
from services.youtube_service import fetch_youtube_stats

WAIT_ACCOUNT = 1
WAIT_FIELD_UPDATE = 2


async def accounts_home(update, context):
    accs = storage.get_accounts()
    rows = [[InlineKeyboardButton(f"{p} ({len(accs.get(p, {}))})", callback_data=f"acc:{p}")]
            for p in config.PLATFORMS]
    rows.append([InlineKeyboardButton("➕ Add Another Platform", callback_data="menu:add_platform")])
    rows.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")])
    await show(update, "📺 কোন প্ল্যাটফর্ম ম্যানেজ করবে?", InlineKeyboardMarkup(rows))


async def _render_platform(update, p):
    chans = storage.get_accounts().get(p, {})
    rows = []

    if chans:
        body = f"📋 **{p} — যুক্ত করা চ্যানেল/আইডি তালিকা:**\nযেকোনো আইডির বিস্তারিত স্টুডিও রিপোর্ট, API সেটআপ বা স্ট্যাটাস দেখতে নিচের বাটনে ক্লিক করো:"
        for name, info in chans.items():
            # নতুন বা পুরনো দুই ধরনের ডেটা ফরম্যাটই সাপোর্ট করবে
            if isinstance(info, dict):
                has_key = "🟢" if (info.get("api_key") or info.get("oauth_token")) else "🟡"
            else:
                has_key = "🟡"
            rows.append([InlineKeyboardButton(f"{has_key} {name}", callback_data=f"acc_item:{p}:{name}")])
    else:
        body = f"📋 **{p}**\n\nএখনো কোনো অ্যাকাউন্ট বা চ্যানেল যোগ করা হয়নি।"

    rows.append([InlineKeyboardButton("➕ Add Account/Channel", callback_data=f"acc_add:{p}")])
    rows.append([InlineKeyboardButton("🔙 Platforms", callback_data="menu:accounts")])

    await show(update, body, InlineKeyboardMarkup(rows))


async def platform_view(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    await _render_platform(update, p)


def _normalize_info(info):
    if isinstance(info, dict):
        return {
            "link": info.get("link", "লিংক নেই"),
            "channel_id": info.get("channel_id", ""),
            "api_key": info.get("api_key", ""),
            "oauth_token": info.get("oauth_token", None),
            "stats": info.get("stats", {"subscribers": "0", "views": "0", "videos": "0"})
        }
    return {
        "link": str(info),
        "channel_id": "",
        "api_key": "",
        "oauth_token": None,
        "stats": {"subscribers": "0", "views": "0", "videos": "0"}
    }


async def _render_channel_dashboard(update, p, name, notice=""):
    chans = storage.get_accounts().get(p, {})
    if name not in chans:
        await _render_platform(update, p)
        return

    info = _normalize_info(chans[name])
    stats = info.get("stats") or {}

    api_status = "✅ সংযুক্ত" if info.get("api_key") else "❌ নেই"
    oauth_status = "✅ সংযুক্ত (Upload Ready)" if info.get("oauth_token") else "❌ নেই"
    ch_id = info.get("channel_id") or "সেট করা নেই"

    text = (
        f"📊 **{p} Studio — {name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **লিংক:** {info.get('link')}\n"
        f"🆔 **Channel/Page ID:** `{ch_id}`\n"
        f"🔑 **Data API Key:** {api_status}\n"
        f"🔐 **OAuth Access:** {oauth_status}\n\n"
        f"📈 **চ্যানেল/আইডি অ্যানালিটিক্স:**\n"
        f"• 👥 সাবস্ক্রাইবার / ফলোয়ার: **{stats.get('subscribers', '0')}**\n"
        f"• 👁 মোট ভিউ (Reach): **{stats.get('views', '0')}**\n"
        f"• 🎬 মোট ভিডিও: **{stats.get('videos', '0')}**\n"
    )
    if notice:
        text += f"\n💡 {notice}\n"

    rows = [
        [
            InlineKeyboardButton("🔄 Sync Live Stats", callback_data=f"acc_sync:{p}:{name}"),
            InlineKeyboardButton("🆔 Set Channel ID", callback_data=f"acc_edit:{p}:{name}:channel_id"),
        ],
        [
            InlineKeyboardButton("🔑 Set API Key", callback_data=f"acc_edit:{p}:{name}:api_key"),
            InlineKeyboardButton("🔐 Set OAuth Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
        ],
        [
            InlineKeyboardButton("🔗 Edit Link", callback_data=f"acc_edit:{p}:{name}:link"),
            InlineKeyboardButton("🗑 Remove Account", callback_data=f"acc_del:{p}:{name}"),
        ],
        [InlineKeyboardButton(f"🔙 Back to {p}", callback_data=f"acc:{p}")]
    ]
    await show(update, text, InlineKeyboardMarkup(rows))


async def account_item_view(update, context):
    _, p, name = update.callback_query.data.split(":", 2)
    await _render_channel_dashboard(update, p, name)


async def account_sync(update, context):
    _, p, name = update.callback_query.data.split(":", 2)
    chans = storage.get_accounts().get(p, {})
    if name not in chans:
        await _render_platform(update, p)
        return

    info = _normalize_info(chans[name])

    if p.lower() == "youtube":
        target = info.get("channel_id") or info.get("link")
        res, err = fetch_youtube_stats(target, info.get("api_key", ""))
        if err:
            await _render_channel_dashboard(update, p, name, notice=err)
            return

        info["channel_id"] = res.get("channel_id") or info["channel_id"]
        info["stats"] = {
            "subscribers": res.get("subscribers", "0"),
            "views": res.get("views", "0"),
            "videos": res.get("videos", "0")
        }
        storage.add_account(p, name, info)
        await _render_channel_dashboard(update, p, name, notice="✅ YouTube থেকে সফলভাবে লাইভ ডেটা আপডেট হয়েছে!")
    else:
        await _render_channel_dashboard(update, p, name, notice=f"ℹ️ {p}-এর লাইভ API সিঙ্ক পরের ধাপে যুক্ত হবে।")


async def account_delete(update, context):
    _, p, name = update.callback_query.data.split(":", 2)
    if hasattr(storage, "remove_account"):
        storage.remove_account(p, name)
    await _render_platform(update, p)


async def add_start(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["platform"] = p
    await show(
        update,
        f"➕ **{p}-এ নতুন অ্যাকাউন্ট/চ্যানেল যোগ করো:**\n\n"
        f"নিচের ফরম্যাটে লেখো:\n"
        f"`নাম - লিংক বা Channel ID`\n"
        f"(যেমন: `Clipzilla - youtube.com/@Clipzilla`)\n\n"
        f"বাতিল করতে /cancel"
    )
    return WAIT_ACCOUNT


async def add_save(update, context):
    p = context.user_data.get("platform")
    text = update.message.text.strip()
    name, link = (text.split(" - ", 1) + [""])[:2] if " - " in text else (text, "লিংক নেই")
    name = name.strip()
    link = link.strip() or "লিংক নেই"

    storage.add_account(p, name, {
        "link": link,
        "channel_id": link if link.startswith("UC") else "",
        "api_key": "",
        "oauth_token": None,
        "stats": {"subscribers": "0", "views": "0", "videos": "0"}
    })
    await _render_channel_dashboard(update, p, name, notice="✅ অ্যাকাউন্ট যুক্ত হয়েছে! এবার নিচ থেকে API Key বা Channel ID সেট করতে পারো।")
    return ConversationHandler.END


async def edit_field_start(update, context):
    _, p, name, field = update.callback_query.data.split(":", 3)
    context.user_data["edit_target"] = (p, name, field)

    prompts = {
        "channel_id": "🆔 **Channel ID বা Handle দাও:**\n(যেমন: `UCxxxxxxxxxxxx` অথবা `@MyChannel`)",
        "api_key": "🔑 **Google Cloud / Platform API Key দাও:**\n(নিরাপত্তার জন্য মেসেজটি সেভ হওয়ার সাথে সাথে চ্যাট থেকে ডিলিট হয়ে যাবে)",
        "oauth_token": "🔐 **OAuth Token / Refresh Token JSON দাও:**\n(ভিডিও সরাসরি আপলোড করার অ্যাক্সেসের জন্য)",
        "link": "🔗 **চ্যানেল বা পেজের নতুন লিংক দাও:**"
    }
    await show(update, f"{prompts.get(field, 'নতুন তথ্য দাও:')}\n\nবাতিল করতে /cancel")
    return WAIT_FIELD_UPDATE


async def edit_field_save(update, context):
    target = context.user_data.get("edit_target")
    if not target:
        await show(update, MAIN_TEXT, main_menu_markup())
        return ConversationHandler.END

    p, name, field = target
    val = update.message.text.strip()

    if field in ("api_key", "oauth_token"):
        try:
            await update.message.delete()
        except Exception:
            pass

    chans = storage.get_accounts().get(p, {})
    info = _normalize_info(chans.get(name, {}))
    info[field] = val
    storage.add_account(p, name, info)

    await _render_channel_dashboard(update, p, name, notice=f"✅ `{field}` সফলভাবে সেভ করা হয়েছে!")
    return ConversationHandler.END


async def cancel(update, context):
    await show(update, MAIN_TEXT, main_menu_markup())
    return ConversationHandler.END


conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_start, pattern=r"^acc_add:"),
        CallbackQueryHandler(edit_field_start, pattern=r"^acc_edit:"),
        CallbackQueryHandler(account_item_view, pattern=r"^acc_item:"),
        CallbackQueryHandler(account_sync, pattern=r"^acc_sync:"),
        CallbackQueryHandler(account_delete, pattern=r"^acc_del:"),
    ],
    states={
        WAIT_ACCOUNT: [
            CallbackQueryHandler(cancel, pattern=r"^menu:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_save),
        ],
        WAIT_FIELD_UPDATE: [
            CallbackQueryHandler(cancel, pattern=r"^menu:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_save),
        ],
    },
    fallbacks=[CommandHandler(["start", "cancel"], cancel)],
)
