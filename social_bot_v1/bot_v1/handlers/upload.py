"""V7 : ভিডিও আপলোড (এখন শুধু কাঠামো)।"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.common import show

BACK = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")]])


async def upload_home(update, context):
    await show(update, "⬆️ Upload Video\n🚧 V7 এ আসছে: ভিডিও পাঠাবে → প্ল্যাটফর্ম বাছবে → টাইটেল/ডিসক্রিপশন/হ্যাশট্যাগসহ সব জায়গায় আপলোড।", BACK)


async def on_video(update, context):
    await update.message.reply_text("🎬 ভিডিও পেয়েছি, কিন্তু আপলোড ফিচার এখনো বানানো হয়নি (V7)।")
