from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

import config
import storage
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup
from services.ai_providers import ask

WAIT_KEY = 1


async def ai_home(update, context):
    keys = storage.get_ai_keys()
    active = storage.get_active_ai()
    rows = []
    for p in config.AI_PROVIDERS:
        mark = ("✅" if p in keys else "❌") + (" ⭐" if p == active else "")
        rows.append([InlineKeyboardButton(f"{p} {mark}", callback_data=f"ai:{p}")])
    rows.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")])
    await show(update, "🤖 AI Connectors\n✅ = key আছে, ⭐ = active (সাধারণ মেসেজের উত্তর দেয়)", InlineKeyboardMarkup(rows))


async def _render_provider(update, p, extra=""):
    has = p in storage.get_ai_keys()
    active = storage.get_active_ai() == p
    text = (f"🤖 {p}\nKey: {'✅ আছে' if has else '❌ নেই'}\n"
            f"Active: {'⭐ হ্যাঁ' if active else 'না'}\nModel: {config.AI_MODELS[p]}")
    if extra:
        text += f"\n\n{extra}"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 API Key দাও", callback_data=f"ai_key:{p}")],
        [InlineKeyboardButton("⭐ Active করো", callback_data=f"ai_active:{p}"),
         InlineKeyboardButton("🧪 Test", callback_data=f"ai_test:{p}")],
        [InlineKeyboardButton("🔙 AI List", callback_data="menu:ai")],
    ])
    await show(update, text, markup)


async def provider_view(update, context):
    await _render_provider(update, update.callback_query.data.split(":", 1)[1])


async def set_active(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    if p not in storage.get_ai_keys():
        await update.callback_query.answer("আগে API key দাও", show_alert=True)
        return
    storage.set_active_ai(p)
    await _render_provider(update, p, "✅ এখন থেকে এটা active।")


async def test_ai(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    key = storage.get_ai_keys().get(p)
    if not key:
        await update.callback_query.answer("আগে API key দাও", show_alert=True)
        return
    await update.callback_query.answer("টেস্ট চলছে...")
    reply = await ask(p, key, "Reply with one short friendly sentence.")
    await _render_provider(update, p, f"🧪 Test:\n{reply[:800]}")


async def key_start(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["ai_provider"] = p
    await show(update, f"{p}-এর API key পাঠাও। (পাঠানোর পর আমি মেসেজটা মুছে দেব।)\nবাতিল করতে /cancel")
    return WAIT_KEY


async def key_save(update, context):
    p = context.user_data.get("ai_provider")
    storage.set_ai_key(p, update.message.text.strip())
    try:
        await update.message.delete()   # চ্যাটে key পড়ে না থাকে
    except Exception:
        pass
    if not storage.get_active_ai():
        storage.set_active_ai(p)
    await _render_provider(update, p, "✅ Key সেভ হয়েছে। এবার 🧪 Test দাও।")
    return ConversationHandler.END


async def cancel(update, context):
    await show(update, MAIN_TEXT, main_menu_markup())
    return ConversationHandler.END


async def chat(update, context):
    """মেনুর বাইরে যেকোনো টেক্সট → active AI উত্তর দেবে।"""
    keys = storage.get_ai_keys()
    if not keys:
        await update.message.reply_text("আগে 🤖 AI Connectors থেকে একটা API key দাও।", reply_markup=main_menu_markup())
        return
    p = storage.get_active_ai()
    if p not in keys:
        p = next(iter(keys))
    wait = await update.message.reply_text(f"⏳ {p} ভাবছে...")
    answer = await ask(p, keys[p], update.message.text)
    await wait.edit_text(answer[:4000])


conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(key_start, pattern=r"^ai_key:")],
    states={WAIT_KEY: [
        CallbackQueryHandler(cancel, pattern=r"^menu:"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, key_save),
    ]},
    fallbacks=[CommandHandler(["start", "cancel"], cancel)],
)
