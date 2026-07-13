from django.urls import path

from .views import NearbyPriestsDebugView

app_name = "routing"

urlpatterns = [
    path("nearby-priests/", NearbyPriestsDebugView.as_view(), name="nearby-priests"),
]
