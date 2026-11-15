from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, ConversationHandler,
                          MessageHandler, filters)

import config
import storage
from handlers.common import show
from keyboards import main_menu_markup
from services.ai_providers import ask

WAIT_KEY = 1

T = {
 "bn": {
  "home":"🤖 AI কানেক্টর", "hint":"যে AI Provider ব্যবহার করতে চাও, সেটি নির্বাচন করো। ✅ = API Key সেভ আছে, ⭐ = Active AI (সাধারণ মেসেজের উত্তর দেয়)।",
  "add":"➕ অন্য AI Connector যোগ করো", "main":"🔙 মেইন মেনু", "key":"🔑 API Key যোগ করো",
  "active":"⭐ Active করো", "test":"🧪 পরীক্ষা", "list":"🔙 AI তালিকা", "yes":"হ্যাঁ", "no":"না",
  "key_status":"Key", "active_status":"Active", "model":"মডেল", "no_key":"❌ নেই", "has_key":"✅ আছে",
  "before":"আগে API Key যোগ করো।", "active_ok":"✅ এখন থেকে এই AI Active।", "test_running":"পরীক্ষা চলছে…",
  "test_title":"🧪 পরীক্ষার ফল:", "send_key":"এর API Key পাঠাও। নিরাপত্তার জন্য সেভ হওয়ার পর তোমার মেসেজ মুছে দেওয়া হবে।\nবাতিল করতে /cancel",
  "saved":"✅ Key সেভ হয়েছে। এখন 🧪 Test দিয়ে পরীক্ষা করো।", "cancelled":"অপারেশন বাতিল করা হয়েছে।",
  "need_key":"আগে AI Connectors থেকে একটি API Key যোগ করো।", "thinking":"ভাবছে…", "none":"কোনোটি নেই",
  "key_saved":"API Key সেভ হয়েছে", "test_error":"⚠️ পরীক্ষা ব্যর্থ হয়েছে: "
 },
 "en": {
  "home":"🤖 AI Connectors", "hint":"Choose the AI provider you want to use. ✅ = API key saved, ⭐ = Active AI (answers general messages).",
  "add":"➕ Add Another Connector", "main":"🔙 Main Menu", "key":"🔑 Add API Key", "active":"⭐ Set Active",
  "test":"🧪 Test", "list":"🔙 AI List", "yes":"Yes", "no":"No", "key_status":"Key", "active_status":"Active",
  "model":"Model", "no_key":"❌ Missing", "has_key":"✅ Saved", "before":"Please add an API key first.",
  "active_ok":"✅ This AI provider is now active.", "test_running":"Running test…", "test_title":"🧪 Test result:",
  "send_key":"Send the API key for this provider. For security, your message will be deleted after it is saved.\nSend /cancel to cancel.",
  "saved":"✅ Key saved. Run 🧪 Test to verify it.", "cancelled":"Operation cancelled.",
  "need_key":"Add an API key from AI Connectors first.", "thinking":"is thinking…", "none":"None",
  "key_saved":"API key saved", "test_error":"⚠️ Test failed: "
 },
 "hi": {
  "home":"🤖 AI कनेक्टर", "hint":"उपयोग करने वाला AI प्रदाता चुनें। ✅ = API कुंजी सुरक्षित, ⭐ = सक्रिय AI।",
  "add":"➕ दूसरा Connector जोड़ें", "main":"🔙 मुख्य मेनू", "key":"🔑 API कुंजी जोड़ें", "active":"⭐ सक्रिय करें",
  "test":"🧪 परीक्षण", "list":"🔙 AI सूची", "yes":"हाँ", "no":"नहीं", "key_status":"कुंजी", "active_status":"सक्रिय",
  "model":"मॉडल", "no_key":"❌ नहीं", "has_key":"✅ सुरक्षित", "before":"पहले API कुंजी जोड़ें।",
  "active_ok":"✅ यह AI अब सक्रिय है।", "test_running":"परीक्षण चल रहा है…", "test_title":"🧪 परीक्षण परिणाम:",
  "send_key":"इस प्रदाता की API कुंजी भेजें। सुरक्षित रखने के लिए सहेजने के बाद संदेश हटा दिया जाएगा।\nरद्द करने के लिए /cancel भेजें।",
  "saved":"✅ कुंजी सुरक्षित है। इसे जाँचने के लिए 🧪 Test दबाएँ।", "cancelled":"कार्रवाई रद्द की गई।",
  "need_key":"पहले AI Connectors से API कुंजी जोड़ें।", "thinking":"सोच रहा है…", "none":"कोई नहीं",
  "key_saved":"API कुंजी सुरक्षित", "test_error":"⚠️ परीक्षण विफल: "
 },
 "ur": {
  "home":"🤖 AI کنیکٹرز", "hint":"استعمال کرنے والا AI فراہم کنندہ منتخب کریں۔ ✅ = API Key محفوظ، ⭐ = فعال AI۔",
  "add":"➕ ایک اور Connector شامل کریں", "main":"🔙 مین مینو", "key":"🔑 API Key شامل کریں", "active":"⭐ فعال کریں",
  "test":"🧪 ٹیسٹ", "list":"🔙 AI فہرست", "yes":"ہاں", "no":"نہیں", "key_status":"Key", "active_status":"فعال",
  "model":"ماڈل", "no_key":"❌ موجود نہیں", "has_key":"✅ محفوظ", "before":"پہلے API Key شامل کریں۔",
  "active_ok":"✅ یہ AI اب فعال ہے۔", "test_running":"ٹیسٹ جاری ہے…", "test_title":"🧪 ٹیسٹ کا نتیجہ:",
  "send_key":"اس فراہم کنندہ کی API Key بھیجیں۔ حفاظت کے لیے محفوظ ہونے کے بعد پیغام حذف کر دیا جائے گا۔\nمنسوخ کرنے کے لیے /cancel بھیجیں۔",
  "saved":"✅ Key محفوظ ہو گئی۔ تصدیق کے لیے 🧪 Test چلائیں۔", "cancelled":"عمل منسوخ کر دیا گیا۔",
  "need_key":"پہلے AI Connectors سے API Key شامل کریں۔", "thinking":"سوچ رہا ہے…", "none":"کوئی نہیں",
  "key_saved":"API Key محفوظ", "test_error":"⚠️ ٹیسٹ ناکام: "
 },
 "zh": {
  "home":"🤖 AI 连接器", "hint":"选择要使用的 AI 服务。✅ = API 密钥已保存，⭐ = 当前启用的 AI。",
  "add":"➕ 添加其他连接器", "main":"🔙 主菜单", "key":"🔑 添加 API 密钥", "active":"⭐ 设为当前使用",
  "test":"🧪 测试", "list":"🔙 AI 列表", "yes":"是", "no":"否", "key_status":"密钥", "active_status":"已启用",
  "model":"模型", "no_key":"❌ 未添加", "has_key":"✅ 已保存", "before":"请先添加 API 密钥。",
  "active_ok":"✅ 此 AI 服务现已启用。", "test_running":"正在测试…", "test_title":"🧪 测试结果：",
  "send_key":"请发送此服务的 API 密钥。为确保安全，保存后将删除你的消息。\n发送 /cancel 取消。",
  "saved":"✅ 密钥已保存。请运行 🧪 Test 进行验证。", "cancelled":"操作已取消。",
  "need_key":"请先从 AI Connectors 添加 API 密钥。", "thinking":"正在思考…", "none":"无",
  "key_saved":"API 密钥已保存", "test_error":"⚠️ 测试失败："
 },
 "ar": {
  "home":"🤖 موصلات الذكاء الاصطناعي", "hint":"اختر مزود الذكاء الاصطناعي. ✅ = مفتاح API محفوظ، ⭐ = المزود النشط.",
  "add":"➕ إضافة موصل آخر", "main":"🔙 القائمة الرئيسية", "key":"🔑 إضافة مفتاح API", "active":"⭐ تعيين كنشط",
  "test":"🧪 اختبار", "list":"🔙 قائمة AI", "yes":"نعم", "no":"لا", "key_status":"المفتاح", "active_status":"نشط",
  "model":"النموذج", "no_key":"❌ غير موجود", "has_key":"✅ محفوظ", "before":"أضف مفتاح API أولاً.",
  "active_ok":"✅ أصبح مزود AI هذا نشطاً الآن.", "test_running":"جارٍ الاختبار…", "test_title":"🧪 نتيجة الاختبار:",
  "send_key":"أرسل مفتاح API لهذا المزود. لحمايته، سيتم حذف رسالتك بعد الحفظ.\nأرسل /cancel للإلغاء.",
  "saved":"✅ تم حفظ المفتاح. شغّل 🧪 Test للتحقق منه.", "cancelled":"تم إلغاء العملية.",
  "need_key":"أضف مفتاح API من AI Connectors أولاً.", "thinking":"يفكر…", "none":"لا يوجد",
  "key_saved":"تم حفظ مفتاح API", "test_error":"⚠️ فشل الاختبار: "
 },
 "ne": {
  "home":"🤖 AI कनेक्टरहरू", "hint":"प्रयोग गर्न चाहेको AI प्रदायक छान्नुहोस्। ✅ = API Key सुरक्षित, ⭐ = सक्रिय AI।",
  "add":"➕ अर्को Connector थप्नुहोस्", "main":"🔙 मुख्य मेनु", "key":"🔑 API Key थप्नुहोस्", "active":"⭐ सक्रिय बनाउनुहोस्",
  "test":"🧪 परीक्षण", "list":"🔙 AI सूची", "yes":"हो", "no":"होइन", "key_status":"Key", "active_status":"सक्रिय",
  "model":"मोडेल", "no_key":"❌ छैन", "has_key":"✅ सुरक्षित", "before":"पहिले API Key थप्नुहोस्।",
  "active_ok":"✅ यो AI अब सक्रिय भयो।", "test_running":"परीक्षण हुँदैछ…", "test_title":"🧪 परीक्षण नतिजा:",
  "send_key":"यस प्रदायकको API Key पठाउनुहोस्। सुरक्षाका लागि सुरक्षित भएपछि तपाईंको सन्देश मेटाइनेछ।\nरद्द गर्न /cancel पठाउनुहोस्।",
  "saved":"✅ Key सुरक्षित भयो। जाँच गर्न 🧪 Test चलाउनुहोस्।", "cancelled":"कार्य रद्द गरियो।",
  "need_key":"पहिले AI Connectors बाट API Key थप्नुहोस्।", "thinking":"सोच्दैछ…", "none":"कुनै छैन",
  "key_saved":"API Key सुरक्षित भयो", "test_error":"⚠️ परीक्षण असफल: "
 },
 "as": {
  "home":"🤖 AI কানেক্টৰ", "hint":"ব্যৱহাৰ কৰিব বিচৰা AI প্ৰদানকাৰী বাছনি কৰক। ✅ = API Key সংৰক্ষিত, ⭐ = সক্ৰিয় AI।",
  "add":"➕ আন এটা Connector যোগ কৰক", "main":"🔙 মূল মেনু", "key":"🔑 API Key যোগ কৰক", "active":"⭐ সক্ৰিয় কৰক",
  "test":"🧪 পৰীক্ষা", "list":"🔙 AI তালিকা", "yes":"হয়", "no":"নহয়", "key_status":"Key", "active_status":"সক্ৰিয়",
  "model":"মডেল", "no_key":"❌ নাই", "has_key":"✅ সংৰক্ষিত", "before":"প্ৰথমে API Key যোগ কৰক।",
  "active_ok":"✅ এই AI এতিয়াৰ পৰা সক্ৰিয়।", "test_running":"পৰীক্ষা চলি আছে…", "test_title":"🧪 পৰীক্ষাৰ ফলাফল:",
  "send_key":"এই প্ৰদানকাৰীৰ API Key পঠিয়াওক। সুৰক্ষাৰ বাবে সংৰক্ষণৰ পিছত আপোনাৰ বাৰ্তাটো মচি দিয়া হ’ব।\nবাতিল কৰিবলৈ /cancel পঠিয়াওক।",
  "saved":"✅ Key সংৰক্ষিত হৈছে। পৰীক্ষা কৰিবলৈ 🧪 Test চলাওক।", "cancelled":"কাৰ্য বাতিল কৰা হৈছে।",
  "need_key":"প্ৰথমে AI Connectors-ৰ পৰা API Key যোগ কৰক।", "thinking":"ভাবি আছে…", "none":"একো নাই",
  "key_saved":"API Key সংৰক্ষিত", "test_error":"⚠️ পৰীক্ষা বিফল: "
 }
}


