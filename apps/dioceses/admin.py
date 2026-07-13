from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Deanery, Diocese, Institution, Parish


@admin.register(Diocese)
class DioceseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "bishop_name", "is_active")
    search_fields = ("name", "code")


@admin.register(Deanery)
class DeaneryAdmin(admin.ModelAdmin):
    list_display = ("name", "diocese")
    list_filter = ("diocese",)
    search_fields = ("name",)


@admin.register(Parish)
class ParishAdmin(GISModelAdmin):
    list_display = ("name", "diocese", "deanery", "is_active")
    list_filter = ("diocese", "is_active")
    search_fields = ("name", "address")


@admin.register(Institution)
class InstitutionAdmin(GISModelAdmin):
    list_display = ("name", "institution_type", "diocese", "parish", "assigned_chaplain", "is_active")
    list_filter = ("institution_type", "diocese", "is_active")
    search_fields = ("name",)
