import telebot
import requests

# 1. إعداد توكن البوت الخاص بك من @BotFather
BOT_TOKEN = "8699110958:AAFI59UvH_BkpP7EhyvkMiY53L874SvHiD8"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. روابط سيرفر أوريدو (Endpoints القياسية المعتمدة)
OOREDOO_BASE_URL = "https://api.ooredoo.com"  # أو الرابط الذي يصيده المستخدم
OTP_SEND_URL = f"{OOREDOO_BASE_URL}/one-time-password-sms/v4/send-code"
GIFT_CLAIM_URL = f"{OOREDOO_BASE_URL}/v1/campaigns/wheel/claim"

# قاموس لتخزين بيانات المستخدمين مؤقتاً في ذاكرة البوت
user_data = {}

# ترحيب بالبوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك في بوت هدايا أوريدو! 🎁\nمن فضلك أرسل رقم هاتفك الآن (مثال: 0555xxxxxx):")

# الخطوة 1: استقبال رقم الهاتف وإرسال الـ OTP
@bot.message_handler(func=lambda message: message.text.isdigit() and len(message.text) == 10)
def handle_phone(message):
    phone_number = message.text
    chat_id = message.chat.id
    user_data[chat_id] = {'phone': phone_number}
    
    bot.send_message(chat_id, "جاري طلب رمز التحقق (OTP) من سيرفر أوريدو... ⏳")
    
    # الطلب الموجه لسيرفر أوريدو لإرسال الـ SMS
    payload = {
        "phoneNumber": phone_number,
        "message": "Your verification code is:"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(OTP_SEND_URL, json=payload, headers=headers)
        if response.status_code == 200:
            # حفظ معرف العملية (authId) إذا كان السيرفر يتطلبه لتوثيق الرمز
            auth_id = response.json().get("authenticationId")
            user_data[chat_id]['auth_id'] = auth_id
            bot.send_message(chat_id, "تم إرسال الرمز بنجاح! 💬\nمن فضلك أرسل كود الـ OTP الذي وصلك في رسالة:")
            bot.register_next_step_handler(message, handle_otp)
        else:
            bot.send_message(chat_id, f"فشل إرسال الرمز. خطأ من السيرفر: {response.status_code}")
    except Exception as e:
        bot.send_message(chat_id, "حدث خطأ أثناء الاتصال بسيرفر أوريدو.")

# الخطوة 2: استقبال الـ OTP وتفعيل الهدية
def handle_otp(message):
    otp_code = message.text
    chat_id = message.chat.id
    phone_number = user_data[chat_id]['phone']
    
    bot.send_message(chat_id, "جاري التحقق وتفعيل الهدية... 🎡")
    
    # تفاصيل تفعيل الهدية (الـ الثغرة أو طلب العجلة)
    gift_payload = {
        "phoneNumber": phone_number,
        "code": otp_code,
        "campaignId": "wheel_2026"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(GIFT_CLAIM_URL, json=gift_payload, headers=headers)
        if response.status_code == 200:
            bot.send_message(chat_id, "مبروك! 🎉 تم تفعيل الهدية بنجاح على رقمك.")
        else:
            bot.send_message(chat_id, f"السيرفر رفض التفعيل. رمز الخطأ: {response.status_code}\nتأكد من صحة الكود أو انتهاء صلاحية العرض.")
    except Exception as e:
        bot.send_message(chat_id, "خطأ في اتصال الشبكة أثناء تفعيل الهدية.")

# تشغيل البوت بدون توقف
bot.polling()
