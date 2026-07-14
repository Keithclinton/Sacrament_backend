from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from apps.dioceses.models import Diocese, Parish

# Real, well-established Kenyan Catholic (arch)dioceses - names only are
# verified public knowledge. Coordinates are approximate city-centre
# locations (not precise chancery/cathedral addresses), and contact fields
# are deliberately left blank rather than fabricated - a real diocesan admin
# should fill those in via /admin/. This is a starting skeleton for testing
# routing, not an authoritative church directory.
DIOCESES = [
    ("Archdiocese of Nairobi", "NRB", -1.2921, 36.8219),
    ("Archdiocese of Mombasa", "MSA", -4.0435, 39.6682),
    ("Archdiocese of Kisumu", "KSM", -0.0917, 34.7680),
    ("Archdiocese of Nyeri", "NYE", -0.4201, 36.9476),
    ("Diocese of Nakuru", "NAK", -0.3031, 36.0800),
    ("Diocese of Machakos", "MCK", -1.5177, 37.2634),
    ("Diocese of Meru", "MER", 0.0470, 37.6553),
    ("Diocese of Kakamega", "KAK", 0.2827, 34.7519),
    ("Diocese of Eldoret", "ELD", 0.5143, 35.2698),
    ("Diocese of Kitui", "KTI", -1.3667, 38.0106),
]


class Command(BaseCommand):
    help = "Seeds a starting skeleton of real Kenyan Catholic dioceses (names only verified; contact info left blank for real diocesan admins to fill in)."

    def handle(self, *args, **options):
        for name, code, lat, lng in DIOCESES:
            diocese, created = Diocese.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            action = "Created" if created else "Already exists"
            self.stdout.write(f"{action}: {diocese.name} ({diocese.code})")

            parish, parish_created = Parish.objects.get_or_create(
                diocese=diocese,
                name=f"{name} Cathedral Parish",
                defaults={"location": Point(lng, lat, srid=4326)},
            )
            parish_action = "Created" if parish_created else "Already exists"
            self.stdout.write(f"  {parish_action} placeholder parish: {parish.name}")

        self.stdout.write(self.style.SUCCESS(f"Done. {len(DIOCESES)} dioceses processed."))
