"""
Импорт российских продуктов из Open Food Facts.
Запуск: DATABASE_URL="..." python3 import_off_russia.py
"""
import psycopg2, os, urllib.request, json, time

DATABASE_URL = os.environ.get("DATABASE_URL")

def safe_float(val):
    try:
        v = float(str(val).replace(',','.'))
        return v if 0 <= v <= 9999 else 0.0
    except: return 0.0

def is_russian(text):
    return any('\u0400' <= c <= '\u04FF' for c in text)

CATEGORY_MAP = {
    'dairy':'Молочные','milk':'Молочные','yogurt':'Молочные','cheese':'Молочные',
    'meat':'Мясо','chicken':'Мясо','beef':'Мясо','sausage':'Мясо',
    'fish':'Рыба','seafood':'Рыба','salmon':'Рыба',
    'bread':'Хлеб','bakery':'Хлеб','biscuit':'Хлеб',
    'chocolate':'Сладкое','candy':'Сладкое','sweet':'Сладкое','cake':'Сладкое',
    'beverage':'Напитки','drink':'Напитки','juice':'Напитки','water':'Напитки','coffee':'Напитки',
    'snack':'Снеки','chip':'Снеки',
    'cereal':'Крупы','grain':'Крупы','rice':'Крупы','pasta':'Крупы','oat':'Крупы',
    'fruit':'Фрукты','vegetable':'Овощи',
    'nut':'Орехи','seed':'Орехи',
    'oil':'Масла','butter':'Масла',
    'sauce':'Соусы','condiment':'Соусы',
    'frozen':'Заморозка','pizza':'Пицца','soup':'Готовые блюда',
    'sport':'Спортпит','protein':'Спортпит',
    'alcohol':'Алкоголь','beer':'Алкоголь','wine':'Алкоголь',
    'baby':'Детское питание',
}

def get_category(cats):
    if not cats: return 'Другое'
    c = cats.lower()
    for k, v in CATEGORY_MAP.items():
        if k in c: return v
    return 'Другое'

def fetch_page(page):
    url = (f"https://world.openfoodfacts.org/cgi/search.pl"
           f"?action=process&tagtype_0=countries&tag_contains_0=contains&tag_0=en:russia"
           f"&json=1&page_size=100&page={page}&sort_by=unique_scans_n")
    req = urllib.request.Request(url, headers={'User-Agent': 'KaloreiApp/1.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def main():
    print("Подключаемся к базе...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT LOWER(name) FROM custom_foods")
    existing = set(r[0] for r in cur.fetchall())
    print(f"Уже в базе: {len(existing)}")

    added = 0
    page = 1
    total_pages = 336  # 33546 / 100

    while page <= total_pages:
        try:
            data = fetch_page(page)
            products = data.get('products', [])
            if not products:
                break

            for p in products:
                # Берём только продукты с русским названием
                name = p.get('product_name_ru', '').strip()
                if not name:
                    name = p.get('product_name', '').strip()
                
                if not name or not is_russian(name) or len(name) < 2 or len(name) > 150:
                    continue

                n = p.get('nutriments', {})
                cal = safe_float(n.get('energy-kcal_100g') or n.get('energy_100g', 0))
                if cal <= 0 or cal > 2000:
                    continue

                protein = safe_float(n.get('proteins_100g', 0))
                fat = safe_float(n.get('fat_100g', 0))
                carbs = safe_float(n.get('carbohydrates_100g', 0))
                barcode = p.get('code', '') or None
                cats = p.get('categories_tags', []) or []; category = get_category(' '.join(cats) if isinstance(cats, list) else str(cats))

                if name.lower() in existing:
                    continue

                cur.execute("""INSERT INTO custom_foods (name,cal,protein,fat,carbs,category,barcode,added_by,created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'off_russia','2026-01-01')""",
                    (name, round(cal), round(protein,1), round(fat,1), round(carbs,1), category, barcode))
                existing.add(name.lower())
                added += 1

            if added % 500 == 0 and added > 0:
                conn.commit()
                print(f"  ✓ Страница {page}/{total_pages} | добавлено: {added}")

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  Ошибка на странице {page}: {e}")
            time.sleep(2)
            page += 1
            continue

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM custom_foods")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"\n✅ Готово! Добавлено: {added}")
    print(f"📦 Всего в базе: {total:,}")

if __name__ == "__main__":
    main()
