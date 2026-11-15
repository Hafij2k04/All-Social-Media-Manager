import logging
import re
import secrets
import time
import os

import config
import oauth
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


PLATFORM_ACCOUNT_FIELDS = {
    "youtube": [("channel_id","🆔 Set Channel ID / @Handle"),("api_key","🔑 Set YouTube API Key (public data)"),("oauth_token","🔐 Set YouTube OAuth Token (upload/private data)")],
    "facebook": [("channel_id","🆔 Set Facebook Page ID"),("oauth_token","🔐 Set Facebook Page Access Token")],
    "instagram": [("channel_id","🆔 Set Instagram Professional Account ID"),("oauth_token","🔐 Set Instagram Access Token")],
    "tiktok": [("channel_id","👤 Set TikTok Username / Profile"),("open_id","🆔 Set TikTok Open ID"),("oauth_token","🔐 Set TikTok User Access Token")],
    "linkedin": [("channel_id","🆔 Set LinkedIn Person / Organization URN"),("oauth_token","🔐 Set LinkedIn Access Token")],
}

def _platform_fields(platform: str):
    return PLATFORM_ACCOUNT_FIELDS.get(platform.lower(), [])


async def _render_channel_dashboard(update: Update, p: str, name: str, notice: str = ""):
    chans = storage.get_accounts().get(p, {})
    if name not in chans:
        await _render_platform(update, p)
        return
    info = _normalize_info(chans[name], p)
    storage.add_account(p, name, info)
    stats = info.get("stats") or {}
    low = p.lower()
    lang = storage.get_user_lang(update.effective_user.id)
    labels = {
        "bn": ["সেট করা নেই","সেভ করা আছে","সেট করা হয়নি","চ্যানেল লিংক","পেজ লিংক","প্রোফাইল লিংক","লিংক","চ্যানেল অ্যানালিটিক্স","পেজ অ্যানালিটিক্স","সাবস্ক্রাইবার","মোট ভিউ","মোট ভিডিও","ফলোয়ার","পেজ লাইক","লিংক এডিট","অ্যাকাউন্ট মুছুন","ফিরে যান"],
        "en": ["Not set","Saved","Not configured","Channel link","Page link","Profile link","Link","Channel analytics","Page analytics","Subscribers","Total views","Total videos","Followers","Page likes","Edit link","Remove account","Back to"],
        "hi": ["सेट नहीं","सेव है","सेट नहीं किया","चैनल लिंक","पेज लिंक","प्रोफ़ाइल लिंक","लिंक","चैनल विश्लेषण","पेज विश्लेषण","सब्सक्राइबर","कुल व्यू","कुल वीडियो","फ़ॉलोअर","पेज लाइक","लिंक संपादित करें","अकाउंट हटाएँ","वापस"],
        "ur": ["سیٹ نہیں","محفوظ ہے","سیٹ نہیں","چینل لنک","پیج لنک","پروفائل لنک","لنک","چینل تجزیات","پیج تجزیات","سبسکرائبرز","کل ویوز","کل ویڈیوز","فالوورز","پیج لائکس","لنک تبدیل کریں","اکاؤنٹ ہٹائیں","واپس"],
        "zh": ["未设置","已保存","未配置","频道链接","主页链接","个人资料链接","链接","频道分析","主页分析","订阅者","总观看量","视频总数","关注者","主页点赞","编辑链接","删除账号","返回"],
        "ar": ["غير مضبوط","تم الحفظ","غير مهيأ","رابط القناة","رابط الصفحة","رابط الملف الشخصي","الرابط","تحليلات القناة","تحليلات الصفحة","المشتركون","المشاهدات","الفيديوهات","المتابعون","إعجابات الصفحة","تعديل الرابط","حذف الحساب","رجوع"],
        "ne": ["सेट गरिएको छैन","सुरक्षित छ","सेट छैन","च्यानल लिंक","पेज लिंक","प्रोफाइल लिंक","लिंक","च्यानल विश्लेषण","पेज विश्लेषण","सब्सक्राइबर","कुल भ्यु","कुल भिडियो","फलोअर","पेज लाइक","लिंक सम्पादन","खाता हटाउनुहोस्","फर्कनुहोस्"],
        "as": ["ছেট কৰা হোৱা নাই","সংৰক্ষিত","ছেট কৰা হোৱা নাই","চেনেল লিংক","পেজ লিংক","প্ৰফাইল লিংক","লিংক","চেনেল বিশ্লেষণ","পেজ বিশ্লেষণ","ছাবস্ক্ৰাইবাৰ","মুঠ ভিউ","মুঠ ভিডিঅ’","ফ’ল’ৱাৰ","পেজ লাইক","লিংক সম্পাদনা","একাউণ্ট আঁতৰাওক","উভতি যাওক"],
    }
    t = labels.get(lang, labels["bn"])
    link_label = t[3] if low=="youtube" else t[4] if low=="facebook" else t[5] if low in ("instagram","tiktok") else t[6]
    text = f"📊 **{p} — {name}**\n━━━━━━━━━━━━━━━━━━━━\n🔗 **{link_label}:** {info.get('link') or t[0]}\n"
    rows = []
    for field, button in _platform_fields(p):
        value = info.get(field)
        if field == "oauth_token" and low == "youtube":
            try:
                value = storage.get_youtube_oauth(p, name).get("access_token")
            except Exception:
                value = None
        if field == "oauth_token" and low == "facebook":
            value = value or info.get("api_key")  # legacy Facebook token compatibility
        status = f"✅ {t[1]}" if value else f"⚪ {t[2]}"
        field_labels = {
            "youtube": {"channel_id":"Channel ID / Handle","api_key":"YouTube API Key (public data)","oauth_token":"YouTube OAuth 2.0 Token"},
            "facebook": {"channel_id":"Facebook Page ID","oauth_token":"Facebook Page Access Token"},
            "instagram": {"channel_id":"Instagram Professional Account ID","oauth_token":"Instagram Access Token"},
            "tiktok": {"channel_id":"TikTok Username / Profile","open_id":"TikTok Open ID","oauth_token":"TikTok User Access Token"},
            "linkedin": {"channel_id":"LinkedIn Person / Organization URN","oauth_token":"LinkedIn OAuth Access Token"},
        }
        label = field_labels.get(low, {}).get(field, field.replace("_", " ").title())
        text += f"• **{label}:** {status}\n"
        rows.append([InlineKeyboardButton(button, callback_data=f"acc_edit:{p}:{name}:{field}")])
    if low == "youtube":
        rows.insert(0, [InlineKeyboardButton("🔗 Connect YouTube with Google", callback_data=f"yt_oauth:{name}")])
        text += f"\n📈 **{t[7]}:**\n• {t[9]}: **{stats.get('subscribers','0')}**\n• {t[10]}: **{stats.get('views','0')}**\n• {t[11]}: **{stats.get('videos','0')}**\n"
        rows.insert(0,[InlineKeyboardButton("🔄 Sync YouTube Stats",callback_data=f"acc_sync:{p}:{name}")])
    elif low == "facebook":
        text += f"\n📈 **{t[8]}:**\n• {t[12]}: **{stats.get('subscribers','0')}**\n• {t[13]}: **{stats.get('views','0')}**\n"
        rows.insert(0,[InlineKeyboardButton("🔄 Sync Facebook Page Stats",callback_data=f"acc_sync:{p}:{name}")])
    elif low in ("instagram","tiktok","linkedin"):
        text += "\nℹ️ API access depends on official app approval and granted permissions."
    if notice:
        text += f"\n💡 {notice}\n"
    rows.append([InlineKeyboardButton("🔗 "+t[14],callback_data=f"acc_edit:{p}:{name}:link"),InlineKeyboardButton("🗑 "+t[15],callback_data=f"acc_del:{p}:{name}")])
    rows.append([InlineKeyboardButton("🔙 "+t[16]+f" {p}",callback_data=f"acc:{p}")])
    await show(update,text,InlineKeyboardMarkup(rows))


