from telebot import types
from utils import django_setup

from worklog.models import WorkPrice, WorkType
from warehouse.models import Part, PhoneModel, PhoneModelRange


def work_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Добавити', 'Переглянути сьогодні')
    markup.row('Загальний список', 'Попередній місяць')
    return markup


def show_model_range():
    markup = types.InlineKeyboardMarkup()
    row = [
        types.InlineKeyboardButton(r.name, callback_data=f'wp:model_range:{r.pk}')
        for r in PhoneModelRange.objects.all().order_by('pk')
    ]
    markup.add(*row, row_width=4)
    return markup


def show_phone_model(model_range_id):
    markup = types.InlineKeyboardMarkup()
    models = PhoneModel.objects.filter(phone_model_range=model_range_id).distinct()
    row = [
        types.InlineKeyboardButton(m.name, callback_data=f'wp:phone_model:{m.pk}')
        for m in models
    ]
    markup.add(*row, row_width=3)
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='wp:back:'))
    return markup


def show_work_list(phone_model_id, selected_ids: list[int], client_bonus: bool = False):
    markup = types.InlineKeyboardMarkup()
    works = WorkPrice.objects.filter(phone_model=phone_model_id).select_related('work_type')

    buttons = []
    for work in works:
        is_selected = work.pk in selected_ids
        icon = '❇️' if is_selected else ''
        buttons.append(types.InlineKeyboardButton(
            f'{icon} {work.work_type.name} ({work.points} б)',
            callback_data=f'wp:toggle:{work.pk}'
        ))

    markup.add(*buttons, row_width=2)

    # Кнопка "Клієнтський"
    client_icon = '❇️' if client_bonus else ''
    markup.add(types.InlineKeyboardButton(
        f'{client_icon} Клієнтський (+20%)',
        callback_data='wp:client_bonus:'
    ))

    # Підрахунок з бонусом
    total = sum(
        WorkPrice.objects.filter(pk__in=selected_ids).values_list('points', flat=True)
    ) if selected_ids else 0
    discount = 0.85 if len(selected_ids) > 1 else 1
    total = round(total * (1.20 if client_bonus else 1) * discount, 3)

    markup.add(types.InlineKeyboardButton(
        f'✅ Підтвердити ({total} балів)',
        callback_data='wp:ask_repair_number:'
    ))
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='wp:back:'))

    return markup


def apply_exclusive_logic(work_id: int, selected: list, phone_model_id) -> list:
    toggled = WorkPrice.objects.prefetch_related(
        "work_type__exclusive_groups"
    ).get(pk=work_id)
    groups = toggled.work_type.exclusive_groups.all()

    if work_id in selected:
        selected.remove(work_id)
        return selected

    new_selected = list(selected)

    if any(g.cancels_all for g in groups):
        new_selected = []
    else:
        cancels_all_ids = list(
            WorkPrice.objects.filter(
                phone_model=phone_model_id,
                work_type__exclusive_groups__cancels_all=True
            ).values_list("pk", flat=True)
        )
        new_selected = [s for s in new_selected if s not in cancels_all_ids]

        for group in groups:
            conflict_ids = list(
                WorkPrice.objects.filter(
                    phone_model=phone_model_id,
                    work_type__exclusive_groups=group
                ).exclude(pk=work_id).values_list("pk", flat=True)
            )
            new_selected = [s for s in new_selected if s not in conflict_ids]

    new_selected.append(work_id)
    return new_selected
