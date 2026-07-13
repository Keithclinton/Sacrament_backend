from django.urls import path

from .views import (
    AcceptRequestView,
    CancelRequestView,
    DeclineRequestView,
    RequestsSummaryAnalyticsView,
    SacramentRequestCreateView,
    SacramentRequestDetailView,
    SacramentRequestListView,
    TrackRequestView,
    UpdateRequestStatusView,
)

app_name = "requests_app"

urlpatterns = [
    path("", SacramentRequestCreateView.as_view(), name="request-create"),
    path("mine/", SacramentRequestListView.as_view(), name="request-list"),
    path("analytics/summary/", RequestsSummaryAnalyticsView.as_view(), name="request-analytics-summary"),
    path("<uuid:pk>/", SacramentRequestDetailView.as_view(), name="request-detail"),
    path("track/<str:tracking_code>/", TrackRequestView.as_view(), name="request-track"),
    path("<uuid:pk>/accept/", AcceptRequestView.as_view(), name="request-accept"),
    path("<uuid:pk>/decline/", DeclineRequestView.as_view(), name="request-decline"),
    path("<uuid:pk>/status/", UpdateRequestStatusView.as_view(), name="request-status"),
    path("<uuid:pk>/cancel/", CancelRequestView.as_view(), name="request-cancel"),
]
