from apps.core.enums import EmergencyLevel, HospitalOrHome, SacramentType

MAIN_MENU = "main_menu"
SACRAMENT_TYPE = "sacrament_type"
EMERGENCY_LEVEL = "emergency_level"
PATIENT_NAME = "patient_name"
LOCATION = "location"
PHONE = "phone"
TRACK_CODE = "track_code"

SACRAMENT_CHOICES = {
    "1": SacramentType.CONFESSION,
    "2": SacramentType.COMMUNION_FOR_SICK,
    "3": SacramentType.ANOINTING_OF_THE_SICK,
    "4": SacramentType.LAST_RITES,
    "5": SacramentType.SPIRITUAL_COUNSELLING,
}

EMERGENCY_CHOICES = {
    "1": EmergencyLevel.EMERGENCY_DANGER_OF_DEATH,
    "2": EmergencyLevel.URGENT,
    "3": EmergencyLevel.ROUTINE,
}


def handle_ussd_input(session, text: str) -> str:
    """
    Advances the session one step and returns the raw AT response body
    ("CON ..." to continue, "END ..." to terminate). Only the *last* segment
    of `text` (the newest keypress) is parsed - state is tracked explicitly
    in USSDSession.current_step / collected_data rather than by replaying
    the whole input history each time.
    """
    last_input = text.split("*")[-1] if text else ""
    state = session.current_step

    if state == "init":
        return _advance(session, MAIN_MENU, "CON Welcome to the Sacrament Assistance Platform.\n1. Request a priest\n2. Check request status")

    if state == MAIN_MENU:
        if last_input == "1":
            return _advance(
                session,
                SACRAMENT_TYPE,
                "CON Select sacrament needed:\n1. Confession\n2. Communion for the sick\n"
                "3. Anointing of the Sick\n4. Last Rites\n5. Spiritual counselling",
            )
        if last_input == "2":
            return _advance(session, TRACK_CODE, "CON Enter your request reference code (e.g. SAC-XXXXX):")
        return _end(session, "END Invalid choice. Please dial in again.")

    if state == SACRAMENT_TYPE:
        sacrament_type = SACRAMENT_CHOICES.get(last_input)
        if not sacrament_type:
            return _end(session, "END Invalid choice. Please dial in again.")
        session.collected_data["sacrament_type"] = sacrament_type
        return _advance(
            session,
            EMERGENCY_LEVEL,
            "CON How urgent?\n1. Emergency (danger of death)\n2. Urgent\n3. Routine",
        )

    if state == EMERGENCY_LEVEL:
        emergency_level = EMERGENCY_CHOICES.get(last_input)
        if not emergency_level:
            return _end(session, "END Invalid choice. Please dial in again.")
        session.collected_data["emergency_level"] = emergency_level
        return _advance(session, PATIENT_NAME, "CON Enter the patient's name:")

    if state == PATIENT_NAME:
        if not last_input.strip():
            return _end(session, "END Patient name is required. Please dial in again.")
        session.collected_data["patient_name"] = last_input.strip()
        return _advance(
            session, LOCATION, "CON Enter location/landmark (e.g. hospital name, ward, or nearest town):"
        )

    if state == LOCATION:
        if not last_input.strip():
            return _end(session, "END Location is required. Please dial in again.")
        session.collected_data["location_description"] = last_input.strip()
        return _advance(session, PHONE, "CON Enter a contact phone number, or 0 to use this number:")

    if state == PHONE:
        phone = session.phone_number if last_input.strip() == "0" else last_input.strip()
        return _submit_request(session, phone)

    if state == TRACK_CODE:
        return _track_request(session, last_input.strip().upper())

    return _end(session, "END Session error. Please dial in again.")


def _advance(session, next_step: str, prompt: str) -> str:
    session.current_step = next_step
    session.save(update_fields=["current_step", "collected_data", "last_interaction_at"])
    return prompt


def _end(session, message: str) -> str:
    session.is_active = False
    session.save(update_fields=["is_active", "last_interaction_at"])
    return message


def _submit_request(session, phone: str) -> str:
    from apps.requests_app.services import create_sacrament_request

    data = {
        "requester_name": session.collected_data["patient_name"],
        "requester_phone": phone,
        "patient_name": session.collected_data["patient_name"],
        "sacrament_type": session.collected_data["sacrament_type"],
        "emergency_level": session.collected_data["emergency_level"],
        "location_description": session.collected_data["location_description"],
        "hospital_or_home": HospitalOrHome.OTHER,
    }
    sacrament_request = create_sacrament_request(data=data, channel="ussd")
    return _end(
        session,
        f"END Your request has been submitted. Reference: {sacrament_request.tracking_code}. "
        "You will be contacted shortly.",
    )


def _track_request(session, tracking_code: str) -> str:
    from apps.requests_app.models import SacramentRequest

    try:
        sacrament_request = SacramentRequest.objects.get(tracking_code=tracking_code)
        message = f"END Status: {sacrament_request.get_status_display()}"
    except SacramentRequest.DoesNotExist:
        message = "END No request found with that reference code."
    return _end(session, message)
