import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import storage
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup
from services.youtube_service import fetch_youtube_stats, fetch_facebook_stats

logger = logging.getLogger(__name__)

WAIT_ACCOUNT = 1
WAIT_FIELD_UPDATE = 2
WAIT_NEW_PLATFORM = 3


ACCOUNT_UI = {
 "bn": {"choose":"📺 কোন প্ল্যাটফর্ম ম্যানেজ করবে?\nনিচ থেকে প্ল্যাটফর্ম সিলেক্ট করো:", "add_platform":"➕ Add Another Platform", "main":"🔙 মেইন মেনু", "list":"যুক্ত করা অ্যাকাউন্ট তালিকা:", "connected":"🟢 = কানেক্টেড | 🟡 = টোকেন/API সেটআপ বাকি", "open":"ড্যাশবোর্ডে যেতে অ্যাকাউন্টের নাম চাপো:", "empty":"এখনো কোনো অ্যাকাউন্ট যোগ করা হয়নি।\nনতুন অ্যাকাউন্ট যোগ করতে নিচের বাটনে চাপো।", "add":"➕ Add {p} Account", "all":"🔙 All Platforms"},
 "en": {"choose":"📺 Which platform would you like to manage?\nSelect a platform below:", "add_platform":"➕ Add Another Platform", "main":"🔙 Main Menu", "list":"Connected accounts:", "connected":"🟢 = Connected | 🟡 = Token/API setup required", "open":"Select an account name to open its dashboard:", "empty":"No accounts have been added yet.\nUse the button below to add a new account.", "add":"➕ Add {p} Account", "all":"🔙 All Platforms"},
 "hi": {"choose":"📺 आप किस प्लेटफ़ॉर्म को प्रबंधित करना चाहते हैं?\nनीचे से प्लेटफ़ॉर्म चुनें:", "add_platform":"➕ दूसरा प्लेटफ़ॉर्म जोड़ें", "main":"🔙 मुख्य मेनू", "list":"जोड़े गए अकाउंट:", "connected":"🟢 = कनेक्टेड | 🟡 = टोकन/API सेटअप बाकी", "open":"डैशबोर्ड खोलने के लिए अकाउंट का नाम चुनें:", "empty":"अभी कोई अकाउंट नहीं जोड़ा गया।\nनया अकाउंट जोड़ने के लिए नीचे दबाएँ।", "add":"➕ {p} अकाउंट जोड़ें", "all":"🔙 सभी प्लेटफ़ॉर्म"},
 "ur": {"choose":"📺 آپ کس پلیٹ فارم کو منظم کرنا چاہتے ہیں؟\nنیچے سے پلیٹ فارم منتخب کریں:", "add_platform":"➕ ایک اور پلیٹ فارم شامل کریں", "main":"🔙 مین مینو", "list":"شامل کردہ اکاؤنٹس:", "connected":"🟢 = منسلک | 🟡 = ٹوکن/API سیٹ اپ باقی", "open":"ڈیش بورڈ کھولنے کے لیے اکاؤنٹ کا نام منتخب کریں:", "empty":"ابھی کوئی اکاؤنٹ شامل نہیں۔\nنیا اکاؤنٹ شامل کرنے کے لیے نیچے دبائیں۔", "add":"➕ {p} اکاؤنٹ شامل کریں", "all":"🔙 تمام پلیٹ فارمز"},
 "zh": {"choose":"📺 请选择要管理的平台：\n从下方选择平台：", "add_platform":"➕ 添加其他平台", "main":"🔙 主菜单", "list":"已添加的账号：", "connected":"🟢 = 已连接 | 🟡 = 需要设置令牌/API", "open":"点击账号名称打开控制面板：", "empty":"尚未添加账号。\n点击下方按钮添加账号。", "add":"➕ 添加 {p} 账号", "all":"🔙 所有平台"},
 "ar": {"choose":"📺 ما المنصة التي تريد إدارتها؟\nاختر منصة أدناه:", "add_platform":"➕ إضافة منصة أخرى", "main":"🔙 القائمة الرئيسية", "list":"الحسابات المضافة:", "connected":"🟢 = متصل | 🟡 = إعداد الرمز/API مطلوب", "open":"اختر اسم الحساب لفتح لوحة التحكم:", "empty":"لم تتم إضافة أي حساب بعد.\nاضغط أدناه لإضافة حساب جديد.", "add":"➕ إضافة حساب {p}", "all":"🔙 كل المنصات"},
 "ne": {"choose":"📺 कुन प्लेटफर्म व्यवस्थापन गर्न चाहनुहुन्छ?\nतलबाट प्लेटफर्म छान्नुहोस्:", "add_platform":"➕ अर्को प्लेटफर्म थप्नुहोस्", "main":"🔙 मुख्य मेनु", "list":"थपिएका खाताहरू:", "connected":"🟢 = जडान भयो | 🟡 = Token/API सेटअप बाँकी", "open":"ड्यासबोर्ड खोल्न खाताको नाम छान्नुहोस्:", "empty":"अहिलेसम्म कुनै खाता थपिएको छैन।\nनयाँ खाता थप्न तल थिच्नुहोस्।", "add":"➕ {p} खाता थप्नुहोस्", "all":"🔙 सबै प्लेटफर्म"},
 "as": {"choose":"📺 কোনটো প্লেটফৰ্ম পৰিচালনা কৰিব বিচাৰে?\nতলৰ পৰা প্লেটফৰ্ম বাছনি কৰক:", "add_platform":"➕ আন এটা প্লেটফৰ্ম যোগ কৰক", "main":"🔙 মূল মেনু", "list":"যোগ কৰা একাউণ্টসমূহ:", "connected":"🟢 = সংযুক্ত | 🟡 = Token/API ছেটআপ বাকী", "open":"ডেশ্বব’ৰ্ড খুলিবলৈ একাউণ্টৰ নামত ক্লিক কৰক:", "empty":"এতিয়াও কোনো একাউণ্ট যোগ কৰা হোৱা নাই।\nনতুন একাউণ্ট যোগ কৰিবলৈ তলত ক্লিক কৰক।", "add":"➕ {p} একাউণ্ট যোগ কৰক", "all":"🔙 সকলো প্লেটফৰ্ম"},
}


