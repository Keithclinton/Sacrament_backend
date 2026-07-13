from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.core.enums import UserRole

from .models import DiocesanAdminProfile, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Embeds role (and verification status, for priests) directly in the JWT so
    permission classes and the frontend can branch without an extra API call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        if user.role == UserRole.PRIEST:
            profile = getattr(user, "priest_profile", None)
            token["verification_status"] = profile.verification_status if profile else None
        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "preferred_language",
            "role",
            "date_joined",
        )
        read_only_fields = ("id", "role", "date_joined")


class MemberRegistrationSerializer(serializers.ModelSerializer):
    """
    Self-registration for ordinary members only. `role` is never accepted
    from the client - it is hardcoded to MEMBER here so nobody can register
    themselves as a priest or admin through this endpoint.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "preferred_language",
            "password",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=UserRole.MEMBER, **validated_data)
        user.set_password(password)
        user.save()
        return user


class DiocesanAdminCreateSerializer(serializers.ModelSerializer):
    """
    Diocesan admins are appointed, not self-registered - this is a
    super_admin-only endpoint (see IsSuperAdmin on the view), unlike member
    or priest registration which are open self-signup flows.
    """

    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = DiocesanAdminProfile
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "diocese",
        )
        read_only_fields = ("id",)

    @transaction.atomic
    def create(self, validated_data):
        user_fields = {
            key: validated_data.pop(key)
            for key in ("username", "email", "first_name", "last_name", "phone_number", "password")
        }
        password = user_fields.pop("password")
        user = User(role=UserRole.DIOCESAN_ADMIN, **user_fields)
        user.set_password(password)
        user.save()
        return DiocesanAdminProfile.objects.create(user=user, **validated_data)


class DiocesanAdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiocesanAdminProfile
        fields = ("id", "user", "diocese")
        read_only_fields = fields
