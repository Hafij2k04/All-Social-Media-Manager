MESSAGES = {
    "en": {
        "welcome": "Welcome!",
        "select_lang": "Please select a language."
    },
    "bn": {
        "welcome": "স্বাগতম!",
        "select_lang": "অনুগ্রহ করে একটি ভাষা নির্বাচন করুন।"
    },
    "ar": {
        "welcome": "أهلاً بك!",
        "select_lang": "يرجى تحديد لغة."
    },
    "hi": {
        "welcome": "स्वागत है!",
        "select_lang": "कृपया एक भाषा चुनें।"
    }
}

def get_text(lang_code, key):
    return MESSAGES.get(lang_code, MESSAGES["en"]).get(key, MESSAGES["en"][key])
