MESSAGE_TEMPLATES = {
    "request_submitted_ack": "We've received your sacrament request, ref {tracking_code}. A priest will be notified shortly.",
    "priest_new_request_alert": "New {emergency_level} sacrament request assigned to you. Ref {tracking_code}. Please open the app to respond.",
    "request_accepted_confirmation": "{priest_name} has accepted your request (ref {tracking_code}) and will be in touch.",
    "escalation_alert": "Sacrament request {tracking_code} needs attention: {reason}.",
    "status_update": "Your sacrament request {tracking_code} status is now: {status}.",
    "verification_decision": "Your priest verification status is now: {to_status}. {notes}",
}


def render_message(notification_type: str, context: dict) -> str:
    template = MESSAGE_TEMPLATES.get(notification_type, "Sacrament Assistance Platform update: {context}")
    try:
        return template.format(**context)
    except KeyError:
        return template
