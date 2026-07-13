from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.permissions import IsSuperAdmin

from .models import DiocesanAdminProfile, User
from .serializers import (
    CustomTokenObtainPairSerializer,
    DiocesanAdminCreateSerializer,
    DiocesanAdminProfileSerializer,
    MemberRegistrationSerializer,
    UserSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MemberRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = MemberRegistrationSerializer
    permission_classes = (permissions.AllowAny,)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class DiocesanAdminListCreateView(generics.ListCreateAPIView):
    """Super-admin-only: diocesan admins are appointed, not self-registered."""

    queryset = DiocesanAdminProfile.objects.all()
    permission_classes = (IsSuperAdmin,)
    filterset_fields = ("diocese",)

    def get_serializer_class(self):
        return DiocesanAdminCreateSerializer if self.request.method == "POST" else DiocesanAdminProfileSerializer
