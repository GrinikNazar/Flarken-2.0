from telebot import types
from utils import django_setup

from worklog.models import WorkPrice, WorkType
from warehouse.models import Part, PhoneModel, PhoneModelRange


def work_board():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Добавити', 'Переглянути сьогодні', 'Загальний список')
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


def show_work_list(phone_model_id, selected_ids: list[int]):
    """
    Відображає список робіт з чекбоксами.
    selected_ids — список id WorkPrice які зараз вибрані.
    """
    markup = types.InlineKeyboardMarkup()
    works = WorkPrice.objects.filter(phone_model=phone_model_id).select_related('work_type')

    for work in works:
        is_selected = work.pk in selected_ids
        icon = '✅' if is_selected else '⬜'
        markup.add(types.InlineKeyboardButton(
            f'{icon} {work.work_type.name} ({work.points} б)',
            callback_data=f'wp:toggle:{work.pk}'
        ))

    total = sum(
        WorkPrice.objects.get(pk=wid).points for wid in selected_ids
    ) if selected_ids else 0

    markup.add(types.InlineKeyboardButton(
        f'✅ Підтвердити ({total} балів)',
        callback_data='wp:confirm:'
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
