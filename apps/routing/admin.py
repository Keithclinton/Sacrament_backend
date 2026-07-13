from django.contrib import admin

from .models import RequestEscalation


@admin.register(RequestEscalation)
class RequestEscalationAdmin(admin.ModelAdmin):
    list_display = (
        "request",
        "escalation_level",
        "escalated_to_priest",
        "escalated_to_admin",
        "reason",
        "escalated_at",
        "resolved_at",
    )
    list_filter = ("reason", "escalation_level")
    readonly_fields = ("request", "escalation_level", "escalated_to_priest", "escalated_to_admin", "reason", "escalated_at")
