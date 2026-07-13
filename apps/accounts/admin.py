from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import DiocesanAdminProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "phone_number", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Sacrament Platform", {"fields": ("role", "phone_number", "preferred_language", "last_known_location")}),
    )


@admin.register(DiocesanAdminProfile)
class DiocesanAdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "diocese")
    list_filter = ("diocese",)
    search_fields = ("user__username", "user__email")
