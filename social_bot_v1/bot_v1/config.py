"""সব সেটিংস এখানে। সিক্রেট শুধু Render Environment Variables থেকে আসবে।"""
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# কমা দিয়ে একাধিক ID দেওয়া যায়: 123456789,987654321
ALLOWED_IDS = {
    int(x) for x in os.environ.get("ALLOWED_IDS", "").replace(" ", "").split(",")
    if x.strip().isdigit()
}

PORT = int(os.environ.get("PORT", 8080))
DATA_FILE = os.environ.get("DATA_FILE", "bot_data.json")  # V2 তে ডাটাবেস দিয়ে বদলাবে

PLATFORMS = ["YouTube", "Facebook", "TikTok", "Instagram", "LinkedIn"]
AI_PROVIDERS = ["Claude", "ChatGPT", "Gemini", "Grok"]

# মডেলের নাম Render Environment থেকে বদলানো যাবে (কোড না ছুঁয়ে)।
# নাম কাজ না করলে সংশ্লিষ্ট কোম্পানির ডকুমেন্টেশনে এখনকার নাম দেখে env-এ বসাও।
AI_MODELS = {
    "Claude": os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5"),
    "ChatGPT": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    "Gemini": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
    "Grok": os.environ.get("GROK_MODEL", "grok-4"),
}