async def youtube_oauth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.callback_query.data.split(":", 1)[1]
    platform = "YouTube"
    accounts = storage.get_accounts().get(platform, {})
    if name not in accounts:
        await _render_platform(update, platform)
        return ConversationHandler.END
    required = (config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET, config.GOOGLE_REDIRECT_URI, os.environ.get("TOKEN_ENCRYPTION_KEY", ""))
    if not all(required):
        await show(update, "⚠️ YouTube OAuth এখনো কনফিগার করা হয়নি। Render Environment Variables-এ GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI এবং TOKEN_ENCRYPTION_KEY সেট করতে হবে।", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Account Dashboard", callback_data=f"acc_item:{platform}:{name}")]]))
        return ConversationHandler.END
    state = secrets.token_urlsafe(32)
    storage.create_oauth_state(state, {"platform": platform, "name": name, "user_id": update.effective_user.id}, int(time.time()) + 600)
    try:
        auth_url = oauth.build_authorization_url(state)
    except Exception as exc:
        logger.exception("Could not create YouTube OAuth URL")
        await _render_channel_dashboard(update, platform, name, notice=f"OAuth setup error: {exc}")
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Continue with Google", url=auth_url)], [InlineKeyboardButton("🔙 Account Dashboard", callback_data=f"acc_item:{platform}:{name}")]])
    await show(update, f"🔐 **Connect {name} with Google**\n\nContinue with Google, choose the correct YouTube channel owner account, and approve the requested YouTube permissions. After approval, return to Telegram.", keyboard)
    return ConversationHandler.END

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
            "open_id": "",
            "stats": {"subscribers": "0", "views": "0", "videos": "0"},
        },
    )

    hints = {
        "youtube": "✅ YouTube চ্যানেল যুক্ত হয়েছে। Public statistics-এর জন্য API Key এবং ভিডিও upload/private data access-এর জন্য OAuth 2.0 Token আলাদাভাবে সেট করো।",
        "facebook": "✅ Facebook Page যুক্ত হয়েছে। Page ID ও Page Access Token সেট করো; token-এ প্রয়োজনীয় Page permissions থাকতে হবে।",
        "instagram": "✅ Instagram account যুক্ত হয়েছে। Professional account ID ও অনুমোদিত Instagram/Meta Access Token সেট করো।",
        "tiktok": "✅ TikTok account যুক্ত হয়েছে। TikTok OAuth থেকে পাওয়া Open ID ও User Access Token সেট করতে হবে; Content Posting-এর জন্য app approval এবং video.publish scope লাগে।",
        "linkedin": "✅ LinkedIn account যুক্ত হয়েছে। Person/Organization URN ও অনুমোদিত OAuth Access Token সেট করো।",
    }
    hint = hints.get(p.lower(), f"✅ {p} account added. This platform's authentication fields are not configured yet; add its schema to PLATFORM_ACCOUNT_FIELDS before connecting it.")

    await _render_channel_dashboard(update, p, name, notice=hint)
    return ConversationHandler.END


