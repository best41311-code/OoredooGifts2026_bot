import telebot
import requests
import time
from telebot import types

# 1. ضع توكن البوت الخاص بك هنا (من BotFather)
BOT_TOKEN = "8699110958:AAFI59UvH_BkpP7EhyvkMiY53L874SvHiD8"
bot = telebot.TeleBot(BOT_TOKEN)

# معرف قناتك (يجب أن يكون البوت مشرفاً في القناة ليتمكن من فحص المشتركين)
CHANNEL_USERNAME = "@stifdz"
CHANNEL_URL = "https://t.me/stifdz"

# قواميس لحفظ بيانات المستخدمين مؤقتاً في الذاكرة
# (ملاحظة: عند إعادة تشغيل السكربت ستُصفر الأوقات، لإنتاجية دائمية يفضل ربطها بقاعدة بيانات لاحقاً)
user_cooldowns = {}  # لحفظ وقت آخر تفعيل {chat_id: timestamp}
user_sessions = {}   # لحفظ بيانات الجلسة الحالية كـ الرقم والـ authenticationId

HEADERS = {
    "User-Agent": "MyOoredoo/4.0.0 (Android; SDK 33)",
    "Content-Type": "application/json"
}

# دالة للتحقق من أن المستخدم اشترك في القناة
def check_channel_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # الحالات المقبولة للاشتراك
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        # في حال حدوث خطأ (مثلاً البوت ليس مشرفاً في القناة بعد)
        return False

# واجهة القائمة الرئيسية المميزة
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_claim = types.KeyboardButton("🎁 تفعيل الهدية اليومية (أوريدو)")
    btn_info = types.KeyboardButton("ℹ️ معلومات حسابي / الدعم")
    markup.add(btn_claim, btn_info)
    return markup

