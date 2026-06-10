from django.db import models
from django.db.models import Sum
from django.utils.timezone import now

from warehouse.models import PhoneModel, UserProfile


class ExclusiveGroup(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Назва групи")
    cancels_all = models.BooleanField(
        default=False,
        verbose_name="Скасовує всі інші роботи",
        help_text=(
            "Якщо увімкнено — при виборі цієї роботи знімаються ВСІ інші вибрані роботи. "
            "Наприклад: 'Діагностика без ремонту'."
        )
    )

    def __str__(self):
        marker = " ⚡" if self.cancels_all else ""
        return f"{self.name}{marker}"

    class Meta:
        verbose_name = "Група взаємовиключення"
        verbose_name_plural = "Групи взаємовиключення"
        ordering = ("name",)


class WorkType(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Тип роботи")
    exclusive_groups = models.ManyToManyField(
        ExclusiveGroup,
        blank=True,
        related_name="work_types",
        verbose_name="Групи взаємовиключення",
        help_text="Робота може належати до кількох груп одночасно."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип роботи"
        verbose_name_plural = "Типи робіт"
        ordering = ("name",)


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
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE,
        related_name="work_logs", verbose_name="Майстер"
    )
    phone_model = models.ForeignKey(
        PhoneModel, on_delete=models.CASCADE,
        verbose_name="Модель пристрою"
    )
    date = models.DateField(auto_now_add=True, verbose_name="Дата")
    works = models.ManyToManyField(WorkPrice, verbose_name="Роботи")
    total_points = models.FloatField(verbose_name="Сума балів")

    class Meta:
        verbose_name = "Запис роботи"
        verbose_name_plural = "Записи робіт"
        ordering = ("-date",)

    def __str__(self):
        return f"{self.user} | {self.phone_model} | {self.date} | {self.total_points} б"


# ─── Хелпери для рейтингу ─────────────────────────────────────────────────────

def get_daily_ranking(date=None):
    """
    Повертає список майстрів з сумою балів за вказаний день (default: сьогодні).
    Формат: [{'user': UserProfile, 'total': float}, ...]
    """
    if date is None:
        date = now().date()

    return (
        UserProfile.objects
        .filter(work_logs__date=date)
        .annotate(total=Sum("work_logs__total_points"))
        .order_by("-total")
    )


def get_monthly_ranking(year=None, month=None):
    """
    Повертає список майстрів з сумою балів за вказаний місяць (default: поточний).
    """
    today = now().date()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    return (
        UserProfile.objects
        .filter(work_logs__date__year=year, work_logs__date__month=month)
        .annotate(total=Sum("work_logs__total_points"))
        .order_by("-total")
    )
