from flask import Flask, request, jsonify, send_from_directory
import json, os
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder="static")
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id BIGINT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            name TEXT NOT NULL,
            grams REAL NOT NULL,
            meal_type TEXT NOT NULL,
            cal INTEGER NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            carbs REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            data JSONB NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_foods (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            cal INTEGER NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            carbs REAL NOT NULL,
            category TEXT DEFAULT 'Сканер',
            barcode TEXT,
            added_by TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_foods (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            food_id INTEGER NOT NULL,
            food_source TEXT DEFAULT 'custom',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            name TEXT NOT NULL,
            calories_burned INTEGER NOT NULL,
            duration_minutes INTEGER,
            activity_type TEXT DEFAULT 'other',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weight_log (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            weight REAL NOT NULL,
            UNIQUE(user_id, date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS water (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS water_goals (
            user_id TEXT PRIMARY KEY,
            goal INTEGER DEFAULT 2500
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            user_id TEXT PRIMARY KEY,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            freezes INTEGER DEFAULT 2,
            last_logged_date TEXT DEFAULT ''
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

FOODS_DB = [
    {
        "id": 1,
        "name": "Куриная грудка",
        "cal": 165,
        "protein": 31.0,
        "fat": 3.6,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 2,
        "name": "Куриное бедро",
        "cal": 209,
        "protein": 26.0,
        "fat": 11.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 3,
        "name": "Куриное филе",
        "cal": 110,
        "protein": 23.0,
        "fat": 1.2,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 4,
        "name": "Говядина",
        "cal": 250,
        "protein": 26.0,
        "fat": 17.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 5,
        "name": "Говядина нежирная",
        "cal": 187,
        "protein": 28.7,
        "fat": 7.4,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 6,
        "name": "Свинина",
        "cal": 310,
        "protein": 25.0,
        "fat": 23.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 7,
        "name": "Свинина нежирная",
        "cal": 215,
        "protein": 27.0,
        "fat": 12.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 8,
        "name": "Индейка филе",
        "cal": 115,
        "protein": 24.0,
        "fat": 1.5,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 9,
        "name": "Индейка фарш",
        "cal": 170,
        "protein": 22.0,
        "fat": 9.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 10,
        "name": "Говяжий фарш",
        "cal": 254,
        "protein": 24.0,
        "fat": 17.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 11,
        "name": "Куриный фарш",
        "cal": 143,
        "protein": 17.0,
        "fat": 8.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 12,
        "name": "Баранина",
        "cal": 294,
        "protein": 25.0,
        "fat": 21.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 13,
        "name": "Кролик",
        "cal": 183,
        "protein": 21.0,
        "fat": 11.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 14,
        "name": "Утка",
        "cal": 337,
        "protein": 19.0,
        "fat": 29.0,
        "carbs": 0.0,
        "category": "Мясо"
    },
    {
        "id": 15,
        "name": "Ветчина",
        "cal": 145,
        "protein": 17.0,
        "fat": 8.0,
        "carbs": 1.5,
        "category": "Мясо"
    },
    {
        "id": 16,
        "name": "Колбаса варёная",
        "cal": 260,
        "protein": 13.0,
        "fat": 23.0,
        "carbs": 1.8,
        "category": "Мясо"
    },
    {
        "id": 17,
        "name": "Сосиски",
        "cal": 256,
        "protein": 11.0,
        "fat": 23.0,
        "carbs": 1.6,
        "category": "Мясо"
    },
    {
        "id": 18,
        "name": "Бекон",
        "cal": 541,
        "protein": 37.0,
        "fat": 42.0,
        "carbs": 1.4,
        "category": "Мясо"
    },
    {
        "id": 19,
        "name": "Лосось",
        "cal": 208,
        "protein": 20.0,
        "fat": 13.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 20,
        "name": "Форель",
        "cal": 148,
        "protein": 21.0,
        "fat": 7.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 21,
        "name": "Тунец конс.",
        "cal": 100,
        "protein": 22.0,
        "fat": 1.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 22,
        "name": "Тунец свежий",
        "cal": 144,
        "protein": 23.0,
        "fat": 5.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 23,
        "name": "Треска",
        "cal": 82,
        "protein": 18.0,
        "fat": 0.7,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 24,
        "name": "Хек",
        "cal": 86,
        "protein": 17.0,
        "fat": 2.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 25,
        "name": "Минтай",
        "cal": 72,
        "protein": 16.0,
        "fat": 1.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 26,
        "name": "Скумбрия",
        "cal": 262,
        "protein": 18.0,
        "fat": 21.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 27,
        "name": "Сельдь",
        "cal": 217,
        "protein": 18.0,
        "fat": 16.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 28,
        "name": "Сардина конс.",
        "cal": 208,
        "protein": 25.0,
        "fat": 11.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 29,
        "name": "Креветки",
        "cal": 99,
        "protein": 24.0,
        "fat": 0.3,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 30,
        "name": "Кальмар",
        "cal": 92,
        "protein": 18.0,
        "fat": 1.4,
        "carbs": 1.0,
        "category": "Рыба"
    },
    {
        "id": 31,
        "name": "Мидии",
        "cal": 86,
        "protein": 12.0,
        "fat": 2.2,
        "carbs": 3.7,
        "category": "Рыба"
    },
    {
        "id": 32,
        "name": "Краб",
        "cal": 97,
        "protein": 19.0,
        "fat": 1.5,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 33,
        "name": "Икра красная",
        "cal": 263,
        "protein": 32.0,
        "fat": 14.0,
        "carbs": 0.0,
        "category": "Рыба"
    },
    {
        "id": 34,
        "name": "Яйцо куриное",
        "cal": 155,
        "protein": 13.0,
        "fat": 11.0,
        "carbs": 1.0,
        "category": "Молочные"
    },
    {
        "id": 35,
        "name": "Яичный белок",
        "cal": 52,
        "protein": 11.0,
        "fat": 0.2,
        "carbs": 0.7,
        "category": "Молочные"
    },
    {
        "id": 36,
        "name": "Творог 0%",
        "cal": 79,
        "protein": 18.0,
        "fat": 0.2,
        "carbs": 1.8,
        "category": "Молочные"
    },
    {
        "id": 37,
        "name": "Творог 5%",
        "cal": 121,
        "protein": 17.0,
        "fat": 5.0,
        "carbs": 2.7,
        "category": "Молочные"
    },
    {
        "id": 38,
        "name": "Творог 9%",
        "cal": 159,
        "protein": 16.0,
        "fat": 9.0,
        "carbs": 2.0,
        "category": "Молочные"
    },
    {
        "id": 39,
        "name": "Греческий йогурт 0%",
        "cal": 66,
        "protein": 10.0,
        "fat": 0.4,
        "carbs": 4.0,
        "category": "Молочные"
    },
    {
        "id": 40,
        "name": "Греческий йогурт",
        "cal": 97,
        "protein": 10.0,
        "fat": 5.0,
        "carbs": 3.6,
        "category": "Молочные"
    },
    {
        "id": 41,
        "name": "Йогурт натуральный",
        "cal": 61,
        "protein": 5.0,
        "fat": 3.2,
        "carbs": 3.5,
        "category": "Молочные"
    },
    {
        "id": 42,
        "name": "Кефир 1%",
        "cal": 40,
        "protein": 3.3,
        "fat": 1.0,
        "carbs": 4.1,
        "category": "Молочные"
    },
    {
        "id": 43,
        "name": "Молоко 1.5%",
        "cal": 46,
        "protein": 3.0,
        "fat": 1.5,
        "carbs": 4.7,
        "category": "Молочные"
    },
    {
        "id": 44,
        "name": "Молоко 2.5%",
        "cal": 52,
        "protein": 2.8,
        "fat": 2.5,
        "carbs": 4.7,
        "category": "Молочные"
    },
    {
        "id": 45,
        "name": "Молоко 3.2%",
        "cal": 60,
        "protein": 2.8,
        "fat": 3.2,
        "carbs": 4.7,
        "category": "Молочные"
    },
    {
        "id": 46,
        "name": "Сыр твёрдый",
        "cal": 380,
        "protein": 25.0,
        "fat": 30.0,
        "carbs": 0.5,
        "category": "Молочные"
    },
    {
        "id": 47,
        "name": "Сыр Пармезан",
        "cal": 431,
        "protein": 38.0,
        "fat": 29.0,
        "carbs": 4.0,
        "category": "Молочные"
    },
    {
        "id": 48,
        "name": "Сыр Моцарелла",
        "cal": 280,
        "protein": 28.0,
        "fat": 17.0,
        "carbs": 2.2,
        "category": "Молочные"
    },
    {
        "id": 49,
        "name": "Сыр Фета",
        "cal": 264,
        "protein": 14.0,
        "fat": 21.0,
        "carbs": 4.0,
        "category": "Молочные"
    },
    {
        "id": 50,
        "name": "Сметана 15%",
        "cal": 158,
        "protein": 2.6,
        "fat": 15.0,
        "carbs": 3.0,
        "category": "Молочные"
    },
    {
        "id": 51,
        "name": "Сметана 20%",
        "cal": 206,
        "protein": 2.8,
        "fat": 20.0,
        "carbs": 3.2,
        "category": "Молочные"
    },
    {
        "id": 52,
        "name": "Масло сливочное",
        "cal": 748,
        "protein": 0.5,
        "fat": 82.5,
        "carbs": 0.8,
        "category": "Молочные"
    },
    {
        "id": 53,
        "name": "Овсянка сухая",
        "cal": 350,
        "protein": 12.0,
        "fat": 6.0,
        "carbs": 62.0,
        "category": "Крупы"
    },
    {
        "id": 54,
        "name": "Гречка варёная",
        "cal": 110,
        "protein": 4.2,
        "fat": 1.1,
        "carbs": 21.0,
        "category": "Крупы"
    },
    {
        "id": 55,
        "name": "Гречка сухая",
        "cal": 313,
        "protein": 12.6,
        "fat": 3.3,
        "carbs": 62.0,
        "category": "Крупы"
    },
    {
        "id": 56,
        "name": "Рис варёный",
        "cal": 130,
        "protein": 2.7,
        "fat": 0.3,
        "carbs": 28.0,
        "category": "Крупы"
    },
    {
        "id": 57,
        "name": "Рис бурый варёный",
        "cal": 111,
        "protein": 2.6,
        "fat": 0.9,
        "carbs": 23.0,
        "category": "Крупы"
    },
    {
        "id": 58,
        "name": "Макароны варёные",
        "cal": 158,
        "protein": 5.5,
        "fat": 0.9,
        "carbs": 31.0,
        "category": "Крупы"
    },
    {
        "id": 59,
        "name": "Макароны сухие",
        "cal": 350,
        "protein": 12.0,
        "fat": 1.5,
        "carbs": 71.0,
        "category": "Крупы"
    },
    {
        "id": 60,
        "name": "Перловка варёная",
        "cal": 109,
        "protein": 3.6,
        "fat": 0.4,
        "carbs": 22.0,
        "category": "Крупы"
    },
    {
        "id": 61,
        "name": "Киноа варёная",
        "cal": 120,
        "protein": 4.4,
        "fat": 1.9,
        "carbs": 21.3,
        "category": "Крупы"
    },
    {
        "id": 62,
        "name": "Чечевица варёная",
        "cal": 116,
        "protein": 9.0,
        "fat": 0.4,
        "carbs": 20.0,
        "category": "Крупы"
    },
    {
        "id": 63,
        "name": "Нут варёный",
        "cal": 164,
        "protein": 8.9,
        "fat": 2.6,
        "carbs": 27.0,
        "category": "Крупы"
    },
    {
        "id": 64,
        "name": "Фасоль варёная",
        "cal": 127,
        "protein": 8.7,
        "fat": 0.5,
        "carbs": 22.0,
        "category": "Крупы"
    },
    {
        "id": 65,
        "name": "Хлеб ржаной",
        "cal": 259,
        "protein": 9.0,
        "fat": 3.0,
        "carbs": 48.0,
        "category": "Хлеб"
    },
    {
        "id": 66,
        "name": "Хлеб белый",
        "cal": 265,
        "protein": 8.0,
        "fat": 3.0,
        "carbs": 51.0,
        "category": "Хлеб"
    },
    {
        "id": 67,
        "name": "Хлеб цельнозерновой",
        "cal": 247,
        "protein": 9.0,
        "fat": 3.0,
        "carbs": 46.0,
        "category": "Хлеб"
    },
    {
        "id": 68,
        "name": "Лаваш",
        "cal": 239,
        "protein": 7.5,
        "fat": 1.5,
        "carbs": 50.0,
        "category": "Хлеб"
    },
    {
        "id": 69,
        "name": "Хлебцы рисовые",
        "cal": 392,
        "protein": 7.0,
        "fat": 3.0,
        "carbs": 83.0,
        "category": "Хлеб"
    },
    {
        "id": 70,
        "name": "Хлебцы ржаные",
        "cal": 336,
        "protein": 9.0,
        "fat": 2.0,
        "carbs": 72.0,
        "category": "Хлеб"
    },
    {
        "id": 71,
        "name": "Картофель варёный",
        "cal": 80,
        "protein": 2.0,
        "fat": 0.1,
        "carbs": 17.0,
        "category": "Овощи"
    },
    {
        "id": 72,
        "name": "Батат варёный",
        "cal": 86,
        "protein": 1.6,
        "fat": 0.1,
        "carbs": 20.0,
        "category": "Овощи"
    },
    {
        "id": 73,
        "name": "Огурец",
        "cal": 15,
        "protein": 0.7,
        "fat": 0.1,
        "carbs": 2.5,
        "category": "Овощи"
    },
    {
        "id": 74,
        "name": "Помидор",
        "cal": 18,
        "protein": 0.9,
        "fat": 0.2,
        "carbs": 3.5,
        "category": "Овощи"
    },
    {
        "id": 75,
        "name": "Перец болгарский",
        "cal": 31,
        "protein": 1.0,
        "fat": 0.3,
        "carbs": 6.0,
        "category": "Овощи"
    },
    {
        "id": 76,
        "name": "Морковь",
        "cal": 41,
        "protein": 0.9,
        "fat": 0.2,
        "carbs": 9.6,
        "category": "Овощи"
    },
    {
        "id": 77,
        "name": "Капуста белокочанная",
        "cal": 27,
        "protein": 1.8,
        "fat": 0.1,
        "carbs": 5.0,
        "category": "Овощи"
    },
    {
        "id": 78,
        "name": "Капуста цветная",
        "cal": 25,
        "protein": 1.9,
        "fat": 0.3,
        "carbs": 4.0,
        "category": "Овощи"
    },
    {
        "id": 79,
        "name": "Брокколи",
        "cal": 34,
        "protein": 2.8,
        "fat": 0.4,
        "carbs": 7.0,
        "category": "Овощи"
    },
    {
        "id": 80,
        "name": "Шпинат",
        "cal": 23,
        "protein": 2.9,
        "fat": 0.4,
        "carbs": 3.6,
        "category": "Овощи"
    },
    {
        "id": 81,
        "name": "Салат листовой",
        "cal": 15,
        "protein": 1.3,
        "fat": 0.2,
        "carbs": 2.0,
        "category": "Овощи"
    },
    {
        "id": 82,
        "name": "Руккола",
        "cal": 25,
        "protein": 2.6,
        "fat": 0.7,
        "carbs": 3.7,
        "category": "Овощи"
    },
    {
        "id": 83,
        "name": "Лук репчатый",
        "cal": 41,
        "protein": 1.1,
        "fat": 0.1,
        "carbs": 9.0,
        "category": "Овощи"
    },
    {
        "id": 84,
        "name": "Чеснок",
        "cal": 149,
        "protein": 6.4,
        "fat": 0.5,
        "carbs": 33.0,
        "category": "Овощи"
    },
    {
        "id": 85,
        "name": "Грибы шампиньоны",
        "cal": 27,
        "protein": 3.1,
        "fat": 0.3,
        "carbs": 3.3,
        "category": "Овощи"
    },
    {
        "id": 86,
        "name": "Баклажан",
        "cal": 25,
        "protein": 1.2,
        "fat": 0.2,
        "carbs": 5.0,
        "category": "Овощи"
    },
    {
        "id": 87,
        "name": "Кабачок",
        "cal": 24,
        "protein": 1.5,
        "fat": 0.3,
        "carbs": 4.6,
        "category": "Овощи"
    },
    {
        "id": 88,
        "name": "Тыква",
        "cal": 26,
        "protein": 1.0,
        "fat": 0.1,
        "carbs": 6.5,
        "category": "Овощи"
    },
    {
        "id": 89,
        "name": "Свёкла варёная",
        "cal": 44,
        "protein": 1.7,
        "fat": 0.0,
        "carbs": 10.0,
        "category": "Овощи"
    },
    {
        "id": 90,
        "name": "Кукуруза варёная",
        "cal": 123,
        "protein": 4.0,
        "fat": 2.0,
        "carbs": 25.0,
        "category": "Овощи"
    },
    {
        "id": 91,
        "name": "Горошек зелёный",
        "cal": 73,
        "protein": 5.0,
        "fat": 0.4,
        "carbs": 13.0,
        "category": "Овощи"
    },
    {
        "id": 92,
        "name": "Спаржа",
        "cal": 20,
        "protein": 2.2,
        "fat": 0.1,
        "carbs": 3.9,
        "category": "Овощи"
    },
    {
        "id": 93,
        "name": "Яблоко",
        "cal": 47,
        "protein": 0.4,
        "fat": 0.4,
        "carbs": 10.0,
        "category": "Фрукты"
    },
    {
        "id": 94,
        "name": "Банан",
        "cal": 89,
        "protein": 1.1,
        "fat": 0.3,
        "carbs": 23.0,
        "category": "Фрукты"
    },
    {
        "id": 95,
        "name": "Апельсин",
        "cal": 43,
        "protein": 0.9,
        "fat": 0.1,
        "carbs": 9.4,
        "category": "Фрукты"
    },
    {
        "id": 96,
        "name": "Мандарин",
        "cal": 38,
        "protein": 0.6,
        "fat": 0.2,
        "carbs": 8.6,
        "category": "Фрукты"
    },
    {
        "id": 97,
        "name": "Грейпфрут",
        "cal": 42,
        "protein": 0.8,
        "fat": 0.1,
        "carbs": 10.0,
        "category": "Фрукты"
    },
    {
        "id": 98,
        "name": "Груша",
        "cal": 57,
        "protein": 0.4,
        "fat": 0.1,
        "carbs": 15.0,
        "category": "Фрукты"
    },
    {
        "id": 99,
        "name": "Виноград",
        "cal": 67,
        "protein": 0.6,
        "fat": 0.2,
        "carbs": 17.0,
        "category": "Фрукты"
    },
    {
        "id": 100,
        "name": "Персик",
        "cal": 39,
        "protein": 0.9,
        "fat": 0.3,
        "carbs": 9.5,
        "category": "Фрукты"
    },
    {
        "id": 101,
        "name": "Слива",
        "cal": 46,
        "protein": 0.7,
        "fat": 0.3,
        "carbs": 11.0,
        "category": "Фрукты"
    },
    {
        "id": 102,
        "name": "Клубника",
        "cal": 32,
        "protein": 0.7,
        "fat": 0.3,
        "carbs": 7.7,
        "category": "Фрукты"
    },
    {
        "id": 103,
        "name": "Малина",
        "cal": 52,
        "protein": 1.2,
        "fat": 0.7,
        "carbs": 11.0,
        "category": "Фрукты"
    },
    {
        "id": 104,
        "name": "Черника",
        "cal": 57,
        "protein": 0.7,
        "fat": 0.3,
        "carbs": 14.0,
        "category": "Фрукты"
    },
    {
        "id": 105,
        "name": "Арбуз",
        "cal": 30,
        "protein": 0.6,
        "fat": 0.2,
        "carbs": 7.6,
        "category": "Фрукты"
    },
    {
        "id": 106,
        "name": "Дыня",
        "cal": 33,
        "protein": 0.6,
        "fat": 0.2,
        "carbs": 8.0,
        "category": "Фрукты"
    },
    {
        "id": 107,
        "name": "Ананас",
        "cal": 50,
        "protein": 0.5,
        "fat": 0.1,
        "carbs": 13.0,
        "category": "Фрукты"
    },
    {
        "id": 108,
        "name": "Манго",
        "cal": 65,
        "protein": 0.5,
        "fat": 0.3,
        "carbs": 17.0,
        "category": "Фрукты"
    },
    {
        "id": 109,
        "name": "Авокадо",
        "cal": 160,
        "protein": 2.0,
        "fat": 15.0,
        "carbs": 9.0,
        "category": "Фрукты"
    },
    {
        "id": 110,
        "name": "Киви",
        "cal": 61,
        "protein": 1.1,
        "fat": 0.5,
        "carbs": 15.0,
        "category": "Фрукты"
    },
    {
        "id": 111,
        "name": "Хурма",
        "cal": 70,
        "protein": 0.5,
        "fat": 0.3,
        "carbs": 18.0,
        "category": "Фрукты"
    },
    {
        "id": 112,
        "name": "Гранат",
        "cal": 83,
        "protein": 1.7,
        "fat": 1.2,
        "carbs": 19.0,
        "category": "Фрукты"
    },
    {
        "id": 113,
        "name": "Финики",
        "cal": 282,
        "protein": 2.5,
        "fat": 0.4,
        "carbs": 75.0,
        "category": "Фрукты"
    },
    {
        "id": 114,
        "name": "Орехи грецкие",
        "cal": 654,
        "protein": 15.0,
        "fat": 65.0,
        "carbs": 14.0,
        "category": "Орехи"
    },
    {
        "id": 115,
        "name": "Миндаль",
        "cal": 579,
        "protein": 21.0,
        "fat": 50.0,
        "carbs": 22.0,
        "category": "Орехи"
    },
    {
        "id": 116,
        "name": "Кешью",
        "cal": 553,
        "protein": 18.0,
        "fat": 44.0,
        "carbs": 30.0,
        "category": "Орехи"
    },
    {
        "id": 117,
        "name": "Фундук",
        "cal": 628,
        "protein": 15.0,
        "fat": 61.0,
        "carbs": 17.0,
        "category": "Орехи"
    },
    {
        "id": 118,
        "name": "Арахис",
        "cal": 567,
        "protein": 26.0,
        "fat": 49.0,
        "carbs": 16.0,
        "category": "Орехи"
    },
    {
        "id": 119,
        "name": "Фисташки",
        "cal": 562,
        "protein": 20.0,
        "fat": 45.0,
        "carbs": 28.0,
        "category": "Орехи"
    },
    {
        "id": 120,
        "name": "Семена подсолнечника",
        "cal": 584,
        "protein": 21.0,
        "fat": 51.0,
        "carbs": 20.0,
        "category": "Орехи"
    },
    {
        "id": 121,
        "name": "Семена тыквы",
        "cal": 559,
        "protein": 30.0,
        "fat": 49.0,
        "carbs": 11.0,
        "category": "Орехи"
    },
    {
        "id": 122,
        "name": "Семена чиа",
        "cal": 486,
        "protein": 17.0,
        "fat": 31.0,
        "carbs": 42.0,
        "category": "Орехи"
    },
    {
        "id": 123,
        "name": "Арахисовая паста",
        "cal": 588,
        "protein": 25.0,
        "fat": 50.0,
        "carbs": 20.0,
        "category": "Орехи"
    },
    {
        "id": 124,
        "name": "Оливковое масло",
        "cal": 884,
        "protein": 0.0,
        "fat": 100.0,
        "carbs": 0.0,
        "category": "Масла"
    },
    {
        "id": 125,
        "name": "Подсолнечное масло",
        "cal": 884,
        "protein": 0.0,
        "fat": 100.0,
        "carbs": 0.0,
        "category": "Масла"
    },
    {
        "id": 126,
        "name": "Кокосовое масло",
        "cal": 892,
        "protein": 0.0,
        "fat": 100.0,
        "carbs": 0.0,
        "category": "Масла"
    },
    {
        "id": 127,
        "name": "Мёд",
        "cal": 304,
        "protein": 0.3,
        "fat": 0.0,
        "carbs": 82.0,
        "category": "Сладкое"
    },
    {
        "id": 128,
        "name": "Сахар",
        "cal": 387,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 100.0,
        "category": "Сладкое"
    },
    {
        "id": 129,
        "name": "Шоколад тёмный 70%",
        "cal": 598,
        "protein": 8.0,
        "fat": 43.0,
        "carbs": 46.0,
        "category": "Сладкое"
    },
    {
        "id": 130,
        "name": "Шоколад молочный",
        "cal": 535,
        "protein": 8.0,
        "fat": 30.0,
        "carbs": 60.0,
        "category": "Сладкое"
    },
    {
        "id": 131,
        "name": "Мороженое",
        "cal": 207,
        "protein": 3.5,
        "fat": 11.0,
        "carbs": 24.0,
        "category": "Сладкое"
    },
    {
        "id": 132,
        "name": "Протеин сывороточный",
        "cal": 370,
        "protein": 75.0,
        "fat": 4.0,
        "carbs": 8.0,
        "category": "Спортпит"
    },
    {
        "id": 133,
        "name": "Протеин казеиновый",
        "cal": 360,
        "protein": 78.0,
        "fat": 2.0,
        "carbs": 7.0,
        "category": "Спортпит"
    },
    {
        "id": 134,
        "name": "Гейнер",
        "cal": 380,
        "protein": 30.0,
        "fat": 2.0,
        "carbs": 60.0,
        "category": "Спортпит"
    },
    {
        "id": 135,
        "name": "Молоко овсяное",
        "cal": 45,
        "protein": 1.0,
        "fat": 1.5,
        "carbs": 6.5,
        "category": "Напитки"
    },
    {
        "id": 136,
        "name": "Молоко миндальное",
        "cal": 17,
        "protein": 0.6,
        "fat": 1.1,
        "carbs": 1.4,
        "category": "Напитки"
    },
    {
        "id": 137,
        "name": "Молоко соевое",
        "cal": 54,
        "protein": 3.3,
        "fat": 1.8,
        "carbs": 6.3,
        "category": "Напитки"
    },
    {
        "id": 138,
        "name": "Сок апельсиновый",
        "cal": 45,
        "protein": 0.7,
        "fat": 0.2,
        "carbs": 10.4,
        "category": "Напитки"
    },
    {
        "id": 139,
        "name": "Сок яблочный",
        "cal": 46,
        "protein": 0.1,
        "fat": 0.1,
        "carbs": 11.3,
        "category": "Напитки"
    },
    {
        "id": 140,
        "name": "Борщ",
        "cal": 50,
        "protein": 2.5,
        "fat": 2.0,
        "carbs": 5.5,
        "category": "Готовые блюда"
    },
    {
        "id": 141,
        "name": "Котлета",
        "cal": 220,
        "protein": 15.0,
        "fat": 14.0,
        "carbs": 8.0,
        "category": "Готовые блюда"
    },
    {
        "id": 142,
        "name": "Пельмени",
        "cal": 275,
        "protein": 11.0,
        "fat": 11.0,
        "carbs": 32.0,
        "category": "Готовые блюда"
    },
    {
        "id": 143,
        "name": "Вареники",
        "cal": 213,
        "protein": 8.0,
        "fat": 5.0,
        "carbs": 35.0,
        "category": "Готовые блюда"
    },
    {
        "id": 144,
        "name": "Блины",
        "cal": 233,
        "protein": 6.0,
        "fat": 9.0,
        "carbs": 33.0,
        "category": "Готовые блюда"
    },
    {
        "id": 145,
        "name": "Омлет",
        "cal": 184,
        "protein": 12.0,
        "fat": 14.0,
        "carbs": 2.0,
        "category": "Готовые блюда"
    },
    {
        "id": 146,
        "name": "Суши ролл",
        "cal": 150,
        "protein": 6.0,
        "fat": 3.5,
        "carbs": 24.0,
        "category": "Готовые блюда"
    },
    {
        "id": 147,
        "name": "Шаурма",
        "cal": 245,
        "protein": 14.0,
        "fat": 12.0,
        "carbs": 22.0,
        "category": "Готовые блюда"
    },
    {
        "id": 148,
        "name": "Картошка фри",
        "cal": 312,
        "protein": 3.5,
        "fat": 15.0,
        "carbs": 41.0,
        "category": "Готовые блюда"
    },
    {
        "id": 149,
        "name": "Каша овсяная на воде",
        "cal": 88,
        "protein": 3.0,
        "fat": 1.7,
        "carbs": 15.0,
        "category": "Готовые блюда"
    },
    {
        "id": 150,
        "name": "Каша овсяная на молоке",
        "cal": 135,
        "protein": 5.0,
        "fat": 4.5,
        "carbs": 20.0,
        "category": "Готовые блюда"
    },
    {
        "id": 151,
        "name": "Творожная запеканка",
        "cal": 160,
        "protein": 14.0,
        "fat": 6.0,
        "carbs": 12.0,
        "category": "Готовые блюда"
    },
    {
        "id": 152,
        "name": "Салат Оливье",
        "cal": 198,
        "protein": 8.0,
        "fat": 15.0,
        "carbs": 10.0,
        "category": "Готовые блюда"
    },
    {
        "id": 153,
        "name": "Цезарь с курицей",
        "cal": 179,
        "protein": 14.0,
        "fat": 11.0,
        "carbs": 7.0,
        "category": "Готовые блюда"
    },
    {
        "id": 154,
        "name": "Гречка с курицей",
        "cal": 135,
        "protein": 13.0,
        "fat": 2.5,
        "carbs": 17.0,
        "category": "Готовые блюда"
    },
    {
        "id": 155,
        "name": "Паста болоньезе",
        "cal": 185,
        "protein": 11.0,
        "fat": 7.0,
        "carbs": 21.0,
        "category": "Готовые блюда"
    },
    {
        "id": 156,
        "name": "Плов",
        "cal": 220,
        "protein": 9.0,
        "fat": 9.0,
        "carbs": 28.0,
        "category": "Готовые блюда"
    },
    {
        "id": 157,
        "name": "Стейк говяжий",
        "cal": 271,
        "protein": 26.0,
        "fat": 18.0,
        "carbs": 0.0,
        "category": "Готовые блюда"
    },
    {
        "id": 158,
        "name": "Куриный гриль",
        "cal": 165,
        "protein": 29.0,
        "fat": 5.0,
        "carbs": 0.0,
        "category": "Готовые блюда"
    },
    {
        "id": 159,
        "name": "Тефтели",
        "cal": 194,
        "protein": 14.0,
        "fat": 12.0,
        "carbs": 9.0,
        "category": "Готовые блюда"
    },
    {
        "id": 160,
        "name": "Творог с ягодами",
        "cal": 140,
        "protein": 16.0,
        "fat": 5.0,
        "carbs": 8.0,
        "category": "Готовые блюда"
    }
]

def get_user_id():
    return request.headers.get("X-User-Id", "default")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def calc_macros_from_goal(profile):
    """Рассчитывает КБЖУ на основе цели пользователя"""
    goal = profile.get("goal", 2000)
    goal_type = profile.get("goal_type", "maintain")
    weight = float(profile.get("weight", 70))

    if goal_type == "lose":
        # Похудение: высокий белок, мало углеводов, умеренный жир
        protein = round(weight * 2.0)   # 2г на кг
        fat = round(weight * 0.8)       # 0.8г на кг
        carbs = round((goal - protein*4 - fat*9) / 4)
    elif goal_type == "gain_weight":
        # Набор веса: профицит, умеренный белок
        protein = round(weight * 1.5)
        fat = round(weight * 1.0)
        carbs = round((goal - protein*4 - fat*9) / 4)
    elif goal_type == "muscle":
        # Набор мышц: очень высокий белок, много углеводов
        protein = round(weight * 2.2)
        fat = round(weight * 0.8)
        carbs = round((goal - protein*4 - fat*9) / 4)
    else:
        # Поддержание: баланс
        protein = round(weight * 1.6)
        fat = round(weight * 0.9)
        carbs = round((goal - protein*4 - fat*9) / 4)

    carbs = max(carbs, 50)  # минимум 50г углеводов
    return {"protein": protein, "fat": fat, "carbs": carbs}

def calc_meal_distribution(profile):
    """Рассчитывает распределение калорий по приёмам пищи на основе профиля"""
    goal = profile.get("goal", 2000)
    goal_type = profile.get("goal_type", "maintain")
    activity = float(profile.get("activity", 1.55))

    if goal_type == "lose":
        # Похудение — плотный завтрак, умеренный обед, лёгкий ужин
        dist = {"Завтрак": 0.30, "Обед": 0.35, "Ужин": 0.25, "Перекус": 0.10}
    elif goal_type == "gain_weight":
        # Набор веса — много еды равномерно
        dist = {"Завтрак": 0.25, "Обед": 0.35, "Ужин": 0.30, "Перекус": 0.10}
    elif goal_type == "muscle":
        # Набор мышц — много на завтрак и обед, перекус важен
        dist = {"Завтрак": 0.28, "Обед": 0.35, "Ужин": 0.25, "Перекус": 0.12}
    else:
        # Поддержание
        dist = {"Завтрак": 0.25, "Обед": 0.35, "Ужин": 0.30, "Перекус": 0.10}

    if activity >= 1.725:
        dist["Обед"] = min(dist["Обед"] + 0.05, 0.40)
        dist["Ужин"] = max(dist["Ужин"] - 0.05, 0.20)

    return {k: round(v * goal) for k, v in dist.items()}

def update_streak(user_id, conn):
    cur = conn.cursor()
    today = today_str()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    cur.execute("SELECT * FROM streaks WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO streaks (user_id, current_streak, longest_streak, freezes, last_logged_date) VALUES (%s,1,1,2,%s)", (user_id, today))
    else:
        last = row["last_logged_date"]
        current = row["current_streak"]
        longest = row["longest_streak"]
        freezes = row["freezes"]
        if last == today:
            pass
        elif last == yesterday:
            current += 1
            longest = max(longest, current)
            cur.execute("UPDATE streaks SET current_streak=%s, longest_streak=%s, last_logged_date=%s WHERE user_id=%s", (current, longest, today, user_id))
        else:
            days_missed = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(last, "%Y-%m-%d")).days - 1 if last else 999
            if days_missed <= freezes and freezes > 0:
                freezes -= days_missed
                current += 1
                longest = max(longest, current)
                cur.execute("UPDATE streaks SET current_streak=%s, longest_streak=%s, freezes=%s, last_logged_date=%s WHERE user_id=%s", (current, longest, freezes, today, user_id))
            else:
                cur.execute("UPDATE streaks SET current_streak=1, last_logged_date=%s WHERE user_id=%s", (today, user_id))
    conn.commit()
    cur.close()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/foods")
def get_foods():
    q = request.args.get("q", "").lower()
    cat = request.args.get("category", "")

    # Если есть поисковый запрос — ищем в обеих таблицах
    if q:
        # Словарь русско-английских переводов для поиска
        RU_EN = {
            'шоколад':'chocolate','молоко':'milk','хлеб':'bread','курица':'chicken',
            'говядина':'beef','свинина':'pork','рыба':'fish','яйцо':'egg','яйца':'egg',
            'сыр':'cheese','йогурт':'yogurt','творог':'cottage','кефир':'kefir',
            'масло':'butter oil','сахар':'sugar','мёд':'honey','мед':'honey',
            'овсянка':'oatmeal oat','рис':'rice','гречка':'buckwheat','макароны':'pasta',
            'картошка':'potato','картофель':'potato','помидор':'tomato','огурец':'cucumber',
            'яблоко':'apple','банан':'banana','апельсин':'orange','клубника':'strawberry',
            'орехи':'nuts','миндаль':'almond','арахис':'peanut','кешью':'cashew',
            'кофе':'coffee','чай':'tea','сок':'juice','вода':'water','пиво':'beer',
            'вино':'wine','мороженое':'ice cream','торт':'cake','печенье':'cookie biscuit',
            'пицца':'pizza','суши':'sushi','бургер':'burger','чипсы':'chips crisps',
            'протеин':'protein whey','гейнер':'gainer','батончик':'bar',
            'авокадо':'avocado','лосось':'salmon','тунец':'tuna','креветки':'shrimp',
            'капуста':'cabbage','морковь':'carrot','лук':'onion','чеснок':'garlic',
            'виноград':'grape','персик':'peach','слива':'plum','черника':'blueberry',
            'колбаса':'sausage','ветчина':'ham','бекон':'bacon','сосиски':'hotdog sausage',
            'кола':'cola','спрайт':'sprite','фанта':'fanta','энергетик':'energy red bull',
            'снэкс':'snacks','мюсли':'muesli granola','хлопья':'flakes cereal',
        }
        
        q_lower = q.lower()
        search_terms = [q_lower]
        
        # Если запрос на русском — добавляем английский перевод
        if any('Ѐ' <= c <= 'ӿ' for c in q_lower):
            for ru, en in RU_EN.items():
                if ru in q_lower or q_lower in ru:
                    search_terms.extend(en.split())
                    break

        conn = get_db()
        cur = conn.cursor()
        
        # Ищем по всем вариантам
        conditions = " OR ".join(["LOWER(name) LIKE %s"] * len(search_terms))
        params = [f"%{t}%" for t in search_terms]
        sql = f"SELECT id+100000 as id, name, cal, protein, fat, carbs, category FROM custom_foods WHERE ({conditions})"
        if cat:
            sql += " AND category=%s"
            params.append(cat)
        sql += " ORDER BY CASE WHEN LOWER(name) LIKE %s THEN 0 ELSE 1 END, name LIMIT 100"
        params.append(f"%{q_lower}%")
        
        cur.execute(sql, params)
        db_results = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()

        # Добавляем из встроенной базы
        local = [f for f in FOODS_DB if q_lower in f["name"].lower()]
        if cat:
            local = [f for f in local if f.get("category") == cat]

        # Объединяем: сначала локальные, потом из БД
        seen = {f["name"].lower() for f in local}
        for f in db_results:
            if f["name"].lower() not in seen:
                local.append(f)
                seen.add(f["name"].lower())
        return jsonify(local[:100])

    # Без запроса — показываем из custom_foods если есть категория, иначе встроенные
    if cat:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id+100000 as id, name, cal, protein, fat, carbs, category 
            FROM custom_foods WHERE category=%s ORDER BY name LIMIT 200
        """, (cat,))
        db_results = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        local = [f for f in FOODS_DB if f.get("category") == cat]
        seen = {f["name"].lower() for f in local}
        for f in db_results:
            if f["name"].lower() not in seen:
                local.append(f)
                seen.add(f["name"].lower())
        return jsonify(local)
    
    result = FOODS_DB
    return jsonify(result)

@app.route("/api/foods/categories")
def get_categories():
    # Фиксированный порядок категорий
    ORDERED_CATS = [
        "Мясо", "Рыба", "Молочные", "Крупы", "Хлеб", "Овощи", "Фрукты",
        "Орехи", "Масла", "Сладкое", "Снеки", "Напитки", "Алкоголь",
        "Спортпит", "Завтраки", "Соусы", "Заморозка", "Готовые блюда",
        "Фастфуд", "Пицца", "Японская кухня", "Кофейни", "ВкусВилл",
        "Молочные бренды", "Детское питание", "Другое"
    ]
    conn = get_db()
    cur = conn.cursor()
    # Берём только категории у которых есть продукты
    cur.execute("""
        SELECT DISTINCT category FROM custom_foods 
        WHERE category IS NOT NULL AND category != ''
        UNION
        SELECT DISTINCT category FROM (VALUES %s) AS t(category)
    """ % ",".join(f"('{c}')" for c in set(f["category"] for f in FOODS_DB)))
    existing = set(r["category"] for r in cur.fetchall())
    cur.close()
    conn.close()
    # Возвращаем только те что есть в базе в правильном порядке
    result = [c for c in ORDERED_CATS if c in existing]
    # Добавляем оставшиеся которых нет в списке
    for c in existing:
        if c not in result:
            result.append(c)
    return jsonify(result)

@app.route("/api/diary", methods=["GET"])
def get_diary():
    user_id = get_user_id()
    date = request.args.get("date", today_str())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM diary WHERE user_id=%s AND date=%s ORDER BY id", (user_id, date))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/diary", methods=["POST"])
def add_entry():
    user_id = get_user_id()
    body = request.json
    entry_id = int(datetime.now().timestamp() * 1000)
    date = today_str()
    conn = get_db()
    cur = conn.cursor()

    if body.get("food_id") == -1:
        # Продукт из штрихкода — данные уже посчитаны
        cur.execute("INSERT INTO diary (id,user_id,date,name,grams,meal_type,cal,protein,fat,carbs) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (entry_id, user_id, date,
             body.get("name","Продукт"), float(body.get("grams",100)),
             body.get("meal_type","Обед"),
             int(body.get("cal",0)), float(body.get("protein",0)),
             float(body.get("fat",0)), float(body.get("carbs",0))))
    elif body.get("food_source") == "custom":
        # Продукт из custom_foods
        conn2 = get_db()
        cur2 = conn2.cursor()
        cur2.execute("SELECT * FROM custom_foods WHERE id=%s", (body["food_id"],))
        food = cur2.fetchone()
        cur2.close(); conn2.close()
        if not food:
            cur.close(); conn.close()
            return jsonify({"error": "Food not found"}), 404
        grams = float(body["grams"])
        cur.execute("INSERT INTO diary (id,user_id,date,name,grams,meal_type,cal,protein,fat,carbs) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (entry_id, user_id, date, food["name"], grams, body.get("meal_type","Обед"),
             round(food["cal"]*grams/100), round(food["protein"]*grams/100,1),
             round(food["fat"]*grams/100,1), round(food["carbs"]*grams/100,1)))
    else:
        food = next((f for f in FOODS_DB if f["id"] == body["food_id"]), None)
        if not food:
            cur.close(); conn.close()
            return jsonify({"error": "Food not found"}), 404
        grams = float(body["grams"])
        cur.execute("INSERT INTO diary (id,user_id,date,name,grams,meal_type,cal,protein,fat,carbs) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (entry_id, user_id, date, food["name"], grams, body.get("meal_type","Обед"),
             round(food["cal"]*grams/100), round(food["protein"]*grams/100,1),
             round(food["fat"]*grams/100,1), round(food["carbs"]*grams/100,1)))

    conn.commit()
    update_streak(user_id, conn)
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/diary/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM diary WHERE id=%s AND user_id=%s", (entry_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/profile", methods=["GET"])
def get_profile():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT data FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify(row["data"])
    # Первый вход — сохраняем дату
    default = {"goal":2000,"protein_goal":150,"fat_goal":70,"carbs_goal":250,"joined_date":today_str()}
    return jsonify(default)

@app.route("/api/profile", methods=["POST"])
def save_profile():
    user_id = get_user_id()
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    # Если joined_date уже есть — не перезаписываем
    cur.execute("SELECT data FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if row and row["data"].get("joined_date") and not data.get("joined_date"):
        data["joined_date"] = row["data"]["joined_date"]
    if not data.get("joined_date"):
        data["joined_date"] = today_str()
    cur.execute("INSERT INTO profiles (user_id,data) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET data=EXCLUDED.data",
        (user_id, json.dumps(data)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/meal_targets")
def get_meal_targets():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT data FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    profile = row["data"] if row else {}
    return jsonify(calc_meal_distribution(profile))

@app.route("/api/calc_macros")
def get_calc_macros():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT data FROM profiles WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    profile = row["data"] if row else {}
    return jsonify(calc_macros_from_goal(profile))

@app.route("/api/week_macros")
def get_week_macros():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COALESCE(SUM(protein),0) as total_protein,
            COALESCE(SUM(fat),0) as total_fat,
            COALESCE(SUM(carbs),0) as total_carbs,
            COUNT(DISTINCT date) as days
        FROM diary
        WHERE user_id=%s AND date >= (CURRENT_DATE - INTERVAL '7 days')::text
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    days = max(int(row["days"]), 1)
    return jsonify({
        "protein": round(float(row["total_protein"]) / days, 1),
        "fat": round(float(row["total_fat"]) / days, 1),
        "carbs": round(float(row["total_carbs"]) / days, 1),
        "days": int(row["days"])
    })

@app.route("/api/month")
def get_month():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, COALESCE(SUM(cal),0) as total_cal,
               COALESCE(SUM(protein),0) as total_protein,
               COALESCE(SUM(fat),0) as total_fat,
               COALESCE(SUM(carbs),0) as total_carbs
        FROM diary
        WHERE user_id=%s AND date >= (CURRENT_DATE - INTERVAL '30 days')::text
        GROUP BY date ORDER BY date
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/week")
def get_week():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    result = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cur.execute("SELECT COALESCE(SUM(cal),0) as total FROM diary WHERE user_id=%s AND date=%s", (user_id, date))
        row = cur.fetchone()
        result.append({"date":date,"day":(datetime.now()-timedelta(days=i)).strftime("%a"),"cal":int(row["total"])})
    cur.close()
    conn.close()
    return jsonify(result)

@app.route("/api/streak")
def get_streak():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM streaks WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"current_streak":0,"longest_streak":0,"freezes":2,"last_logged_date":""})

@app.route("/api/barcode/<barcode>")
def lookup_barcode(barcode):
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()

    # Сначала ищем в нашей базе
    cur.execute("SELECT * FROM custom_foods WHERE barcode=%s LIMIT 1", (barcode,))
    row = cur.fetchone()
    if row:
        d = dict(row)
        # Сохраняем в избранное пользователя
        cur.execute("INSERT INTO user_foods (user_id, food_id, food_source, created_at) VALUES (%s,%s,'custom',%s) ON CONFLICT DO NOTHING",
            (user_id, d['id'], datetime.now().isoformat()))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"found": True, "id": d['id'], "name": d['name'], "cal": d['cal'],
                        "protein": d['protein'], "fat": d['fat'], "carbs": d['carbs'], "barcode": barcode, "source": "db"})

    cur.close(); conn.close()

    # Ищем в Open Food Facts
    import urllib.request
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'KaloreiApp/1.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        if data.get('status') != 1:
            return jsonify({"found": False})
        p = data['product']
        n = p.get('nutriments', {})
        name = p.get('product_name_ru') or p.get('product_name') or 'Неизвестный продукт'
        cal = round(float(n.get('energy-kcal_100g') or n.get('energy_100g', 0) or 0))
        protein = round(float(n.get('proteins_100g', 0) or 0), 1)
        fat = round(float(n.get('fat_100g', 0) or 0), 1)
        carbs = round(float(n.get('carbohydrates_100g', 0) or 0), 1)

        # Сохраняем в нашу базу автоматически
        conn2 = get_db()
        cur2 = conn2.cursor()
        cur2.execute("""
            INSERT INTO custom_foods (name, cal, protein, fat, carbs, category, barcode, added_by, created_at)
            VALUES (%s,%s,%s,%s,%s,'Сканер',%s,%s,%s) RETURNING id
        """, (name, cal, protein, fat, carbs, barcode, user_id, datetime.now().isoformat()))
        new_id = cur2.fetchone()['id']
        # Добавляем в избранное пользователя
        cur2.execute("INSERT INTO user_foods (user_id, food_id, food_source, created_at) VALUES (%s,%s,'custom',%s)",
            (user_id, new_id, datetime.now().isoformat()))
        conn2.commit()
        cur2.close(); conn2.close()

        return jsonify({"found": True, "id": new_id, "name": name, "cal": cal,
                        "protein": protein, "fat": fat, "carbs": carbs, "barcode": barcode, "source": "off"})
    except Exception as e:
        return jsonify({"found": False, "error": str(e)})

@app.route("/api/custom_foods", methods=["GET"])
def get_custom_foods():
    """Все продукты из нашей расширенной базы"""
    user_id = get_user_id()
    q = request.args.get("q", "").lower()
    conn = get_db()
    cur = conn.cursor()
    if q:
        cur.execute("SELECT * FROM custom_foods WHERE LOWER(name) LIKE %s ORDER BY id DESC LIMIT 50", (f'%{q}%',))
    else:
        cur.execute("SELECT * FROM custom_foods ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/my_foods", methods=["GET"])
def get_my_foods():
    """Продукты которые пользователь сканировал или добавлял"""
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT cf.*, uf.created_at as scanned_at
        FROM user_foods uf
        JOIN custom_foods cf ON cf.id = uf.food_id
        WHERE uf.user_id = %s
        ORDER BY uf.created_at DESC
        LIMIT 50
    """, (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/custom_foods", methods=["POST"])
def add_custom_food():
    """Добавить свой продукт вручную"""
    user_id = get_user_id()
    body = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_foods (name, cal, protein, fat, carbs, category, added_by, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (body['name'], int(body['cal']), float(body['protein']), float(body['fat']),
          float(body['carbs']), body.get('category','Моё'), user_id, datetime.now().isoformat()))
    new_id = cur.fetchone()['id']
    cur.execute("INSERT INTO user_foods (user_id, food_id, food_source, created_at) VALUES (%s,%s,'custom',%s)",
        (user_id, new_id, datetime.now().isoformat()))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"ok": True, "id": new_id})

@app.route("/api/water", methods=["GET"])
def get_water():
    user_id = get_user_id()
    date = request.args.get("date", today_str())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) as total FROM water WHERE user_id=%s AND date=%s", (user_id, date))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"total": int(row["total"]), "goal": 2500})

@app.route("/api/water", methods=["POST"])
def add_water():
    user_id = get_user_id()
    body = request.json
    amount = int(body.get("amount", 250))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO water (user_id, date, amount, created_at)
        VALUES (%s, %s, %s, %s)
    """, (user_id, today_str(), amount, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/water/goal", methods=["POST"])
def set_water_goal():
    user_id = get_user_id()
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO water_goals (user_id, goal) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET goal=EXCLUDED.goal",
        (user_id, data.get("goal", 2500)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/weight", methods=["GET"])
def get_weight():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM weight_log WHERE user_id=%s ORDER BY date DESC LIMIT 30", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/weight", methods=["POST"])
def add_weight():
    user_id = get_user_id()
    body = request.json
    weight = float(body.get("weight", 0))
    date = body.get("date", today_str())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO weight_log (user_id, date, weight)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, date) DO UPDATE SET weight=EXCLUDED.weight
    """, (user_id, date, weight))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/weight/<date>", methods=["DELETE"])
def delete_weight(date):
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM weight_log WHERE user_id=%s AND date=%s", (user_id, date))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/activity", methods=["GET"])
def get_activity():
    user_id = get_user_id()
    date = request.args.get("date", today_str())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_log WHERE user_id=%s AND date=%s ORDER BY id", (user_id, date))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/activity", methods=["POST"])
