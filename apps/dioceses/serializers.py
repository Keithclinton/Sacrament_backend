from rest_framework import serializers

from .models import Deanery, Diocese, Institution, Parish


class DioceseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diocese
        fields = (
            "id",
            "name",
            "code",
            "bishop_name",
            "contact_email",
            "contact_phone",
            "is_active",
        )


class DeanerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Deanery
        fields = ("id", "diocese", "name")


class ParishSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Parish
        fields = (
            "id",
            "diocese",
            "deanery",
            "name",
            "address",
            "contact_phone",
            "contact_email",
            "is_active",
            "latitude",
            "longitude",
        )

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lat = validated_data.pop("latitude")
        lng = validated_data.pop("longitude")
        validated_data["location"] = Point(lng, lat, srid=4326)
        return super().create(validated_data)


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = (
            "id",
            "name",
            "institution_type",
            "diocese",
            "parish",
            "assigned_chaplain",
            "contact_phone",
            "is_active",
        )
