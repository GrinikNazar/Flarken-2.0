import os
from keyboards import keyboard
import telebot
from dotenv import load_dotenv
from api.client import APIClient
from utils.utils import send_long_message

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
api = APIClient()


# TODO: продумати систему авторизації
@bot.message_handler(commands=['start'])
def send_message_welcome(message):
    bot.send_message(message.chat.id, 'Привіт, вибирай дію \U0001F916', reply_markup=keyboard.main_board())


@bot.message_handler(commands=['my_id'])
def get_my_id(message):
    user_firs_name = message.from_user.first_name
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f'{user_firs_name}: {user_id}')

@bot.message_handler(commands=['purchase_list'])
def get_purchase_list(message):
    bot.send_message(message.chat.id, 'Виберіть постачальника:', reply_markup=keyboard.purchase_list())


@bot.message_handler(commands=['other'])
def other_function(message):
    bot.send_message(message.chat.id, 'Додаткові можливості Флеркена', reply_markup=keyboard.other_key(message.from_user.id))


@bot.callback_query_handler(func=lambda call: True)
def handler(call):
    if call.data.startswith('supplier:'):
        supplier_id = call.data.split(':')[1]
        response = api.get_purchase_list(supplier_id)
        supplier = response['supplier_name']
        text = response['list']

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=supplier)
        for message in send_long_message(text):
            bot.send_message(call.message.chat.id, message)


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
