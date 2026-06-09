from django.db import models

from warehouse.models import PhoneModel, UserProfile


class WorkType(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Тип роботи")
    exclusive_group = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="Група взаємовиключення",
        help_text="Роботи з однаковою групою — взаємовиключні (напр. 'screen_type')"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип роботи"
        verbose_name_plural = "Типи робіт"


class WorkPrice(models.Model):
    work_type = models.ForeignKey(WorkType, on_delete=models.CASCADE,
                                  related_name="prices", verbose_name='Тип роботи')
    phone_model = models.ForeignKey(PhoneModel, on_delete=models.CASCADE,
                                    related_name="work_prices", verbose_name="Модель пристрою")
    points = models.FloatField(verbose_name="Кількість балів")

    class Meta:
        unique_together = ("work_type", "phone_model")
        verbose_name = "Ціна роботи"
        verbose_name_plural = "Ціни робіт"

    def __str__(self):
        return f"{self.work_type} - {self.phone_model} ({self.points})"


class WorkLogEntry(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                             related_name="work_logs", verbose_name="Майстер")
    phone_model = models.ForeignKey(PhoneModel, on_delete=models.CASCADE,
                                    verbose_name="Модель пристрою")
    date = models.DateField(auto_now_add=True, verbose_name="Дата")
    works = models.ManyToManyField(WorkPrice, verbose_name="Роботи")
    total_points = models.FloatField(verbose_name="Сума балів")

    class Meta:
        verbose_name = "Запис роботи"
        verbose_name_plural = "Записи робіт"

    def __str__(self):
        return f"{self.user} | {self.phone_model} | {self.date} | {self.total_points} б"


# TODO: виписати всі типи робіт і записати у базу
# TODO: автоматизувати перехід балів з EXCEL до бази даних щоб не заповнювати все вручну
