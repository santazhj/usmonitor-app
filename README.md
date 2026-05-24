# Serenity Alerts

Invite-only PWA alerts for curated market intelligence. The first list monitors
`@aleabitoreddit` original posts every 15 minutes, summarizes them in Simplified
Chinese, and pushes alerts to iPhone home-screen web apps.

## Local setup

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m app.cli init-db
.\.venv\Scripts\python -m app.cli create-invite "founder"
.\.venv\Scripts\python -m app.cli generate-vapid
.\.venv\Scripts\uvicorn app.main:app --reload
```

This workspace also includes a local `.env` with development-only keys and
`ADMIN_EMAILS=admin@example.com`, so you can start immediately:

```powershell
.\scripts\start-dev.ps1
```

In another terminal:

```powershell
.\.venv\Scripts\python.exe .\scripts\smoke.py
```

If `RESEND_API_KEY` is blank, login requests return a development magic link in
the API response. If `OPENAI_API_KEY` is blank, poll jobs create deterministic
fallback summaries so the end-to-end flow can be tested without model spend.

## Required production secrets

- `APP_BASE_URL`
- `SECRET_KEY`
- `ADMIN_EMAILS`
- `OPENAI_API_KEY`
- `X_BEARER_TOKEN`
- `RESEND_API_KEY`
- `VAPID_PUBLIC_KEY`
- `VAPID_PRIVATE_KEY`
- `VAPID_CONTACT`
- `USDT_TRC20_ADDRESS`
- `USDT_ERC20_ADDRESS`

## Render

Use `render.yaml` as a blueprint. Deploy the web service and cron job in the
Singapore region, attach the Render Postgres database, then set the secret env
vars listed above.

For the first production domain, follow [docs/deploy-usmonitor-app.md](docs/deploy-usmonitor-app.md).

## Operations

- Admin URL: `/admin`
- Create invites from the admin page or `python -m app.cli create-invite`
- Confirm manual USDT payments from `/admin`
- Trigger an immediate poll from `/admin` or `python -m app.jobs.poll_sources`

All alerts include a non-investment-advice disclaimer in the feed. Push
notifications are short by design and link back to the source post and full
alert detail.
