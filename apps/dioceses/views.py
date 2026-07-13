from rest_framework import permissions, viewsets

from apps.core.permissions import IsSuperAdmin

from .models import Deanery, Diocese, Institution, Parish
from .serializers import DeanerySerializer, DioceseSerializer, InstitutionSerializer, ParishSerializer


class DioceseViewSet(viewsets.ModelViewSet):
    queryset = Diocese.objects.filter(is_active=True)
    serializer_class = DioceseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            # Public directory info (diocese names) - a not-yet-registered
            # priest needs this to populate a diocese picker before they have
            # any account at all.
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class DeaneryViewSet(viewsets.ModelViewSet):
    queryset = Deanery.objects.all()
    serializer_class = DeanerySerializer
    filterset_fields = ("diocese",)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]


class ParishViewSet(viewsets.ModelViewSet):
    queryset = Parish.objects.filter(is_active=True)
    serializer_class = ParishSerializer
    filterset_fields = ("diocese", "deanery")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]


class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = InstitutionSerializer
    filterset_fields = ("diocese", "parish", "institution_type")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]
