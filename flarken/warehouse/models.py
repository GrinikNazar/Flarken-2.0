from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


# Модельний ряд
class PhoneModelRange(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Модельний ряд'
        verbose_name_plural = 'Модельні ряди'


# Молель телефонів
class PhoneModel(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва моделі")

    supported_part_types = models.ManyToManyField(
        "PartType",
        related_name="supported_phone_models",
        blank=True,
        verbose_name="Запчастини які підтримуються"
    )

    phone_model_range = models.ForeignKey(
        PhoneModelRange,
        on_delete=models.CASCADE,
        verbose_name='Модельний ряд',
        null=True,
        blank=True,
    )

    release_year = models.PositiveIntegerField(default=0, verbose_name='Рік випуску')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Модель телефону'
        verbose_name_plural = 'Моделі телефонів'


# Тип запчастини (АКБ, Скло і так далі ... )
class PartType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Назва запчастини')

    has_color = models.BooleanField(default=False, verbose_name='З кольором')
    has_chip = models.BooleanField(default=False, verbose_name='Тип чіпа')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип запчастини'
        verbose_name_plural = 'Типи запчастин'


# Таблиця кольору
class Color(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Колір")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Колір'
        verbose_name_plural = 'Кольори'


# Таблиця для сенсорів з чіпом чи без
class ChipType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Тип чіпа')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип чіпу'
        verbose_name_plural = 'Типи чіпів'


# Основна модель, конкретна запчастина. Наприклад АКБ iPhone 7
class Part(models.Model):
    phone_models = models.ManyToManyField(
        PhoneModel,
        related_name="parts",
        verbose_name='Модель телефону'
    )
    part_type = models.ForeignKey(
        PartType,
        on_delete=models.CASCADE,
        related_name="parts",
        verbose_name='Запчастина'
    )

    current_quantity = models.PositiveIntegerField(default=0, verbose_name='Поточна кількість')
    min_quantity = models.IntegerField(default=0, verbose_name='Мінімальна кількість')
    max_quantity = models.IntegerField(default=0, verbose_name='Максимум')

    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Колір'
    )

    chip_type = models.ForeignKey(
        ChipType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name = 'Тип чіпа'
    )


    class Meta:
        unique_together = (
            "part_type",
            "color",
            "chip_type",
        )
        verbose_name = 'Запчастина'
        verbose_name_plural = 'Запчастини'

    # def __str__(self):
    #     parts = [self.part_type.name, self.phone_model.name]
    #
    #     if self.color:
    #         parts.append(self.color.name)
    #
    #     if self.chip_type:
    #         parts.append(self.chip_type.name)
    #
    #     return " - ".join(parts)


class Supplier(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Постачальник'
        verbose_name_plural = 'Постачальники'


class SupplierPartName(models.Model):
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="supplier_names",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="parts",
        verbose_name = "Компанія"
    )

    supplier_name = models.CharField(max_length=255, verbose_name="Назва у постачальника")

    class Meta:
        unique_together = ("part", "supplier")
        verbose_name = 'Постачальник'
        verbose_name_plural = 'Постачальники'

    def __str__(self):
        return f"{self.supplier.name} → {self.supplier_name}"


class PartDependency(models.Model):
    parent_part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="dependencies"
    )

    dependent_part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="used_in"
    )

    class Meta:
        verbose_name = 'Залежність'
        verbose_name_plural = 'Залежності'

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.parent_part} → {self.dependent_part}"

