from django.contrib.gis.geos import Point
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsDiocesanAdminOrSuperAdmin

from .services import find_nearest_available_priests


class NearbyPriestsDebugView(APIView):
    """Admin/debug utility to preview candidate matching for a given point."""

    permission_classes = (IsDiocesanAdminOrSuperAdmin,)

    def get(self, request):
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, ValueError):
            return Response({"detail": "lat and lng query params are required."}, status=400)

        location = Point(lng, lat, srid=4326)
        candidates = find_nearest_available_priests(location)
        return Response(
            [
                {
                    "priest_id": c.id,
                    "priest_name": c.user.get_full_name(),
                    "distance_m": c.distance.m,
                    "parish": c.parish.name if c.parish else None,
                }
                for c in candidates
            ]
        )
