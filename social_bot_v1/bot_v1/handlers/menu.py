from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import config
import storage
from handlers import ai_connectors, automation, platforms
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup


async def start(update, context):
    await update.effective_message.reply_text(MAIN_TEXT, reply_markup=main_menu_markup())


async def status(update, context):
    accs = storage.get_accounts()
    total = sum(len(v) for v in accs.values())
    keys = ", ".join(storage.get_ai_keys().keys()) or "নেই"
    text = (f"⚙️ Status (V1)\n"
            f"• তোমার ID: {update.effective_user.id}\n"
            f"• অনুমোদিত ID সংখ্যা: {len(config.ALLOWED_IDS)}\n"
            f"• সেভ করা অ্যাকাউন্ট: {total}\n"
            f"• AI key আছে: {keys}\n"
            f"• Active AI: {storage.get_active_ai() or 'নেই'}\n"
            f"• স্টোরেজ: JSON ফাইল ⚠️ (Render রিস্টার্টে মুছে যায়, V2 তে ঠিক হবে)")
    await show(update, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")]]))


async def language_home(update, context):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="menu:main"),
         InlineKeyboardButton("🇺🇸 English", callback_data="menu:main")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")],
    ])
    await show(update, "🌐 ভাষা নির্বাচন করো / Select Language:", markup)


async def menu_router(update, context):
    action = update.callback_query.data.split(":", 1)[1]
    if action == "main":
        await show(update, MAIN_TEXT, main_menu_markup())
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
