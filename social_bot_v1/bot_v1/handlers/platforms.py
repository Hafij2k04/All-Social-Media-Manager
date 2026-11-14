import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import storage
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup
from services.youtube_service import fetch_youtube_stats

logger = logging.getLogger(__name__)

WAIT_ACCOUNT = 1
WAIT_FIELD_UPDATE = 2

PLATFORM_ICONS = {
    "youtube": "▶️",
    "facebook": "📘",
    "tiktok": "🎵",
    "instagram": "📸",
    "linkedin": "💼",
}


async def accounts_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accs = storage.get_accounts()
    rows = []
    for p in config.PLATFORMS:
        icon = PLATFORM_ICONS.get(p.lower(), "📺")
        count = len(accs.get(p, {}))
        rows.append([InlineKeyboardButton(f"{icon} {p} ({count})", callback_data=f"acc:{p}")])

    rows.append([InlineKeyboardButton("➕ Add Another Platform", callback_data="menu:add_platform")])
    rows.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")])
    await show(update, "📺 **কোন প্ল্যাটফর্ম ম্যানেজ করবে?**\nনিচ থেকে প্ল্যাটফর্ম সিলেক্ট করো:", InlineKeyboardMarkup(rows))


async def _render_platform(update: Update, p: str):
    chans = storage.get_accounts().get(p, {})
    icon = PLATFORM_ICONS.get(p.lower(), "📋")
    rows = []

    if chans:
        body = (
            f"{icon} **{p} — যুক্ত করা চ্যানেল/পেজ তালিকা:**\n\n"
            f"🟢 = API/Token সংযুক্ত | 🟡 = সেটআপ বাকি\n"
            f"যেকোনো আইডির স্টুডিও ড্যাশবোর্ড বা API সেটআপ করতে নামের ওপর ক্লিক করো:"
        )
        for name, info in chans.items():
            if isinstance(info, dict):
                has_key = "🟢" if (info.get("api_key") or info.get("oauth_token")) else "🟡"
            else:
                has_key = "🟡"
            rows.append([InlineKeyboardButton(f"{has_key} {name}", callback_data=f"acc_item:{p}:{name}")])
    else:
        body = f"{icon} **{p}**\n\nএখনো কোনো অ্যাকাউন্ট বা চ্যানেল যোগ করা হয়নি।\nনতুন চ্যানেল বা পেজ যুক্ত করতে নিচের বাটনে ক্লিক করো।"

    rows.append([InlineKeyboardButton(f"➕ Add {p} Account", callback_data=f"acc_add:{p}")])
    rows.append([InlineKeyboardButton("🔙 All Platforms", callback_data="menu:accounts")])

    await show(update, body, InlineKeyboardMarkup(rows))


async def platform_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.callback_query.data.split(":", 1)[1]
    await _render_platform(update, p)


def _normalize_info(info) -> dict:
    if isinstance(info, dict):
        return {
            "link": info.get("link", "লিংক নেই"),
            "channel_id": info.get("channel_id", ""),
            "api_key": info.get("api_key", ""),
            "oauth_token": info.get("oauth_token", None),
            "stats": info.get("stats", {"subscribers": "0", "views": "0", "videos": "0"}),
        }
    return {
        "link": str(info),
        "channel_id": "",
        "api_key": "",
        "oauth_token": None,
        "stats": {"subscribers": "0", "views": "0", "videos": "0"},
    }


async def _render_channel_dashboard(update: Update, p: str, name: str, notice: str = ""):
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
        f"🔑 **API Key / App Token:** {api_status}\n"
        f"🔐 **OAuth / Page Access Token:** {oauth_status}\n\n"
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
            InlineKeyboardButton("🆔 Set ID / Handle", callback_data=f"acc_edit:{p}:{name}:channel_id"),
        ],
        [
            InlineKeyboardButton("🔑 Set API Key", callback_data=f"acc_edit:{p}:{name}:api_key"),
            InlineKeyboardButton("🔐 Set Access Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
        ],
        [
            InlineKeyboardButton("🔗 Edit Link", callback_data=f"acc_edit:{p}:{name}:link"),
            InlineKeyboardButton("🗑 Remove Account", callback_data=f"acc_del:{p}:{name}"),
        ],
        [InlineKeyboardButton(f"🔙 Back to {p}", callback_data=f"acc:{p}")],
    ]
    await show(update, text, InlineKeyboardMarkup(rows))


