from django.contrib import admin

from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "phone_number", "current_step", "is_active", "last_interaction_at")
    list_filter = ("is_active", "current_step")
    search_fields = ("session_id", "phone_number")
    readonly_fields = ("session_id", "phone_number", "current_step", "collected_data", "last_interaction_at")