def _t(update, key):
    code = storage.get_user_lang(update.effective_user.id)
    return T.get(code, T["bn"]).get(key, T["en"].get(key, key))


async def ai_home(update, context):
    keys = storage.get_ai_keys()
    active = storage.get_active_ai()
    rows = []
    for p in config.AI_PROVIDERS:
        mark = ("✅" if p in keys else "❌") + (" ⭐" if p == active else "")
        rows.append([InlineKeyboardButton(f"{p} {mark}", callback_data=f"ai:{p}")])
    rows.append([InlineKeyboardButton(_t(update, "add"), callback_data="menu:add_connector")])
    rows.append([InlineKeyboardButton(_t(update, "main"), callback_data="menu:main")])
    await show(update, f"{_t(update, 'home')}\n\n{_t(update, 'hint')}", InlineKeyboardMarkup(rows))


async def _render_provider(update, p, extra=""):
    has = p in storage.get_ai_keys()
    active = storage.get_active_ai() == p
    text = (f"🤖 {p}\n{_t(update, 'key_status')}: {_t(update, 'has_key') if has else _t(update, 'no_key')}\n"
            f"{_t(update, 'active_status')}: {_t(update, 'yes') if active else _t(update, 'no')}\n"
            f"{_t(update, 'model')}: {config.AI_MODELS[p]}")
    if extra:
        text += f"\n\n{extra}"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(_t(update, "key"), callback_data=f"ai_key:{p}")],
        [InlineKeyboardButton(_t(update, "active"), callback_data=f"ai_active:{p}"),
         InlineKeyboardButton(_t(update, "test"), callback_data=f"ai_test:{p}")],
        [InlineKeyboardButton(_t(update, "list"), callback_data="menu:ai")],
    ])
    await show(update, text, markup)


