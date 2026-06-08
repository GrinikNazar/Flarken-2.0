from telebot import types
from utils import django_setup


from warehouse.models import Part, PhoneModel, PhoneModelRange


def get_phone_model_range():
    return [types.InlineKeyboardButton(item.name, callback_data=f'{item.pk}') for item in
           PhoneModelRange.objects.all().distinct().order_by('pk')]


buttons = {
    'Добавити': get_phone_model_range,
    'Переглянути сьогодні': '',
    'Загальний список': ''
}

def work_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for row in [[*buttons.keys()]]:
        markup.row(*row)

    return markup


def actions_from_work_board(message_text):
    markup = types.InlineKeyboardMarkup()
    row = buttons[message_text]()
    markup.add(*row, row_width=4)

    return markup

# TODO: зробити далі послідовний вибір, також треба розібратись як і чи можна вибирати пункти в меню по декілька штук
