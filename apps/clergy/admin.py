from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import PriestProfile, PriestVerificationEvent


class PriestVerificationEventInline(admin.TabularInline):
    model = PriestVerificationEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "notes", "created_at")
    can_delete = False


@admin.register(PriestProfile)
class PriestProfileAdmin(GISModelAdmin):
    list_display = (
        "user",
        "diocese",
        "parish",
        "verification_status",
        "is_available",
        "verified_at",
    )
    list_filter = ("verification_status", "diocese", "is_available")
    search_fields = ("user__username", "user__first_name", "user__last_name", "diocesan_id_number")
    inlines = [PriestVerificationEventInline]
    readonly_fields = ("verified_by", "verified_at")

    actions = ["mark_under_review", "mark_verified", "mark_rejected", "mark_suspended"]

    @admin.action(description="Move selected priests to Under Review")
    def mark_under_review(self, request, queryset):
        self._bulk_transition(request, queryset, "under_review")

    @admin.action(description="Verify selected priests")
    def mark_verified(self, request, queryset):
        self._bulk_transition(request, queryset, "verified")

    @admin.action(description="Reject selected priests")
    def mark_rejected(self, request, queryset):
        self._bulk_transition(request, queryset, "rejected", notes="Rejected via admin bulk action.")

    @admin.action(description="Suspend selected priests")
    def mark_suspended(self, request, queryset):
        self._bulk_transition(request, queryset, "suspended")

    def _bulk_transition(self, request, queryset, to_status, notes=""):
        from django.core.exceptions import PermissionDenied, ValidationError

        from .services import transition_priest_verification

        for priest_profile in queryset:
            try:
                transition_priest_verification(
                    priest_profile=priest_profile, to_status=to_status, actor=request.user, notes=notes
                )
            except (ValidationError, PermissionDenied) as exc:
                self.message_user(request, f"{priest_profile}: {exc}", level="error")


@admin.register(PriestVerificationEvent)
class PriestVerificationEventAdmin(admin.ModelAdmin):
    list_display = ("priest_profile", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)
    readonly_fields = ("priest_profile", "from_status", "to_status", "changed_by", "notes", "created_at")
