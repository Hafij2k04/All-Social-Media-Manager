from telegram.error import BadRequest


async def show(update, text, markup=None):
    """বাটন চাপলে মেসেজ এডিট করে, সাধারণ মেসেজ হলে নতুন রিপ্লাই দেয়।"""
    q = update.callback_query
    if q:
        try:
            await q.answer()
        except Exception:
            pass
        try:
            await q.edit_message_text(text, reply_markup=markup)
        except BadRequest as e:
            if "not modified" not in str(e).lower():
                await q.message.reply_text(text, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text, reply_markup=markup)
