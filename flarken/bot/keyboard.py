from telebot import types
import os
import sys
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flarken.settings")

django.setup()

from warehouse.models import Part, PhoneModel, Color, PartType, ChipType, Supplier

# TODO: придумати як показати клавіатуру
def main_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_2 = types.KeyboardButton('\U0001F6BDКришки')
    button_3 = types.KeyboardButton('\U0001F50BАКБ')
    button_4 = types.KeyboardButton('\U0001F60EСкло')
    button_5 = types.KeyboardButton('\U0001F526Пiдсвiтки')
    button_6 = types.KeyboardButton('\U0001F4F2Сенсори')
    button_7 = types.KeyboardButton('\U0001F4A9Рамки')  
    button_8 = types.KeyboardButton('\U0001F4F2Touch iPad')
    button_9 = types.KeyboardButton('\U0001F250Копії')
    button_10 = types.KeyboardButton('\U0001FA79Клей АКБ + проклейки')
    button_11 = types.KeyboardButton('\U0001F50CІнше')
    row1 = [button_3, button_4, button_5, button_6]
    row2 = [button_7, button_2, button_8, button_9]
    row3 = [button_10, button_11]
    board = [row1, row2, row3]
    for row in board:
        markup.row(*row)
    return markup


def button_inine(call):

    title_message = ''

    markup = types.InlineKeyboardMarkup()
    if len(call.split('_')) == 2:
        title_message += 'Вибір моделі'
        markup.add(*[types.InlineKeyboardButton(f'{key}', callback_data=f'{call}_{key}') for key in iphone_db.choise_models(call.split('_')[0])], row_width=7)
        markup.row(types.InlineKeyboardButton('Назад', callback_data=f'{call}_back'))

    elif len(call.split('_')) == 3:
        title_message += 'Вибір моделі'
        fr_db_data = iphone_db.choise_submodels(call.split('_')[0], call.split('_')[-1])
        if not fr_db_data:
            markup.add(*[types.InlineKeyboardButton(f'{key}', callback_data=f'{call}_{key}_nocolor') for key in fr_db_data], row_width=7)
        else:
            markup.add(*[types.InlineKeyboardButton(f'{key}', callback_data=f'{call}_{key}') for key in fr_db_data], row_width=7)
        markup.row(types.InlineKeyboardButton('Назад', callback_data=f'{call}_back'))

    elif len(call.split('_')) == 4:
        string_color = iphone_db.choise_colors(call.split('_')[0], call.split('_')[-1])
        if string_color:
            title_message += 'Вибір кольору чи підпункту'
            string_color = string_color.split('\r\n')
            markup.add(*[types.InlineKeyboardButton(f'{color_mod.title()}', callback_data=f'{call}_{color_mod}') for color_mod in string_color])
            markup.row(types.InlineKeyboardButton('Назад', callback_data=f'{call}_back'))
        else:
            title_message += 'Кількість'
            markup.row(types.InlineKeyboardButton(f'1', callback_data=f'{call}_nocolor_1'))
            markup.add(*[types.InlineKeyboardButton(f'{i}', callback_data=f'{call}_nocolor_{i}') for i in range(2, 11)])
            markup.row(types.InlineKeyboardButton('Назад', callback_data=f'{call}_back'))

    elif len(call.split('_')) == 5:
        title_message += 'Кількість'
        markup.row(types.InlineKeyboardButton(f'1', callback_data=f'{call}_1'))
        markup.add(*[types.InlineKeyboardButton(f'{i}', callback_data=f'{call}_{i}') for i in range(2, 11)])
        markup.row(types.InlineKeyboardButton('Назад', callback_data=f'{call}_back'))

    return (markup, title_message)


def action_menu_categories(message):
    change_categories = iphone_db.gen_keyboard(message[1:])
    markup = types.InlineKeyboardMarkup()
    try:
        if change_categories[1] == 'order':
            markup.add(types.InlineKeyboardButton('Взяти', callback_data=f'{change_categories[0]}_take'), types.InlineKeyboardButton('Знайти', callback_data=f'{change_categories[0]}_search'), types.InlineKeyboardButton('Список', callback_data=f'list_order_{change_categories[0]}'))
        else:
            markup.add(types.InlineKeyboardButton('Взяти', callback_data=f'{change_categories[0]}_take'), types.InlineKeyboardButton('Знайти', callback_data=f'{change_categories[0]}_search'))
        return markup
    except TypeError:
        print('Проблема з "order"')
    

def purchase_list():
    markup = types.InlineKeyboardMarkup()
    suppliers = Supplier.objects.all()
    buttons_list = [types.InlineKeyboardButton(supplier.name, callback_data=f'supplier:{supplier.pk}') for supplier in suppliers]
    markup.add(*buttons_list)
    return markup


def other_key(user):
    users = iphone_db.select_hose()
    markup = types.InlineKeyboardMarkup()
    work_progress = types.InlineKeyboardButton('WorkProgress', switch_inline_query_current_chat=f'_wp\n{work_progress_db.select_work_progress(user)}')
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