def add_activity():
    user_id = get_user_id()
    body = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO activity_log (user_id, date, name, calories_burned, duration_minutes, activity_type, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (user_id, today_str(), body.get("name"), int(body.get("calories_burned",0)),
          body.get("duration_minutes"), body.get("activity_type","other"), datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/activity/<int:activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM activity_log WHERE id=%s AND user_id=%s", (activity_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/activity/week")
def get_activity_week():
    user_id = get_user_id()
    conn = get_db()
    cur = conn.cursor()
    result = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cur.execute("SELECT COALESCE(SUM(calories_burned),0) as total FROM activity_log WHERE user_id=%s AND date=%s", (user_id, date))
        row = cur.fetchone()
        result.append({"date": date, "burned": int(row["total"])})
    cur.close()
    conn.close()
    return jsonify(result)


@app.route("/api/analyze_photo", methods=["POST"])
def analyze_photo():
    """Анализ фото еды через Google Gemini Vision"""
    import base64, urllib.request
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return jsonify({"error": "Gemini API key not configured"}), 500
    
    body = request.json
    image_data = body.get("image")  # base64 строка
    if not image_data:
        return jsonify({"error": "No image provided"}), 400
    
    # Убираем префикс data:image/...;base64,
    if "," in image_data:
        image_data = image_data.split(",")[1]
    
    prompt = """Ты эксперт-диетолог. Посмотри на фото еды и определи:
1. Какие продукты/блюда на фото
2. Примерный вес каждого в граммах
3. Калории, белки, жиры, углеводы

Ответь ТОЛЬКО в формате JSON, без markdown, без лишнего текста:
{
  "items": [
    {"name": "Название блюда", "grams": 150, "cal": 200, "protein": 15.0, "fat": 8.0, "carbs": 20.0}
  ],
  "total": {"cal": 200, "protein": 15.0, "fat": 8.0, "carbs": 20.0},
  "description": "Краткое описание что на тарелке"
}"""

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
    }
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Парсим JSON из ответа
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        food_data = json.loads(text.strip())
        return jsonify({"ok": True, "data": food_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
