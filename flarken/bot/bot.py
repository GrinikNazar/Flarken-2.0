import os
from keyboards import keyboard, keyboard_wp
import telebot
from dotenv import load_dotenv
from api.client import APIClient
from utils.utils import send_long_message
from utils import django_setup
from keyboards.keyboard import actions_for_part, purchase_list, add_back_button
from keyboards.keyboard_wp import apply_exclusive_logic
import copy
from django.utils.timezone import now
from telebot import types

from warehouse.models import UserProfile, Part, PartDependency, PhoneModel
from worklog.models import WorkPrice, WorkType, WorkLogEntry


load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
api = APIClient()


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


def show_today(message, from_user):
    user_profile = UserProfile.objects.get(telegram_id=from_user.id)
    today = now().date()
    entries = WorkLogEntry.objects.filter(
        user=user_profile, date=today
    ).prefetch_related('works__work_type')

    if not entries:
        bot.send_message(message.chat.id, '📭 Сьогодні записів ще немає.')
        return

    lines = []
    total_day = 0
    for entry in entries:
        works_str = ', '.join(w.work_type.name for w in entry.works.all())
        client_mark = ' 👤' if entry.is_client_device else ''
        lines.append(
            f'#{entry.repair_number} {entry.phone_model.name}{client_mark} — {works_str} | *{entry.total_points} б*')
        total_day += entry.total_points

    lines.append(f'\n*Разом сьогодні: {round(total_day, 3)} б*')

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✏️ Редагувати записи', callback_data='wpe:list:'))

    return '\n'.join(lines), markup


@bot.message_handler(commands=['start'])
@auth_required
def send_message_welcome(message):
    bot.send_message(message.chat.id, 'Привіт, вибирай дію \U0001F916', reply_markup=keyboard.main_board())


@bot.message_handler(commands=['wp'])
@auth_required
def wp_keyboard(message):
    bot.send_message(message.chat.id, 'Яку роботи вибрати ', reply_markup=keyboard_wp.work_board())


@bot.message_handler(commands=['my_id'])
def get_my_id(message):
    user_firs_name = message.from_user.first_name
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f'{user_firs_name}: {user_id}')


@bot.message_handler(commands=['purchase_list'])
@auth_required
def get_purchase_list(message):
    bot.send_message(message.chat.id, 'Виберіть постачальника:', reply_markup=purchase_list())


user_state = {}

def get_state(message_id):
    return user_state.setdefault(message_id, {})


@bot.message_handler(content_types=['text'])
@auth_required
def part_types(message):
    try:
        actions = actions_for_part(message.text)
        bot.send_message(message.chat.id, 'Що робимо далі?', reply_markup=actions)

    except Exception as e:
        if message.text == "Добавити":
            result = keyboard_wp.show_model_range()
            bot.send_message(message.chat.id, 'Виберіть модельний ряд', reply_markup=result)

        elif message.text == 'Переглянути сьогодні':
            lines, markup = show_today(message, message.from_user)

            bot.send_message(
                message.chat.id,
                lines,
                parse_mode='Markdown',
                reply_markup=markup
            )

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
    message_id = call.message.message_id
    state = get_state(message_id)

    parsed = call.data.split(':')
    _, step, value = parsed

    if step == 'start':
        state.clear()
        state['history'] = []
        state['part_type'] = value
        state['step'] = 'model_range'

        edit(call,'З якого модельного ряду списати?', add_back_button(keyboard.show_phone_model_range(state['part_type'])))

    elif step == 'model_range':
        state['history'].append(state.copy())
        state['model_range'] = value
        state['step'] = 'phone_model'

        edit(call,'Вибери модель', add_back_button(keyboard.show_phone_model(state['part_type'], value)))

    elif step == 'model':
        state['history'].append(state.copy())
        state['phone_model'] = value
        state['step'] = 'color_or_chip'

        params, next_step = keyboard.check_exists_color_or_chip_type({
            'part_type': state['part_type'],
            'phone_model': value,
            'color': True,
            'chip_type': True
        })

        if next_step == '':
            edit(call,'Кількість', add_back_button(keyboard.show_quantity()))
        else:
            edit(call, next_step, add_back_button(keyboard.show_color_or_chip_type(**state)))

    elif step == 'color':
        state['history'].append(state.copy())
        state['color'] = value
        state['step'] = 'quantity'

        edit(call,'Кількість', add_back_button(keyboard.show_quantity()))

    elif step == 'chip':
        state['history'].append(state.copy())
        state['chip_type'] = value
        state['step'] = 'quantity'

        edit(call,'Кількість', add_back_button(keyboard.show_quantity()))

    elif step == 'quantity':
        state['history'].append(state.copy())
        state['quantity'] = int(value)

        state.pop('model_range', None)

        data_for_api = copy.deepcopy(state)
        data_for_api.pop('history', None)
        response = api.write_off(**data_for_api)

        data = response.json()
        text = data['message']

        if response.status_code == 200:
            if data['dep_part_type']:
                dep_part = keyboard.write_off_dep_part(data['dep_part_type_name'], state['quantity'])
                state['part_type'] = data['dep_part_type']
                state['color'] = data['dep_part_color']
                state['chip_type'] = data['dep_part_chip_type']
                edit(call, text, dep_part)
            else:
                edit(call, text, None)
                state.clear()
        else:
            edit(call, text, None)
            state.clear()

    elif step == 'back':
        if state.get('history'):
            prev_state = state['history'].pop()
            state.clear()
            state.update(prev_state)
            step = state.get('step')

            if step == 'model_range':
                edit(call, 'З якого модельного ряду списати?',
                     add_back_button(keyboard.show_phone_model_range(state['part_type'])))

            elif step == 'phone_model':
                edit(call, 'Вибери модель',
                     add_back_button(keyboard.show_phone_model(state['part_type'], state['model_range'])))

            elif step == 'color_or_chip':
                edit(call, 'Обери варіант',
                     add_back_button(keyboard.show_color_or_chip_type(**state)))

        else:
            edit(call, 'Що робимо далі?', keyboard.actions_for_part(state['part_type']))


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


