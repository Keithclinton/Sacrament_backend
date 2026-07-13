from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "channel",
        "notification_type",
        "recipient",
        "recipient_phone",
        "status",
        "related_request",
        "created_at",
    )
    list_filter = ("channel", "notification_type", "status")
    search_fields = ("recipient_phone", "recipient__username", "provider_message_id")
    readonly_fields = [f.name for f in NotificationLog._meta.fields]
