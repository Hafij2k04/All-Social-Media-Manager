"""Analysis & Ideas: multi-platform, multi-account selection foundation."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import storage
from handlers.common import show

BACK = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")]
])


def _target_id(platform: str, name: str) -> str:
    return f"{platform}::{name}"


def _selected_targets(context):
    return context.user_data.get("analysis_selected_targets", [])


def _render_home_text(user_id, context):
    selected = _selected_targets(context)
    if not selected:
        selection_text = "এখনো কোনো চ্যানেল/অ্যাকাউন্ট নির্বাচন করা হয়নি।"
    else:
        names = [f"• {item['platform']} — {item['name']}" for item in selected]
        selection_text = "নির্বাচিত অ্যাকাউন্ট:\n" + "\n".join(names)

    return (
        "📊 Analysis & Ideas\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{selection_text}\n\n"
        "প্রথমে যে চ্যানেল বা অ্যাকাউন্টের জন্য কাজ করতে চাও, সেটি নির্বাচন করো। "
        "একাধিক প্ল্যাটফর্মের একাধিক অ্যাকাউন্টও নির্বাচন করা যাবে।"
    )


async def analyze_home(update, context):
    if "analysis_selected_targets" not in context.user_data:
        context.user_data["analysis_selected_targets"] = storage.get_analysis_selection(update.effective_user.id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Select Platforms & Channels", callback_data="an:select")],
        [InlineKeyboardButton("📊 Channel Analysis", callback_data="an:feature:channel")],
        [InlineKeyboardButton("🔥 Niche Research", callback_data="an:feature:niche")],
        [InlineKeyboardButton("💡 Video Ideas", callback_data="an:feature:ideas")],
        [InlineKeyboardButton("🔎 Competitor Analysis", callback_data="an:feature:competitor")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu:main")],
    ])
    await show(update, _render_home_text(update.effective_user.id, context), keyboard)


async def _show_platform_picker(update, context):
    accounts = storage.get_accounts()
    platforms = [p for p, items in accounts.items() if isinstance(items, dict) and items]
    context.user_data["analysis_platform_options"] = platforms
    selected = set(context.user_data.get("analysis_draft_platforms", []))

    rows = []
    for index, platform in enumerate(platforms):
        mark = "✅" if platform in selected else "⬜"
        rows.append([InlineKeyboardButton(
            f"{mark} {platform} ({len(accounts.get(platform, {}))})",
            callback_data=f"an:plat:{index}"
        )])

    if not platforms:
        body = (
            "এখনো কোনো প্ল্যাটফর্মে অ্যাকাউন্ট যুক্ত করা নেই।\n"
            "আগে Main Menu → Accounts থেকে YouTube/Facebook/TikTok ইত্যাদি অ্যাকাউন্ট যুক্ত করো।"
        )
        rows.append([InlineKeyboardButton("📺 Accounts", callback_data="menu:accounts")])
    else:
        body = (
            "🎯 প্রথমে এক বা একাধিক প্ল্যাটফর্ম নির্বাচন করো।\n"
            "যেমন: YouTube + Facebook। এরপর ওই প্ল্যাটফর্মগুলোর নির্দিষ্ট চ্যানেল বেছে নিতে পারবে।"
        )
        rows.append([InlineKeyboardButton("➡️ Next: Select Accounts", callback_data="an:platforms:next")])

    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="an:cancel")])
    await show(update, body, InlineKeyboardMarkup(rows))


async def _show_account_picker(update, context):
    platforms = context.user_data.get("analysis_draft_platforms", [])
    accounts = storage.get_accounts()
    targets = []
    for platform in platforms:
        for name in accounts.get(platform, {}):
            targets.append({"platform": platform, "name": name, "id": _target_id(platform, name)})

    context.user_data["analysis_target_options"] = targets
    selected_ids = set(context.user_data.get("analysis_draft_target_ids", []))
    rows = []
    for index, item in enumerate(targets):
        mark = "✅" if item["id"] in selected_ids else "⬜"
        rows.append([InlineKeyboardButton(
            f"{mark} {item['platform']} — {item['name']}",
            callback_data=f"an:acct:{index}"
        )])

    if not targets:
        body = (
            "নির্বাচিত প্ল্যাটফর্মগুলোতে কোনো অ্যাকাউন্ট পাওয়া যায়নি। "
            "আগে Accounts থেকে অ্যাকাউন্ট যোগ করো।"
        )
    else:
        body = (
            "📺 এখন নির্দিষ্ট চ্যানেল/অ্যাকাউন্ট নির্বাচন করো।\n"
            "একাধিক অ্যাকাউন্টে টিক দিতে পারবে। শুধু নির্বাচিত অ্যাকাউন্টগুলোর তথ্য দিয়েই "
            "পরবর্তী Analysis/Ideas কাজ হবে।"
        )
        rows.append([InlineKeyboardButton("☑️ Select All", callback_data="an:acct:all")])
        rows.append([InlineKeyboardButton("🧹 Clear Selection", callback_data="an:acct:clear")])
        rows.append([InlineKeyboardButton("✅ Confirm Selection", callback_data="an:confirm")])

    rows.append([InlineKeyboardButton("🔙 Back to Platforms", callback_data="an:select")])
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="an:cancel")])
    await show(update, body, InlineKeyboardMarkup(rows))


async def analysis_callback(update, context):
    query = update.callback_query
    data = query.data

    if data == "an:select":
        context.user_data["analysis_draft_platforms"] = []
        context.user_data["analysis_draft_target_ids"] = []
        await _show_platform_picker(update, context)
        return

    if data.startswith("an:plat:"):
        try:
            index = int(data.rsplit(":", 1)[1])
            platform = context.user_data["analysis_platform_options"][index]
        except (ValueError, IndexError, KeyError):
            await query.answer("Selection expired. Please open the selector again.", show_alert=True)
            return
        selected = context.user_data.setdefault("analysis_draft_platforms", [])
        if platform in selected:
            selected.remove(platform)
        else:
            selected.append(platform)
        await _show_platform_picker(update, context)
        return

    if data == "an:platforms:next":
        if not context.user_data.get("analysis_draft_platforms"):
            await query.answer("আগে অন্তত একটি প্ল্যাটফর্ম নির্বাচন করো।", show_alert=True)
            return
        context.user_data["analysis_draft_target_ids"] = []
        await _show_account_picker(update, context)
        return

    if data.startswith("an:acct:"):
        choice = data.rsplit(":", 1)[1]
        options = context.user_data.get("analysis_target_options", [])
        selected = context.user_data.setdefault("analysis_draft_target_ids", [])
        if choice == "all":
            selected[:] = [item["id"] for item in options]
        elif choice == "clear":
            selected.clear()
        else:
            try:
                item = options[int(choice)]
            except (ValueError, IndexError):
                await query.answer("Selection expired. Please open the selector again.", show_alert=True)
                return
            target_id = item["id"]
            if target_id in selected:
                selected.remove(target_id)
            else:
                selected.append(target_id)
        await _show_account_picker(update, context)
        return

    if data == "an:confirm":
        options = context.user_data.get("analysis_target_options", [])
        selected_ids = set(context.user_data.get("analysis_draft_target_ids", []))
        chosen = [
            {"platform": item["platform"], "name": item["name"]}
            for item in options if item["id"] in selected_ids
        ]
        if not chosen:
            await query.answer("কমপক্ষে একটি চ্যানেল/অ্যাকাউন্ট নির্বাচন করো।", show_alert=True)
            return
        storage.set_analysis_selection(update.effective_user.id, chosen)
        context.user_data["analysis_selected_targets"] = chosen
        context.user_data.pop("analysis_draft_platforms", None)
        context.user_data.pop("analysis_draft_target_ids", None)
        await analyze_home(update, context)
        return

    if data == "an:cancel":
        context.user_data.pop("analysis_draft_platforms", None)
        context.user_data.pop("analysis_draft_target_ids", None)
        await analyze_home(update, context)
        return

    if data.startswith("an:feature:"):
        feature = data.rsplit(":", 1)[1]
        selected = _selected_targets(context)
        if not selected:
            await query.answer("আগে Platforms & Channels থেকে চ্যানেল নির্বাচন করো।", show_alert=True)
            await _show_platform_picker(update, context)
            return
        names = "\n".join(f"• {item['platform']} — {item['name']}" for item in selected)
        feature_names = {
            "channel": "Channel Analysis",
            "niche": "Niche Research",
            "ideas": "Video Ideas",
            "competitor": "Competitor Analysis",
        }
        await show(
            update,
            f"📊 {feature_names.get(feature, 'Analysis')}\n\n"
            f"নির্বাচিত অ্যাকাউন্ট:\n{names}\n\n"
            "✅ Account selection foundation প্রস্তুত। পরবর্তী ধাপে এই নির্বাচিত অ্যাকাউন্টের "
            "প্রোফাইল ও ডেটা Active AI-তে পাঠিয়ে ফিচারটি চালু করা হবে।",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Change Selection", callback_data="an:select")],
                [InlineKeyboardButton("🔙 Analysis & Ideas", callback_data="menu:analyze")],
            ])
        )
        return
