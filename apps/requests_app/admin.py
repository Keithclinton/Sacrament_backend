from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import RequestStatusEvent, SacramentRequest


class RequestStatusEventInline(admin.TabularInline):
    model = RequestStatusEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "notes", "created_at")
    can_delete = False


@admin.register(SacramentRequest)
class SacramentRequestAdmin(GISModelAdmin):
    list_display = (
        "tracking_code",
        "sacrament_type",
        "emergency_level",
        "status",
        "assigned_priest",
        "channel",
        "submitted_at",
    )
    list_filter = ("status", "emergency_level", "sacrament_type", "channel")
    search_fields = ("tracking_code", "patient_name", "requester_phone")
    readonly_fields = ("tracking_code", "submitted_at")
    inlines = [RequestStatusEventInline]


@admin.register(RequestStatusEvent)
class RequestStatusEventAdmin(admin.ModelAdmin):
    list_display = ("request", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)