async def account_item_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name = update.callback_query.data.split(":", 2)
    await _render_channel_dashboard(update, p, name)


async def account_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "videos": res.get("videos", "0"),
        }
        storage.add_account(p, name, info)
        await _render_channel_dashboard(update, p, name, notice="✅ YouTube থেকে সফলভাবে লাইভ ডেটা আপডেট হয়েছে!")
    else:
        await _render_channel_dashboard(
            update, p, name, notice=f"ℹ️ {p}-এর লাইভ স্ট্যাটাস সিঙ্ক করতে প্রথমে Access Token ও Page ID যুক্ত করুন।"
        )


async def account_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name = update.callback_query.data.split(":", 2)
    if hasattr(storage, "remove_account"):
        storage.remove_account(p, name)
    await _render_platform(update, p)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["platform"] = p
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 বাতিল করুন (Cancel)", callback_data=f"acc:{p}")]])
    await show(
        update,
        f"➕ **{p}-এ নতুন অ্যাকাউন্ট/চ্যানেল যোগ করো:**\n\n"
        f"নিচের ফরম্যাটে মেসেজ পাঠাও:\n"
        f"`নাম - লিংক বা Channel ID`\n\n"
        f"**উদাহরণ:**\n"
        f"• `Clipzilla - https://youtube.com/@Clipzilla`\n"
        f"• `Nexus Creation - https://facebook.com/NexusCreation`",
        kb,
    )
    return WAIT_ACCOUNT


async def add_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = context.user_data.get("platform", "YouTube")
    text = update.message.text.strip()
    if " - " in text:
        name, link = text.split(" - ", 1)
    else:
        name, link = text, "লিংক নেই"

    # নামের ভেতর ':' থাকলে তা সরিয়ে নেওয়া হচ্ছে যাতে বাটনের callback_data না ভাঙে
    name = name.replace(":", "-").strip()
    link = link.strip() or "লিংক নেই"

    ch_id = ""
    if link.startswith("UC") or link.startswith("@"):
        ch_id = link
    elif "youtube.com/@" in link:
        ch_id = "@" + link.split("youtube.com/@", 1)[1].split("/")[0].split("?")[0]

    storage.add_account(
        p,
        name,
        {
            "link": link,
            "channel_id": ch_id,
            "api_key": "",
            "oauth_token": None,
            "stats": {"subscribers": "0", "views": "0", "videos": "0"},
        },
    )
    await _render_channel_dashboard(
        update, p, name, notice="✅ অ্যাকাউন্ট যুক্ত হয়েছে! এবার নিচ থেকে API Key বা Access Token সেট করতে পারো।"
    )
    return ConversationHandler.END


async def edit_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name, field = update.callback_query.data.split(":", 3)
    context.user_data["edit_target"] = (p, name, field)

    prompts = {
        "channel_id": (
            f"🆔 **{name}-এর Channel ID / Page ID বা Handle দাও:**\n"
            f"• YouTube হলে: `UCxxxxxxxx` অথবা `@Clipzilla`\n"
            f"• Facebook হলে: আপনার Page ID নম্বর"
        ),
        "api_key": (
            f"🔑 **{name}-এর API Key দাও:**\n"
            f"• YouTube লাইভ ভিউ/সাবস্ক্রাইবার দেখার জন্য **YouTube Data API v3 Key** দিন।\n"
            f"*(নিরাপত্তার স্বার্থে মেসেজটি সেভ হওয়ার সাথে সাথে চ্যাট থেকে ডিলিট হয়ে যাবে)*"
        ),
        "oauth_token": (
            f"🔐 **{name}-এর OAuth / Access Token দাও:**\n"
            f"• সরাসরি ভিডিও আপলোড করার জন্য এটি প্রয়োজন।\n"
            f"*(নিরাপত্তার স্বার্থে মেসেজটি সেভ হওয়ার সাথে সাথে চ্যাট থেকে ডিলিট হয়ে যাবে)*"
        ),
        "link": f"🔗 **{name}-এর নতুন লিংক দাও:**",
    }
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 বাতিল করুন (Cancel)", callback_data=f"acc_item:{p}:{name}")]])
    await show(update, prompts.get(field, "নতুন তথ্য দাও:"), kb)
    return WAIT_FIELD_UPDATE


