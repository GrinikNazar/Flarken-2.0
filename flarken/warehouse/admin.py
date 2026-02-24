from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html

from .forms import PartAdminForm
from .models import (
    PhoneModel,
    PartType,
    Part,
    Supplier,
    SupplierPartName,
    Color,
    ChipType,
    PartDependency,
    PhoneModelRange,
)

@admin.register(PhoneModelRange)
class PhoneModelRangeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PhoneModel)
class PhoneModelAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_model_range", "release_year", "display_supported_parts")
    search_fields = ("name", "release_year")
    list_filter = ("phone_model_range",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('phone_model_range').prefetch_related('supported_part_types')

    @admin.display(description='Запчастини які підтримуються')
    def display_supported_parts(self, obj):
        return " | ".join([part.name for part in obj.supported_part_types.all()])


@admin.register(PartType)
class PartTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ChipType)
class ChipTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id","name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_display_links =("name",)



class SupplierPartNameInline(admin.TabularInline):
    model = SupplierPartName
    extra = 1
    # autocomplete_fields = ("supplier",)


class StockLevelFilter(admin.SimpleListFilter):
    title = "Рівень складу"
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return (
            ("below_min", "Менше мінімуму"),
            ("below_max", "Менше максимуму"),
        )

    def queryset(self, request, queryset):
        if self.value() == "below_min":
            return queryset.filter(current_quantity__lt=F("min_quantity"))

        if self.value() == "below_max":
            return queryset.filter(current_quantity__lt=F("max_quantity"))

        return queryset


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    form = PartAdminForm

    list_display = (
        "get_phone_models",
        "part_type",
        "color",
        "chip_type",
        "current_quantity",
        "max_quantity",
        "stock_status"
    )

    filter_horizontal = ("phone_models",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "part_type",
            "color",
            "chip_type",
        ).prefetch_related("phone_models")

    def get_phone_models(self, obj):
        return " | ".join([m.name for m in obj.phone_models.all()])

    get_phone_models.short_description = "Моделі телефонів"

    list_filter = (
        "phone_models",
        "part_type",
        "color",
        "chip_type",
        "phone_models__phone_model_range",
        StockLevelFilter,
    )

    search_fields = (
        "phone_models__name",
        "part_type__name",
        "color__name",
    )

    autocomplete_fields = (
        "phone_models",
        "part_type",
        "color",
        "chip_type",
    )

    inlines = [SupplierPartNameInline]

    list_select_related = (
        "part_type",
    )

    list_editable = (
        "current_quantity",
    )

    ordering = ("current_quantity",)

    def stock_status(self, obj):
        if obj.current_quantity < obj.min_quantity:
            color = "red"
        elif obj.current_quantity < obj.max_quantity:
            color = "orange"
        else:
            color = "green"

        return format_html(
            '<span style="color: {}; font-size: 25px;">●</span>',
            color
        )

    stock_status.short_description = "Статус"


@admin.register(PartDependency)
class PartDependencyAdmin(admin.ModelAdmin):
    pass