def _account_t(update, key, **kwargs):
    code = storage.get_user_lang(update.effective_user.id)
    table = ACCOUNT_UI.get(code, ACCOUNT_UI["bn"])
    return table.get(key, ACCOUNT_UI["en"].get(key, key)).format(**kwargs)


PLATFORM_ICONS = {
    "youtube": "▶️",
    "facebook": "📘",
    "tiktok": "🎵",
    "instagram": "📸",
    "linkedin": "💼",
}


def _auto_extract_id(platform: str, link: str) -> str:
    """লিংক থেকে প্ল্যাটফর্ম অনুযায়ী অটোমেটিক Channel ID, Page ID বা Username বের করে।"""
    p = platform.lower()
    s = (link or "").strip()
    if not s or s == "লিংক নেই":
        return ""

    if p == "youtube":
        m_uc = re.search(r"(UC[a-zA-Z0-9_-]{22})", s)
        if m_uc:
            return m_uc.group(1)
        m_handle = re.search(r"@([a-zA-Z0-9_.-]+)", s)
        if m_handle:
            return "@" + m_handle.group(1).split("/")[0].split("?")[0]

    elif p == "facebook":
        # profile.php?id=61596169348807 থেকে সংখ্যাটি বের করবে
        m_id = re.search(r"[?&]id=(\d+)", s)
        if m_id:
            return m_id.group(1)
        m_num = re.search(r"facebook\.com/(\d{10,})", s)
        if m_num:
            return m_num.group(1)
        m_page = re.search(r"facebook\.com/([a-zA-Z0-9.]+)/?", s)
        if m_page and m_page.group(1).lower() not in ("profile.php", "pages", "groups", "share"):
            return m_page.group(1)

    elif p == "tiktok":
        m_tt = re.search(r"@([a-zA-Z0-9_.-]+)", s)
        if m_tt:
            return "@" + m_tt.group(1).split("/")[0].split("?")[0]

    return ""


async def accounts_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accs = storage.get_accounts()
    platforms = storage.get_all_platforms()
    rows = []
    for p in platforms:
        icon = PLATFORM_ICONS.get(p.lower(), "📺")
        count = len(accs.get(p, {}))
        rows.append([InlineKeyboardButton(f"{icon} {p} ({count})", callback_data=f"acc:{p}")])

    rows.append([InlineKeyboardButton(_account_t(update, "add_platform"), callback_data="menu:add_platform")])
    rows.append([InlineKeyboardButton(_account_t(update, "main"), callback_data="menu:main")])
    await show(update, _account_t(update, "choose"), InlineKeyboardMarkup(rows))


async def _render_platform(update: Update, p: str):
    chans = storage.get_accounts().get(p, {})
    icon = PLATFORM_ICONS.get(p.lower(), "📋")
    rows = []

    if chans:
        body = (
            f"{icon} **{p} — {_account_t(update, 'list')}**\n\n"
            f"{_account_t(update, 'connected')}\n"
            f"{_account_t(update, 'open')}"
        )
        for name, info in chans.items():
            if isinstance(info, dict):
                has_key = "🟢" if (info.get("api_key") or info.get("oauth_token")) else "🟡"
            else:
                has_key = "🟡"
            rows.append([InlineKeyboardButton(f"{has_key} {name}", callback_data=f"acc_item:{p}:{name}")])
    else:
        body = f"{icon} **{p}**\n\n{_account_t(update, 'empty')}"

    rows.append([InlineKeyboardButton(_account_t(update, "add", p=p), callback_data=f"acc_add:{p}")])
    rows.append([InlineKeyboardButton(_account_t(update, "all"), callback_data="menu:accounts")])
    await show(update, body, InlineKeyboardMarkup(rows))


async def platform_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.callback_query.data.split(":", 1)[1]
    await _render_platform(update, p)


def _normalize_info(info, platform: str = "") -> dict:
    if isinstance(info, dict):
        # Preserve profile and future account metadata while normalizing known fields.
        normalized = dict(info)
        link = info.get("link", "লিংক নেই")
        ch_id = info.get("channel_id", "") or _auto_extract_id(platform, link)
        normalized.update({
            "link": link,
            "channel_id": ch_id,
            "api_key": info.get("api_key", ""),
            "oauth_token": info.get("oauth_token", None),
            "stats": info.get("stats", {"subscribers": "0", "views": "0", "videos": "0"}),
        })
        return normalized
    link = str(info)
    return {
        "link": link,
        "channel_id": _auto_extract_id(platform, link),
        "api_key": "",
        "oauth_token": None,
        "stats": {"subscribers": "0", "views": "0", "videos": "0"},
    }


