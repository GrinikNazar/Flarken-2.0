from django.contrib import admin
from .models import *


# TODO: посортувати нормально у боковій панелі
@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ("name", )


# TODO: зробити фільтр і пошук по моделі і типу робіт
@admin.register(WorkPrice)
class WorkPriceAdmin(admin.ModelAdmin):
    list_display = ("work_type", "phone_model", "points")