async def provider_view(update, context):
    await _render_provider(update, update.callback_query.data.split(":", 1)[1])


async def set_active(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    if p not in storage.get_ai_keys():
        await update.callback_query.answer(_t(update, "before"), show_alert=True)
        return
    storage.set_active_ai(p)
    await _render_provider(update, p, _t(update, "active_ok"))


async def test_ai(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    key = storage.get_ai_keys().get(p)
    if not key:
        await update.callback_query.answer(_t(update, "before"), show_alert=True)
        return
    await update.callback_query.answer(_t(update, "test_running"))
    reply = await ask(p, key, "Reply with one short friendly sentence.")
    if reply.startswith("⚠️"):
        reply = _t(update, "test_error") + reply
    await _render_provider(update, p, f"{_t(update, 'test_title')}\n{reply[:800]}")


async def key_start(update, context):
    p = update.callback_query.data.split(":", 1)[1]
    context.user_data["ai_provider"] = p
    await show(update, f"{p} — {_t(update, 'send_key')}",
               InlineKeyboardMarkup([[InlineKeyboardButton(_t(update, "cancelled"), callback_data="menu:ai")]]))
    return WAIT_KEY


async def key_save(update, context):
    p = context.user_data.get("ai_provider")
    if not p or p not in config.AI_PROVIDERS:
        await update.message.reply_text(_t(update, "cancelled"))
        return ConversationHandler.END
    storage.set_ai_key(p, update.message.text.strip())
    try:
        await update.message.delete()
    except Exception:
        pass
    if not storage.get_active_ai():
        storage.set_active_ai(p)
    await _render_provider(update, p, _t(update, "saved"))
    return ConversationHandler.END


async def cancel(update, context):
    await show(update, _t(update, "cancelled"), main_menu_markup(storage.get_user_lang(update.effective_user.id)))
    return ConversationHandler.END


async def chat(update, context):
    """Free-text chat routed to the configured active AI provider."""
    keys = storage.get_ai_keys()
    if not keys:
        await update.message.reply_text(
            _t(update, "need_key"),
            reply_markup=main_menu_markup(storage.get_user_lang(update.effective_user.id))
        )
        return
    p = storage.get_active_ai()
    if p not in keys:
        p = next(iter(keys))
    wait = await update.message.reply_text(f"⏳ {p} {_t(update, 'thinking')}")
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
