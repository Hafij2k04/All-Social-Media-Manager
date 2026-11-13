from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Accounts", callback_data="menu:accounts"),
         InlineKeyboardButton("🤖 AI Connectors", callback_data="menu:ai")],
        [InlineKeyboardButton("⬆️ Upload Video", callback_data="menu:upload"),
         InlineKeyboardButton("📊 Analyze & Ideas", callback_data="menu:analyze")],
        [InlineKeyboardButton("⚙️ Status", callback_data="menu:status")],
    ])


MAIN_TEXT = "🏠 Social Media Manager\nনিচের মেনু থেকে বেছে নাও।"
