import os
import threading
import asyncio
from datetime import datetime, time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "8537251737:AAFBUIMjZ8kyCFWDTjVGZ6xD69WiCBW0UOo"
WEBAPP_URL = "https://calorie-app-56jv.onrender.com"

# Flask для Render
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ── BOT HANDLERS ──────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🥗 Открыть Kalorei", web_app=WebAppInfo(url=WEBAPP_URL))
    ]]
    await update.message.reply_text(
        "👋 Привет! Я твой помощник по питанию.\n\nНажми кнопку чтобы открыть приложение 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для управления напоминаниями"""
    keyboard = [
        [InlineKeyboardButton("🌅 Завтрак (8:00)", callback_data="remind_breakfast")],
        [InlineKeyboardButton("☀️ Обед (13:00)", callback_data="remind_lunch")],
        [InlineKeyboardButton("🌙 Ужин (19:00)", callback_data="remind_dinner")],
        [InlineKeyboardButton("💧 Вода (каждые 2ч)", callback_data="remind_water")],
        [InlineKeyboardButton("⚖️ Взвешивание (9:00)", callback_data="remind_weight")],
    ]
    await update.message.reply_text(
        "⏰ Выбери напоминания которые хочешь включить:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reminders = {
        "remind_breakfast": "🌅 Напоминание о завтраке включено! Буду напоминать в 8:00",
        "remind_lunch": "☀️ Напоминание об обеде включено! Буду напоминать в 13:00",
        "remind_dinner": "🌙 Напоминание об ужине включено! Буду напоминать в 19:00",
        "remind_water": "💧 Напоминание о воде включено! Буду напоминать каждые 2 часа",
        "remind_weight": "⚖️ Напоминание о взвешивании включено! Буду напоминать в 9:00",
    }

    msg = reminders.get(query.data, "Готово!")
    keyboard = [[InlineKeyboardButton("🥗 Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # Сохраняем chat_id и тип напоминания для отправки уведомлений
    if not hasattr(context.bot_data, 'reminders'):
        context.bot_data['reminders'] = {}
    chat_id = query.message.chat_id
    remind_type = query.data.replace('remind_', '')
    if chat_id not in context.bot_data['reminders']:
        context.bot_data['reminders'][chat_id] = set()
    context.bot_data['reminders'][chat_id].add(remind_type)

async def send_reminders(context):
    """Отправляет напоминания в нужное время"""
    now = datetime.now()
    hour = now.hour
    reminders = context.bot_data.get('reminders', {})

    messages = {
        8:  ('breakfast', '🌅 Время завтрака! Не забудь записать что поел в Kalorei'),
        13: ('lunch', '☀️ Время обеда! Запиши свой обед в Kalorei'),
        19: ('dinner', '🌙 Время ужина! Не забудь записать ужин в Kalorei'),
        21: ('water', '💧 Как с водой сегодня? Не забывай пить!'),
        9:  ('weight', '⚖️ Доброе утро! Взвесься и запиши вес в Kalorei'),
    }

    if hour in messages:
        remind_key, text = messages[hour]
        keyboard = [[InlineKeyboardButton("📱 Открыть Kalorei", web_app=WebAppInfo(url=WEBAPP_URL))]]
        for chat_id, types in reminders.items():
            if remind_key in types:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    print(f"Error sending reminder to {chat_id}: {e}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
threading.Thread(target=run_flask, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("remind", remind))
app.add_handler(CallbackQueryHandler(button_handler))

# Планировщик напоминаний — каждый час проверяем
app.job_queue.run_repeating(send_reminders, interval=3600, first=10)

print("Бот запущен...")
app.run_polling()
