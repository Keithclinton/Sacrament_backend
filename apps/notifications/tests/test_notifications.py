import pytest

from apps.core.enums import NotificationStatus
from apps.core.factories import UserFactory
from apps.notifications import channels as notification_channels
from apps.notifications.models import NotificationLog
from apps.notifications.services import notify

# transaction=True: notify() dispatches via transaction.on_commit, which
# never fires under the default (rolled-back) django_db transaction.
pytestmark = pytest.mark.django_db(transaction=True)


class _FakeChannel:
    def __init__(self, success=True, provider_id="fake-id", error=""):
        self.success = success
        self.provider_id = provider_id
        self.error = error
        self.calls = []

    def send(self, *, phone, email, message):
        self.calls.append((phone, email, message))
        return self.success, self.provider_id, self.error


class TestNotifyDispatcher:
    def test_skips_email_channel_when_no_email(self):
        user = UserFactory(email="")
        logs = notify(
            user=user, notification_type="request_submitted_ack", context={"tracking_code": "SAC-TEST1"},
            channels=["email"],
        )
        assert logs == []
        assert NotificationLog.objects.count() == 0

    def test_skips_sms_channel_when_no_phone(self):
        logs = notify(
            user=None, phone="", notification_type="request_submitted_ack",
            context={"tracking_code": "SAC-TEST2"}, channels=["sms"],
        )
        assert logs == []

    def test_creates_one_log_per_valid_channel(self):
        user = UserFactory(email="priest@example.com")
        logs = notify(
            user=user, notification_type="request_submitted_ack", context={"tracking_code": "SAC-TEST3"},
            channels=["sms", "email"],
        )
        assert len(logs) == 2
        assert {log.channel for log in logs} == {"sms", "email"}

    def test_dispatch_updates_log_status_on_success(self, monkeypatch):
        fake = _FakeChannel(success=True, provider_id="msg-123")
        monkeypatch.setitem(notification_channels.CHANNEL_REGISTRY, "sms", fake)

        user = UserFactory()
        notify(
            user=user, notification_type="request_submitted_ack", context={"tracking_code": "SAC-TEST4"},
            channels=["sms"],
        )
        log = NotificationLog.objects.get(notification_type="request_submitted_ack")
        assert log.status == NotificationStatus.SENT
        assert log.provider_message_id == "msg-123"
        assert fake.calls  # channel.send() was actually invoked by the (eager) Celery task

    def test_dispatch_marks_failed_on_error(self, monkeypatch):
        fake = _FakeChannel(success=False, error="gateway down")
        monkeypatch.setitem(notification_channels.CHANNEL_REGISTRY, "sms", fake)

        user = UserFactory()
        notify(
            user=user, notification_type="status_update", context={"tracking_code": "SAC-TEST5", "status": "accepted"},
            channels=["sms"],
        )
        log = NotificationLog.objects.get(notification_type="status_update")
        assert log.status == NotificationStatus.FAILED
        assert log.error_message == "gateway down"

    def test_log_persists_regardless_of_send_outcome(self, monkeypatch):
        """Auditable: a failed gateway send still leaves a permanent record."""
        fake = _FakeChannel(success=False, error="network error")
        monkeypatch.setitem(notification_channels.CHANNEL_REGISTRY, "sms", fake)

        user = UserFactory()
        before = NotificationLog.objects.count()
        notify(user=user, notification_type="status_update", context={"status": "completed"}, channels=["sms"])
        assert NotificationLog.objects.count() == before + 1
