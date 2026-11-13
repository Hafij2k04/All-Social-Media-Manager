from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

import config
import storage
from handlers.common import show
from keyboards import MAIN_TEXT, main_menu_markup

WAIT_ACCOUNT = 1


async def accounts_home(update, context):
    accs = storage.get_accounts()
    rows = [[InlineKeyboardButton(f"{p} ({len(accs.get(p, {}))})", callback_data=f"acc:{p}")]
            for p in config.PLATFORMS]
    rows.append([InlineKeyboardButton("➕ Add Another Platform", callback_data="menu:add_platform")])
    rows.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")])
    await show(update, "📺 কোন প্ল্যাটফর্ম ম্যানেজ করবে?", InlineKeyboardMarkup(rows))


async def _render_platform(update, p):
    chans = storage.get_accounts().get(p, {})
    body = "\n".join(f"• {n}: {l}" for n, l in chans.items()) or "এখনো কিছু যোগ করা হয়নি।"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Account/Channel", callback_data=f"acc_add:{p}")],
        [InlineKeyboardButton("🔙 Platforms", callback_data="menu:accounts")],
    ])
    await show(update, f"📋 {p}\n\n{body}\n\n(V1: এখানে শুধু নাম-লিংক সেভ হয়। আসল কানেকশন V4+ এ।)", markup)


async def platform_view(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    await _render_platform(update, p)


async def add_start(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["platform"] = p
    await show(update, f"{p}-এর জন্য লেখো:\nনাম - লিংক\n(যেমন: MyChannel - youtube.com/@mychannel)\n\nবাতিল করতে /cancel")
    return WAIT_ACCOUNT


async def add_save(update, context):
    p = context.user_data.get("platform")
    text = update.message.text.strip()
    name, link = (text.split(" - ", 1) + [""])[:2] if " - " in text else (text, "লিংক নেই")
    storage.add_account(p, name.strip(), link.strip() or "লিংক নেই")
    await _render_platform(update, p)
    return ConversationHandler.END


async def cancel(update, context):
    await show(update, MAIN_TEXT, main_menu_markup())
    return ConversationHandler.END


conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_start, pattern=r"^acc_add:")],
    states={WAIT_ACCOUNT: [
        CallbackQueryHandler(cancel, pattern=r"^menu:"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_save),
    ]},
    fallbacks=[CommandHandler(["start", "cancel"], cancel)],
)
