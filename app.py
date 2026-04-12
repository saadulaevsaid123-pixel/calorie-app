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
    conn.commit()
    cur.close()
    conn.close()

FOODS_DB = [
    {"id":1,  "name":"Куриная грудка",    "cal":165,"protein":31.0,"fat":3.6, "carbs":0.0},
    {"id":2,  "name":"Лосось",            "cal":208,"protein":20.0,"fat":13.0,"carbs":0.0},
    {"id":3,  "name":"Говядина",          "cal":250,"protein":26.0,"fat":17.0,"carbs":0.0},
    {"id":4,  "name":"Тунец конс.",       "cal":100,"protein":22.0,"fat":1.0, "carbs":0.0},
    {"id":5,  "name":"Яйцо куриное",      "cal":155,"protein":13.0,"fat":11.0,"carbs":1.0},
    {"id":6,  "name":"Творог 5%",         "cal":121,"protein":17.0,"fat":5.0, "carbs":2.7},
    {"id":7,  "name":"Греческий йогурт",  "cal":97, "protein":10.0,"fat":5.0, "carbs":3.6},
    {"id":8,  "name":"Молоко 2.5%",       "cal":52, "protein":2.8, "fat":2.5, "carbs":4.7},
    {"id":9,  "name":"Сыр твёрдый",       "cal":380,"protein":25.0,"fat":30.0,"carbs":0.5},
    {"id":10, "name":"Овсянка",           "cal":350,"protein":12.0,"fat":6.0, "carbs":62.0},
    {"id":11, "name":"Рис варёный",       "cal":130,"protein":2.7, "fat":0.3, "carbs":28.0},
    {"id":12, "name":"Гречка варёная",    "cal":110,"protein":4.2, "fat":1.1, "carbs":21.0},
    {"id":13, "name":"Макароны варёные",  "cal":158,"protein":5.5, "fat":0.9, "carbs":31.0},
    {"id":14, "name":"Хлеб ржаной",      "cal":259,"protein":9.0, "fat":3.0, "carbs":48.0},
    {"id":15, "name":"Картофель варёный", "cal":80, "protein":2.0, "fat":0.1, "carbs":17.0},
    {"id":16, "name":"Яблоко",           "cal":47, "protein":0.4, "fat":0.4, "carbs":10.0},
    {"id":17, "name":"Банан",            "cal":89, "protein":1.1, "fat":0.3, "carbs":23.0},
    {"id":18, "name":"Апельсин",         "cal":43, "protein":0.9, "fat":0.1, "carbs":9.4},
    {"id":19, "name":"Огурец",           "cal":15, "protein":0.7, "fat":0.1, "carbs":2.5},
    {"id":20, "name":"Помидор",          "cal":18, "protein":0.9, "fat":0.2, "carbs":3.5},
    {"id":21, "name":"Брокколи",         "cal":34, "protein":2.8, "fat":0.4, "carbs":7.0},
    {"id":22, "name":"Морковь",          "cal":41, "protein":0.9, "fat":0.2, "carbs":9.6},
    {"id":23, "name":"Авокадо",          "cal":160,"protein":2.0, "fat":15.0,"carbs":9.0},
    {"id":24, "name":"Оливковое масло",  "cal":884,"protein":0.0, "fat":100.0,"carbs":0.0},
    {"id":25, "name":"Орехи грецкие",    "cal":654,"protein":15.0,"fat":65.0,"carbs":14.0},
]

def get_user_id():
    return request.headers.get("X-User-Id", "default")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/foods")
def get_foods():
    q = request.args.get("q", "").lower()
    result = [f for f in FOODS_DB if q in f["name"].lower()] if q else FOODS_DB
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
    food = next((f for f in FOODS_DB if f["id"] == body["food_id"]), None)
    if not food:
        return jsonify({"error": "Food not found"}), 404
    grams = float(body["grams"])
    entry_id = int(datetime.now().timestamp() * 1000)
    date = today_str()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO diary (id, user_id, date, name, grams, meal_type, cal, protein, fat, carbs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        entry_id, user_id, date, food["name"], grams,
        body.get("meal_type", "Обед"),
        round(food["cal"] * grams / 100),
        round(food["protein"] * grams / 100, 1),
        round(food["fat"] * grams / 100, 1),
        round(food["carbs"] * grams / 100, 1),
    ))
    conn.commit()
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
    return jsonify({"goal":2000,"protein_goal":150,"fat_goal":70,"carbs_goal":250})

@app.route("/api/profile", methods=["POST"])
def save_profile():
    user_id = get_user_id()
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO profiles (user_id, data) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data
    """, (user_id, json.dumps(data)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})

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
        result.append({
            "date": date,
            "day": (datetime.now() - timedelta(days=i)).strftime("%a"),
            "cal": int(row["total"])
        })
    cur.close()
    conn.close()
    return jsonify(result)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