async def edit_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, p, name, field = update.callback_query.data.split(":", 3)
    context.user_data["edit_target"] = (p, name, field)
    low = p.lower()
    if field == "channel_id":
        prompts = {
            "youtube": f"🆔 **{name}-এর YouTube Channel ID বা @Handle দাও:**\nউদাহরণ: `UCxxxxxxxxxxxxxxxxxxxxxx` অথবা `@channelname`",
            "facebook": f"🆔 **{name}-এর Facebook Page ID দাও:**",
            "instagram": f"🆔 **{name}-এর Instagram Professional Account ID দাও:**",
            "tiktok": f"👤 **{name}-এর TikTok Username / Profile link দাও:** (যেমন: @username)",
            "linkedin": f"🆔 **{name}-এর LinkedIn Person অথবা Organization URN দাও:**",
        }
        msg = prompts.get(low, f"🆔 **{name}-এর platform account ID দাও:**")
    elif field == "open_id" and low == "tiktok":
        msg = f"🆔 **{name}-এর TikTok Open ID দাও:**\\nএটি TikTok OAuth user authorization-এর response থেকে পাওয়া যায়। Profile username (@name) Open ID নয়।"
    elif field == "api_key" and low == "youtube":
        msg = (f"🔑 **{name}-এর YouTube Data API v3 Key দাও:**\n"
               "এটি শুধু public channel/video data পড়ার জন্য। ভিডিও upload বা private data access-এর জন্য OAuth 2.0 প্রয়োজন।\n"
               "Google Cloud Console থেকে API Key পেস্ট করো। মেসেজটি সেভের পর ডিলিট হবে।")
    elif field == "oauth_token":
        prompts = {
            "youtube": "YouTube OAuth 2.0 token দিন। এটি private channel data ও video upload-এর জন্য; API Key একা যথেষ্ট নয়।",
            "facebook": "Meta OAuth থেকে Facebook Page Access Token দিন। প্রয়োজনীয় Page permissions থাকতে হবে।",
            "instagram": "Instagram Professional account-এর অনুমোদিত OAuth Access Token দিন।",
            "tiktok": "TikTok user OAuth Access Token দিন। Content Posting-এর জন্য app approval ও video.publish scope প্রয়োজন।",
            "linkedin": "LinkedIn OAuth 2.0 Access Token দিন। প্রয়োজনীয় posting permission থাকতে হবে।",
        }
        msg = f"🔐 **{name} — Access Token**\n{prompts.get(low, 'এই প্ল্যাটফর্মের OAuth Access Token দিন।')}\n*(নিরাপত্তার জন্য সেভের পর এই মেসেজ ডিলিট হবে)*"
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
        CallbackQueryHandler(youtube_oauth_start, pattern=r"^yt_oauth:"),
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
