# USSD Setup Guide (Africa's Talking)

This walks through connecting the already-built USSD backend
(`apps/ussd/views.py`, webhook at `POST /api/ussd/webhook/`) to Africa's
Talking (AT), from sandbox testing through to a production short code.

## 1. Create an Africa's Talking account

1. Sign up at their developer portal (search "Africa's Talking" - no link
   guessed here, use whatever URL you already have or find yourself).
2. Every new account starts with a **Sandbox** app - free, fully functional
   for development, uses a shared test service code (`*384*...#` style) and
   simulated phone numbers. Use this for all local development; do not wait
   for a live account to start building.
3. From the sandbox dashboard, copy:
   - **Username** — literally `sandbox` for the sandbox app.
   - **API Key** — under Settings / API Key in the dashboard.

## 2. Configure this backend with your credentials

Edit `.env` (never commit real credentials):

```bash
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=<your sandbox API key>
AFRICASTALKING_SENDER_ID=            # leave blank in sandbox
USSD_SHARED_SECRET=<generate a long random string>
```

Generate a strong `USSD_SHARED_SECRET` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

This secret is **not** an Africa's Talking setting - it's ours. AT will
append it as a query parameter when calling our webhook, and
`apps/ussd/views.py` rejects any request that doesn't present it (via a
constant-time comparison, so it can't be brute-forced by timing). Keep it
private; treat it like a password.

## 3. Expose your local server to the internet (dev only)

Africa's Talking's servers call *your* webhook over the public internet -
`localhost:8000` is not reachable from them. For local development, tunnel
your dev server with a tool like `ngrok`:

```bash
ngrok http 8000
```

This gives you a public HTTPS URL like `https://abc123.ngrok-free.app`. Your
webhook URL to register with AT becomes:

```
https://abc123.ngrok-free.app/api/ussd/webhook/?secret=<your USSD_SHARED_SECRET>
```

Keep the `ngrok` process running while testing - the URL changes every time
you restart it on the free tier, so you'll need to re-register it in the AT
dashboard after every restart (or use a paid ngrok plan with a static
domain, or deploy to a real staging server instead).

## 4. Register the callback URL in the AT dashboard

1. In the Sandbox app, go to **USSD** in the left nav.
2. Click **Create Channel** (sandbox gives you a shared test service code
   automatically, e.g. `*384*XXXXX#` - note the exact code, you'll dial this
   in the simulator).
3. Set the **Callback URL** to the ngrok URL from step 3, including the
   `?secret=...` query string.
4. Save.

## 5. Test it end-to-end

AT's dashboard includes a **USSD Simulator** (a phone-shaped widget) - use
it to dial the service code and click through the menu exactly like a real
phone would. You should see the same flow implemented in
`apps/ussd/menu.py`:

```
1. Request a priest
2. Check request status
```

Watch your Django server logs (or `apps/ussd/models.USSDSession` via
`/admin/`) to confirm sessions are being created and advancing through
`current_step` correctly.

You can also simulate it entirely with `curl`, without AT at all, exactly
as the automated tests do (see `apps/ussd/tests/test_ussd.py`):

```bash
SECRET=$(grep USSD_SHARED_SECRET .env | cut -d= -f2)
curl -X POST "http://127.0.0.1:8000/api/ussd/webhook/?secret=$SECRET" \
  -d "sessionId=test1&phoneNumber=+254700000000&text="
# then repeat with text=1, text=1*4, text=1*4*1, ... following the prompts
```

## 6. SMS (uses the same AT account/credentials)

No separate signup needed - the same `AFRICASTALKING_USERNAME` /
`AFRICASTALKING_API_KEY` power `apps/notifications/channels.py`'s
`SMSChannel`. In sandbox mode, SMS sends are simulated (visible in the AT
dashboard's SMS logs) and never actually reach a real phone. To send real
SMS even before going fully live, AT sandbox supports adding real phone
numbers as verified test numbers under **Settings → Simulator numbers**.

For production, you'll eventually want a registered **Sender ID** (a short
alphanumeric name recipients see instead of a long number) - request this
under **SMS → Sender IDs** once you have a live account; approval can take
a few business days. Until then, leave `AFRICASTALKING_SENDER_ID` blank and
AT uses a shared default.

## 7. Going live (production)

1. Apply for a live AT account (business registration/KYC documents
   required - this is specific to Kenya/AT's compliance process, follow
   their dashboard prompts).
2. Once approved, you get **live** credentials (different API key/username
   from sandbox) - update the production `.env` (or your secrets manager)
   with these, never reuse sandbox credentials in prod.
3. Apply for a **dedicated USSD service code** (e.g. `*789*12345#`) - shared
   sandbox codes are not usable in production. This goes through Kenya's
   telecom regulatory process via AT and can take longer than the account
   approval itself - start this early if you have a launch date in mind.
4. Point the live channel's callback URL at your real deployed domain
   (not ngrok), e.g. `https://api.yourdomain.org/api/ussd/webhook/?secret=...`,
   over HTTPS only - the shared secret must never travel over plain HTTP in
   production (see `SECURE_SSL_REDIRECT` already enabled in
   `config/settings/prod.py`).
5. Rotate `USSD_SHARED_SECRET` to a fresh production-only value distinct
   from whatever you used in dev/sandbox.

## Troubleshooting

- **403 from the webhook**: the `?secret=` query param doesn't match
  `USSD_SHARED_SECRET` in your running server's environment - check for
  trailing whitespace/quotes when copying the secret into the AT dashboard.
- **AT dashboard shows a timeout**: your tunnel (ngrok) isn't running, the
  Django dev server isn't running, or a firewall is blocking the inbound
  connection - confirm `curl` against the public ngrok URL works before
  blaming AT.
- **Session seems to restart from the main menu unexpectedly**: check
  `USSDSession.is_active` and `current_step` in `/admin/` for that
  `session_id` - if a prior session with the same ID was already marked
  inactive (e.g. by the `cleanup_stale_ussd_sessions` periodic task after 5
  minutes of inactivity), AT sending a new `sessionId` will start fresh,
  which is expected; a *stuck* session usually means an unhandled exception
  in `apps/ussd/menu.py` - check the Django/Celery logs.
- **"Too many requests" response**: the per-phone-number rate limit in
  `apps/ussd/views.py` (`USSD_RATE_LIMIT`, default 30 keypresses per 5
  minutes) was hit - expected under abuse/retries-in-a-loop, not expected
  for a normal user.
