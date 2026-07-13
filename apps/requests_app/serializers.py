from rest_framework import serializers

from .models import RequestStatusEvent, SacramentRequest
from .services import create_sacrament_request


class RequestStatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestStatusEvent
        fields = ("from_status", "to_status", "notes", "created_at")


class SacramentRequestCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = SacramentRequest
        fields = (
            "id",
            "tracking_code",
            "requester_name",
            "requester_phone",
            "patient_name",
            "sacrament_type",
            "emergency_level",
            "latitude",
            "longitude",
            "location_description",
            "address_text",
            "hospital_or_home",
            "institution",
            "family_contact_name",
            "family_contact_phone",
            "logistics_notes",
            "status",
        )
        read_only_fields = ("id", "tracking_code", "status")

    def create(self, validated_data):
        request = self.context["request"]
        requester = request.user if request.user.is_authenticated else None
        return create_sacrament_request(data=validated_data, channel="web", requester=requester)


class SacramentRequestSerializer(serializers.ModelSerializer):
    timeline = RequestStatusEventSerializer(many=True, read_only=True)

    class Meta:
        model = SacramentRequest
        fields = (
            "id",
            "tracking_code",
            "requester_name",
            "requester_phone",
            "patient_name",
            "sacrament_type",
            "emergency_level",
            "location_description",
            "address_text",
            "hospital_or_home",
            "institution",
            "family_contact_name",
            "family_contact_phone",
            "logistics_notes",
            "status",
            "assigned_priest",
            "assigned_parish",
            "channel",
            "submitted_at",
            "responded_at",
            "completed_at",
            "timeline",
        )
        read_only_fields = fields


class TrackingLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SacramentRequest
        fields = ("tracking_code", "status", "sacrament_type", "submitted_at")


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["en_route", "completed"])
