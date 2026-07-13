from django.urls import path

from .views import (
    ClaimPriestView,
    MyPriestProfileView,
    PriestDetailView,
    PriestRegistrationView,
    RejectPriestView,
    ReinstatePriestView,
    SuspendPriestView,
    VerificationQueueView,
    VerifyPriestView,
)

app_name = "clergy"

urlpatterns = [
    path("priests/register/", PriestRegistrationView.as_view(), name="priest-register"),
    path("priests/me/", MyPriestProfileView.as_view(), name="priest-me"),
    path("verification-queue/", VerificationQueueView.as_view(), name="verification-queue"),
    path("priests/<int:pk>/", PriestDetailView.as_view(), name="priest-detail"),
    path("priests/<int:pk>/claim/", ClaimPriestView.as_view(), name="priest-claim"),
    path("priests/<int:pk>/verify/", VerifyPriestView.as_view(), name="priest-verify"),
    path("priests/<int:pk>/reject/", RejectPriestView.as_view(), name="priest-reject"),
    path("priests/<int:pk>/suspend/", SuspendPriestView.as_view(), name="priest-suspend"),
    path("priests/<int:pk>/reinstate/", ReinstatePriestView.as_view(), name="priest-reinstate"),
]
