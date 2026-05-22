from django.db import models

from warehouse.models import PhoneModel


# TODO: виписати всі типи робіт і записати у базу
class WorkType(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Тип роботи")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип роботи"
        verbose_name_plural = "Типи робіт"

# TODO: автоматизувати перехід балів з EXCEL до бази даних щоб не заповнювати все вручну
class WorkPrice(models.Model):
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name='Тип роботи'
    )

    phone_model = models.ForeignKey(
        PhoneModel,
        on_delete=models.CASCADE,
        related_name="work_prices",
        verbose_name="Модель пристрою"
    )

    points = models.FloatField(verbose_name="Кількість балів")

    class Meta:
        unique_together = ("work_type", "phone_model")
        verbose_name = "Ціна роботи"
        verbose_name_plural = "Ціни робіт"

    def __str__(self):
        return f"{self.work_type} - {self.phone_model} ({self.points})"
