from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils.timezone import now
from .models import WorkType, WorkPrice, WorkLogEntry, ExclusiveGroup
from .models import get_daily_ranking, get_monthly_ranking


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


# ─── WorkPrice ────────────────────────────────────────────────────────────────

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


class WorkLogWorksInline(admin.TabularInline):
    model = WorkLogEntry.works.through
    extra = 0
    verbose_name = "Робота"
    verbose_name_plural = "Роботи"
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


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
        (None, {"fields": ("user", "phone_model", "date")}),
        ("Результат", {"fields": ("works_detail", "total_points")}),
    )

    @admin.display(description="Роботи")
    def works_summary(self, obj):
        names = [wp.work_type.name for wp in obj.works.all()[:3]]
        suffix = "..." if obj.works.count() > 3 else ""
        return ", ".join(names) + suffix

    @admin.display(description="Деталі робіт")
    def works_detail(self, obj):
        rows = "".join(
            f"<tr>"
            f"<td style='padding:3px 16px 3px 0'>{wp.work_type.name}</td>"
            f"<td style='text-align:right'>{wp.points} б</td>"
            f"</tr>"
            for wp in obj.works.all()
        )
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

    # ── Кастомна сторінка з рейтингом ─────────────────────────────────────────

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        today = now().date()
        daily = get_daily_ranking(today)
        monthly = get_monthly_ranking(today.year, today.month)

        def render_ranking(qs, title):
            medals = ["🥇", "🥈", "🥉"]
            rows = ""
            for i, master in enumerate(qs):
                medal = medals[i] if i < 3 else f"{i + 1}."
                rows += (
                    f"<tr>"
                    f"<td style='padding:4px 12px 4px 0'>{medal} {master.user}</td>"
                    f"<td style='text-align:right;font-weight:bold'>{master.total:.1f} б</td>"
                    f"</tr>"
                )
            if not rows:
                rows = "<tr><td colspan='2' style='color:#999'>Немає даних</td></tr>"
            return format_html(
                "<div style='margin-bottom:24px'>"
                "<h3 style='margin:0 0 8px'>{}</h3>"
                "<table style='border-collapse:collapse;min-width:260px'>{}</table>"
                "</div>",
                title,
                format_html(rows),
            )

        extra_context["daily_ranking"] = render_ranking(
            daily, f"🏆 Рейтинг сьогодні ({today.strftime('%d.%m.%Y')})"
        )
        extra_context["monthly_ranking"] = render_ranking(
            monthly, f"📅 Рейтинг за місяць ({today.strftime('%m.%Y')})"
        )

        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {}