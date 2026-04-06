from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

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
    UserProfile,
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'email', 'get_telegram_id')
    list_display_links = ('username',)


    def get_telegram_id(self, obj):
        return obj.userprofile.telegram_id if hasattr(obj, 'userprofile') else None

    get_telegram_id.short_description = 'Telegram id'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(PhoneModelRange)
class PhoneModelRangeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PhoneModel)
class PhoneModelAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_model_range", "release_year", "display_supported_parts")
    search_fields = ("name", "release_year")
    list_filter = ("phone_model_range",)

    ordering = ("-release_year",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('phone_model_range').prefetch_related('supported_part_types')

    @admin.display(description='Запчастини які підтримуються')
    def display_supported_parts(self, obj):
        return " | ".join([part.name for part in obj.supported_part_types.all()])


@admin.register(PartType)
class PartTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)
    list_display_links = ("name",)


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
    autocomplete_fields = ("supplier",)


class StockLevelFilter(admin.SimpleListFilter):
    title = "Рівень складу"
    parameter_name = "stock_level"

    def lookups(self, request, model_admin):
        return (
            ("below_min", "Менше мінімуму"),
            ("between", "Між мінімум і максимум"),
            ("above_max", "Більше максимуму"),
        )

    def queryset(self, request, queryset):

        if self.value() == "below_min":
            return queryset.filter(
                current_quantity__lt=F("min_quantity")
            )

        if self.value() == "between":
            return queryset.filter(
                current_quantity__gte=F("min_quantity"),
                current_quantity__lte=F("max_quantity")
            )

        if self.value() == "above_max":
            return queryset.filter(
                current_quantity__gt=F("max_quantity")
            )

        return queryset


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    form = PartAdminForm

    list_display = (
        "get_phone_models",
        "part_type",
        "current_quantity",
        "max_quantity",
        'display_suppliers',
        "stock_status",
    )

    filter_horizontal = ("phone_models",)

    def get_list_display(self, request):
        list_display = list(self.list_display)

        part_type_id = request.GET.get("part_type__id__exact")

        if part_type_id:
            try:
                part_type = PartType.objects.get(id=part_type_id)
                if part_type.has_chip:
                    list_display.insert(2, "chip_type")
                elif part_type.has_color:
                    list_display.insert(2, "color")
            except PartType.DoesNotExist:
                pass
        else:
            list_display.insert(2, "chip_type")
            list_display.insert(2, "color")

        return list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "part_type",
            "color",
            "chip_type",
        ).prefetch_related("phone_models", "supplier_names__supplier")

    def get_phone_models(self, obj):
        return " | ".join(m.name for m in obj.phone_models.all())


    @admin.display(description="Постачальники")
    def display_suppliers(self, obj):
        return " | ".join(
            s.supplier.name for s in obj.supplier_names.all()[:3]
        )

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
        "max_quantity",
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


@admin.register(PartDependency)
class PartDependencyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parent_part",
        "dependent_part"
    )

    list_display_links = (
        "parent_part",
    )
