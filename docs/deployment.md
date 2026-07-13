# Deployment Guide

The project splits across two hosts: **Vercel** for the Next.js frontend, **Railway** for
the Django backend (it needs PostgreSQL+PostGIS, Redis, and an always-running Celery
worker — none of which run on Vercel's serverless model).

This doc is a checklist for when you're ready to actually deploy — nothing here has been
run yet.

## Backend on Railway

Services needed in one Railway project:

1. **Web** — runs `gunicorn config.wsgi` (see `Procfile`'s `web` line). Railway auto-detects
   this via the `Procfile` at the repo root.
2. **Worker** — runs `celery -A config worker` (the `Procfile`'s `worker` line) as a
   separate Railway service pointed at the same repo/image. Without this, no
   notifications send and no emergency escalation timeouts ever fire.
3. **Beat** (optional but recommended) — `celery -A config beat` (the `Procfile`'s `beat`
   line), for the periodic USSD session cleanup job.
4. **PostgreSQL** — Railway's standard Postgres template.
5. **Redis** — Railway's Redis template (backs Celery's broker/result backend, DRF
   throttling, and the USSD rate limiter).

**⚠️ PostGIS check before you commit to a Postgres provider.** This app hard-requires the
`postgis` extension (GeoDjango). Verify Railway's Postgres image supports
`CREATE EXTENSION postgis;` before deploying — if their default image doesn't ship
PostGIS, you'll need either a custom Docker image with it installed, or a
Postgres-with-PostGIS-specific provider (e.g. Supabase, Crunchy Bridge, or a
self-managed instance). Don't find this out after everything else is wired up — test the
extension first against whatever Postgres instance you provision.

**Environment variables to set** (mirrors `.env.example`):

```
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<generate a new one, never reuse the dev one>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-railway-domain>
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT   # from Railway's Postgres service
CELERY_BROKER_URL, CELERY_RESULT_BACKEND          # from Railway's Redis service
REDIS_CACHE_URL                                    # same Redis, different db index (see config/settings/base.py CACHES)
AFRICASTALKING_USERNAME, AFRICASTALKING_API_KEY, AFRICASTALKING_SENDER_ID
USSD_SHARED_SECRET                                 # rotate to a fresh prod-only value
ALLOWED_CHURCH_EMAIL_DOMAINS
```

Note: `CORS_ALLOWED_ORIGINS` is *not* needed — the Next.js frontend talks to Django
server-side only (BFF pattern via `djangoFetch`), never from the browser directly, so
there's no cross-origin browser request to configure.

Run once after first deploy: `python manage.py createsuperuser` (via Railway's shell/exec),
and confirm it got `role=super_admin` (the custom `UserManager` handles this
automatically — see `apps/accounts/models.py`).

## Frontend on Vercel

- **Root Directory**: set to `frontend/` in the Vercel project settings (this is a
  monorepo — Django lives at the repo root, the Next.js app is in `frontend/`).
- **Environment variable**: `DJANGO_API_URL=https://<your-railway-backend-domain>`
  (server-side only, no `NEXT_PUBLIC_` prefix — the browser never talks to it directly).
- No other config needed; Vercel auto-detects Next.js App Router.

## Post-deploy smoke test

Same checklist as local dev (see main `README.md`'s "Verifying it works" section), just
against the real domains:
1. Submit a request anonymously at `https://<vercel-domain>/`
2. Register a priest, verify them via `/admin/verification-queue`
3. Confirm the priest dashboard location-share + accept flow works
4. Point Africa's Talking's USSD callback at
   `https://<railway-domain>/api/ussd/webhook/?secret=<USSD_SHARED_SECRET>` (see
   `docs/ussd_setup.md` — this replaces the ngrok tunnel used for local dev, since Railway
   gives you a real public HTTPS URL for free)
