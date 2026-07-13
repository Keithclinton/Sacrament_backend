import factory
from django.contrib.gis.geos import Point

from apps.accounts.models import DiocesanAdminProfile, User
from apps.clergy.models import PriestProfile
from apps.core.enums import UserRole, VerificationStatus
from apps.dioceses.models import Diocese, Parish


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    phone_number = factory.Sequence(lambda n: f"+25470000{n:04d}")
    first_name = "Test"
    last_name = "User"
    role = UserRole.MEMBER

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "TestPass123!")
        if create:
            self.save()


class DioceseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Diocese

    name = factory.Sequence(lambda n: f"Diocese {n}")
    code = factory.Sequence(lambda n: f"D{n:03d}")


class ParishFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Parish

    diocese = factory.SubFactory(DioceseFactory)
    name = factory.Sequence(lambda n: f"Parish {n}")
    location = factory.LazyFunction(lambda: Point(36.8172, -1.2841, srid=4326))


class DiocesanAdminProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DiocesanAdminProfile

    user = factory.SubFactory(UserFactory, role=UserRole.DIOCESAN_ADMIN)
    diocese = factory.SubFactory(DioceseFactory)


class PriestProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PriestProfile

    user = factory.SubFactory(UserFactory, role=UserRole.PRIEST)
    diocese = factory.SubFactory(DioceseFactory)
    parish = factory.SubFactory(ParishFactory)
    diocesan_id_number = factory.Sequence(lambda n: f"PRIEST-{n:04d}")
    verification_status = VerificationStatus.PENDING
    is_available = True
    current_location = factory.LazyFunction(lambda: Point(36.8172, -1.2841, srid=4326))
    coverage_radius_km = 15
