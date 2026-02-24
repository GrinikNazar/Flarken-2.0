from django import forms
from django.core.exceptions import ValidationError

from warehouse.models import Part


class PartAdminForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = "__all__"
        widgets = {
            "phone_models": forms.SelectMultiple(
                attrs={
                    "class": "form-control",
                    "style": "width: 50%;",
                }
            )
        }

    def clean(self):
        cleaned_data = super().clean()

        part_type = cleaned_data.get("part_type")
        color = cleaned_data.get("color")
        chip_type = cleaned_data.get("chip_type")
        phone_models = cleaned_data.get("phone_models")

        if not part_type:
            return cleaned_data

        if not part_type.has_color and color:
            raise ValidationError("Для цього типу запчастини колір не потрібен.")

        if not part_type.has_chip and chip_type:
            raise ValidationError("Для цього типу запчастини чіп не потрібен.")

        if phone_models:
            for model in phone_models:
                if not model.supported_part_types.filter(id=part_type.id).exists():
                    raise ValidationError(
                        f"{model.name} не підтримує цей тип запчастини."
                    )

        return cleaned_data
