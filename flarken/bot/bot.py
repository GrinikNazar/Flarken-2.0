import os
import keyboard
import telebot
from dotenv import load_dotenv
import requests

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# TODO: продумати систему авторизації
@bot.message_handler(commands=['start'])
def send_message_welcome(message):
    bot.send_message(message.chat.id, 'Привіт, вибирай дію \U0001F916', reply_markup=keyboard.main_board())


@bot.message_handler(commands=['my_id'])
def get_my_id(message):
    user_firs_name = message.from_user.first_name
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f'{user_firs_name}: {user_id}')

# TODO: нормально переіменувати змінні зроити по людськи
@bot.message_handler(commands=['list_ref'])
def get_list_ref(message):
    bot.send_message(message.chat.id, 'Виберіть варіант формування списку:', reply_markup=keyboard.list_ref_parts())


@bot.message_handler(commands=['other'])
def other_function(message):
    bot.send_message(message.chat.id, 'Додаткові можливості Флеркена', reply_markup=keyboard.other_key(message.from_user.id))


@bot.callback_query_handler(func=lambda call: True)
def handler(call):
    if call.data.startswith('supplier:'):
        supplier_id = call.data.split(':')[1]
        endpoint_list = 'http://127.0.0.1:8000/warehouse/purchase-list/'
        response = requests.get(endpoint_list, params={'supplier_id': supplier_id}).json()
        text = f"{response['supplier_name']}\n{response['list']}"

        # TODO: зробити щоб не вилітало коли завелике повідомлення

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
