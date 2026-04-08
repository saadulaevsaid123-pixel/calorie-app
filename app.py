from flask import Flask, request, jsonify, send_from_directory
import json, os
from datetime import datetime, timedelta

app = Flask(__name__, static_folder="static")
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

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
    uid = request.headers.get("X-User-Id", "default")
    print(f"[DEBUG] User ID: {uid}")
    return uid

def get_user_file(user_id):
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_data(user_id):
    f = get_user_file(user_id)
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    return {"profile": {"goal":2000,"protein_goal":150,"fat_goal":70,"carbs_goal":250}, "diary":{}}

def save_data(user_id, data):
    with open(get_user_file(user_id), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)

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
    data = load_data(user_id)
    date = request.args.get("date", today_str())
    return jsonify(data["diary"].get(date, []))

@app.route("/api/diary", methods=["POST"])
def add_entry():
    user_id = get_user_id()
    data = load_data(user_id)
    body = request.json
    food = next((f for f in FOODS_DB if f["id"] == body["food_id"]), None)
    if not food:
        return jsonify({"error": "Food not found"}), 404
    grams = float(body["grams"])
    date = today_str()
    if date not in data["diary"]:
        data["diary"][date] = []
    entry = {
        "id": int(datetime.now().timestamp() * 1000),
        "name": food["name"],
        "grams": grams,
        "meal_type": body.get("meal_type", "Обед"),
        "cal": round(food["cal"] * grams / 100),
        "protein": round(food["protein"] * grams / 100, 1),
        "fat": round(food["fat"] * grams / 100, 1),
        "carbs": round(food["carbs"] * grams / 100, 1),
    }
    data["diary"][date].append(entry)
    save_data(user_id, data)
    return jsonify(entry)

@app.route("/api/diary/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    user_id = get_user_id()
    data = load_data(user_id)
    date = today_str()
    data["diary"][date] = [e for e in data["diary"].get(date, []) if e["id"] != entry_id]
    save_data(user_id, data)
    return jsonify({"ok": True})

@app.route("/api/profile", methods=["GET"])
def get_profile():
    user_id = get_user_id()
    return jsonify(load_data(user_id)["profile"])

@app.route("/api/profile", methods=["POST"])
def save_profile():
    user_id = get_user_id()
    data = load_data(user_id)
    data["profile"] = request.json
    save_data(user_id, data)
    return jsonify({"ok": True})

@app.route("/api/week")
def get_week():
    user_id = get_user_id()
    data = load_data(user_id)
    result = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        entries = data["diary"].get(date, [])
        result.append({
            "date": date,
            "day": (datetime.now() - timedelta(days=i)).strftime("%a"),
            "cal": sum(e["cal"] for e in entries)
        })
    return jsonify(result)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=True)
