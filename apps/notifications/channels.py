from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import send_mail


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, *, phone: str | None, email: str | None, message: str) -> tuple[bool, str, str]:
        """Returns (success, provider_message_id, error_message)."""
        raise NotImplementedError


class SMSChannel(NotificationChannel):
    def send(self, *, phone, email, message):
        if not phone:
            return False, "", "No phone number provided."
        try:
            import africastalking

            africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
            sms = africastalking.SMS
            kwargs = {}
            if settings.AFRICASTALKING_SENDER_ID:
                kwargs["sender_id"] = settings.AFRICASTALKING_SENDER_ID
            response = sms.send(message, [phone], **kwargs)
            recipients = response.get("SMSMessageData", {}).get("Recipients", [])
            if recipients and recipients[0].get("status") == "Success":
                return True, recipients[0].get("messageId", ""), ""
            error = recipients[0].get("status") if recipients else "Unknown SMS gateway error"
            return False, "", error
        except Exception as exc:  # gateway/network failures must never break the request flow
            return False, "", str(exc)


class EmailChannel(NotificationChannel):
    def send(self, *, phone, email, message):
        if not email:
            return False, "", "No email address provided."
        try:
            send_mail(
                subject="Sacrament Assistance Platform Notification",
                message=message,
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
            return True, "", ""
        except Exception as exc:
            return False, "", str(exc)


class PushChannel(NotificationChannel):
    """
    Stub until a mobile app / push provider (FCM, Expo, OneSignal) is chosen.
    Logs intent only; SMS remains the reliable channel for v1.
    """

    def send(self, *, phone, email, message):
        return False, "", "Push notifications not yet configured."


CHANNEL_REGISTRY = {
    "sms": SMSChannel(),
    "email": EmailChannel(),
    "push": PushChannel(),
}
