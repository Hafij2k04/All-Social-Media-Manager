from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import config
import storage
from handlers import ai_connectors, automation, platforms
from handlers.common import show
from keyboards import get_main_text, main_menu_markup
from lang import LANGUAGE_NAMES, get_text


async def show_update_main_text_menu(update, context, notice=""):
    lang_code = storage.get_user_lang(update.effective_user.id)
    text = get_main_text(lang_code)
    if notice:
        text = notice + "\n\n" + text
    await show(update, text, main_menu_markup(lang_code))


async def start(update, context):
    lang_code = storage.get_user_lang(update.effective_user.id)
    await update.effective_message.reply_text(
        get_main_text(lang_code),
        reply_markup=main_menu_markup(lang_code)
    )


async def status(update, context):
    """Show the bot's current configuration without exposing any secret values."""
    import os

    user_id = update.effective_user.id
    lang_code = storage.get_user_lang(user_id)
    accs = storage.get_accounts()
    keys = storage.get_ai_keys()
    active_ai = storage.get_active_ai()

    # Count saved accounts and accounts that have a credential stored.
    total_accounts = 0
    platform_lines = []
    for platform, accounts in accs.items():
        if not isinstance(accounts, dict):
            continue
        count = len(accounts)
        if not count:
            continue
        total_accounts += count
        with_credentials = 0
        for info in accounts.values():
            if isinstance(info, dict) and (info.get("oauth_token") or info.get("api_key")):
                with_credentials += 1
        platform_lines.append((platform, count, with_credentials))

    # These indicators report saved configuration, not live API verification.
    translations = {
        "bn": {
            "title": "⚙️ বটের বর্তমান স্ট্যাটাস",
            "bot": "বট: সচল",
            "access": "আপনার অ্যাক্সেস: অনুমোদিত",
            "accounts": "সেভ করা অ্যাকাউন্ট",
            "platforms": "প্ল্যাটফর্ম অনুযায়ী",
            "none": "কোনোটি নেই",
            "ai": "সেভ করা AI API Key",
            "active": "Active AI",
            "storage": "ডাটা ফাইল",
            "exists": "পাওয়া গেছে",
            "missing": "এখনো তৈরি হয়নি",
            "note": "নোট: Key/Token সেভ আছে কি না দেখানো হচ্ছে; এগুলো লাইভ API দিয়ে যাচাই করা হয়নি।",
            "credential": "Credential সেভ",
        },
        "en": {
            "title": "⚙️ Current Bot Status",
            "bot": "Bot: Running",
            "access": "Your access: Authorized",
            "accounts": "Saved accounts",
            "platforms": "By platform",
            "none": "None",
            "ai": "Saved AI API keys",
            "active": "Active AI",
            "storage": "Data file",
            "exists": "Found",
            "missing": "Not created yet",
            "note": "Note: This shows whether credentials are saved; live API validity has not been checked.",
            "credential": "credentials saved",
        },
        "hi": {
            "title": "⚙️ बॉट की वर्तमान स्थिति",
            "bot": "बॉट: चालू",
            "access": "आपकी पहुँच: अधिकृत",
            "accounts": "सहेजे गए अकाउंट",
            "platforms": "प्लेटफ़ॉर्म के अनुसार",
            "none": "कोई नहीं",
            "ai": "सहेजी गई AI API कुंजियाँ",
            "active": "सक्रिय AI",
            "storage": "डेटा फ़ाइल",
            "exists": "मिल गई",
            "missing": "अभी नहीं बनी",
            "note": "नोट: यह केवल सहेजे गए क्रेडेंशियल दिखाता है; लाइव API जाँच नहीं हुई है।",
            "credential": "क्रेडेंशियल सहेजे",
        },
        "ur": {
            "title": "⚙️ بوٹ کی موجودہ حالت",
            "bot": "بوٹ: چل رہا ہے",
            "access": "آپ کی رسائی: مجاز",
            "accounts": "محفوظ اکاؤنٹس",
            "platforms": "پلیٹ فارم کے لحاظ سے",
            "none": "کوئی نہیں",
            "ai": "محفوظ AI API کیز",
            "active": "فعال AI",
            "storage": "ڈیٹا فائل",
            "exists": "موجود ہے",
            "missing": "ابھی نہیں بنی",
            "note": "نوٹ: یہ صرف محفوظ اسناد دکھاتا ہے؛ لائیو API کی تصدیق نہیں ہوئی۔",
            "credential": "اسناد محفوظ",
        },
        "zh": {
            "title": "⚙️ 机器人当前状态",
            "bot": "机器人：运行中",
            "access": "您的访问权限：已授权",
            "accounts": "已保存的账号",
            "platforms": "按平台分类",
            "none": "无",
            "ai": "已保存的 AI API 密钥",
            "active": "当前 AI",
            "storage": "数据文件",
            "exists": "已找到",
            "missing": "尚未创建",
            "note": "说明：这里只显示凭据是否已保存，尚未进行实时 API 验证。",
            "credential": "已保存凭据",
        },
        "ar": {
            "title": "⚙️ حالة البوت الحالية",
            "bot": "البوت: يعمل",
            "access": "صلاحية الوصول: مصرح بها",
            "accounts": "الحسابات المحفوظة",
            "platforms": "حسب المنصة",
            "none": "لا يوجد",
            "ai": "مفاتيح AI API المحفوظة",
            "active": "الذكاء الاصطناعي النشط",
            "storage": "ملف البيانات",
            "exists": "موجود",
            "missing": "لم يتم إنشاؤه بعد",
            "note": "ملاحظة: يعرض هذا حفظ بيانات الاعتماد فقط، ولم يتم التحقق من API مباشرة.",
            "credential": "بيانات اعتماد محفوظة",
        },
        "ne": {
            "title": "⚙️ बोटको हालको अवस्था",
            "bot": "बोट: चलिरहेको",
            "access": "तपाईंको पहुँच: अधिकृत",
            "accounts": "सुरक्षित खाताहरू",
            "platforms": "प्लेटफर्म अनुसार",
            "none": "कुनै छैन",
            "ai": "सुरक्षित AI API कुञ्जीहरू",
            "active": "सक्रिय AI",
            "storage": "डेटा फाइल",
            "exists": "भेटियो",
            "missing": "अहिलेसम्म बनेको छैन",
            "note": "नोट: यसले सुरक्षित प्रमाणहरू मात्र देखाउँछ; लाइभ API जाँच गरिएको छैन।",
            "credential": "प्रमाण सुरक्षित",
        },
        "as": {
            "title": "⚙️ বটৰ বৰ্তমান অৱস্থা",
            "bot": "বট: চলি আছে",
            "access": "আপোনাৰ প্ৰৱেশাধিকাৰ: অনুমোদিত",
            "accounts": "সংৰক্ষিত একাউণ্ট",
            "platforms": "প্লেটফৰ্ম অনুসৰি",
            "none": "এটাও নাই",
            "ai": "সংৰক্ষিত AI API Key",
            "active": "সক্ৰিয় AI",
            "storage": "ডাটা ফাইল",
            "exists": "পোৱা গৈছে",
            "missing": "এতিয়াও সৃষ্টি হোৱা নাই",
            "note": "টোকা: ইয়াত কেৱল Key/Token সংৰক্ষিত আছে নে নাই দেখুওৱা হৈছে; Live API পৰীক্ষা কৰা হোৱা নাই।",
            "credential": "Credential সংৰক্ষিত",
        },
    }
    t = translations.get(lang_code, translations["bn"])

    lines = [
        t["title"],
        "━━━━━━━━━━━━━━━━━━━━",
        f"🟢 {t['bot']}",
        f"🛡️ {t['access']}",
        f"👤 Telegram ID: {user_id}",
        "",
        f"📺 {t['accounts']}: {total_accounts}",
        f"{t['platforms']}:",
    ]
    lines.extend(
        [f"  • {platform}: {count} ({t['credential']}: {with_credentials})"
         for platform, count, with_credentials in platform_lines]
        if platform_lines else [f"  • {t['none']}"]
    )
    lines.extend([
        "",
        f"🤖 {t['ai']}: {', '.join(keys.keys()) if keys else t['none']}",
        f"⭐ {t['active']}: {active_ai or t['none']}",
        f"💾 {t['storage']}: {t['exists'] if os.path.exists(config.DATA_FILE) else t['missing']}",
        "",
        f"ℹ️ {t['note']}",
    ])

    back = get_text(lang_code, "back")
    await show(update, "\n".join(lines), InlineKeyboardMarkup([
        [InlineKeyboardButton(back, callback_data="menu:main")]
    ]))

