"""
Телеграм-бот для запуска Mini App.
Установка: pip install python-telegram-bot
Запуск: python bot.py
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Вставь сюда свой токен от @BotFather
BOT_TOKEN = "8537251737:AAGf8M90pV_77TXXku0aUDAXX0lZQPofPW0"

# Вставь сюда публичный URL твоего сервера (после запуска ngrok)
WEBAPP_URL = "https://unrefreshed-buffy-parchedly.ngrok-free.dev"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "🥗 Открыть счётчик калорий",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    await update.message.reply_text(
        "Привет! Нажми кнопку ниже, чтобы открыть счётчик калорий 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("Бот запущен...")
app.run_polling()
