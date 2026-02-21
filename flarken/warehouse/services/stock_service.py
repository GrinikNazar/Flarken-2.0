from django.db import transaction
from django.core.exceptions import ValidationError

from warehouse.models import Part
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
        part = Part.objects.select_for_update().get(
            phone_model__name=phone_model,
            part_type__name=part_type,
            color__name=color,
            chip_type__name=chip_type,
            )

    except Part.DoesNotExist:
        raise ValidationError("Такої запчастини не існує")

    if part.current_quantity < quantity:
        raise ValidationError("Немає потрібної кількості")

    dependencies = (
        PartDependency.objects
        .select_related("dependent_part")
        .select_for_update()
        .filter(parent_part=part)
    )

    for dep in dependencies:
        required_qty = dep.quantity * quantity

        if dep.dependent_part.current_quantity < required_qty:
            raise ValidationError(
                f"Недостатньо залежної деталі: {dep.dependent_part}"
            )

    part.current_quantity -= quantity
    part.save()

    for dep in dependencies:
        required_qty = dep.quantity * quantity
        child = dep.dependent_part
        child.current_quantity -= required_qty
        child.save()

    return part


def generate_purchase_list(supplier_id: int):
    supplier_parts = SupplierPartName.objects.select_related("part").filter(supplier_id=supplier_id)

    result = []

    for item in supplier_parts:
        part = item.part

        if part.current_quantity < part.max_quantity:
            to_order = part.max_quantity - part.current_quantity
            result.append(f"{part.phone_model} {item.supplier_name} - {to_order}")

    return '\n'.join(result)