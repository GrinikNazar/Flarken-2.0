from django.db import transaction
from django.core.exceptions import ValidationError
from warehouse.models import Part


@transaction.atomic
def write_off_part(
    phone_model: str,
    part_type: str,
    quantity: int,
    color: str | None = None,
    chip_type: str | None = None,
):
    try:
        part = Part.objects.select_for_update().get(
            phone_model__name=phone_model,
            part_type__name=part_type,
            color__name=color,
            chip_type__name=chip_type,
            )

    except Part.DoesNotExist:
        raise ValidationError("Такої запчастини не існує")

    if part.current_quantity < quantity:
        raise ValidationError("Недостатньо товару на складі")

    part.current_quantity -= quantity
    part.save()

    return part
