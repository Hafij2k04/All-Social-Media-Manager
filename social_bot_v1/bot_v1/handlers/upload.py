import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import storage
from handlers.common import show
from handlers.platforms import (
    build_upload_platform_keyboard,
    get_available_targets,
    toggle_upload_platform,
)
from keyboards import MAIN_TEXT, main_menu_markup

logger = logging.getLogger(__name__)

# Conversation States
WAIT_VIDEO, UPLOAD_DASHBOARD, WAIT_TEXT_INPUT, WAIT_THUMB_INPUT = range(4)


def _init_session(file_id: str, width: int, height: int) -> dict:
    is_vertical = height > width
    aspect_label = "9:16 (Vertical / Shorts / Reels)" if is_vertical else "16:9 (Horizontal / Standard)"
    
    # ডিফল্টভাবে সব সেভ করা অ্যাকাউন্ট সিলেক্টেড থাকবে
    all_targets = [t["id"] for t in get_available_targets()]

    return {
        "file_id": file_id,
        "width": width,
        "height": height,
        "aspect": aspect_label,
        "plat_open": False,
        "selected_targets": all_targets,
        "mode": "manual",  # 'ai' অথবা 'manual'
        "title": "",
        "description": "",
        "hashtags": "",
        "keywords": "",
        "thumbnail_id": None,
        "editing_field": None,
    }


def _render_dashboard_text(data: dict) -> str:
    active_ai = storage.get_active_ai() or "Default AI"
    mode_text = f"🤖 AI অটো-জেনারেট ({active_ai})" if data["mode"] == "ai" else "✍️ ম্যানুয়াল ইনপুট"
    
    selected_names = [t.split(":", 1)[1] for t in data["selected_targets"]]
    targets_display = ", ".join(selected_names) if selected_names else "কোনোটিই সিলেক্ট করা হয়নি"

    thumb_status = (
        "✅ কাস্টম থাম্বনেইল যুক্ত হয়েছে"
        if data["thumbnail_id"]
        else ("🤖 AI তৈরি করবে" if data["mode"] == "ai" else "❌ দেওয়া হয়নি")
    )

    desc_preview = (
        (data["description"][:45] + "...")
        if len(data["description"]) > 45
        else (data["description"] or "_সেট করা নেই_")
    )

    return (
        f"🎬 **ভিডিও আপলোড ড্যাশবোর্ড**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 **রেশিও:** {data['aspect']}\n"
        f"⚙️ **মোড:** {mode_text}\n"
        f"📡 **চ্যানেল/পেজ:** {targets_display}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 **Title:** {data['title'] or '_সেট করা নেই_'}\n"
        f"📄 **Description:** {desc_preview}\n"
        f"🏷️ **Hashtags:** {data['hashtags'] or '_সেট করা নেই_'}\n"
        f"🔑 **SEO Keywords:** {data['keywords'] or '_সেট করা নেই_'}\n"
        f"🖼️ **Thumbnail:** {thumb_status}\n"
    )