@bot.callback_query_handler(func=lambda call: call.data.startswith('wp:'))
@auth_required
def handle_wp(call):
    message_id = call.message.message_id
    state = get_state(message_id)

    _, step, value = call.data.split(':')

    if step == 'model_range':
        state.clear()
        state['history'] = []
        state['model_range'] = value
        state['step'] = 'phone_model'
        state['selected'] = []
        edit(call, 'Виберіть модель:', keyboard_wp.show_phone_model(value))

    elif step == 'phone_model':
        state['history'].append(state.copy())
        state['phone_model'] = value
        state['step'] = 'work_list'
        edit(call, f'Виберіть роботи:', keyboard_wp.show_work_list(value, []))

    elif step == 'toggle':
        work_id = int(value)
        selected = state.get('selected', [])
        state['selected'] = apply_exclusive_logic(work_id, selected, state['phone_model'])
        edit(call, 'Виберіть роботи:', keyboard_wp.show_work_list(
            state['phone_model'], state['selected'], state.get('client_bonus', False)
        ))

    elif step == 'client_bonus':
        state['client_bonus'] = not state.get('client_bonus', False)
        edit(call, 'Виберіть роботи:', keyboard_wp.show_work_list(
            state['phone_model'], state['selected'], state['client_bonus']
        ))

    elif step == 'ask_repair_number':
        def handle_repair_number_input(message, state):
            repair_number = message.text.strip()
            selected = state.get('selected', [])
            user_profile = UserProfile.objects.get(telegram_id=message.from_user.id)
            works = WorkPrice.objects.filter(pk__in=selected)
            total = sum(w.points for w in works)
            discount = 0.85 if len(selected) > 1 else 1
            total = round(total * (1.20 if state.get('client_bonus') else 1) * discount, 3)

            works_text = '\n'.join(f'  • {w.work_type.name} — {w.points} б' for w in works)
            client_mark = ' 👤 Клієнтський' if state.get('client_bonus') else ''

            editing_id = state.get('editing_entry_id')

            if editing_id:
                # Оновити існуючий запис
                entry = WorkLogEntry.objects.get(pk=editing_id)
                entry.repair_number = repair_number
                entry.total_points = total
                entry.is_client_device = state.get('client_bonus', False)
                entry.save()
                entry.works.set(works)

                bot.send_message(
                    message.chat.id,
                    f'✅ Запис оновлено!\n\n{works_text}{client_mark}\n\nРемонт №{repair_number}\nРазом: {total} б'
                )
            else:
                # Створити новий запис
                entry = WorkLogEntry.objects.create(
                    user=user_profile,
                    phone_model_id=state['phone_model'],
                    total_points=total,
                    repair_number=repair_number,
                    is_client_device=state.get('client_bonus', False)
                )
                entry.works.set(works)

                bot.send_message(
                    message.chat.id,
                    f'✅ Збережено!\n\n{works_text}{client_mark}\n\nРемонт №{repair_number}\nРазом: {total} б'
                )

            state.clear()

        if not state.get('selected'):
            bot.answer_callback_query(call.id, '⚠️ Виберіть хоча б одну роботу!')
            return

        msg = bot.send_message(call.message.chat.id, '🔢 Введіть номер ремонту:')
        bot.register_next_step_handler(msg, handle_repair_number_input, state)

    elif step == 'back':
        if state.get('history'):
            prev = state['history'].pop()
            state.clear()
            state.update(prev)
            if state.get('step') == 'phone_model':
                edit(call, 'Виберіть модель:', keyboard_wp.show_phone_model(state['model_range']))
            else:
                edit(call, 'Виберіть модельний ряд:', keyboard_wp.show_model_range())
        else:
            edit(call, 'Виберіть модельний ряд:', keyboard_wp.show_model_range())


