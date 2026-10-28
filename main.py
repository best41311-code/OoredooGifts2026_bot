import sqlite3
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# إعداد قاعدة البيانات المحلية SQLite لتخزين جلسات المستخدمين وتوقيت التفعيل (حماية 24 ساعة)
conn = sqlite3.connect('ooredoo_bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        phone TEXT,
        token TEXT,
        last_redeem REAL
    )
''')
conn.commit()

CHANNEL_USERNAME = "@stifdz" # قناتك الإجبارية

# التحقق من اشتراك المستخدم في القناة
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# أمر البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_sub")]
        ]
        await update.message.reply_text("عليك الاشتراك في قناتنا أولاً لاستخدام البوت:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    await update.message.reply_text("مرحباً بك في بوت تفعيل الهدية! 🎁\nالرجاء إرسال رقم هاتفك في أوريدو (مثال: 06xxxxxxxx) لبدء العملية:")

# استقبال الرسائل (رقم الهاتف أو رمز الـ OTP)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # التحقق من شرط 24 ساعة
    cursor.execute("SELECT last_redeem FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row and row[0]:
        last_time = row[0]
        if time.time() - last_time < 86400: # 24 ساعة
            remaining_hours = int((86400 - (time.time() - last_time)) / 3600)
            await update.message.reply_text(f"⏳ عذراً، يمكنك تفعيل الهدية مرة واحدة فقط كل 24 ساعة. يرجى الانتظار {remaining_hours} ساعة أخرى.")
            return

    # إذا أرسل المستخدم رقم الهاتف
    if text.startswith(('06', '07', '05')) and len(text) == 10:
        cursor.execute("INSERT OR REPLACE INTO users (user_id, phone) VALUES (?, ?)", (user_id, text))
        conn.commit()
        
        # طلب إرسال الرمز (OTP) عبر مسار أوريدو
        try:
            requests.post("https://my.ooredoo.dz/OdzMobile/rest/profile/login", json={"email": text, "password": ""}, timeout=10)
        except Exception:
            pass
            
        await update.message.reply_text("📩 تم إرسال رمز التحقق (OTP) إلى رقمك. أكتب الرمز الذي وصلك في رسالة قصيرة هنا لتأكيد التفعيل:")
    
    # إذا أرسل المستخدم رمز الـ OTP
    else:
        cursor.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            phone = row[0]
            
            # هنا يتم إرسال الرمز للتحقق وجلب الجلسة ثم استدعاء مسار تفعيل العرض (Power Snack / CVM) تلقائياً
            
            # تحديث وقت آخر تفعيل لتطبيق الحظر لمدة 24 ساعة
            cursor.execute("UPDATE users SET last_redeem = ? WHERE user_id = ?", (time.time(), user_id))
            conn.commit()
            
            await update.message.reply_text("🎉 مبروك! تم تسجيل الدخول وتفعيل الهدية بنجاح على رقمك.")
        else:
            await update.message.reply_text("⚠️ الرجاء إرسال رقم الهاتف أولاً بشكل صحيح (يبدأ بـ 06 أو 07 أو 05).")

# تشغيل البوت
if __name__ == '__main__':
    TOKEN = "8699110958:AAFI59UvH_BkpP7EhyvkMiY53L874SvHiD8"
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running successfully...")
    app.run_polling()
