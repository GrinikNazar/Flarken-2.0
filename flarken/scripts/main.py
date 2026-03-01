import os
import sys
import django
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flarken.settings")

django.setup()

from warehouse.models import Part, PhoneModel, Color, PartType


def import_excel():
    df = pd.read_excel('data.xlsx')

    phone_models = {p.name: p for p in PhoneModel.objects.all()}
    part_types = {p.name: p for p in PartType.objects.all()}
    colors = {c.name: c for c in Color.objects.all()}

    for index, row in df.iterrows():
        phone_model = row['Модель'].strip()
        part_type = 'Кришка'
        color = row['Колір'].strip()
        quantity = row['Наявність']
        min_quantity = row['Мінімум']
        max_quantity = row['Максимум']

        phone_model = phone_models[phone_model]
        part_type = part_types[part_type]
        color = colors.get(color)
        part = Part(
            part_type = part_type,
            color = color,
            current_quantity = quantity,
            min_quantity = min_quantity,
            max_quantity = max_quantity,
        )

        part.save()

        part.phone_models.add(phone_model)


if __name__ == '__main__':
    import_excel()