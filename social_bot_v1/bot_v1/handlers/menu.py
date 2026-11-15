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
    accs = storage.get_accounts()
    total = sum(len(v) for v in accs.values())
    keys = ", ".join(storage.get_ai_keys().keys()) or "নেই"
    text = (f"⚙️ Status (V1)\n"
            f"• তোমার ID: {update.effective_user.id}\n"
            f"• অনুমোদিত ID সংখ্যা: {len(config.ALLOWED_IDS)}\n"
            f"• সেভ করা অ্যাকাউন্ট: {total}\n"
            f"• AI key আছে: {keys}\n"
            f"• Active AI: {storage.get_active_ai() or 'নেই'}\n"
            f"• স্টোরেজ: JSON ফাইল ⚠️ (Render রিস্টার্টে মুছে যেতে পারে)")
    lang_code = storage.get_user_lang(update.effective_user.id)
    back = get_text(lang_code, "back")
    await show(update, text, InlineKeyboardMarkup([
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
