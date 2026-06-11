"""
Скрипт імпорту балів з WorkProgress.xlsx у моделі WorkType та WorkPrice.

Запуск з кореня Django проєкту:
    python import_work_prices.py

Або через Django shell:
    python manage.py shell < import_work_prices.py
"""

import os
import sys
import django

# ── Django setup ──────────────────────────────────────────────────────────────
# Вкажи шлях до свого settings якщо запускаєш напряму
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flarken.settings')
django.setup()

import pandas as pd
from worklog.models import WorkType, WorkPrice
from warehouse.models import PhoneModel

EXCEL_PATH = 'WorkProgress.xlsx'
SHEET_NAME = 'Scores'

# ── Читаємо Excel ─────────────────────────────────────────────────────────────
df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, index_col=0)

# Прибираємо повністю порожні рядки і стовпці
df = df.dropna(how='all').dropna(axis=1, how='all')

print(f"📊 Знайдено: {len(df)} типів робіт, {len(df.columns)} моделей\n")

# ── Мапи назв моделей з Excel → PhoneModel у БД ───────────────────────────────
# Якщо назви в Excel не збігаються точно з БД — додай маппінг нижче
MODEL_NAME_MAP = {
    # 'назва в Excel': 'назва в БД',
    # Наприклад:
    # 'iphone 6Plus': 'iPhone 6 Plus',
}

# ── Лічильники для звіту ──────────────────────────────────────────────────────
created_work_types = 0
created_prices = 0
updated_prices = 0
skipped_models = set()
skipped_values = 0

# ── Кешуємо всі PhoneModel з БД ──────────────────────────────────────────────
all_phone_models = {m.name.lower().strip(): m for m in PhoneModel.objects.all()}

def find_phone_model(excel_name: str):
    """Шукає PhoneModel по назві з Excel (з маппінгом і fuzzy lower-case)."""
    mapped = MODEL_NAME_MAP.get(excel_name, excel_name)
    return all_phone_models.get(mapped.lower().strip())

# ── Основний імпорт ───────────────────────────────────────────────────────────
for work_name, row in df.iterrows():
    work_name = str(work_name).strip()
    if not work_name:
        continue

    work_type, wt_created = WorkType.objects.get_or_create(name=work_name)
    if wt_created:
        created_work_types += 1
        print(f"  ✅ Новий тип роботи: «{work_name}»")

    for model_name, points in row.items():
        model_name = str(model_name).strip()

        # Пропускаємо порожні/некоректні значення
        if pd.isna(points):
            continue
        try:
            points = float(points)
        except (ValueError, TypeError):
            skipped_values += 1
            continue

        phone_model = find_phone_model(model_name)
        if phone_model is None:
            skipped_models.add(model_name)
            continue

        price, price_created = WorkPrice.objects.update_or_create(
            work_type=work_type,
            phone_model=phone_model,
            defaults={'points': points}
        )
        if price_created:
            created_prices += 1
        else:
            updated_prices += 1

# ── Звіт ─────────────────────────────────────────────────────────────────────
print("\n" + "─" * 50)
print(f"✅ Нових типів робіт створено:  {created_work_types}")
print(f"✅ Нових цін додано:            {created_prices}")
print(f"🔄 Існуючих цін оновлено:       {updated_prices}")
print(f"⚠️  Пропущено некоректних значень: {skipped_values}")

if skipped_models:
    print(f"\n❌ Моделі НЕ знайдено в БД ({len(skipped_models)} шт.) — додай у MODEL_NAME_MAP:")
    for name in sorted(skipped_models):
        print(f"   '{name}': '',")
else:
    print("\n🎉 Всі моделі знайдено в БД!")