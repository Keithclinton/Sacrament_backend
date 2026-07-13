# Sacrament Assistance Platform — Backend

Django + DRF backend for a Catholic sacramental assistance platform (Kenya v1): connects
the faithful in urgent need with verified, diocesan-approved priests for physical
pastoral care. This service is strictly a **coordination and logistics layer** — it never
stores confession content or any sacramental conversation, only request metadata,
location, urgency, and contact details.

Channels: REST API (web/mobile) and USSD (Africa's Talking), both backed by the same
request-creation service layer.

## Stack

- Django 5 + Django REST Framework
- PostgreSQL + PostGIS (GeoDjango) — nearest-priest geo matching
- JWT auth via `djangorestframework-simplejwt`
- Celery + Redis — async notifications and time-boxed emergency escalation
- Africa's Talking — SMS + USSD gateway
- drf-spectacular — OpenAPI schema / Swagger docs

## Apps

| App | Owns |
|---|---|
| `apps.core` | Base models, shared enums, permission classes |
| `apps.accounts` | Custom `User` model, JWT auth, `DiocesanAdminProfile` |
| `apps.dioceses` | Diocese → Deanery → Parish hierarchy, Institutions (hospitals/chaplaincies) |
| `apps.clergy` | `PriestProfile`, diocesan verification workflow |
| `apps.requests_app` | `SacramentRequest`, status timeline, the shared request-creation service |
| `apps.routing` | PostGIS nearest-priest matching, emergency escalation |
| `apps.notifications` | SMS/email/push channel abstraction, `NotificationLog` |
| `apps.ussd` | Africa's Talking webhook, USSD menu state machine |
| `apps.audit` | Cross-cutting immutable audit log (fed by signals) |

## Local setup

System dependencies (already installed in this Codespace): PostgreSQL 16 + PostGIS,
GDAL/GEOS/PROJ, Redis.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env   # adjust secrets/credentials as needed

python manage.py migrate
python manage.py createsuperuser
```

Run the stack (three processes):

```bash
# 1. API server
python manage.py runserver 0.0.0.0:8000

# 2. Celery worker (notifications + escalation timeouts)
celery -A config worker --loglevel=info

# 3. (optional) Celery beat, for periodic USSD session cleanup
celery -A config beat --loglevel=info
```

Settings modules: `config.settings.dev` (default via `manage.py`), `.test`, `.prod`
(used by `wsgi.py`/`asgi.py`).

## Running the tests

```bash
python -m pytest
```

Uses `pytest-django` + `factory_boy` (see `apps/core/factories.py` for shared factories).
A real Postgres/Redis are required (not mocked) — tests use `config.settings.test`
(`pytest.ini`), which creates/drops a throwaway test database each run. Most test
classes are marked `django_db(transaction=True)` rather than the plain `django_db`
default: several code paths (`notify()`, escalation scheduling) dispatch via
`transaction.on_commit`, which never fires under the default rolled-back test
transaction — see the comment in `apps/requests_app/tests/test_requests.py` if adding
new tests that touch notifications or routing.

## USSD (Africa's Talking) setup

See **[docs/ussd_setup.md](docs/ussd_setup.md)** for the full walkthrough — sandbox
account, exposing your local server via ngrok, registering the callback URL, testing
with AT's simulator, and what changes when going live with a production service code.

## Verifying it works (no frontend yet)

- **Django Admin** (`/admin/`) — fastest end-to-end check: create a Diocese/Parish,
  register a priest, walk `pending → under_review → verified` via the `PriestProfile`
  admin actions, watch a `SacramentRequest` move through its timeline.
- **Swagger / OpenAPI docs** — `/api/docs/` (schema at `/api/schema/`).
- **DRF Browsable API** — enabled in dev settings; any endpoint can be exercised from a
  browser.
- **curl smoke test** (happy path):
  1. `POST /api/requests/` — create a request anonymously (no auth needed; a member can
     also register/login first via `/api/accounts/register/` + `/api/accounts/auth/token/`
     to get request history under `/api/requests/mine/`)
  2. `POST /api/clergy/priests/register/` — register a priest (starts `pending`)
  3. Verify the priest via `/admin/` or `POST /api/clergy/priests/{id}/verify/`
     (diocesan_admin/super_admin only — create one via
     `POST /api/accounts/diocesan-admins/` as a super_admin, or Django admin)
  4. `POST /api/requests/{id}/accept/` (as the verified priest)
  5. `GET /api/requests/track/{tracking_code}/` — public status lookup, no auth

- **USSD**: point Africa's Talking's USSD callback at
  `POST /api/ussd/webhook/?secret=<USSD_SHARED_SECRET>` (or simulate with curl, POSTing
  `sessionId`, `phoneNumber`, `text` form fields — see the menu tree in `apps/ussd/menu.py`).

## Key design notes

- **No sacramental content, ever.** `SacramentRequest` has no field for confession/
  spiritual content by design — only logistics (`logistics_notes`, max 1000 chars).
- **Anonymous or logged-in, both work.** `SacramentRequestCreateView` is deliberately
  `AllowAny` (see [apps/requests_app/views.py](apps/requests_app/views.py)) — a panicking
  family member shouldn't have to register mid-emergency. `requester` stays `null` for
  guest submissions; logged-in members get theirs linked for history under
  `/api/requests/mine/`. USSD is anonymous by necessity, same underlying behavior.
- **Verification gate.** `apps.core.permissions.IsVerifiedPriest` is the single choke
  point for all priest-only functionality — being `role=priest` is never sufficient on
  its own; every priest-only view checks both role and `PriestProfile.verification_status
  == verified`. Diocesan admins are appointed via a super_admin-only endpoint
  (`POST /api/accounts/diocesan-admins/`), never self-registered.
- **One service layer, two entry points.** `apps.requests_app.services.create_sacrament_request`
  is called by both the DRF serializer and the USSD webhook, so request-creation logic
  never has two implementations.
- **Emergency routing, workload-aware.** Nearest-priest matching widens its search
  radius in tiers (`ROUTING_RADIUS_TIERS_KM`), then ranks candidates by distance plus a
  penalty per currently active assigned request (`WORKLOAD_PENALTY_METERS_PER_ACTIVE_REQUEST`)
  so a nearby but already-overloaded priest doesn't always get piled on. Falls back to
  notifying diocesan admins if nobody is found. Unaccepted requests escalate
  automatically after a timeout keyed by emergency level (`ESCALATION_TIMEOUT_MINUTES`),
  via a Celery task guarded against races with acceptance/cancellation.
- **USSD location fallback.** USSD has no GPS, only a free-text landmark description.
  `apps.routing.geocoding.resolve_location_from_description` matches that text against
  known Parish/Institution names (case-insensitive substring match, checked in both
  directions) before giving up — a deliberately simple v1 heuristic, not a real geocoder;
  see the module docstring for when to revisit it.
- **Notifications are always logged**, in `NotificationLog`, regardless of whether the
  underlying SMS/email/push send succeeds — auditable even when the gateway fails.
  `notify()` defers Celery dispatch via `transaction.on_commit` to avoid a race where
  the worker processes a task before its DB row is committed.
- **Throttling.** Anonymous/guest request creation and the public tracking lookup are
  rate-limited (`DEFAULT_THROTTLE_RATES` in `config/settings/base.py`) since both are
  unauthenticated endpoints that can trigger real SMS sends. The USSD webhook has its
  own per-phone-number limiter (`apps/ussd/views.py`) since DRF throttling doesn't apply
  to it. Both share the Redis-backed cache (`CACHES`), so limits hold across worker
  processes, not just per-process.
- **Auth.** JWT (`djangorestframework-simplejwt`) is primary; `SessionAuthentication` is
  also registered so staff can use the Browsable API / admin session without minting a
  token — CSRF is still enforced automatically for session-authenticated writes.

## Known gaps / next steps

- Push notifications (`PushChannel`) are a stub pending a mobile app + provider choice
  (FCM/Expo/OneSignal) — can't be finished until the frontend/mobile stack exists.
- Africa's Talking and SMTP credentials in `.env` are placeholders; real sends will fail
  until production credentials are configured (see `docs/ussd_setup.md`).
- The USSD location-matching heuristic (see above) iterates parishes/institutions in
  Python rather than pushing the match into SQL — fine for a single-country v1, revisit
  (e.g. `pg_trgm` similarity, or a real geocoding API) if coverage grows substantially.
