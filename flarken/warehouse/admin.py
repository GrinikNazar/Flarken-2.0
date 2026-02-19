from django.contrib import admin
from django.db.models import F
from .models import (
    PhoneModel,
    PartType,
    Part,
    Supplier,
    SupplierPartName,
    Color,
    ChipType,
    PartDependency,
)


@admin.register(PhoneModel)
class PhoneModelAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(PartType)
class PartTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    # list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ChipType)
class ChipTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    # list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)


class SupplierPartNameInline(admin.TabularInline):
    model = SupplierPartName
    extra = 1
    # autocomplete_fields = ("supplier",)


class BelowMinimumFilter(admin.SimpleListFilter):
    title = "Менше мінімуму"
    parameter_name = "below_minimum"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Менше мінімуму"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(current_quantity__lt=F("min_quantity"))
        return queryset


class BelowMaximumFilter(admin.SimpleListFilter):
    title = "Менше максимуму"
    parameter_name = "below_maximum"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Менше максимуму"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(current_quantity__lt=F("max_quantity"))
        return queryset


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):

    list_display = (
        "phone_model",
        "part_type",
        "color",
        "chip_type",
        "current_quantity",
        "max_quantity",
    )

    list_filter = (
        "phone_model",
        "part_type",
        "color",
        "chip_type",
    )

    search_fields = (
        "phone_model__name",
        "part_type__name",
        "color__name",
    )

    autocomplete_fields = (
        "phone_model",
        "part_type",
        "color",
        "chip_type",
    )

    inlines = [SupplierPartNameInline]

    list_select_related = (
        "phone_model",
        "part_type",
    )

    list_editable = (
        "current_quantity",
    )

    ordering = ("current_quantity",)


@admin.register(PartDependency)
class PartDependencyAdmin(admin.ModelAdmin):
    pass