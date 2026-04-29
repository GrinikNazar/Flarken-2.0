from django.db import models

from warehouse.models import PhoneModelRange


class WorkType(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип роботи"
        verbose_name_plural = "Типи робіт"


class WorkPrice(models.Model):
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.CASCADE,
        related_name="prices"
    )

    phone_model = models.ForeignKey(
        PhoneModelRange,
        on_delete=models.CASCADE,
        related_name="work_prices"
    )

    points = models.PositiveIntegerField()

    class Meta:
        unique_together = ("work_type", "phone_model")
        verbose_name = "Ціна роботи"
        verbose_name_plural = "Ціни робіт"

    def __str__(self):
        return f"{self.work_type} - {self.phone_model} ({self.points})"
