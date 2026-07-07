from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import WorkType, WorkPrice, WorkLogEntry, ExclusiveGroup


class WorkLogEntryForm(forms.ModelForm):
    class Meta:
        model = WorkLogEntry
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.phone_model_id:
            self.fields['works'].queryset = WorkPrice.objects.filter(
                phone_model=self.instance.phone_model
            ).select_related('work_type')
            self.fields['works'].help_text = ''
        else:
            # Новий запис — показуємо всі
            self.fields['works'].queryset = WorkPrice.objects.select_related(
                'work_type', 'phone_model'
            ).order_by('phone_model__name', 'work_type__name')
            self.fields['works'].help_text = (
                '⚠️ Спочатку збережіть запис з моделлю пристрою — '
                'тоді список робіт відфільтрується по вибраній моделі.'
            )

        self.fields['works'].label_from_instance = lambda obj: (
            f"{obj.phone_model.name} — {obj.work_type.name} ({obj.points} б)"
        )


@admin.register(ExclusiveGroup)
class ExclusiveGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "cancels_all_badge", "work_types_count")
    list_filter = ("cancels_all",)
    search_fields = ("name",)

    @admin.display(description="Скасовує всі")
    def cancels_all_badge(self, obj):
        if obj.cancels_all:
            return format_html('<span style="color:#c0392b;font-weight:bold">⚡ Так</span>')
        return "—"

    @admin.display(description="Кількість робіт")
    def work_types_count(self, obj):
        return obj.work_types.count()


class WorkPriceInline(admin.TabularInline):
    model = WorkPrice
    extra = 1
    fields = ("phone_model", "points")
    autocomplete_fields = ("phone_model",)
    verbose_name = "Ціна для моделі"
    verbose_name_plural = "Ціни по моделях"


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "groups_display", "price_count")
    search_fields = ("name",)
    filter_horizontal = ("exclusive_groups",)

    fieldsets = (
        (None, {"fields": ("name",)}),
        ("Взаємовиключення", {
            "fields": ("exclusive_groups",),
            "description": (
                "Оберіть групи, до яких належить ця робота. "
                "При виборі роботи в боті — інші роботи з тих самих груп будуть зняті."
            ),
        }),
    )

    @admin.display(description="Групи")
    def groups_display(self, obj):
        groups = obj.exclusive_groups.all()
        if not groups:
            return "—"
        badges = []
        for g in groups:
            color = "#c0392b" if g.cancels_all else "#2980b9"
            badges.append(
                f'<span style="background:{color};color:#fff;'
                f'padding:2px 8px;border-radius:10px;margin:1px;'
                f'font-size:11px">{g.name}</span>'
            )
        return format_html("".join(badges))

    @admin.display(description="Моделей з ціною")
    def price_count(self, obj):
        return obj.prices.count()


@admin.register(WorkPrice)
class WorkPriceAdmin(admin.ModelAdmin):
    list_display = ("work_type", "groups_display", "phone_model", "points")
    list_filter = ("work_type__exclusive_groups", "phone_model__phone_model_range", "phone_model", "work_type")
    search_fields = ("work_type__name", "phone_model__name")
    ordering = ("work_type__name", "phone_model__name")
    autocomplete_fields = ("work_type", "phone_model")
    list_editable = ("points",)

    @admin.display(description="Групи")
    def groups_display(self, obj):
        groups = obj.work_type.exclusive_groups.all()
        if not groups:
            return "—"
        return ", ".join(g.name for g in groups)


@admin.register(WorkLogEntry)
class WorkLogEntryAdmin(admin.ModelAdmin):

    form = WorkLogEntryForm

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        instance = form.instance
        works = instance.works.all()
        total = sum(w.points for w in works)
        discount = 0.85 if works.count() > 1 else 1
        bonus = 1.20 if instance.is_client_device else 1
        instance.total_points = round(total * bonus * discount, 3)
        instance.save()

    list_display = ("date", "repair_number", "is_client_device", "user", "phone_model", "works_summary", "total_points")
    list_filter = ("date", "user", "phone_model__phone_model_range")
    search_fields = ("user__name", "phone_model__name", "repair_number")
    ordering = ("-date", "user")
    date_hierarchy = "date"
    readonly_fields = ("total_points", "works_detail")

    fieldsets = (
        ("Основна інформація", {
            "fields": ("user", "phone_model", "date", "repair_number", "is_client_device")
        }),
        ("Роботи", {
            "fields": ("works",),
        }),
        ("Підсумок", {
            "fields": ("works_detail", "total_points"),
        }),
    )

    @admin.display(description="Роботи")
    def works_summary(self, obj):
        names = [wp.work_type.name for wp in obj.works.all()[:3]]
        suffix = "..." if obj.works.count() > 3 else ""
        return ", ".join(names) + suffix

    @admin.display(description="Деталі робіт")
    def works_detail(self, obj):
        if not obj.pk:
            return "—"
        rows = "".join(
            f"<tr>"
            f"<td style='padding:3px 16px 3px 0'>{wp.work_type.name}</td>"
            f"<td style='text-align:right'>{wp.points} б</td>"
            f"</tr>"
            for wp in obj.works.all()
        )
        if not rows:
            return "—"
        return format_html(
            "<table style='border-collapse:collapse;min-width:280px'>"
            "<thead><tr>"
            "<th style='text-align:left;padding:3px 16px 3px 0'>Робота</th>"
            "<th style='text-align:right'>Бали</th>"
            "</tr></thead>"
            "<tbody>{}</tbody>"
            "<tfoot><tr>"
            "<td><strong>Разом</strong></td>"
            "<td style='text-align:right'><strong>{} б</strong></td>"
            "</tr></tfoot>"
            "</table>",
            format_html(rows),
            obj.total_points,
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("works__work_type")