async def edit_field_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def cancel_to_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("acc_item:"):
        _, p, name = data.split(":", 2)
        await _render_channel_dashboard(update, p, name)
    elif data.startswith("acc:"):
        p = data.split(":", 1)[1]
        await _render_platform(update, p)
    else:
        await show(update, MAIN_TEXT, main_menu_markup())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("platform", None)
    context.user_data.pop("edit_target", None)
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
            CallbackQueryHandler(cancel_to_platform, pattern=r"^(acc:|menu:)"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_save),
        ],
        WAIT_FIELD_UPDATE: [
            CallbackQueryHandler(cancel_to_platform, pattern=r"^(acc_item:|acc:|menu:)"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_save),
        ],
    },
    fallbacks=[
        CommandHandler(["start", "cancel"], cancel),
        CallbackQueryHandler(cancel, pattern=r"^menu:main$"),
    ],
    allow_reentry=True,
)


# =====================================================================
# আপলোড মেনুর জন্য প্ল্যাটফর্ম সিলেকশন হেল্পার ফাংশনসমূহ
# =====================================================================

def get_available_targets() -> list[dict]:
    """storage.py থেকে সেভ করা সব প্ল্যাটফর্ম ও চ্যানেল/পেজ নিয়ে আসে।"""
    accs = storage.get_accounts()
    targets = []
    for plat, channels in accs.items():
        icon = PLATFORM_ICONS.get(plat.lower(), "📡")
        for ch_name in channels.keys():
            targets.append({
                "id": f"{plat}:{ch_name}",
                "platform": plat,
                "name": ch_name,
                "label": f"{icon} {plat.capitalize()} ({ch_name})",
            })
    return targets


def build_upload_platform_keyboard(selected_ids: list[str], is_open: bool) -> list[list[InlineKeyboardButton]]:
    """ড্রপডাউন অ্যারো (▼/▲) এবং টিকবক্স (✅/⬜) সহ প্ল্যাটফর্ম সিলেকশন বাটন তৈরি করে।"""
    arrow = "▲" if is_open else "▼"
    count = len(selected_ids)
    rows = [[
        InlineKeyboardButton(
            f"📡 প্ল্যাটফর্ম নির্বাচন ({count} টি সিলেক্টেড) {arrow}",
            callback_data="up_plat_dropdown",
        )
    ]]

    if is_open:
        targets = get_available_targets()
        if not targets:
            rows.append([
                InlineKeyboardButton("⚠️ কোনো অ্যাকাউন্ট যুক্ত নেই (Accounts-এ যান)", callback_data="menu:accounts")
            ])
        else:
            for item in targets:
                checked = "✅" if item["id"] in selected_ids else "⬜"
                rows.append([
                    InlineKeyboardButton(
                        f"{checked} {item['label']}",
                        callback_data=f"up_plat_tog|{item['id']}",
                    )
                ])
    return rows


async def toggle_upload_platform(context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """টিকবক্স ও ড্রপডাউন বাটনের ক্লিক হ্যান্ডেল করে।"""
    data = context.user_data.get("upload_session")
    if not data:
        return

    if action == "up_plat_dropdown":
        data["plat_open"] = not data["plat_open"]
    elif action.startswith("up_plat_tog|"):
        target_id = action.split("|", 1)[1]
        if target_id in data["selected_targets"]:
            data["selected_targets"].remove(target_id)
        else:
            data["selected_targets"].append(target_id)
