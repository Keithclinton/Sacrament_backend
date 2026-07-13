from rest_framework.routers import DefaultRouter

from .views import DeaneryViewSet, DioceseViewSet, InstitutionViewSet, ParishViewSet

app_name = "dioceses"

router = DefaultRouter()
router.register("dioceses", DioceseViewSet, basename="diocese")
router.register("deaneries", DeaneryViewSet, basename="deanery")
router.register("parishes", ParishViewSet, basename="parish")
router.register("institutions", InstitutionViewSet, basename="institution")

urlpatterns = router.urls