async def _render_channel_dashboard(update: Update, p: str, name: str, notice: str = ""):
    chans = storage.get_accounts().get(p, {})
    if name not in chans:
        await _render_platform(update, p)
        return

    info = _normalize_info(chans[name], p)
    # যদি অটো-এক্সট্রাক্ট হয়ে থাকে তবে সেভ করে রাখবে
    storage.add_account(p, name, info)

    stats = info.get("stats") or {}
    p_low = p.lower()
    ch_id = info.get("channel_id") or "সেট করা নেই"
    api_ok = "✅ সংযুক্ত" if info.get("api_key") else "❌ নেই"
    oauth_ok = "✅ সংযুক্ত (Ready)" if info.get("oauth_token") else "❌ নেই"

    # ---- প্ল্যাটফর্ম অনুযায়ী আলাদা আলাদা ড্যাশবোর্ড ও বাটন ----
    if p_low == "youtube":
        text = (
            f"▶️ **YouTube Studio — {name}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **চ্যানেল লিংক:** {info.get('link')}\n"
            f"🆔 **Channel ID:** `{ch_id}`\n"
            f"🔑 **YouTube Data API v3:** {api_ok}\n"
            f"🔐 **OAuth Token (Upload):** {oauth_ok}\n\n"
            f"📈 **YouTube চ্যানেল অ্যানালিটিক্স:**\n"
            f"• 👥 সাবস্ক্রাইবার: **{stats.get('subscribers', '0')}**\n"
            f"• 👁 মোট ভিউ: **{stats.get('views', '0')}**\n"
            f"• 🎬 মোট ভিডিও: **{stats.get('videos', '0')}**\n"
        )
        rows = [
            [
                InlineKeyboardButton("🔄 Sync YouTube Stats", callback_data=f"acc_sync:{p}:{name}"),
                InlineKeyboardButton("🆔 Set Channel ID", callback_data=f"acc_edit:{p}:{name}:channel_id"),
            ],
            [
                InlineKeyboardButton("🔑 Set YouTube API Key", callback_data=f"acc_edit:{p}:{name}:api_key"),
                InlineKeyboardButton("🔐 Set OAuth Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
            ],
        ]

    elif p_low == "facebook":
        fb_token_ok = "✅ সংযুক্ত (Ready)" if (info.get("oauth_token") or info.get("api_key")) else "❌ নেই"
        text = (
            f"📘 **Facebook Page Studio — {name}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **পেজ লিংক:** {info.get('link')}\n"
            f"🆔 **Facebook Page ID:** `{ch_id}`\n"
            f"🔐 **Page Access Token:** {fb_token_ok}\n\n"
            f"📈 **Facebook পেজ অ্যানালিটিক্স:**\n"
            f"• 👥 মোট ফলোয়ার: **{stats.get('subscribers', '0')}**\n"
            f"• 👍 পেজ লাইক: **{stats.get('views', '0')}**\n"
            f"• 📡 আপলোড স্ট্যাটাস: **{stats.get('videos', 'Not Synced')}**\n"
        )
        # ফেসবুকে কোনো আলাদা API Key লাগে না, শুধু Page ID ও Page Access Token
        rows = [
            [
                InlineKeyboardButton("🔄 Sync Page Stats", callback_data=f"acc_sync:{p}:{name}"),
                InlineKeyboardButton("🆔 Set Page ID", callback_data=f"acc_edit:{p}:{name}:channel_id"),
            ],
            [
                InlineKeyboardButton("🔐 Set Page Access Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
            ],
        ]

    elif p_low == "tiktok":
        text = (
            f"🎵 **TikTok Studio — {name}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **প্রোফাইল লিংক:** {info.get('link')}\n"
            f"🆔 **TikTok @Username:** `{ch_id}`\n"
            f"🔑 **Client Key:** {api_ok}\n"
            f"🔐 **Access Token (Upload):** {oauth_ok}\n\n"
            f"📈 **TikTok প্রোফাইল অ্যানালিটিক্স:**\n"
            f"• 👥 ফলোয়ার: **{stats.get('subscribers', '0')}**\n"
            f"• ❤️ মোট লাইক: **{stats.get('views', '0')}**\n"
            f"• 🎬 মোট ভিডিও: **{stats.get('videos', '0')}**\n"
        )
        rows = [
            [
                InlineKeyboardButton("🔄 Check Status", callback_data=f"acc_sync:{p}:{name}"),
                InlineKeyboardButton("🆔 Set @Username", callback_data=f"acc_edit:{p}:{name}:channel_id"),
            ],
            [
                InlineKeyboardButton("🔑 Set Client Key", callback_data=f"acc_edit:{p}:{name}:api_key"),
                InlineKeyboardButton("🔐 Set Access Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
            ],
        ]

    else:
        text = (
            f"📊 **{p} Studio — {name}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **লিংক:** {info.get('link')}\n"
            f"🆔 **Account ID:** `{ch_id}`\n"
            f"🔐 **Access Token:** {oauth_ok}\n"
        )
        rows = [
            [
                InlineKeyboardButton("🆔 Set Account ID", callback_data=f"acc_edit:{p}:{name}:channel_id"),
                InlineKeyboardButton("🔐 Set Access Token", callback_data=f"acc_edit:{p}:{name}:oauth_token"),
            ],
        ]

    if notice:
        text += f"\n💡 {notice}\n"

    rows.append([
        InlineKeyboardButton("🔗 Edit Link", callback_data=f"acc_edit:{p}:{name}:link"),
        InlineKeyboardButton("🗑 Remove Account", callback_data=f"acc_del:{p}:{name}"),
    ])
    rows.append([InlineKeyboardButton(f"🔙 Back to {p}", callback_data=f"acc:{p}")])

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

    info = _normalize_info(chans[name], p)

    if p.lower() == "youtube":
        target = info.get("channel_id") or info.get("link") or name
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

    elif p.lower() == "facebook":
        token = info.get("oauth_token") or info.get("api_key") or ""
        target_id = info.get("channel_id") or "me"
        res, err = fetch_facebook_stats(target_id, token)
        if err:
            await _render_channel_dashboard(update, p, name, notice=err)
            return

        info["channel_id"] = res.get("channel_id") or info["channel_id"]
        info["stats"] = {
            "subscribers": res.get("subscribers", "0"),
            "views": res.get("views", "0"),
            "videos": res.get("videos", "Ready"),
        }
        storage.add_account(p, name, info)
        await _render_channel_dashboard(update, p, name, notice="✅ Facebook Page থেকে সফলভাবে লাইভ ডেটা আপডেট হয়েছে!")

    else:
        has_token = bool(info.get("oauth_token") or info.get("api_key"))
        msg = (
            f"✅ {p} অ্যাকাউন্টের টোকেন প্রস্তুত আছে (Upload Ready)।"
            if has_token
            else f"⚠️ {p}-এ কানেক্ট করতে প্রথমে Access Token যুক্ত করুন।"
        )
        await _render_channel_dashboard(update, p, name, notice=msg)


async def account_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name = update.callback_query.data.split(":", 2)
    if hasattr(storage, "remove_account"):
        storage.remove_account(p, name)
    await _render_platform(update, p)


async def add_platform_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 বাতিল করুন (Cancel)", callback_data="menu:accounts")]])
    await show(
        update,
        "➕ **নতুন প্ল্যাটফর্মের নাম লেখো:**\n(যেমন: `Instagram`, `LinkedIn`, `X`)",
        kb,
    )
    return WAIT_NEW_PLATFORM


async def add_platform_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plat_name = update.message.text.strip().replace(":", "")
    if plat_name:
        storage.add_custom_platform(plat_name)
    await accounts_home(update, context)
    return ConversationHandler.END


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["platform"] = p
    p_low = p.lower()

    if p_low == "youtube":
        example = "`Hafiz Islamic Story - https://youtube.com/channel/UCMY29TCNAzSNXbhimee1f8A`"
    elif p_low == "facebook":
        example = "`Hafiz Islamic Story - https://www.facebook.com/profile.php?id=61596169348807`"
    elif p_low == "tiktok":
        example = "`Clipzilla - https://www.tiktok.com/@clipzilla`"
    else:
        example = f"`My Account - https://{p_low}.com/myprofile`"

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 বাতিল করুন (Cancel)", callback_data=f"acc:{p}")]])
    await show(
        update,
        f"➕ **{p}-এ নতুন অ্যাকাউন্ট যোগ করো:**\n\n"
        f"নিচের ফরম্যাটে মেসেজ পাঠাও:\n"
        f"`নাম - লিংক`\n\n"
        f"**উদাহরণ:**\n{example}",
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

    name = name.replace(":", "-").strip()
    link = link.strip() or "লিংক নেই"
    ch_id = _auto_extract_id(p, link)

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

    if p.lower() == "facebook":
        hint = "✅ পেজ যুক্ত হয়েছে! এবার নিচ থেকে **🔐 Set Page Access Token** সেট করো।"
    elif p.lower() == "youtube":
        hint = "✅ চ্যানেল যুক্ত হয়েছে! এবার **🔑 Set YouTube API Key** দিলে লাইভ ভিউ/সাবস্ক্রাইবার দেখতে পাবে।"
    else:
        hint = "✅ অ্যাকাউন্ট যুক্ত হয়েছে! এবার নিচ থেকে প্রয়োজনীয় টোকেন সেট করো।"

    await _render_channel_dashboard(update, p, name, notice=hint)
    return ConversationHandler.END


async def edit_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name, field = update.callback_query.data.split(":", 3)
    context.user_data["edit_target"] = (p, name, field)
    p_low = p.lower()

    if field == "channel_id":
        if p_low == "youtube":
            msg = f"🆔 **{name}-এর YouTube Channel ID বা @Handle দাও:**\n(যেমন: `UCMY29TCNAzSNXbhimee1f8A` অথবা `@Clipzilla`)"
        elif p_low == "facebook":
            msg = f"🆔 **{name}-এর Facebook Page ID দাও:**\n(যেমন: `61596169348807`)"
        elif p_low == "tiktok":
            msg = f"🆔 **{name}-এর TikTok @Username দাও:**\n(যেমন: `@clipzilla`)"
        else:
            msg = f"🆔 **{name}-এর Account ID দাও:**"

    elif field == "api_key":
        if p_low == "youtube":
            msg = (
                f"🔑 **{name}-এর YouTube Data API v3 Key দাও:**\n"
                f"Google Cloud Console থেকে পাওয়া `AIzaSy...` কি-টি এখানে পেস্ট করো।\n"
                f"*(নিরাপত্তার স্বার্থে মেসেজটি সেভ হওয়ার সাথে সাথে ডিলিট হয়ে যাবে)*"
            )
        elif p_low == "tiktok":
            msg = f"🔑 **{name}-এর TikTok Developer Client Key দাও:**"
        else:
            msg = f"🔑 **{name}-এর API Key দাও:**"

    elif field == "oauth_token":
        if p_low == "youtube":
            msg = (
                f"🔐 **{name}-এর YouTube OAuth Token JSON দাও:**\n"
                f"সরাসরি ভিডিও আপলোড করার জন্য OAuth Refresh Token বা JSON পেস্ট করো।\n"
                f"*(মেসেজটি অটো-ডিলিট হবে)*"
            )
        elif p_low == "facebook":
            msg = (
                f"🔐 **{name}-এর Facebook Page Access Token দাও:**\n"
                f"Meta Developer / Graph API Explorer থেকে পাওয়া `EAA...` পেজ টোকেনটি পেস্ট করো।\n"
                f"এই একটি টোকেন দিয়েই ফলোয়ার সিঙ্ক এবং ভিডিও/রিলস আপলোড দুটোই হবে!\n"
                f"*(মেসেজটি অটো-ডিলিট হবে)*"
            )
        elif p_low == "tiktok":
            msg = f"🔐 **{name}-এর TikTok Access Token দাও:**\n*(মেসেজটি অটো-ডিলিট হবে)*"
        else:
            msg = f"🔐 **{name}-এর Access Token দাও:**"

    else:
        msg = f"🔗 **{name}-এর নতুন লিংক দাও:**"

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 বাতিল করুন (Cancel)", callback_data=f"acc_item:{p}:{name}")]])
    await show(update, msg, kb)
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
    info = _normalize_info(chans.get(name, {}), p)
    info[field] = val
    if field == "link" and not info.get("channel_id"):
        info["channel_id"] = _auto_extract_id(p, val)

    storage.add_account(p, name, info)
    await _render_channel_dashboard(update, p, name, notice="✅ তথ্য সফলভাবে সেভ করা হয়েছে!")
    return ConversationHandler.END


async def cancel_to_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("acc_item:"):
        _, p, name = data.split(":", 2)
        await _render_channel_dashboard(update, p, name)
    elif data.startswith("acc:"):
        p = data.split(":", 1)[1]
        await _render_platform(update, p)
    elif data == "menu:accounts":
        await accounts_home(update, context)
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
        CallbackQueryHandler(add_platform_start, pattern=r"^menu:add_platform$"),
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
        WAIT_NEW_PLATFORM: [
            CallbackQueryHandler(cancel_to_platform, pattern=r"^menu:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform_save),
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
