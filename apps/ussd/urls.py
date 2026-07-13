from django.urls import path

from .views import USSDWebhookView

app_name = "ussd"

urlpatterns = [
    path("webhook/", USSDWebhookView.as_view(), name="webhook"),
]