async def language_home(update, context):
    user_id = update.effective_user.id
    current = storage.get_user_lang(user_id)
    rows = []
    codes = list(LANGUAGE_NAMES.keys())
    for i in range(0, len(codes), 2):
        row = []
        for code in codes[i:i + 2]:
            label = LANGUAGE_NAMES[code]
            if code == current:
                label = "✅ " + label
            row.append(InlineKeyboardButton(label, callback_data=f"lang:{code}"))
        rows.append(row)

    rows.append([InlineKeyboardButton(
        get_text(current, "back"), callback_data="menu:main"
    )])
    await show(
        update,
        get_text(current, "language_title") + f"\n\nবর্তমান ভাষা: {LANGUAGE_NAMES[current]}",
        InlineKeyboardMarkup(rows)
    )


async def menu_router(update, context):
    callback_data = update.callback_query.data

    # Language buttons use "lang:<code>", not the "menu:<action>" prefix.
    # Handle them before parsing menu actions.
    if callback_data.startswith("lang:"):
        lang_code = callback_data.split(":", 1)[1]
        await update.callback_query.answer()
        if storage.set_user_lang(update.effective_user.id, lang_code):
            await show_update_main_text_menu(
                update, context, get_text(lang_code, "language_saved")
            )
        else:
            await update.callback_query.answer(
                "Unsupported language", show_alert=True
            )
        return

    action = callback_data.split(":", 1)[1]
    if action == "main":
        await show_update_main_text_menu(update, context)
    elif action == "accounts":
        await platforms.accounts_home(update, context)
    elif action == "ai":
        await ai_connectors.ai_home(update, context)
    elif action == "analyze":
        await automation.analyze_home(update, context)
    elif action == "status":
        await status(update, context)
    elif action == "language":
        await language_home(update, context)
    elif action == "add_platform":
        await show(update, "➕ নতুন প্ল্যাটফর্ম যোগ করার অপশন পরবর্তী ধাপে চালু করা হবে।",
                   InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu:accounts")]]))
    elif action == "add_connector":
        await show(update, "➕ নতুন AI Connector যোগ করার অপশন পরবর্তী ধাপে চালু করা হবে।",
                   InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu:ai")]]))
