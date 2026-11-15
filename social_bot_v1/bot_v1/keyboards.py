from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from lang import get_text


def main_menu_markup(lang_code="bn"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(lang_code, "menu_accounts"), callback_data="menu:accounts"),
         InlineKeyboardButton(get_text(lang_code, "menu_ai"), callback_data="menu:ai")],
        [InlineKeyboardButton(get_text(lang_code, "menu_upload"), callback_data="menu:upload"),
         InlineKeyboardButton(get_text(lang_code, "menu_analyze"), callback_data="menu:analyze")],
        [InlineKeyboardButton(get_text(lang_code, "menu_status"), callback_data="menu:status"),
         InlineKeyboardButton(get_text(lang_code, "menu_language"), callback_data="menu:language")],
    ])


def get_main_text(lang_code="bn"):
    return get_text(lang_code, "welcome") + "\n" + (
        "নিচের মেনু থেকে বেছে নাও।" if lang_code == "bn"
        else "Choose an option from the menu below."
    )


# Backward-compatible default for existing imports.
MAIN_TEXT = get_main_text("bn")
