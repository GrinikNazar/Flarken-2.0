import os
import sys
import django
import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flarken.settings")

django.setup()

from warehouse.models import Part, PhoneModel, Color, PartType, ChipType

sheet_name = 'Екран копія'

def import_excel():
    df = pd.read_excel('data.xlsx', sheet_name=sheet_name)

    phone_models = {p.name: p for p in PhoneModel.objects.all()}
    part_types = {p.name: p for p in PartType.objects.all()}
    colors = {c.name: c for c in Color.objects.all()}
    chip_type = {c.name: c for c in ChipType.objects.all()}

    for index, row in df.iterrows():
        phone_model = row['Модель'].strip()
        part_type = sheet_name
        try:
            color = row['Колір'].strip().title()
            color = colors[color]
        except Exception:
            color = None

        try:
            chip = row['Тип чіпа']
            chip_t = chip_type[chip]
        except Exception:
            chip_t = None

        quantity = row['Наявність']
        min_quantity = row['Мінімум']
        max_quantity = row['Максимум']

        models_list = [model.strip() for model in phone_model.split('|')]
        phone_model = [phone_models[model] for model in models_list]


        part_type = part_types[part_type]

        part = Part(
            part_type = part_type,
            color = color,
            current_quantity = quantity,
            min_quantity = min_quantity,
            max_quantity = max_quantity,
            chip_type=chip_t,
        )

        part.save()

        part.phone_models.add(*phone_model)


if __name__ == '__main__':
    import_excel()