def _render_dashboard_keyboard(data: dict) -> InlineKeyboardMarkup:
    keyboard = []

    # ১. প্ল্যাটফর্ম ড্রপডাউন ও টিকবক্স
    keyboard.extend(build_upload_platform_keyboard(data["selected_targets"], data["plat_open"]))

    # ২. AI বনাম Manual সুইচার বাটন
    ai_icon = "🟢" if data["mode"] == "ai" else "⚪"
    man_icon = "🟢" if data["mode"] == "manual" else "⚪"
    keyboard.append([
        InlineKeyboardButton(f"{ai_icon} AI সব করবে", callback_data="up_mode:ai"),
        InlineKeyboardButton(f"{man_icon} Manual সেটআপ", callback_data="up_mode:manual"),
    ])

    # ৩. মোড অনুযায়ী ডাইনামিক বাটন
    if data["mode"] == "manual":
        keyboard.extend([
            [
                InlineKeyboardButton("📝 Title", callback_data="up_edit:title"),
                InlineKeyboardButton("📄 Description", callback_data="up_edit:description"),
            ],
            [
                InlineKeyboardButton("🏷️ Hashtags", callback_data="up_edit:hashtags"),
                InlineKeyboardButton("🔑 SEO Keywords", callback_data="up_edit:keywords"),
            ],
            [
                InlineKeyboardButton("🖼️ Thumbnail আপলোড", callback_data="up_edit:thumbnail"),
            ],
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔄 AI দিয়ে নতুন করে জেনারেট করুন", callback_data="up_ai_regen")
        ])

    # ৪. পাবলিশ ও ব্যাক বাটন
    keyboard.append([
        InlineKeyboardButton("🚀 এখনই আপলোড / পাবলিশ করুন", callback_data="up_publish")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ বাতিল", callback_data="up_cancel"),
        InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def _generate_ai_metadata(data: dict) -> None:
    """AI মোড সিলেক্ট করলে অটোমেটিক টাইটেল, ডেসক্রিপশন, হ্যাশট্যাগ ও কিওয়ার্ড তৈরি করবে।"""
    is_short = "9:16" in data["aspect"]
    if is_short:
        data["title"] = "অসাধারণ একটি শর্ট ভিডিও! 🔥 #Shorts"
        data["description"] = "ভিডিওটি ভালো লাগলে লাইক ও সাবস্ক্রাইব করে সাথেই থাকুন।"
        data["hashtags"] = "#Shorts #Trending #Viral #Bangla"
        data["keywords"] = "trending shorts, viral video, bangla shorts"
    else:
        data["title"] = "সম্পূর্ণ নতুন ভিডিও উপস্থাপনা | Full HD"
        data["description"] = "আমাদের চ্যানেলের নতুন এই ভিডিওটি দেখার জন্য ধন্যবাদ। মতামত কমেন্টে জানান।"
        data["hashtags"] = "#Video #FullHD #BanglaContent"
        data["keywords"] = "full video, bangla content, new episode"


async def upload_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main Menu থেকে Upload Video চাপলে এটি চালু হবে।"""
    text = (
        "📤 **ভিডিও আপলোড সেকশন**\n\n"
        "আপনি যে ভিডিওটি আপলোড করতে চান সেটি এখন এখানে পাঠান (9:16 অথবা 16:9 ফরম্যাটে)।"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")]
    ])
    await show(update, text, markup)
    return WAIT_VIDEO


async def handle_uploaded_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    video = msg.video or (
        msg.document if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/") else None
    )

    if not video:
        await msg.reply_text("⚠️ দয়া করে একটি সঠিক ভিডিও ফাইল পাঠান।")
        return WAIT_VIDEO

    width = getattr(video, "width", 1080) or 1080
    height = getattr(video, "height", 1920) or 1920
    data = _init_session(video.file_id, width, height)
    context.user_data["upload_session"] = data

    # ভিডিও প্রিভিউ ডিসপ্লে
    await msg.reply_video(
        video=video.file_id,
        caption=f"🎞️ **ভিডিও প্রিভিউ লোড হয়েছে** ({data['aspect']})",
        parse_mode="Markdown"
    )

    # ড্যাশবোর্ড মেসেজ
    await msg.reply_text(
        _render_dashboard_text(data),
        reply_markup=_render_dashboard_keyboard(data),
        parse_mode="Markdown"
    )
    return UPLOAD_DASHBOARD


async def handle_dashboard_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data
    data = context.user_data.get("upload_session")

    if action == "menu:main" or action == "up_cancel":
        context.user_data.pop("upload_session", None)
        await show(update, MAIN_TEXT, main_menu_markup())
        return ConversationHandler.END

    if action == "menu:accounts":
        context.user_data.pop("upload_session", None)
        from handlers import platforms
        await platforms.accounts_home(update, context)
        return ConversationHandler.END

    if not data:
        await query.edit_message_text("⚠️ সেশন শেষ হয়ে গেছে। আবার Main Menu থেকে শুরু করুন।")
        return ConversationHandler.END

    # প্ল্যাটফর্ম টিকবক্স ও ড্রপডাউন
    if action == "up_plat_dropdown" or action.startswith("up_plat_tog|"):
        await toggle_upload_platform(context, action)

    # AI বা Manual মোড পরিবর্তন
    elif action.startswith("up_mode:"):
        chosen_mode = action.split(":", 1)[1]
        data["mode"] = chosen_mode
        if chosen_mode == "ai":
            await _generate_ai_metadata(data)

    elif action == "up_ai_regen":
        await _generate_ai_metadata(data)

    # ম্যানুয়াল ফিল্ড এডিট
    elif action.startswith("up_edit:"):
        field = action.split(":", 1)[1]
        data["editing_field"] = field
        if field == "thumbnail":
            await query.message.reply_text("🖼️ আপনার থাম্বনেইল ছবিটি (Photo) পাঠান:")
            return WAIT_THUMB_INPUT

        prompts = {
            "title": "📝 ভিডিওর **Title** লিখুন:",
            "description": "📄 ভিডিওর **Description** লিখুন:",
            "hashtags": "🏷️ **Hashtags** লিখুন (যেমন: #funny #cartoon):",
            "keywords": "🔑 **SEO Keywords** লিখুন (কমা দিয়ে আলাদা করুন):",
        }
        await query.message.reply_text(prompts.get(field, "✍️ তথ্য লিখুন:"), parse_mode="Markdown")
        return WAIT_TEXT_INPUT

    # পাবলিশ বাটন
    elif action == "up_publish":
        if not data["selected_targets"]:
            await query.answer("⚠️ অন্তত একটি প্ল্যাটফর্ম/চ্যানেল সিলেক্ট করুন!", show_alert=True)
            return UPLOAD_DASHBOARD

        targets_str = ", ".join(t.split(":", 1)[1] for t in data["selected_targets"])
        await query.edit_message_text(
            f"🚀 **আপলোড প্রক্রিয়া শুরু হয়েছে!**\n\n"
            f"📡 **টার্গেট চ্যানেল:** {targets_str}\n"
            f"📝 **Title:** {data['title'] or 'Untitled'}\n"
            f"⚙️ **মোড:** {data['mode'].upper()}\n\n"
            f"✅ সব প্ল্যাটফর্মে আপলোড কিউতে যুক্ত করা হয়েছে।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")]]),
            parse_mode="Markdown"
        )
        context.user_data.pop("upload_session", None)
        return ConversationHandler.END

    await query.edit_message_text(
        _render_dashboard_text(data),
        reply_markup=_render_dashboard_keyboard(data),
        parse_mode="Markdown"
    )
    return UPLOAD_DASHBOARD


async def receive_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("upload_session")
    if data and data.get("editing_field"):
        field = data["editing_field"]
        data[field] = update.message.text.strip()
        data["editing_field"] = None

    await update.message.reply_text(
        _render_dashboard_text(data),
        reply_markup=_render_dashboard_keyboard(data),
        parse_mode="Markdown"
    )
    return UPLOAD_DASHBOARD


async def receive_thumb_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("upload_session")
    msg = update.message
    if data:
        if msg.photo:
            data["thumbnail_id"] = msg.photo[-1].file_id
        elif msg.document:
            data["thumbnail_id"] = msg.document.file_id
        data["editing_field"] = None

    await msg.reply_text(
        _render_dashboard_text(data),
        reply_markup=_render_dashboard_keyboard(data),
        parse_mode="Markdown"
    )
    return UPLOAD_DASHBOARD

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass
def get_upload_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(upload_home, pattern="^menu:upload$")],
        states={
            WAIT_VIDEO: [
                MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video),
                CallbackQueryHandler(handle_dashboard_action, pattern="^menu:main$"),
            ],
            UPLOAD_DASHBOARD: [
                CallbackQueryHandler(handle_dashboard_action, pattern="^(up_|menu:main$|menu:accounts$)"),
            ],
            WAIT_TEXT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text_input),
            ],
            WAIT_THUMB_INPUT: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_thumb_input),
            ],
        },
        fallbacks=[
            CommandHandler("start", lambda u, c: ConversationHandler.END),
            CallbackQueryHandler(handle_dashboard_action, pattern="^menu:main$"),
        ],
        allow_reentry=True,
    )
