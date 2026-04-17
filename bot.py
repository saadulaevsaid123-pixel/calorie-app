import os
import threading
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import urllib.request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8537251737:AAFJiWVoVnFCmjaPbiz74731c2lhrh02SmQ")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://calorie-app-56jv.onrender.com")
PORT = int(os.environ.get("PORT", 8080))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

# Flask для keep-alive
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Kalorei Bot is running! 🔥"

@flask_app.route("/health")
def health():
    return "OK"

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

# ── BOT HANDLERS ──────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🥗 Открыть Kalorei", web_app=WebAppInfo(url=WEBAPP_URL))
    ]]
    await update.message.reply_text(
        "👋 Привет! Я твой помощник по питанию.\n\n"
        "Считай калории, следи за весом и достигай целей 🎯\n\n"
        "Нажми кнопку чтобы открыть приложение 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌅 Завтрак (8:00)", callback_data="remind_breakfast")],
        [InlineKeyboardButton("☀️ Обед (13:00)", callback_data="remind_lunch")],
        [InlineKeyboardButton("🌙 Ужин (19:00)", callback_data="remind_dinner")],
        [InlineKeyboardButton("💧 Вода (21:00)", callback_data="remind_water")],
        [InlineKeyboardButton("⚖️ Взвешивание (9:00)", callback_data="remind_weight")],
    ]
    await update.message.reply_text(
        "⏰ Выбери напоминания:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reminders = {
        "remind_breakfast": "🌅 Буду напоминать о завтраке в 8:00!",
        "remind_lunch": "☀️ Буду напоминать об обеде в 13:00!",
        "remind_dinner": "🌙 Буду напоминать об ужине в 19:00!",
        "remind_water": "💧 Буду напоминать о воде в 21:00!",
        "remind_weight": "⚖️ Буду напоминать о взвешивании в 9:00!",
    }

    msg = reminders.get(query.data, "Готово!")
    keyboard = [[InlineKeyboardButton("🥗 Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    if 'reminders' not in context.bot_data:
        context.bot_data['reminders'] = {}
    chat_id = query.message.chat_id
    remind_type = query.data.replace('remind_', '')
    if chat_id not in context.bot_data['reminders']:
        context.bot_data['reminders'][chat_id] = set()
    context.bot_data['reminders'][chat_id].add(remind_type)

async def send_reminders(context):
    hour = datetime.now().hour
    reminders = context.bot_data.get('reminders', {})

    messages = {
        8:  ('weight', '⚖️ Доброе утро! Взвесься и запиши вес в Kalorei'),
        8:  ('breakfast', '🌅 Время завтрака! Не забудь записать что поел'),
        13: ('lunch', '☀️ Время обеда! Запиши свой обед в Kalorei'),
        19: ('dinner', '🌙 Время ужина! Не забудь записать ужин'),
        21: ('water', '💧 Как с водой сегодня? Не забывай пить!'),
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
                    print(f"Error: {e}")

async def keep_alive(context):
    """Пингуем себя чтобы Render не засыпал"""
    if RENDER_URL:
        try:
            urllib.request.urlopen(f"{RENDER_URL}/health", timeout=10)
            print(f"Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive error: {e}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
threading.Thread(target=run_flask, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("remind", remind))
app.add_handler(CallbackQueryHandler(button_handler))

# Напоминания каждый час
app.job_queue.run_repeating(send_reminders, interval=3600, first=10)
# Keep-alive каждые 10 минут
app.job_queue.run_repeating(keep_alive, interval=600, first=30)

print(f"Бот запущен на порту {PORT}...")
app.run_polling()
