from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils.timezone import now
from .models import WorkType, WorkPrice, WorkLogEntry


# ─── Інлайн: ціни робіт всередині WorkType ───────────────────────────────────

class WorkPriceInline(admin.TabularInline):
    model = WorkPrice
    extra = 1
    fields = ("phone_model", "points")
    autocomplete_fields = ("phone_model",)
    verbose_name = "Ціна для моделі"
    verbose_name_plural = "Ціни по моделях"


# ─── WorkType ─────────────────────────────────────────────────────────────────

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "exclusive_group_badge", "price_count")
    list_filter = ("exclusive_group",)
    search_fields = ("name", "exclusive_group")
    ordering = ("exclusive_group", "name")
    inlines = (WorkPriceInline,)

    fieldsets = (
        (None, {
            "fields": ("name",)
        }),
        ("Взаємовиключення", {
            "fields": ("exclusive_group",),
            "description": (
                "Роботи з однаковою групою взаємовиключають одна одну при виборі в боті. "
                "Наприклад: 'screen_type' для 'Повна заміна екрану' і 'Часткова заміна екрану'."
            ),
        }),
    )

    @admin.display(description="Група взаємовиключення")
    def exclusive_group_badge(self, obj):
        if obj.exclusive_group:
            return format_html(
                '<span style="background:#e0f0ff;padding:2px 8px;border-radius:10px;">{}</span>',
                obj.exclusive_group
            )
        return "—"

    @admin.display(description="Моделей з ціною")
    def price_count(self, obj):
        return obj.prices.count()


# ─── WorkPrice ────────────────────────────────────────────────────────────────

@admin.register(WorkPrice)
class WorkPriceAdmin(admin.ModelAdmin):
    list_display = ("work_type", "exclusive_group", "phone_model", "points")
    list_filter = ("work_type__exclusive_group", "phone_model__phone_model_range", "phone_model", "work_type")
    search_fields = ("work_type__name", "phone_model__name")
    ordering = ("work_type__exclusive_group", "work_type__name", "phone_model__name")
    autocomplete_fields = ("work_type", "phone_model")
    list_editable = ("points",)

    @admin.display(description="Група", ordering="work_type__exclusive_group")
    def exclusive_group(self, obj):
        return obj.work_type.exclusive_group or "—"


# ─── Інлайн: список робіт всередині WorkLogEntry ─────────────────────────────

class WorkLogWorksInline(admin.TabularInline):
    model = WorkLogEntry.works.through
    extra = 0
    verbose_name = "Робота"
    verbose_name_plural = "Роботи"
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ─── WorkLogEntry ─────────────────────────────────────────────────────────────

@admin.register(WorkLogEntry)
class WorkLogEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "phone_model", "works_summary", "total_points")
    list_filter = ("date", "user", "phone_model__phone_model_range")
    search_fields = ("user__name", "phone_model__name")
    ordering = ("-date", "user")
    date_hierarchy = "date"
    readonly_fields = ("total_points", "works_detail")
    inlines = (WorkLogWorksInline,)

    fieldsets = (
        (None, {
            "fields": ("user", "phone_model", "date")
        }),
        ("Результат", {
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
        rows = "".join(
            f"<tr><td>{wp.work_type.name}</td><td style='text-align:right'>{wp.points} б</td></tr>"
            for wp in obj.works.all()
        )
        return format_html(
            "<table style='border-collapse:collapse;min-width:300px'>"
            "<thead><tr>"
            "<th style='text-align:left;padding:4px 12px 4px 0'>Робота</th>"
            "<th style='text-align:right'>Бали</th>"
            "</tr></thead>"
            "<tbody>{}</tbody>"
            "<tfoot><tr>"
            "<td><strong>Разом</strong></td>"
            "<td style='text-align:right'><strong>{} б</strong></td>"
            "</tr></tfoot>"
            "</table>",
            format_html(rows),
            obj.total_points
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("works__work_type")