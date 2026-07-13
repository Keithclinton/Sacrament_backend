from rest_framework import serializers

from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = (
            "id",
            "recipient",
            "recipient_phone",
            "channel",
            "notification_type",
            "related_request",
            "status",
            "provider_message_id",
            "payload_summary",
            "error_message",
            "sent_at",
            "created_at",
        )
        read_only_fields = fields
