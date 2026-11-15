"""Localized multi-account Analysis & Ideas workflow."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import storage
from handlers.common import show
from services.ai_providers import ask

TEXT = {
    "bn": {
        "home": "📊 অ্যানালাইসিস ও আইডিয়া", "none": "এখনো কোনো চ্যানেল/অ্যাকাউন্ট নির্বাচন করা হয়নি।",
        "selected": "নির্বাচিত অ্যাকাউন্ট:", "intro": "প্রথমে যে চ্যানেল বা অ্যাকাউন্টের জন্য কাজ করতে চাও, সেটি নির্বাচন করো। একাধিক প্ল্যাটফর্ম ও অ্যাকাউন্ট বেছে নেওয়া যাবে।",
        "pick": "🎯 প্ল্যাটফর্ম ও চ্যানেল নির্বাচন", "channel": "📊 চ্যানেল অ্যানালাইসিস", "niche": "🔥 নিশ রিসার্চ",
        "ideas": "💡 ভিডিও আইডিয়া", "competitor": "🔎 কম্পিটিটর অ্যানালাইসিস", "all": "🚀 All Analysis — সম্পূর্ণ রিসার্চ",
        "main": "🔙 মেইন মেনু", "no_platform": "এখনো কোনো প্ল্যাটফর্মে অ্যাকাউন্ট যোগ করা হয়নি। আগে Accounts থেকে অ্যাকাউন্ট যোগ করো।",
        "choose_platform": "🎯 এক বা একাধিক প্ল্যাটফর্ম নির্বাচন করো।", "next": "➡️ পরবর্তী: অ্যাকাউন্ট নির্বাচন",
        "cancel": "❌ বাতিল", "choose_account": "📺 নির্দিষ্ট চ্যানেল/অ্যাকাউন্ট নির্বাচন করো। একাধিকটি বেছে নিতে পারবে।",
        "all_accounts": "☑️ সব নির্বাচন", "clear": "🧹 নির্বাচন মুছুন", "confirm": "✅ নির্বাচন নিশ্চিত করো",
        "back_platform": "🔙 প্ল্যাটফর্মে ফিরে যাও", "empty": "নির্বাচিত প্ল্যাটফর্মে কোনো অ্যাকাউন্ট পাওয়া যায়নি।",
        "need_platform": "আগে অন্তত একটি প্ল্যাটফর্ম নির্বাচন করো।", "need_account": "কমপক্ষে একটি চ্যানেল/অ্যাকাউন্ট নির্বাচন করো।",
        "expired": "নির্বাচনটি মেয়াদোত্তীর্ণ। আবার সিলেক্টর খোলো।", "need_selection": "আগে Platforms & Channels থেকে চ্যানেল নির্বাচন করো।",
        "change": "🎯 নির্বাচন পরিবর্তন", "back": "🔙 Analysis & Ideas", "no_ai": "আগে AI Connectors থেকে একটি API key যোগ করে সেটিকে Active করো।",
        "working": "⏳ নির্বাচিত অ্যাকাউন্টগুলোর সম্পূর্ণ রিসার্চ চলছে। একটু অপেক্ষা করো…",
        "report": "📊 সম্পূর্ণ অ্যানালাইসিস রিপোর্ট", "error": "AI থেকে রিপোর্ট তৈরি করা যায়নি: ",
        "scope": "বিশ্লেষণের অ্যাকাউন্ট", "all_desc": "একসঙ্গে Channel Analysis, Niche Research, Video Ideas এবং Competitor Analysis করা হবে।",
        "feature_wait": "এই আলাদা বিশ্লেষণটি পরবর্তী ধাপে চালু হবে। আপাতত All Analysis ব্যবহার করলে চারটি বিভাগ একসঙ্গে পাওয়া যাবে।"
    },
    "en": {
        "home": "📊 Analysis & Ideas", "none": "No channel/account selected yet.",
        "selected": "Selected accounts:", "intro": "First select the channels or accounts you want to work with. You can choose multiple platforms and accounts.",
        "pick": "🎯 Select Platforms & Channels", "channel": "📊 Channel Analysis", "niche": "🔥 Niche Research",
        "ideas": "💡 Video Ideas", "competitor": "🔎 Competitor Analysis", "all": "🚀 All Analysis — Complete Research",
        "main": "🔙 Main Menu", "no_platform": "No platform accounts have been added yet. Add accounts from Accounts first.",
        "choose_platform": "🎯 Select one or more platforms.", "next": "➡️ Next: Select Accounts",
        "cancel": "❌ Cancel", "choose_account": "📺 Select the channels/accounts to analyze. You can select multiple.",
        "all_accounts": "☑️ Select All", "clear": "🧹 Clear Selection", "confirm": "✅ Confirm Selection",
        "back_platform": "🔙 Back to Platforms", "empty": "No accounts found under the selected platforms.",
        "need_platform": "Select at least one platform first.", "need_account": "Select at least one channel/account.",
        "expired": "This selection expired. Please open the selector again.", "need_selection": "Select channels from Platforms & Channels first.",
        "change": "🎯 Change Selection", "back": "🔙 Analysis & Ideas", "no_ai": "Add an API key in AI Connectors and set that provider as Active first.",
        "working": "⏳ Running complete research for your selected accounts. Please wait…",
        "report": "📊 Complete Analysis Report", "error": "Could not generate the AI report: ",
        "scope": "Accounts in scope", "all_desc": "Runs Channel Analysis, Niche Research, Video Ideas, and Competitor Analysis together.",
        "feature_wait": "This individual analysis will be enabled in a later step. For now, use All Analysis to get all four sections together."
    },
    "hi": {
        "home": "📊 विश्लेषण और सुझाव", "none": "अभी कोई चैनल/अकाउंट नहीं चुना गया।", "selected": "चुने गए अकाउंट:",
        "intro": "पहले वे चैनल या अकाउंट चुनें जिन पर काम करना है। कई प्लेटफ़ॉर्म और अकाउंट चुन सकते हैं।",
        "pick": "🎯 प्लेटफ़ॉर्म और चैनल चुनें", "channel": "📊 चैनल विश्लेषण", "niche": "🔥 निच रिसर्च", "ideas": "💡 वीडियो आइडिया",
        "competitor": "🔎 प्रतिस्पर्धी विश्लेषण", "all": "🚀 सभी विश्लेषण — पूरी रिसर्च", "main": "🔙 मुख्य मेनू",
        "no_platform": "अभी कोई अकाउंट नहीं जोड़ा गया। पहले Accounts से अकाउंट जोड़ें।", "choose_platform": "एक या अधिक प्लेटफ़ॉर्म चुनें।",
        "next": "➡️ आगे: अकाउंट चुनें", "cancel": "❌ रद्द करें", "choose_account": "विश्लेषण के लिए चैनल/अकाउंट चुनें। कई चुन सकते हैं।",
        "all_accounts": "☑️ सभी चुनें", "clear": "🧹 चयन हटाएँ", "confirm": "✅ चयन की पुष्टि करें", "back_platform": "🔙 प्लेटफ़ॉर्म पर वापस",
        "empty": "चुने गए प्लेटफ़ॉर्म में कोई अकाउंट नहीं मिला।", "need_platform": "पहले कम से कम एक प्लेटफ़ॉर्म चुनें।",
        "need_account": "कम से कम एक चैनल/अकाउंट चुनें।", "expired": "चयन समाप्त हो गया। फिर से खोलें।",
        "need_selection": "पहले Platforms & Channels से चैनल चुनें।", "change": "🎯 चयन बदलें", "back": "🔙 विश्लेषण मेनू",
        "no_ai": "पहले AI Connectors में API key जोड़कर उसे Active करें।", "working": "⏳ पूरी रिसर्च चल रही है। कृपया प्रतीक्षा करें…",
        "report": "📊 पूरी विश्लेषण रिपोर्ट", "error": "AI रिपोर्ट नहीं बना सका: ", "scope": "चुने गए अकाउंट",
        "all_desc": "चैनल विश्लेषण, निच रिसर्च, वीडियो आइडिया और प्रतिस्पर्धी विश्लेषण एक साथ होंगे।",
        "feature_wait": "अलग-अलग विश्लेषण बाद में सक्रिय होंगे। अभी चारों के लिए All Analysis चुनें।"
    },
    "ur": {
        "home": "📊 تجزیہ اور آئیڈیاز", "none": "ابھی کوئی چینل/اکاؤنٹ منتخب نہیں کیا گیا۔", "selected": "منتخب اکاؤنٹس:",
        "intro": "پہلے مطلوبہ چینلز یا اکاؤنٹس منتخب کریں۔ متعدد پلیٹ فارمز اور اکاؤنٹس منتخب کیے جا سکتے ہیں۔",
        "pick": "🎯 پلیٹ فارم اور چینلز منتخب کریں", "channel": "📊 چینل تجزیہ", "niche": "🔥 نِش ریسرچ", "ideas": "💡 ویڈیو آئیڈیاز",
        "competitor": "🔎 حریفوں کا تجزیہ", "all": "🚀 تمام تجزیے — مکمل تحقیق", "main": "🔙 مین مینو",
        "no_platform": "ابھی کوئی اکاؤنٹ شامل نہیں۔ پہلے Accounts سے اکاؤنٹ شامل کریں۔", "choose_platform": "ایک یا زیادہ پلیٹ فارم منتخب کریں۔",
        "next": "➡️ اگلا: اکاؤنٹس منتخب کریں", "cancel": "❌ منسوخ", "choose_account": "تجزیے کے لیے چینلز/اکاؤنٹس منتخب کریں۔",
        "all_accounts": "☑️ سب منتخب کریں", "clear": "🧹 انتخاب صاف کریں", "confirm": "✅ انتخاب کی تصدیق",
        "back_platform": "🔙 پلیٹ فارمز پر واپس", "empty": "منتخب پلیٹ فارمز میں کوئی اکاؤنٹ نہیں ملا۔",
        "need_platform": "پہلے کم از کم ایک پلیٹ فارم منتخب کریں۔", "need_account": "کم از کم ایک چینل/اکاؤنٹ منتخب کریں۔",
        "expired": "انتخاب ختم ہو گیا، دوبارہ کھولیں۔", "need_selection": "پہلے Platforms & Channels سے چینل منتخب کریں۔",
        "change": "🎯 انتخاب تبدیل کریں", "back": "🔙 تجزیہ مینو", "no_ai": "AI Connectors میں API key شامل کرکے اسے Active کریں۔",
        "working": "⏳ مکمل تحقیق جاری ہے، انتظار کریں…", "report": "📊 مکمل تجزیاتی رپورٹ", "error": "AI رپورٹ نہیں بنا سکا: ",
        "scope": "منتخب اکاؤنٹس", "all_desc": "چینل تجزیہ، نِش ریسرچ، ویڈیو آئیڈیاز اور حریفوں کا تجزیہ اکٹھا ہوگا۔",
        "feature_wait": "الگ تجزیے بعد میں فعال ہوں گے۔ فی الحال چاروں کے لیے All Analysis استعمال کریں۔"
    },
    "zh": {
        "home": "📊 分析与创意", "none": "尚未选择频道/账号。", "selected": "已选账号：",
        "intro": "请先选择要分析的频道或账号。可以选择多个平台和账号。", "pick": "🎯 选择平台和频道",
        "channel": "📊 频道分析", "niche": "🔥 领域研究", "ideas": "💡 视频创意", "competitor": "🔎 竞争对手分析",
        "all": "🚀 全部分析 — 完整研究", "main": "🔙 主菜单", "no_platform": "尚未添加平台账号，请先在 Accounts 中添加。",
        "choose_platform": "请选择一个或多个平台。", "next": "➡️ 下一步：选择账号", "cancel": "❌ 取消",
        "choose_account": "请选择要分析的频道/账号，可以多选。", "all_accounts": "☑️ 全选", "clear": "🧹 清除选择",
        "confirm": "✅ 确认选择", "back_platform": "🔙 返回平台", "empty": "所选平台下没有账号。",
        "need_platform": "请先至少选择一个平台。", "need_account": "请至少选择一个频道/账号。",
        "expired": "选择已过期，请重新打开。", "need_selection": "请先从 Platforms & Channels 选择频道。",
        "change": "🎯 更改选择", "back": "🔙 分析菜单", "no_ai": "请先在 AI Connectors 添加 API 密钥并设为 Active。",
        "working": "⏳ 正在为所选账号执行完整研究，请稍候…", "report": "📊 完整分析报告", "error": "无法生成 AI 报告：",
        "scope": "分析账号", "all_desc": "同时执行频道分析、领域研究、视频创意和竞争对手分析。",
        "feature_wait": "单项分析将在后续启用。现在可使用 All Analysis 一次获取四个部分。"
    },
    "ar": {
        "home": "📊 التحليل والأفكار", "none": "لم يتم اختيار أي قناة/حساب بعد.", "selected": "الحسابات المحددة:",
        "intro": "اختر أولاً القنوات أو الحسابات المطلوبة. يمكنك اختيار عدة منصات وحسابات.", "pick": "🎯 اختر المنصات والقنوات",
        "channel": "📊 تحليل القناة", "niche": "🔥 بحث المجال", "ideas": "💡 أفكار الفيديو", "competitor": "🔎 تحليل المنافسين",
        "all": "🚀 كل التحليلات — بحث شامل", "main": "🔙 القائمة الرئيسية", "no_platform": "لم تتم إضافة حسابات بعد. أضف حساباً من Accounts أولاً.",
        "choose_platform": "اختر منصة واحدة أو أكثر.", "next": "➡️ التالي: اختيار الحسابات", "cancel": "❌ إلغاء",
        "choose_account": "اختر القنوات/الحسابات للتحليل. يمكنك اختيار عدة حسابات.", "all_accounts": "☑️ تحديد الكل",
        "clear": "🧹 مسح التحديد", "confirm": "✅ تأكيد الاختيار", "back_platform": "🔙 العودة إلى المنصات",
        "empty": "لا توجد حسابات ضمن المنصات المحددة.", "need_platform": "اختر منصة واحدة على الأقل أولاً.",
        "need_account": "اختر قناة/حساباً واحداً على الأقل.", "expired": "انتهت صلاحية الاختيار. افتح المحدد مرة أخرى.",
        "need_selection": "اختر القنوات من Platforms & Channels أولاً.", "change": "🎯 تغيير الاختيار", "back": "🔙 قائمة التحليل",
        "no_ai": "أضف مفتاح API من AI Connectors واجعله Active أولاً.", "working": "⏳ جارٍ تنفيذ البحث الشامل للحسابات المحددة…",
        "report": "📊 تقرير التحليل الشامل", "error": "تعذر إنشاء تقرير AI: ", "scope": "الحسابات المحددة",
        "all_desc": "تنفيذ تحليل القناة وبحث المجال وأفكار الفيديو وتحليل المنافسين معاً.",
        "feature_wait": "سيتم تفعيل التحليلات الفردية لاحقاً. استخدم All Analysis حالياً للأقسام الأربعة."
    },
    "ne": {
        "home": "📊 विश्लेषण र विचार", "none": "अहिलेसम्म कुनै च्यानल/खाता चयन गरिएको छैन।", "selected": "चयन गरिएका खाताहरू:",
        "intro": "पहिले काम गर्न चाहेको च्यानल वा खाता छान्नुहोस्। धेरै प्लेटफर्म र खाता छान्न सकिन्छ।",
        "pick": "🎯 प्लेटफर्म र च्यानल छान्नुहोस्", "channel": "📊 च्यानल विश्लेषण", "niche": "🔥 निच अनुसन्धान",
        "ideas": "💡 भिडियो विचार", "competitor": "🔎 प्रतिस्पर्धी विश्लेषण", "all": "🚀 सबै विश्लेषण — पूर्ण अनुसन्धान",
        "main": "🔙 मुख्य मेनु", "no_platform": "अहिलेसम्म खाता थपिएको छैन। पहिले Accounts बाट थप्नुहोस्।",
        "choose_platform": "एक वा बढी प्लेटफर्म छान्नुहोस्।", "next": "➡️ अर्को: खाता छान्नुहोस्", "cancel": "❌ रद्द गर्नुहोस्",
        "choose_account": "विश्लेषणका लागि च्यानल/खाता छान्नुहोस्। धेरै छान्न सकिन्छ।", "all_accounts": "☑️ सबै छान्नुहोस्",
        "clear": "🧹 चयन हटाउनुहोस्", "confirm": "✅ चयन पुष्टि गर्नुहोस्", "back_platform": "🔙 प्लेटफर्ममा फर्कनुहोस्",
        "empty": "छानिएका प्लेटफर्ममा कुनै खाता भेटिएन।", "need_platform": "पहिले कम्तीमा एउटा प्लेटफर्म छान्नुहोस्।",
        "need_account": "कम्तीमा एउटा च्यानल/खाता छान्नुहोस्।", "expired": "चयनको समय सकियो। फेरि खोल्नुहोस्।",
        "need_selection": "पहिले Platforms & Channels बाट च्यानल छान्नुहोस्।", "change": "🎯 चयन बदल्नुहोस्", "back": "🔙 विश्लेषण मेनु",
        "no_ai": "पहिले AI Connectors मा API key थपेर Active बनाउनुहोस्।", "working": "⏳ पूर्ण अनुसन्धान हुँदैछ, कृपया पर्खनुहोस्…",
        "report": "📊 पूर्ण विश्लेषण रिपोर्ट", "error": "AI रिपोर्ट बनाउन सकेन: ", "scope": "छानिएका खाताहरू",
        "all_desc": "च्यानल विश्लेषण, निच अनुसन्धान, भिडियो विचार र प्रतिस्पर्धी विश्लेषण एकैसाथ हुन्छ।",
        "feature_wait": "अलग विश्लेषण पछि सक्रिय हुनेछन्। अहिले चारैका लागि All Analysis प्रयोग गर्नुहोस्।"
    },
    "as": {
        "home": "📊 বিশ্লেষণ আৰু আইডিয়া", "none": "এতিয়ালৈ কোনো চেনেল/একাউণ্ট বাছনি কৰা হোৱা নাই।", "selected": "বাছনি কৰা একাউণ্ট:",
        "intro": "প্ৰথমে কাম কৰিব বিচৰা চেনেল বা একাউণ্ট বাছনি কৰক। একাধিক প্লেটফৰ্ম আৰু একাউণ্ট বাছনি কৰিব পাৰিব।",
        "pick": "🎯 প্লেটফৰ্ম আৰু চেনেল বাছনি", "channel": "📊 চেনেল বিশ্লেষণ", "niche": "🔥 নিশ গৱেষণা",
        "ideas": "💡 ভিডিঅ’ আইডিয়া", "competitor": "🔎 প্ৰতিযোগী বিশ্লেষণ", "all": "🚀 সকলো বিশ্লেষণ — সম্পূৰ্ণ গৱেষণা",
        "main": "🔙 মূল মেনু", "no_platform": "এতিয়াও কোনো একাউণ্ট যোগ কৰা হোৱা নাই। প্ৰথমে Accounts-ৰ পৰা যোগ কৰক।",
        "choose_platform": "এটা বা ততোধিক প্লেটফৰ্ম বাছনি কৰক।", "next": "➡️ পৰৱৰ্তী: একাউণ্ট বাছনি", "cancel": "❌ বাতিল",
        "choose_account": "বিশ্লেষণৰ বাবে চেনেল/একাউণ্ট বাছনি কৰক। একাধিক বাছনি কৰিব পাৰিব।",
        "all_accounts": "☑️ সকলো বাছনি", "clear": "🧹 বাছনি আঁতৰাওক", "confirm": "✅ বাছনি নিশ্চিত কৰক",
        "back_platform": "🔙 প্লেটফৰ্মলৈ উভতি যাওক", "empty": "বাছনি কৰা প্লেটফৰ্মত কোনো একাউণ্ট পোৱা নগ’ল।",
        "need_platform": "প্ৰথমে অন্ততঃ এটা প্লেটফৰ্ম বাছনি কৰক।", "need_account": "অন্ততঃ এটা চেনেল/একাউণ্ট বাছনি কৰক।",
        "expired": "বাছনিৰ সময় শেষ হৈছে। পুনৰ খোলক।", "need_selection": "প্ৰথমে Platforms & Channels-ৰ পৰা চেনেল বাছনি কৰক।",
        "change": "🎯 বাছনি সলনি কৰক", "back": "🔙 বিশ্লেষণ মেনু", "no_ai": "প্ৰথমে AI Connectors-ত API key যোগ কৰি Active কৰক।",
        "working": "⏳ সম্পূৰ্ণ গৱেষণা চলি আছে, অনুগ্ৰহ কৰি অপেক্ষা কৰক…", "report": "📊 সম্পূৰ্ণ বিশ্লেষণ প্ৰতিবেদন",
        "error": "AI প্ৰতিবেদন তৈয়াৰ কৰিব নোৱাৰিলে: ", "scope": "বাছনি কৰা একাউণ্ট",
        "all_desc": "চেনেল বিশ্লেষণ, নিশ গৱেষণা, ভিডিঅ’ আইডিয়া আৰু প্ৰতিযোগী বিশ্লেষণ একেলগে কৰা হ’ব।",
        "feature_wait": "পৃথক বিশ্লেষণ পিছত সক্ৰিয় হ’ব। এতিয়া চাৰিওটাৰ বাবে All Analysis ব্যৱহাৰ কৰক।"
    },
}


def _t(context, key):
    lang = storage.get_user_lang(context._user_id) if getattr(context, "_user_id", None) else "bn"
    return TEXT.get(lang, TEXT["bn"]).get(key, TEXT["en"].get(key, key))


def _lang(update):
    return storage.get_user_lang(update.effective_user.id)


def _target_id(platform: str, name: str) -> str:
    return f"{platform}::{name}"


def _selected_targets(context):
    return context.user_data.get("analysis_selected_targets", [])


def _home_text(update, context):
    t = TEXT.get(_lang(update), TEXT["bn"])
    selected = _selected_targets(context)
    selection = t["none"] if not selected else t["selected"] + "\n" + "\n".join(
        f"• {item['platform']} — {item['name']}" for item in selected
    )
    return f"{t['home']}\n━━━━━━━━━━━━━━━━━━━━\n{selection}\n\n{t['intro']}"


async def analyze_home(update, context):
    if "analysis_selected_targets" not in context.user_data:
        context.user_data["analysis_selected_targets"] = storage.get_analysis_selection(update.effective_user.id)
    t = TEXT.get(_lang(update), TEXT["bn"])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t["pick"], callback_data="an:select")],
        [InlineKeyboardButton(t["channel"], callback_data="an:feature:channel")],
        [InlineKeyboardButton(t["niche"], callback_data="an:feature:niche")],
        [InlineKeyboardButton(t["ideas"], callback_data="an:feature:ideas")],
        [InlineKeyboardButton(t["competitor"], callback_data="an:feature:competitor")],
        [InlineKeyboardButton(t["all"], callback_data="an:feature:all")],
        [InlineKeyboardButton(t["main"], callback_data="menu:main")],
    ])
    await show(update, _home_text(update, context), keyboard)


async def _show_platform_picker(update, context):
    t = TEXT.get(_lang(update), TEXT["bn"])
    accounts = storage.get_accounts()
    platforms = [p for p, items in accounts.items() if isinstance(items, dict) and items]
    context.user_data["analysis_platform_options"] = platforms
    selected = set(context.user_data.get("analysis_draft_platforms", []))
    rows = []
    for index, platform in enumerate(platforms):
        mark = "✅" if platform in selected else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {platform} ({len(accounts.get(platform, {}))})", callback_data=f"an:plat:{index}")])
    if not platforms:
        body = t["no_platform"]
        rows.append([InlineKeyboardButton("📺 Accounts", callback_data="menu:accounts")])
    else:
        body = t["choose_platform"]
        rows.append([InlineKeyboardButton(t["next"], callback_data="an:platforms:next")])
    rows.append([InlineKeyboardButton(t["cancel"], callback_data="an:cancel")])
    await show(update, body, InlineKeyboardMarkup(rows))


async def _show_account_picker(update, context):
    t = TEXT.get(_lang(update), TEXT["bn"])
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
        rows.append([InlineKeyboardButton(f"{mark} {item['platform']} — {item['name']}", callback_data=f"an:acct:{index}")])
    if not targets:
        body = t["empty"]
    else:
        body = t["choose_account"]
        rows.extend([
            [InlineKeyboardButton(t["all_accounts"], callback_data="an:acct:all")],
            [InlineKeyboardButton(t["clear"], callback_data="an:acct:clear")],
            [InlineKeyboardButton(t["confirm"], callback_data="an:confirm")],
        ])
    rows.extend([
        [InlineKeyboardButton(t["back_platform"], callback_data="an:back_platform")],
        [InlineKeyboardButton(t["cancel"], callback_data="an:cancel")],
    ])
    await show(update, body, InlineKeyboardMarkup(rows))


async def _run_all_analysis(update, context, selected):
    t = TEXT.get(_lang(update), TEXT["bn"])
    keys = storage.get_ai_keys()
    provider = storage.get_active_ai()
    if provider not in keys:
        provider = next(iter(keys), None)
    if not provider:
        await show(update, t["no_ai"], InlineKeyboardMarkup([[InlineKeyboardButton(t["back"], callback_data="menu:analyze")]]))
        return

    accounts = storage.get_accounts()
    details = []
    for item in selected:
        info = accounts.get(item["platform"], {}).get(item["name"], {})
        if not isinstance(info, dict):
            info = {"link": str(info)}
        stats = info.get("stats") or {}
        details.append({
            "platform": item["platform"], "account": item["name"],
            "link": info.get("link", ""), "channel_id": info.get("channel_id", ""),
            "saved_stats": stats, "profile": info.get("profile", {}),
        })

    language_names = {"bn": "Bengali", "en": "English", "hi": "Hindi", "ur": "Urdu", "zh": "Simplified Chinese", "ar": "Arabic", "ne": "Nepali", "as": "Assamese"}
    prompt = (
        f"Respond entirely in {language_names.get(_lang(update), 'Bengali')}. "
        "Prepare one comprehensive social-media research report for the selected accounts below. "
        "Use four clearly separated sections: (1) Channel Analysis: assess only the supplied metrics/profile, "
        "state missing data and actionable improvements; (2) Niche Research: discuss audience/content opportunities "
        "and clearly label general hypotheses versus verified facts; (3) Video Ideas: give 5 tailored ideas per account "
        "with hooks and suggested formats; (4) Competitor Analysis: explain competitor benchmarks and what data is missing, "
        "never invent competitor names, live trends, rankings, or statistics. Finish with a prioritized action plan. "
        "Be explicit that saved metrics may be stale and that no live competitor/trend lookup was performed. "
        "Keep accounts separate and do not mix their audiences or niches.\n\n"
        f"Selected account data:\n{details}"
    )
    wait_message = await update.effective_message.reply_text(t["working"]) if update.callback_query else await update.effective_message.reply_text(t["working"])
    result = await ask(provider, keys[provider], prompt)
    if result.startswith("⚠️"):
        report = t["error"] + result
    else:
        report = f"{t['report']}\n🤖 {provider}\n\n{result}"
    if len(report) > 3900:
        report = report[:3850] + "\n\n[Report shortened to fit Telegram message limit.]"
    await wait_message.edit_text(
        report,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t["change"], callback_data="an:select")],
            [InlineKeyboardButton(t["back"], callback_data="menu:analyze")],
        ])
    )


async def analysis_callback(update, context):
    query = update.callback_query
    data = query.data
    t = TEXT.get(_lang(update), TEXT["bn"])

    if data == "an:select":
        context.user_data["analysis_draft_platforms"] = []
        context.user_data["analysis_draft_target_ids"] = []
        await _show_platform_picker(update, context)
        return

    if data == "an:back_platform":
        await _show_platform_picker(update, context)
        return

    if data.startswith("an:plat:"):
        try:
            platform = context.user_data["analysis_platform_options"][int(data.rsplit(":", 1)[1])]
        except (ValueError, IndexError, KeyError):
            await query.answer(t["expired"], show_alert=True)
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
            await query.answer(t["need_platform"], show_alert=True)
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
                target_id = options[int(choice)]["id"]
            except (ValueError, IndexError):
                await query.answer(t["expired"], show_alert=True)
                return
            if target_id in selected:
                selected.remove(target_id)
            else:
                selected.append(target_id)
        await _show_account_picker(update, context)
        return

    if data == "an:confirm":
        options = context.user_data.get("analysis_target_options", [])
        selected_ids = set(context.user_data.get("analysis_draft_target_ids", []))
        chosen = [{"platform": item["platform"], "name": item["name"]} for item in options if item["id"] in selected_ids]
        if not chosen:
            await query.answer(t["need_account"], show_alert=True)
            return
        chosen = storage.set_analysis_selection(update.effective_user.id, chosen)
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
            await query.answer(t["need_selection"], show_alert=True)
            await _show_platform_picker(update, context)
            return
        if feature == "all":
            await _run_all_analysis(update, context, selected)
            return
        await show(update, f"{t['scope']}:\n" + "\n".join(
            f"• {item['platform']} — {item['name']}" for item in selected
        ) + "\n\n" + t["feature_wait"], InlineKeyboardMarkup([
            [InlineKeyboardButton(t["all"], callback_data="an:feature:all")],
            [InlineKeyboardButton(t["change"], callback_data="an:select")],
            [InlineKeyboardButton(t["back"], callback_data="menu:analyze")],
        ]))
        return
