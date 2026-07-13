from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import User
from apps.core.enums import UserRole, VerificationStatus

from .models import PriestProfile, PriestVerificationEvent


class PriestRegistrationSerializer(serializers.ModelSerializer):
    """
    Priest self-registration. Always creates role=PRIEST with
    verification_status=PENDING - there is no way for a client to create an
    already-verified priest through this or any other endpoint.
    """

    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = PriestProfile
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "diocese",
            "diocesan_id_number",
            "ordination_date",
            "official_church_email",
            "parish_attestation_document",
            "verification_status",
        )
        read_only_fields = ("id", "verification_status")

    @transaction.atomic
    def create(self, validated_data):
        user_fields = {
            key: validated_data.pop(key)
            for key in ("username", "email", "first_name", "last_name", "phone_number", "password")
        }
        password = user_fields.pop("password")
        user = User(role=UserRole.PRIEST, **user_fields)
        user.set_password(password)
        user.save()
        return PriestProfile.objects.create(
            user=user, verification_status=VerificationStatus.PENDING, **validated_data
        )


class PriestProfileSerializer(serializers.ModelSerializer):
    has_location = serializers.SerializerMethodField()

    class Meta:
        model = PriestProfile
        fields = (
            "id",
            "diocese",
            "parish",
            "diocesan_id_number",
            "ordination_date",
            "official_church_email",
            "verification_status",
            "verification_notes",
            "verified_at",
            "is_available",
            "coverage_radius_km",
            "ministry_phone_number",
            "has_location",
        )
        read_only_fields = ("id", "verification_status", "verification_notes", "verified_at", "has_location")

    def get_has_location(self, obj) -> bool:
        return obj.current_location is not None


class PriestProfileSelfUpdateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = PriestProfile
        fields = ("is_available", "coverage_radius_km", "ministry_phone_number", "latitude", "longitude")

    def update(self, instance, validated_data):
        from django.contrib.gis.geos import Point

        lat = validated_data.pop("latitude", None)
        lng = validated_data.pop("longitude", None)
        if lat is not None and lng is not None:
            instance.current_location = Point(lng, lat, srid=4326)
        return super().update(instance, validated_data)


class VerificationDecisionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class PriestVerificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriestVerificationEvent
        fields = ("id", "from_status", "to_status", "changed_by", "notes", "created_at")
