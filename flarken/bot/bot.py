import os
from keyboards import keyboard
import telebot
from dotenv import load_dotenv
from api.client import APIClient
from utils.utils import send_long_message
from keyboards.keyboard import actions_for_part, purchase_list
import sys
import django
from pathlib import Path

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
api = APIClient()


BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flarken.settings")

django.setup()

from warehouse.models import UserProfile, Part, PartDependency, PhoneModel


def is_authorized(user_id):
    return UserProfile.objects.filter(telegram_id=user_id).exists()


def auth_required(func):
    def wrapper(message_or_call, *args, **kwargs):
        user_id = message_or_call.from_user.id

        if not is_authorized(user_id):
            if hasattr(message_or_call, 'message'):
                bot.answer_callback_query(message_or_call.id, '❌ Немає доступу ❌')
            else:
                bot.send_message(message_or_call.chat.id, '❌ Немає доступу ❌')
            return

        return func(message_or_call, *args, **kwargs)
    return wrapper


@bot.message_handler(commands=['start'])
@auth_required
def send_message_welcome(message):
    bot.send_message(message.chat.id, 'Привіт, вибирай дію \U0001F916', reply_markup=keyboard.main_board())


@bot.message_handler(commands=['my_id'])
def get_my_id(message):
    user_firs_name = message.from_user.first_name
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f'{user_firs_name}: {user_id}')


@bot.message_handler(commands=['purchase_list'])
@auth_required
def get_purchase_list(message):
    bot.send_message(message.chat.id, 'Виберіть постачальника:', reply_markup=purchase_list())


@bot.message_handler(content_types=['text'])
@auth_required
def part_types(message):
    actions = actions_for_part(message.text)
    bot.send_message(message.chat.id, 'Що робимо далі?', reply_markup=actions)


user_state = {}

def get_state(user_id):
    return user_state.setdefault(user_id, {})


def edit(call, text, markup):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('write_off'))
@auth_required
def handle_write_off(call):
    user_id = call.from_user.id
    state = get_state(user_id)

    parsed = call.data.split(':')
    _, step, value = parsed

    if step == 'start':
        state.clear()
        state['part_type'] = value

        edit(call,'З якого модельного ряду списати?', keyboard.show_phone_model_range(state['part_type']))

    elif step == 'model_range':
        state['model_range'] = value

        edit(call,'Вибери модель', keyboard.show_phone_model(state['part_type'], value))

    elif step == 'model':
        state['phone_model'] = value

        params, next_step = keyboard.check_exists_color_or_chip_type({
            'part_type': state['part_type'],
            'phone_model': value,
            'color': True,
            'chip_type': True
        })

        if next_step == '':
            edit(call,'Кількість', keyboard.show_quantity())
        else:
            edit(call, next_step, keyboard.show_color_or_chip_type(**state))

    elif step == 'color':
        state['color'] = value

        edit(call,'Кількість',keyboard.show_quantity())

    elif step == 'chip':
        state['chip_type'] = value

        edit(call,'Кількість', keyboard.show_quantity())

    elif step == 'quantity':
        state['quantity'] = int(value)
        state.pop('model_range', None)
        response = api.write_off(**state)
        data = response.json()
        text = data['message']

        # TODO: зробити окрему API для списання залежної деталі яка буде викликатись по кнопці
        if response.status_code == 200:
            if data['dep_part']:
                dep_part = keyboard.write_off_dep_part(data['dep_part']['dep_part_name'])
                edit(call, text, dep_part)
            else:
                edit(call, text, None)
        else:
            edit(call, text, None)

        state.clear()


# Список наявних запчастин
@bot.callback_query_handler(func=lambda call: call.data.startswith('list_of_part_types'))
@auth_required
def get_list_of_part_types(call):
    part_type_id = call.data.split(':')[1]
    response = api.get_list_of_part_types(part_type_id)
    part_type_name = response['part_type_name']
    text = response['list_of_parts']

    edit(call, part_type_name, None)
    for message in send_long_message(text):
        bot.send_message(call.message.chat.id, message)


# Обробник кнопки "Закупка"
@bot.callback_query_handler(func=lambda call: call.data.startswith('purchase_list_part_type_and_supplier'))
@auth_required
def list_part_type_and_supplier(call):
    part_type_id = call.data.split(':')[1]
    edit(call, 'Виберіть постачальника', keyboard.purchase_list(part_type_id))


# Створити список закупки у потрібного постачальника і якщо треба потрібної запчастини
@bot.callback_query_handler(func=lambda call: call.data.startswith('supplier'))
@auth_required
def supplier_handler(call):
    supplier_id = call.data.split(':')[1]
    part_type_id = call.data.split(':')[2]
    if part_type_id:
        response = api.get_purchase_list_part_supplier(supplier_id, part_type_id)
    else:
        response = api.get_purchase_list(supplier_id)

    supplier = response['supplier_name']
    text = response['list']

    edit(call, supplier, None)
    for message in send_long_message(text):
        bot.send_message(call.message.chat.id, message)


@bot.callback_query_handler(func=lambda call: call.data == 'dep_part')
@auth_required
def write_off_dep_part_handler(call):
    pass


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
