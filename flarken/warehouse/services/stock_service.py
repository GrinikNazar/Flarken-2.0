from django.db import transaction
from django.core.exceptions import ValidationError

from warehouse.models import Part, PartType
from warehouse.models import SupplierPartName
from warehouse.models import PartDependency


@transaction.atomic
def write_off_part(
        phone_model: str,
        part_type: str,
        quantity: int,
        color: str | None = None,
        chip_type: str | None = None,
):
    try:
        filters = {
            "part_type": part_type,
            "phone_models": phone_model,
            "color__name": color,
            "chip_type__name": chip_type,
        }

        part_id = (
            Part.objects
            .filter(**filters)
            .values_list("id", flat=True)
            .first()
        )

        part = (
            Part.objects
            .select_for_update()
            .get(id=part_id)
        )

    except Part.DoesNotExist:
        raise ValidationError("Такої запчастини не існує")

    if part.current_quantity < quantity:
        raise ValidationError("Немає потрібної кількості")

    part.current_quantity -= quantity
    part.save()

    dependencies = (
        PartDependency.objects
        .select_related("dependent_part")
        .select_for_update()
        .filter(parent_part=part)
    )

    if dependencies.exists():
        dep_part = dependencies.first()
        return part, dep_part
    else:
        return part, None


def generate_purchase_list(supplier_id: int, part_type_id: int = None):
    queryset = SupplierPartName.objects.select_related(
        "part", "part__part_type"
    ).prefetch_related("part__phone_models").filter(supplier_id=supplier_id).distinct()

    if part_type_id:
        queryset = queryset.filter(part__part_type_id=part_type_id)

    result = []
    for item in queryset:
        part = item.part
        if part.current_quantity >= part.max_quantity:
            continue

        models_str = ' / '.join(m.name for m in part.phone_models.all())
        part_color = f' {part.color.name}' if part.color else ''
        to_order = part.max_quantity - part.current_quantity
        release_year = part.phone_models.all()[0].release_year if part.phone_models.exists() else 0
        result.append((release_year, f"{item.supplier_name} - {models_str}{part_color} - {to_order}"))

    result.sort(key=lambda x: x[0] or 0)
    return '\n'.join(text for _, text in result)


def generate_list_of_type(part_type_id: int):
    list_of_part = Part.objects.filter(
        part_type=part_type_id
    ).prefetch_related('phone_models').distinct()

    result = []
    for part in list_of_part:
        models_str = ' / '.join(m.name for m in part.phone_models.all())
        extra = part.color or part.chip_type or ''
        result.append((
            part.phone_models.all()[0].release_year,
            f"{models_str} {extra} - {part.current_quantity}"
        ))

    result.sort(key=lambda x: x[0] or 0)

    part_type_name = PartType.objects.get(pk=part_type_id).name
    return {
        "part_type_name": part_type_name,
        "list_of_parts": '\n'.join(text for _, text in result)
    }
