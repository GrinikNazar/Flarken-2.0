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

# TODO: проблема з відображенням всіх типів запчастин
def main_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    part_types_list = PartType.objects.all()

    row = []
    for part_type in part_types_list:
        button = types.KeyboardButton(f'{part_type.name}')
        if len(row) == 3:
            markup.row(*row)
            row = []
        else:
            row.append(button)
    else:
        markup.row(*row)

    return markup


def actions_for_part(message_text):
    part = PartType.objects.get(name=message_text)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Взяти', callback_data=f'write_off:{part.pk}'),
        types.InlineKeyboardButton('Кількість', callback_data=f'list_of_part_types:{part.pk}'),
        types.InlineKeyboardButton('Закупка', callback_data=f'purchase_list_part_type_and_supplier:{part.pk}'),
    )
    return markup


def purchase_list(part_type_id=None):
    markup = types.InlineKeyboardMarkup()
    suppliers = Supplier.objects.all()
    buttons_list = [types.InlineKeyboardButton(
        supplier.name,
        callback_data=f'supplier:{supplier.pk}:{part_type_id}') for supplier in suppliers if
        Part.objects.filter(part_type_id=part_type_id, supplier_names__supplier_id=supplier.pk).exists()]
    markup.add(*buttons_list)
    return markup


def show_phone_model_range(part_type_id):
    model_range = PhoneModelRange.objects.filter(phonemodel__supported_part_types=part_type_id).distinct().order_by('pk')

    markup = types.InlineKeyboardMarkup()
    model_range = [types.InlineKeyboardButton(phone_model_range.name, callback_data=f'write_off:{part_type_id}:{phone_model_range.pk}') for phone_model_range in model_range]
    markup.add(*model_range, row_width=4)
    markup.row(types.InlineKeyboardButton('Назад', callback_data=f'back')) # TODO: написати калбек для кнопки назад
    return markup


def show_phone_model(part_type_id, phone_model_range):
    phone_models = PhoneModel.objects.filter(phone_model_range=phone_model_range)
    color = 'color' if PartType.objects.get(pk=part_type_id).has_color else ''
    chip_type = 'chip_type' if PartType.objects.get(pk=part_type_id).has_chip else ''
    markup = types.InlineKeyboardMarkup()
    phone_models = [types.InlineKeyboardButton(
        phone_model.name, callback_data=f'write_off:{part_type_id}:{phone_model.pk}:{color}:{chip_type}'
    ) for phone_model in phone_models]

    markup.add(*phone_models)
    markup.row(types.InlineKeyboardButton('Назад', callback_data=f'back'))
    return markup


# Функція для провірки того чи є в запчастині колір чи тип чіпа сенсора
def check_exists_color_or_chip_type(part_type_id, phone_model, color, chip_type):
    quantity_name = 'Кількість'
    if color:
        cct = Color.objects.filter(part__phone_models=phone_model, part__part_type=part_type_id).distinct()
        return quantity_name if len(cct) == 0 else 'Колір'
    elif chip_type:
        cct = ChipType.objects.filter(part__phone_models=phone_model, part__part_type=part_type_id).distinct()
        return quantity_name if len(cct) == 0 else 'З чіпом чи без'
    else:
        return quantity_name


def show_color_or_chip_type(part_type_id, phone_model, color, chip_type):
    markup = types.InlineKeyboardMarkup()
    if color:
        markup.add(
            *[types.InlineKeyboardButton(color.name, callback_data=f'write_off:{part_type_id}:{phone_model}:{color.name}:{chip_type}'
            ) for color in Color.objects.filter(part__phone_models=phone_model, part__part_type=part_type_id).distinct()]
        )

    elif chip_type:
        markup.add(
            *[types.InlineKeyboardButton(color.name,callback_data=f'write_off:{part_type_id}:{phone_model}:{color}:{chip_type.name}'
            ) for chip_type in ChipType.objects.filter(part__phone_models=phone_model, part__part_type=part_type_id).distinct()]
        )

    markup.row(types.InlineKeyboardButton('Назад', callback_data=f'back'))
    return markup


def show_quantity(part_type_id, phone_model, color, chip_type):
    part_type = PartType.objects.get(pk=part_type_id).name
    phone_model = PhoneModel.objects.get(pk=phone_model).name

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('1', callback_data=f'final_request:{part_type}:{phone_model}:{color}:{chip_type}:{1}'))
    list_of_numbers = [types.InlineKeyboardButton(f'{i}', callback_data=f'final_request:{part_type}:{phone_model}:{color}:{chip_type}:{i}') for i in range(2, 7)]
    markup.add(*list_of_numbers)
    markup.row(types.InlineKeyboardButton('Назад', callback_data=f'back'))
    return markup





def other_key(user):
    users = iphone_db.select_hose()
    markup = types.InlineKeyboardMarkup()
    work_progress = types.InlineKeyboardButton('WorkProgress',
                                               switch_inline_query_current_chat=f'_wp\n{work_progress_db.select_work_progress(user)}')
    data_from_bot = types.InlineKeyboardButton('Скинути дані з бота', callback_data='reset-data-from-bot')
    null_wp = types.InlineKeyboardButton('Обнулити дані WP', callback_data='reset_data_user')
    reset_db_all = types.InlineKeyboardButton('Ресет бази шлангів', callback_data='reset_all_data_user')
    markup.row(work_progress)
    markup.add(null_wp, data_from_bot)
    user_confirm_list = [users['Назар']]  # Список з користувачами адмінами
    if user in user_confirm_list:
        markup.row(reset_db_all)
    return markup


def confirm():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Відправити в чат \U0001F680', callback_data='confirm_button'))
    return markup
