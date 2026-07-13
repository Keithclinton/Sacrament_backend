from django.db import models


class UserRole(models.TextChoices):
    MEMBER = "member", "Member"
    PRIEST = "priest", "Priest"
    DIOCESAN_ADMIN = "diocesan_admin", "Diocesan Admin"
    SUPER_ADMIN = "super_admin", "Super Admin"


class VerificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    UNDER_REVIEW = "under_review", "Under Review"
    VERIFIED = "verified", "Verified"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"


class SacramentType(models.TextChoices):
    CONFESSION = "confession", "Confession"
    COMMUNION_FOR_SICK = "communion_for_sick", "Holy Communion for the Sick"
    ANOINTING_OF_THE_SICK = "anointing_of_the_sick", "Anointing of the Sick"
    LAST_RITES = "last_rites", "Last Rites"
    SPIRITUAL_COUNSELLING = "spiritual_counselling", "Spiritual Counselling"


class EmergencyLevel(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    EMERGENCY_DANGER_OF_DEATH = "emergency_danger_of_death", "Emergency - Danger of Death"


class HospitalOrHome(models.TextChoices):
    HOSPITAL = "hospital", "Hospital"
    HOME = "home", "Home"
    CARE_FACILITY = "care_facility", "Care Facility"
    OTHER = "other", "Other"


class RequestStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    ROUTED = "routed", "Routed"
    ACCEPTED = "accepted", "Accepted"
    EN_ROUTE = "en_route", "En Route"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class RequestChannel(models.TextChoices):
    WEB = "web", "Web"
    MOBILE_APP = "mobile_app", "Mobile App"
    USSD = "ussd", "USSD"
    PHONE_CALL_MANUAL_ENTRY = "phone_call_manual_entry", "Phone Call (Manual Entry)"


class EscalationReason(models.TextChoices):
    INITIAL_ROUTING = "initial_routing", "Initial Routing"
    NO_RESPONSE_TIMEOUT = "no_response_timeout", "No Response Timeout"
    PRIEST_DECLINED = "priest_declined", "Priest Declined"
    PRIEST_UNAVAILABLE = "priest_unavailable", "Priest Unavailable"
    MANUAL_ADMIN_ESCALATION = "manual_admin_escalation", "Manual Admin Escalation"


class NotificationChannel(models.TextChoices):
    SMS = "sms", "SMS"
    PUSH = "push", "Push"
    EMAIL = "email", "Email"


class NotificationType(models.TextChoices):
    REQUEST_SUBMITTED_ACK = "request_submitted_ack", "Request Submitted Acknowledgement"
    PRIEST_NEW_REQUEST_ALERT = "priest_new_request_alert", "New Request Alert to Priest"
    REQUEST_ACCEPTED_CONFIRMATION = "request_accepted_confirmation", "Request Accepted Confirmation"
    ESCALATION_ALERT = "escalation_alert", "Escalation Alert"
    STATUS_UPDATE = "status_update", "Status Update"
    VERIFICATION_DECISION = "verification_decision", "Verification Decision"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    DELIVERED = "delivered", "Delivered"
