from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from .views import CustomTokenObtainPairView, DiocesanAdminListCreateView, MemberRegistrationView, MeView

app_name = "accounts"

urlpatterns = [
    path("register/", MemberRegistrationView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("diocesan-admins/", DiocesanAdminListCreateView.as_view(), name="diocesan-admin-list-create"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
]
