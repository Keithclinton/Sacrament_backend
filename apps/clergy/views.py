from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.enums import UserRole, VerificationStatus
from apps.core.permissions import IsDiocesanAdminOrSuperAdmin

from .models import PriestProfile
from .serializers import (
    PriestProfileSelfUpdateSerializer,
    PriestProfileSerializer,
    PriestRegistrationSerializer,
    VerificationDecisionSerializer,
)
from .services import transition_priest_verification


class PriestRegistrationView(generics.CreateAPIView):
    queryset = PriestProfile.objects.all()
    serializer_class = PriestRegistrationSerializer
    permission_classes = (permissions.AllowAny,)


class MyPriestProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        return PriestProfileSelfUpdateSerializer if self.request.method in ("PATCH", "PUT") else PriestProfileSerializer

    def get_object(self):
        if self.request.user.role != UserRole.PRIEST:
            raise PermissionDenied("Only priests have a priest profile.")
        return get_object_or_404(PriestProfile, user=self.request.user)


class VerificationQueueView(generics.ListAPIView):
    serializer_class = PriestProfileSerializer
    permission_classes = (IsDiocesanAdminOrSuperAdmin,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return PriestProfile.objects.none()
        qs = PriestProfile.objects.filter(
            verification_status__in=[VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]
        )
        user = self.request.user
        if user.role == UserRole.DIOCESAN_ADMIN:
            admin_profile = getattr(user, "diocesan_admin_profile", None)
            qs = qs.filter(diocese=admin_profile.diocese) if admin_profile else qs.none()
        return qs.order_by("created_at")


class PriestDetailView(generics.RetrieveAPIView):
    queryset = PriestProfile.objects.all()
    serializer_class = PriestProfileSerializer
    permission_classes = (IsDiocesanAdminOrSuperAdmin,)


class BaseVerificationTransitionView(APIView):
    permission_classes = (IsDiocesanAdminOrSuperAdmin,)
    serializer_class = VerificationDecisionSerializer
    to_status = None

    def post(self, request, pk):
        priest_profile = get_object_or_404(PriestProfile, pk=pk)
        serializer = VerificationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transition_priest_verification(
                priest_profile=priest_profile,
                to_status=self.to_status,
                actor=request.user,
                notes=serializer.validated_data["notes"],
            )
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(PriestProfileSerializer(priest_profile).data)


class ClaimPriestView(BaseVerificationTransitionView):
    to_status = VerificationStatus.UNDER_REVIEW


class VerifyPriestView(BaseVerificationTransitionView):
    to_status = VerificationStatus.VERIFIED


class RejectPriestView(BaseVerificationTransitionView):
    to_status = VerificationStatus.REJECTED


class SuspendPriestView(BaseVerificationTransitionView):
    to_status = VerificationStatus.SUSPENDED


class ReinstatePriestView(BaseVerificationTransitionView):
    to_status = VerificationStatus.VERIFIED
