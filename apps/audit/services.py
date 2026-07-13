from .models import AuditLog


def log_action(*, actor, action: str, target=None, metadata: dict | None = None):
    AuditLog.objects.create(actor=actor, action=action, target=target, metadata=metadata or {})
