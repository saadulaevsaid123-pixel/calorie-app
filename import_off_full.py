"""
Импорт из локального файла Open Food Facts.
Шаг 1: curl -L -o ~/calorie_app/off_products.csv.gz https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz
Шаг 2: DATABASE_URL="..." python3 import_off_full.py
"""
import psycopg2, os, csv, gzip, io, time
csv.field_size_limit(10**7)  # Fix for large fields in OFF dataset

DATABASE_URL = os.environ.get("DATABASE_URL")
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "off_products.csv.gz")

CATEGORY_MAP = {
    'dairy':'Молочные','milk':'Молочные','yogurt':'Молочные','cheese':'Молочные','cream':'Молочные',
    'meat':'Мясо','chicken':'Мясо','beef':'Мясо','pork':'Мясо','turkey':'Мясо','sausage':'Мясо',
    'fish':'Рыба','seafood':'Рыба','salmon':'Рыба','tuna':'Рыба','shrimp':'Рыба',
    'bread':'Хлеб','bakery':'Хлеб','biscuit':'Хлеб','cracker':'Хлеб','pastry':'Хлеб',
    'chocolate':'Сладкое','candy':'Сладкое','sweet':'Сладкое','confection':'Сладкое','cake':'Сладкое','cookie':'Сладкое',
    'beverage':'Напитки','drink':'Напитки','juice':'Напитки','water':'Напитки','coffee':'Напитки','tea':'Напитки','soda':'Напитки',
    'snack':'Снеки','chip':'Снеки','crisp':'Снеки','popcorn':'Снеки',
    'cereal':'Крупы','grain':'Крупы','rice':'Крупы','pasta':'Крупы','oat':'Крупы','legume':'Крупы','bean':'Крупы',
    'fruit':'Фрукты','vegetable':'Овощи',
    'nut':'Орехи','seed':'Орехи','almond':'Орехи','peanut':'Орехи',
    'oil':'Масла','butter':'Масла',
    'sauce':'Соусы','condiment':'Соусы','ketchup':'Соусы','mayonnaise':'Соусы',
    'frozen':'Заморозка','pizza':'Пицца','soup':'Готовые блюда','meal':'Готовые блюда',
}

def get_category(cats):
    if not cats: return 'Другое'
    c = cats.lower()
    for k, v in CATEGORY_MAP.items():
        if k in c: return v
    return 'Другое'

def safe_float(val):
    try:
        v = float(str(val).replace(',','.'))
        return v if 0 <= v <= 9999 else 0.0
    except: return 0.0

def import_full():
    if not os.path.exists(LOCAL_FILE):
        print(f"❌ Файл не найден: {LOCAL_FILE}")
        print("Сначала скачай:")
        print("curl -L -o ~/calorie_app/off_products.csv.gz https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz")
        return

    file_size = os.path.getsize(LOCAL_FILE) / 1024 / 1024
    print(f"✓ Файл найден: {file_size:.0f}MB")

    print("Подключаемся к базе данных...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS custom_foods (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, cal INTEGER NOT NULL,
        protein REAL NOT NULL, fat REAL NOT NULL, carbs REAL NOT NULL,
        category TEXT DEFAULT 'Другое', barcode TEXT, added_by TEXT, created_at TEXT
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cf_name ON custom_foods(LOWER(name))")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cf_barcode ON custom_foods(barcode) WHERE barcode IS NOT NULL")
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM custom_foods")
    already = cur.fetchone()[0]
    print(f"Уже в базе: {already:,} продуктов")

    print("Начинаем импорт...")
    added = 0
    skipped = 0
    batch = []
    BATCH = 2000
    start = time.time()

    with gzip.open(LOCAL_FILE, 'rt', encoding='utf-8', errors='replace') as gz:
        reader = csv.DictReader(gz, delimiter='\t')

        for i, row in enumerate(reader):
            try:
                name = (row.get('product_name_ru') or row.get('product_name') or '').strip()
                if not name or len(name) < 2 or len(name) > 150:
                    skipped += 1
                    continue

                cal = safe_float(row.get('energy-kcal_100g') or row.get('energy_100g') or 0)
                if cal <= 0 or cal > 2000:
                    skipped += 1
                    continue

                protein = safe_float(row.get('proteins_100g'))
                fat = safe_float(row.get('fat_100g'))
                carbs = safe_float(row.get('carbohydrates_100g'))
                barcode = (row.get('code') or '').strip() or None
                category = get_category(row.get('categories_tags') or row.get('categories') or '')

                batch.append((name, round(cal), round(protein,1), round(fat,1), round(carbs,1), category, barcode))

                if len(batch) >= BATCH:
                    cur.executemany("""
                        INSERT INTO custom_foods (name,cal,protein,fat,carbs,category,barcode,added_by,created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'off_full','2026-01-01')
                        ON CONFLICT DO NOTHING
                    """, batch)
                    conn.commit()
                    added += len(batch)
                    batch = []
                    elapsed = time.time() - start
                    rate = added / elapsed * 60
                    print(f"  ✓ {added:,} добавлено | строка {i:,} | {rate:.0f} прод/мин | {elapsed/60:.1f} мин")

            except csv.Error:
                skipped += 1
                continue
            except Exception:
                skipped += 1
                continue

    if batch:
        cur.executemany("""
            INSERT INTO custom_foods (name,cal,protein,fat,carbs,category,barcode,added_by,created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'off_full','2026-01-01')
            ON CONFLICT DO NOTHING
        """, batch)
        conn.commit()
        added += len(batch)

    cur.execute("SELECT COUNT(*) FROM custom_foods")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()

    elapsed = time.time() - start
    print(f"\n✅ Готово! Добавлено: {added:,} продуктов за {elapsed/60:.1f} минут")
    print(f"📦 Всего в базе: {total:,} продуктов")

if __name__ == "__main__":
    import_full()