@bot.callback_query_handler(func=lambda call: call.data.startswith('wpe:'))
@auth_required
def handle_wp_edit(call):
    _, step, value = call.data.split(':')
    user_profile = UserProfile.objects.get(telegram_id=call.from_user.id)
    today = now().date()

    # Список записів для редагування
    if step == 'list':
        entries = WorkLogEntry.objects.filter(
            user=user_profile, date=today
        ).select_related('phone_model')

        if not entries:
            bot.answer_callback_query(call.id, 'Записів немає.')
            return

        markup = types.InlineKeyboardMarkup()
        for entry in entries:
            markup.add(types.InlineKeyboardButton(
                f'✏️ #{entry.repair_number} {entry.phone_model.name}',
                callback_data=f'wpe:entry:{entry.pk}'
            ))
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='wpe:back_to_today:'))

        edit(call, 'Виберіть запис для редагування:', markup)

    # Деталі одного запису
    elif step == 'entry':
        entry = WorkLogEntry.objects.prefetch_related(
            'works__work_type'
        ).get(pk=value, user=user_profile)

        works_str = '\n'.join(f'  • {w.work_type.name} — {w.points} б' for w in entry.works.all())
        client_mark = ' 👤 Клієнтський' if entry.is_client_device else ''
        text = (
            f'*#{entry.repair_number} {entry.phone_model.name}*{client_mark}\n\n'
            f'{works_str}\n\n'
            f'*Разом: {entry.total_points} б*'
        )

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton('🔄 Змінити роботи', callback_data=f'wpe:edit_works:{entry.pk}'),
            types.InlineKeyboardButton('🗑️ Видалити', callback_data=f'wpe:delete:{entry.pk}')
        )
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='wpe:list:'))

        edit(call, text, markup)

    # Редагування робіт
    elif step == 'edit_works':
        entry = WorkLogEntry.objects.prefetch_related('works').get(pk=value, user=user_profile)
        selected_ids = list(entry.works.values_list('pk', flat=True))
        client_bonus = entry.is_client_device

        state = get_state(call.message.message_id)
        state.clear()
        state['phone_model'] = str(entry.phone_model_id)
        state['selected'] = selected_ids
        state['client_bonus'] = client_bonus
        state['editing_entry_id'] = int(value)
        state['repair_number'] = entry.repair_number

        edit(call, 'Змініть роботи:', keyboard_wp.show_work_list(
            entry.phone_model_id, selected_ids, client_bonus
        ))

    # Підтвердження видалення
    elif step == 'delete':
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton('✅ Так, видалити', callback_data=f'wpe:confirm_delete:{value}'),
            types.InlineKeyboardButton('❌ Ні', callback_data=f'wpe:entry:{value}')
        )
        edit(call, '⚠️ Видалити цей запис?', markup)

    elif step == 'confirm_delete':
        WorkLogEntry.objects.filter(pk=value, user=user_profile).delete()
        edit(call, '🗑️ Запис видалено.', None)

    elif step == 'back_to_today':
        lines, markup = show_today(call, call.from_user)
        edit(call, lines, markup)


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
