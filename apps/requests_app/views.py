from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.enums import UserRole
from apps.core.permissions import IsDiocesanAdminOrSuperAdmin, IsVerifiedPriest

from .models import SacramentRequest
from .permissions import IsOwnerAssignedPriestOrScopedAdmin
from .serializers import (
    SacramentRequestCreateSerializer,
    SacramentRequestSerializer,
    StatusUpdateSerializer,
    TrackingLookupSerializer,
)
from .services import accept_request, cancel_request, decline_request, update_request_status


class SacramentRequestCreateView(generics.CreateAPIView):
    """
    Deliberately AllowAny: a panicking family member shouldn't have to
    register mid-emergency to reach a priest. Matches USSD, which is
    anonymous by necessity. Authenticated requesters are still linked via
    request.user in the serializer so logged-in members get request history.
    """

    queryset = SacramentRequest.objects.all()
    serializer_class = SacramentRequestCreateSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "request_create"


class SacramentRequestListView(generics.ListAPIView):
    serializer_class = SacramentRequestSerializer
    filterset_fields = ("status", "emergency_level", "sacrament_type")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SacramentRequest.objects.none()
        user = self.request.user
        qs = SacramentRequest.objects.all()
        if user.role == UserRole.MEMBER:
            return qs.filter(requester=user)
        if user.role == UserRole.PRIEST:
            priest_profile = getattr(user, "priest_profile", None)
            if not priest_profile:
                return qs.none()
            from apps.routing.services import get_pending_request_ids_for_priest

            pending_ids = get_pending_request_ids_for_priest(priest_profile)
            return qs.filter(Q(id__in=pending_ids) | Q(assigned_priest=priest_profile))
        if user.role == UserRole.DIOCESAN_ADMIN:
            admin_profile = getattr(user, "diocesan_admin_profile", None)
            return qs.filter(assigned_parish__diocese=admin_profile.diocese) if admin_profile else qs.none()
        return qs  # super_admin


class SacramentRequestDetailView(generics.RetrieveAPIView):
    queryset = SacramentRequest.objects.all()
    serializer_class = SacramentRequestSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerAssignedPriestOrScopedAdmin)


class TrackRequestView(APIView):
    """Public, unauthenticated status lookup by tracking code - USSD/SMS parity on the web."""

    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "request_track"
    serializer_class = TrackingLookupSerializer

    def get(self, request, tracking_code):
        sacrament_request = get_object_or_404(SacramentRequest, tracking_code=tracking_code)
        return Response(TrackingLookupSerializer(sacrament_request).data)


class AcceptRequestView(APIView):
    permission_classes = (IsVerifiedPriest,)
    serializer_class = SacramentRequestSerializer

    def post(self, request, pk):
        sacrament_request = get_object_or_404(SacramentRequest, pk=pk)
        try:
            accept_request(sacrament_request=sacrament_request, priest_profile=request.user.priest_profile)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SacramentRequestSerializer(sacrament_request).data)


class DeclineRequestView(APIView):
    permission_classes = (IsVerifiedPriest,)
    serializer_class = SacramentRequestSerializer

    def post(self, request, pk):
        sacrament_request = get_object_or_404(SacramentRequest, pk=pk)
        try:
            decline_request(sacrament_request=sacrament_request, priest_profile=request.user.priest_profile)
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(SacramentRequestSerializer(sacrament_request).data)


class UpdateRequestStatusView(APIView):
    permission_classes = (IsVerifiedPriest,)
    serializer_class = StatusUpdateSerializer

    def post(self, request, pk):
        sacrament_request = get_object_or_404(SacramentRequest, pk=pk)
        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            update_request_status(
                sacrament_request=sacrament_request,
                to_status=serializer.validated_data["status"],
                actor=request.user,
            )
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SacramentRequestSerializer(sacrament_request).data)


class CancelRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsOwnerAssignedPriestOrScopedAdmin)
    serializer_class = SacramentRequestSerializer

    def post(self, request, pk):
        sacrament_request = get_object_or_404(SacramentRequest, pk=pk)
        self.check_object_permissions(request, sacrament_request)
        try:
            cancel_request(sacrament_request=sacrament_request, actor=request.user)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SacramentRequestSerializer(sacrament_request).data)


class RequestsSummaryAnalyticsView(APIView):
    """Admin dashboard: counts by status and emergency level, diocese-scoped for diocesan admins."""

    permission_classes = (IsDiocesanAdminOrSuperAdmin,)

    def get(self, request):
        from django.db.models import Count

        qs = SacramentRequest.objects.all()
        if request.user.role == UserRole.DIOCESAN_ADMIN:
            admin_profile = getattr(request.user, "diocesan_admin_profile", None)
            qs = qs.filter(assigned_parish__diocese=admin_profile.diocese) if admin_profile else qs.none()

        by_status = dict(qs.values("status").annotate(count=Count("id")).values_list("status", "count"))
        by_emergency_level = dict(
            qs.values("emergency_level").annotate(count=Count("id")).values_list("emergency_level", "count")
        )
        return Response(
            {
                "total": qs.count(),
                "by_status": by_status,
                "by_emergency_level": by_emergency_level,
            }
        )
