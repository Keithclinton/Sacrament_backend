from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/clergy/", include("apps.clergy.urls")),
    path("api/", include("apps.dioceses.urls")),
    path("api/requests/", include("apps.requests_app.urls")),
    path("api/routing/", include("apps.routing.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/ussd/", include("apps.ussd.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
