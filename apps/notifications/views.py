from rest_framework import generics

from apps.core.permissions import IsSuperAdmin

from .models import NotificationLog
from .serializers import NotificationLogSerializer


class NotificationLogListView(generics.ListAPIView):
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
    permission_classes = (IsSuperAdmin,)
    filterset_fields = ("channel", "notification_type", "status")
