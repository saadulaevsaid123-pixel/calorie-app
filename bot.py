import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8537251737:AAG-yjEmNtgRqJm84D80pzeJWN5sYyngTqI"
WEBAPP_URL = "https://calorie-app-56jv.onrender.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "🥗 Открыть счётчик калорий",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    await update.message.reply_text(
        "Привет! Нажми кнопку ниже 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("Бот запущен...")
app.run_polling()

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# Запускаем бота
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("Бот запущен...")
app.run_polling()