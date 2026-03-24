import os
from keyboards import keyboard
import telebot
from dotenv import load_dotenv
from api.client import APIClient
from utils.utils import send_long_message
from keyboards.keyboard import actions_for_part, purchase_list

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
    bot.send_message(message.chat.id, 'Виберіть постачальника:', reply_markup=purchase_list())


@bot.message_handler(content_types=['text'])
def part_types(message):
    actions = actions_for_part(message.text)
    bot.send_message(message.chat.id, 'Що робимо далі?', reply_markup=actions)


@bot.callback_query_handler(func=lambda call: True)
def handler(call):
    if call.data.startswith('supplier:'):
        supplier_id = call.data.split(':')[1]
        part_type_id = call.data.split(':')[2]
        if part_type_id:
            response = api.get_purchase_list_part_supplier(supplier_id, part_type_id)
        else:
            response = api.get_purchase_list(supplier_id)

        supplier = response['supplier_name']
        text = response['list']

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=supplier)
        for message in send_long_message(text):
            bot.send_message(call.message.chat.id, message)

    # TODO: Доробити списання
    if call.data.startswith('write_off'):
        quantity_name = 'Кількість'
        parsed_text = call.data.split(':')
        part_type_id = call.data.split(':')[1]

        # Якщо два елемента в рядку - передається part_type_id
        if len(parsed_text) == 2:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='З якого модельного ряду списати?',
                reply_markup=keyboard.show_phone_model_range(part_type_id) # Показати модельні ряди
            )

        elif len(parsed_text) == 3:
            phone_model_range = call.data.split(':')[2]
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Вибери модель',
                reply_markup=keyboard.show_phone_model(part_type_id, phone_model_range) # Показати моделі з модельного ряду
            )

        # Від вибору моделі до вибору кольору або типу чіпа
        elif len(parsed_text) == 5:
            params = {
                'part_type_id': part_type_id,
                'phone_model': call.data.split(':')[2],
                'color': call.data.split(':')[3],
                'chip_type': call.data.split(':')[4]
            }
            empty_or_text = keyboard.check_exists_color_or_chip_type(params)
            params = empty_or_text[0]

            if empty_or_text[1] == '':
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=quantity_name,
                    reply_markup=keyboard.show_quantity(
                        params['part_type_id'],
                        params['phone_model'],
                        params['color'],
                        params['chip_type']
                    )
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=empty_or_text[1],
                    reply_markup=keyboard.show_color_or_chip_type(
                        params['part_type_id'],
                        params['phone_model'],
                        params['color'],
                        params['chip_type']
                    )
                )

        # Кількість
        elif len(parsed_text) == 6:
            phone_model = call.data.split(':')[2]
            color = call.data.split(':')[3]
            chip_type = call.data.split(':')[4]
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=quantity_name,
                reply_markup=keyboard.show_quantity(part_type_id, phone_model, color, chip_type)
            )

    if call.data.startswith('final_request'):
        data = {
            'part_type': call.data.split(':')[1],
            'phone_model': call.data.split(':')[2],
            'quantity': int(call.data.split(':')[5]),
            'color': call.data.split(':')[3],
            'chip_type': call.data.split(':')[4]
        }
        if data['color'] == '':
            data.pop('color')
        if data['chip_type'] == '':
            data.pop('chip_type')
        response = api.write_off(**data)
        response_json = response.json()
        if response.status_code == 200:
            response_text = f'{response_json["stock_status"]}{data["part_type"]} на {data["phone_model"]} залишилось {response_json["message"]} шт.'
        else:
            response_text = response_json['message']

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response_text)


    elif call.data.startswith('list_of_part_types'):
        part_type_id = call.data.split(':')[1]
        response = api.get_list_of_part_types(part_type_id)
        part_type_name = response['part_type_name']
        text = response['list_of_parts']

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=part_type_name)
        for message in send_long_message(text):
            bot.send_message(call.message.chat.id, message)

    elif call.data.startswith('purchase_list_part_type_and_supplier'):
        part_type_id = call.data.split(':')[1]
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Виберіть постачальника',
            reply_markup=keyboard.purchase_list(part_type_id)
        )


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