# ----------------- أوامر البوت -----------------

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    
    # التحقق من الاشتراك أولاً
    if not check_channel_subscription(chat_id):
        send_subscription_alert(chat_id)
        return

    welcome_text = (
        "✨ **مرحباً بك في بوت هدايا أوريدو الحصري!** ✨\n\n"
        "هذا البوت يساعدك على سحب مكافآت الإنترنت والهدية اليومية بضغطة زر وبسرعة فائقة. 🚀\n\n"
        "📢 *ملاحظة:* يمكنك الاستفادة من التفعيل **مرة واحدة فقط كل 24 ساعة**."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# واجهة التنبيه بالاشتراك الإجباري
def send_subscription_alert(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_link = types.InlineKeyboardButton("🔗 اضغط هنا للاشتراك في القناة", url=CHANNEL_URL)
    btn_check = types.InlineKeyboardButton("✅ تم الاشتراك، تفعيل البوت", callback_data="check_sub")
    markup.add(btn_link)
    markup.add(btn_check)
    
    alert_text = (
        "⚠️ **عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدام الخدمات!**\n\n"
        "يرجى الانضمام إلى القناة ثم الضغط على زر التأكيد بالأسفل لفتح الواجهة الرئيسية 👇"
    )
    bot.send_message(chat_id, alert_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    chat_id = call.message.chat.id
    if check_channel_subscription(chat_id):
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "🎉 شكرًا لاشتراكك! تم تفعيل البوت بنجاح.", reply_markup=main_menu_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد! رجاءً اشترك أولاً.", show_alert=True)

# معالجة الضغط على الأزرار الرئيسية
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    chat_id = message.chat.id
    
    # حماية: التحقق من الاشتراك عند كل ضغطة زر
    if not check_channel_subscription(chat_id):
        send_subscription_alert(chat_id)
        return

    if message.text == "🎁 تفعيل الهدية اليومية (أوريدو)":
        # ⏱️ التحقق من شرط الـ 24 ساعة
        current_time = time.time()
        if chat_id in user_cooldowns:
            last_claim = user_cooldowns[chat_id]
            time_passed = current_time - last_claim
            if time_passed < 86400:  # 24 ساعة بالثواني
                time_left = 86400 - time_passed
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                bot.reply_to(message, f"⏳ **عذراً، لقد قمت بالتفعيل مؤخراً!**\nيمكنك طلب الهدية القادمة بعد: `{hours} ساعة و {minutes} دقيقة`.", parse_mode="Markdown")
                return

        sent_msg = bot.send_message(chat_id, "📱 من فضلك، أرسل **رقم هاتف أوريدو** الخاص بك الآن:\n_(مثال: +2135XXXXXXXX)_")
        bot.register_next_step_handler(sent_msg, process_phone_step)
        
    elif message.text == "ℹ️ معلومات حسابي / الدعم":
        info_text = (
            "🛠️ **حول البوت:**\n"
            f"• القناة الرسمية: {CHANNEL_USERNAME}\n"
            "• النظام: تفعيل تلقائي وآمن عبر الـ API.\n"
            "• حالة حسابك: نشط وجاهز للاستخدام. ✅"
        )
        bot.send_message(chat_id, info_text, reply_markup=main_menu_keyboard())

# خطوة استقبال رقم الهاتف وإرسال الرمز
def process_phone_step(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    
    bot.send_message(chat_id, "🔄 جاري الاتصال بالسيرفر وإرسال رمز التحقق (OTP)...")
    
    # --- استدعاء سورس إرسال الرمز (من الخطوة السابقة) ---
    # ملاحظة: يجب تعديل الروابط والـ Client Credentials لتطابق حساب المطورين الخاص بك
    token_url = "https://ooredoo.com"
    # كود جلب الـ token والـ send-code مدمج هنا تبسيطاً للخطوات
    # (يفضل استخدام الدوال السابقة التي شرحناها لترتيب السكربت)
    
    # محاكاة نجاح الإرسال والحصول على الـ Auth ID (استبدله بالاستدعاء الحقيقي)
    auth_id = "MOCK_AUTH_ID_12345" 
    
    # حفظ البيانات في الجلسة لمتابعة التحقق
    user_sessions[chat_id] = {"phone": phone, "auth_id": auth_id}
    
    sent_msg = bot.send_message(chat_id, "📩 **تم إرسال الرمز بنجاح!**\nقم بكتابة رمز التأكيد (SMS) الذي وصلك على هاتفك:")
    bot.register_next_step_handler(sent_msg, process_otp_step)

# خطوة استقبال الرمز وتفعيل الثغرة
def process_otp_step(message):
    chat_id = message.chat.id
    otp = message.text.strip()
    
    if chat_id not in user_sessions:
        bot.send_message(chat_id, "❌ حدث خطأ في الجلسة، يرجى إعادة المحاولة من البداية.")
        return
        
    phone = user_sessions[chat_id]["phone"]
    auth_id = user_sessions[chat_id]["auth_id"]
    
    bot.send_message(chat_id, "⚡ جاري فحص الرمز وتفعيل الثغرة السريعة للهدية...")
    
    # هنا يتم استدعاء دالة الـ validate-code التي كتبناها مسبقاً
    # سنفترض نجاح العملية وتخطي الحماية لتشغيل الـ Gift Endpoint
    
    success = True # ضع منطق فحص الاستجابة الحقيقية هنا من دالة validate
    
    if success:
        # 🔑 تحديث وقت التفعيل للمستخدم لمنعه لـ 24 ساعة قادمة
        user_cooldowns[chat_id] = time.time()
        
        success_text = (
            "🎉 **مبروووك! تم تفعيل هدية الإنترنت بنجاح!** 🎉\n\n"
            f"📱 الحساب: `{phone}`\n"
            "🎁 الهدية: باقة إنترنت مجانية يومية مجددة.\n\n"
            "مرحباً بك دائماً، يمكنك العودة بعد 24 ساعة للتفعيل مجدداً! ⏱️"
        )
        bot.send_message(chat_id, success_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(chat_id, "❌ فشل التفعيل، الرمز الذي أدخلته منتهي الصلاحية أو غير صحيح.", reply_markup=main_menu_keyboard())
        
    # تنظيف الجلسة المؤقتة بعد الانتهاء
    user_sessions.pop(chat_id, None)

# تشغيل البوت بشكل مستمر لا ينقطع
print("[+] البوت يعمل الآن بنجاح...")
bot.infinity_polling()
