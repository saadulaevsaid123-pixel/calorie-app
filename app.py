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
    {"id":1,"name":"Куриная грудка","cal":165,"protein":31.0,"fat":3.6,"carbs":0.0},
    {"id":2,"name":"Лосось","cal":208,"protein":20.0,"fat":13.0,"carbs":0.0},
    {"id":3,"name":"Говядина","cal":250,"protein":26.0,"fat":17.0,"carbs":0.0},
    {"id":4,"name":"Тунец конс.","cal":100,"protein":22.0,"fat":1.0,"carbs":0.0},
    {"id":5,"name":"Яйцо куриное","cal":155,"protein":13.0,"fat":11.0,"carbs":1.0},
    {"id":6,"name":"Творог 5%","cal":121,"protein":17.0,"fat":5.0,"carbs":2.7},
    {"id":7,"name":"Греческий йогурт","cal":97,"protein":10.0,"fat":5.0,"carbs":3.6},
    {"id":8,"name":"Молоко 2.5%","cal":52,"protein":2.8,"fat":2.5,"carbs":4.7},
    {"id":9,"name":"Сыр твёрдый","cal":380,"protein":25.0,"fat":30.0,"carbs":0.5},
    {"id":10,"name":"Овсянка","cal":350,"protein":12.0,"fat":6.0,"carbs":62.0},
    {"id":11,"name":"Рис варёный","cal":130,"protein":2.7,"fat":0.3,"carbs":28.0},
    {"id":12,"name":"Гречка варёная","cal":110,"protein":4.2,"fat":1.1,"carbs":21.0},
    {"id":13,"name":"Макароны варёные","cal":158,"protein":5.5,"fat":0.9,"carbs":31.0},
    {"id":14,"name":"Хлеб ржаной","cal":259,"protein":9.0,"fat":3.0,"carbs":48.0},
    {"id":15,"name":"Картофель варёный","cal":80,"protein":2.0,"fat":0.1,"carbs":17.0},
    {"id":16,"name":"Яблоко","cal":47,"protein":0.4,"fat":0.4,"carbs":10.0},
    {"id":17,"name":"Банан","cal":89,"protein":1.1,"fat":0.3,"carbs":23.0},
    {"id":18,"name":"Апельсин","cal":43,"protein":0.9,"fat":0.1,"carbs":9.4},
    {"id":19,"name":"Огурец","cal":15,"protein":0.7,"fat":0.1,"carbs":2.5},
    {"id":20,"name":"Помидор","cal":18,"protein":0.9,"fat":0.2,"carbs":3.5},
    {"id":21,"name":"Брокколи","cal":34,"protein":2.8,"fat":0.4,"carbs":7.0},
    {"id":22,"name":"Морковь","cal":41,"protein":0.9,"fat":0.2,"carbs":9.6},
    {"id":23,"name":"Авокадо","cal":160,"protein":2.0,"fat":15.0,"carbs":9.0},
    {"id":24,"name":"Оливковое масло","cal":884,"protein":0.0,"fat":100.0,"carbs":0.0},
    {"id":25,"name":"Орехи грецкие","cal":654,"protein":15.0,"fat":65.0,"carbs":14.0},
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
    """Поиск продукта по штрихкоду через Open Food Facts"""
    import urllib.request
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'KaloreiApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            import json as j
            data = j.loads(r.read())
        if data.get('status') != 1:
            return jsonify({"found": False})
        p = data['product']
        n = p.get('nutriments', {})
        name = p.get('product_name_ru') or p.get('product_name') or 'Неизвестный продукт'
        cal = round(float(n.get('energy-kcal_100g') or n.get('energy_100g', 0) or 0))
        protein = round(float(n.get('proteins_100g', 0) or 0), 1)
        fat = round(float(n.get('fat_100g', 0) or 0), 1)
        carbs = round(float(n.get('carbohydrates_100g', 0) or 0), 1)
        return jsonify({
            "found": True,
            "name": name,
            "cal": cal,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "barcode": barcode
        })
    except Exception as e:
        return jsonify({"found": False, "error": str(e)})

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


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
