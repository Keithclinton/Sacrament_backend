"""
Best-effort location resolution for channels with no GPS (USSD, phone-call
manual entry). Rather than call an external geocoding API - extra latency,
cost, and a network dependency in the critical path of an emergency request -
this matches the free-text landmark description against parishes/institutions
we already know about, since what actually matters for routing is proximity
to *our* known coverage points, not a precise street address.

This is a deliberately simple v1 heuristic (case-insensitive substring
match, checked in both directions). It will not scale gracefully to a very
large number of parishes/institutions since it iterates in Python rather
than pushing the match into SQL - acceptable for a single-country v1, worth
revisiting (e.g. trigram similarity via pg_trgm, or a real geocoding API)
if/when coverage grows substantially.
"""


def resolve_location_from_description(location_description: str):
    if not location_description or not location_description.strip():
        return None

    from apps.dioceses.models import Institution, Parish

    normalized = location_description.strip().lower()

    for model in (Institution, Parish):
        for name, location in model.objects.filter(is_active=True).values_list("name", "location"):
            candidate = name.strip().lower()
            if candidate and (candidate in normalized or normalized in candidate):
                return location
    return None
