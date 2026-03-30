from telebot import types
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flarken.settings")

django.setup()

from warehouse.models import Part, PhoneModel, Color, PartType, ChipType, Supplier, PhoneModelRange


def main_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    part_types_list = PartType.objects.all()

    row = []
    for part_type in part_types_list:
        button = types.KeyboardButton(f'{part_type.name}')
        row.append(button)

        if len(row) == 4:
            markup.row(*row)
            row = []

    if row:
        markup.row(*row)

    return markup


def actions_for_part(message_text):
    part = PartType.objects.get(name=message_text)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Кількість', callback_data=f'list_of_part_types:{part.pk}'),
        types.InlineKeyboardButton('Закупка', callback_data=f'purchase_list_part_type_and_supplier:{part.pk}'),
    )
    markup.add(types.InlineKeyboardButton('Взяти', callback_data=f'write_off:start:{part.pk}'))
    return markup


def purchase_list(part_type_id=None):
    markup = types.InlineKeyboardMarkup()
    suppliers = Supplier.objects.all()

    if part_type_id is None:
        row = [types.InlineKeyboardButton(supplier.name, callback_data=f'supplier:{supplier.pk}:') for supplier in suppliers]
        markup.add(*row)
    else:
        buttons_list = [types.InlineKeyboardButton(
            supplier.name,
            callback_data=f'supplier:{supplier.pk}:{part_type_id}') for supplier in suppliers if
            Part.objects.filter(part_type_id=part_type_id, supplier_names__supplier_id=supplier.pk).exists()]
        markup.add(*buttons_list)

    return markup


# Функція для провірки того чи є в запчастині колір чи тип чіпа сенсора
def check_exists_color_or_chip_type(params):
    if PartType.objects.get(pk=params['part_type']).has_color:
        cct = Color.objects.filter(part__phone_models=params['phone_model'],
                                   part__part_type=params['part_type']).distinct()

        if len(cct) == 0:
            params['color'] = ''
            return params, ''
        return params, 'Колір'

    if PartType.objects.get(pk=params['part_type']).has_chip:
        cct = ChipType.objects.filter(part__phone_models=params['phone_model'],
                                      part__part_type=params['part_type']).distinct()

        if len(cct) == 0:
            params['chip_type'] = ''
            return params, ''
        return params, 'З чіпом чи без'

    return params, ''


def show_phone_model_range(part_type):
    markup = types.InlineKeyboardMarkup()

    row = [types.InlineKeyboardButton(item.name, callback_data=f'write_off:model_range:{item.pk}') for item in
           PhoneModelRange.objects.filter(phonemodel__supported_part_types=part_type).distinct().order_by('pk')]

    markup.add(*row, row_width=4)

    return markup


def show_phone_model(part_type, model_range):
    markup = types.InlineKeyboardMarkup()

    row = [types.InlineKeyboardButton(model.name, callback_data=f'write_off:model:{model.pk}') for model in
           PhoneModel.objects.filter(phone_model_range=model_range, supported_part_types=part_type).distinct()]
    markup.add(*row)

    return markup


def show_color_or_chip_type(part_type, phone_model, **kwargs):
    markup = types.InlineKeyboardMarkup()

    colors = Color.objects.filter(part__phone_models=phone_model, part__part_type=part_type).distinct()

    if colors.exists():
        row = [types.InlineKeyboardButton(c.name, callback_data=f'write_off:color:{c.name}') for c in colors]
        markup.add(*row)
        return markup

    chips = ChipType.objects.filter(part__phone_models=phone_model, part__part_type=part_type).distinct()

    if chips.exists():
        row = [types.InlineKeyboardButton(c.name, callback_data=f'write_off:chip:{c.name}') for c in chips]
        markup.add(*row)
        return markup

    return None


def show_quantity():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('1', callback_data=f'write_off:quantity:{1}'))
    row = [types.InlineKeyboardButton(f'{i}', callback_data=f'write_off:quantity:{i}') for i in range(2, 10)]
    markup.add(*row)
    return markup

# параметром передати запчастину яка списалась
def write_off_dep_part(dep_part):
    # state = {
    #     'part_type': data['part_type'],
    #     'phone_model': data['phone_model'],
    #     'quantity': data['quantity'],
    # }
    part_type = PartType.objects.get(pk=dep_part['part_type'])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'Списати деталь {part_type.name}', callback_data=f'write_off_dep_part'))
    return markup



# def other_key(user):
#     users = iphone_db.select_hose()
#     markup = types.InlineKeyboardMarkup()
#     work_progress = types.InlineKeyboardButton('WorkProgress',
#                                                switch_inline_query_current_chat=f'_wp\n{work_progress_db.select_work_progress(user)}')
#     data_from_bot = types.InlineKeyboardButton('Скинути дані з бота', callback_data='reset-data-from-bot')
#     null_wp = types.InlineKeyboardButton('Обнулити дані WP', callback_data='reset_data_user')
#     reset_db_all = types.InlineKeyboardButton('Ресет бази шлангів', callback_data='reset_all_data_user')
#     markup.row(work_progress)
#     markup.add(null_wp, data_from_bot)
#     user_confirm_list = [users['Назар']]  # Список з користувачами адмінами
#     if user in user_confirm_list:
#         markup.row(reset_db_all)
#     return markup
#
#
# def confirm():
#     markup = types.InlineKeyboardMarkup()
#     markup.add(types.InlineKeyboardButton('Відправити в чат \U0001F680', callback_data='confirm_button'))
#     return markup
