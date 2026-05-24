# Deploy `usmonitor.app`

This checklist assumes the app is deployed on Render and the domain is managed
in Dynadot.

## 1. Push the app to GitHub

Render needs access to a Git repository. Create a private GitHub repo and push
this workspace.

## 2. Create the Render Blueprint

In Render:

1. New > Blueprint.
2. Connect the GitHub repo.
3. Select `render.yaml`.
4. Create the web service, cron job, and Postgres database.

Set these production env vars on both the web service and cron job:

- `APP_BASE_URL=https://usmonitor.app`
- `ADMIN_EMAILS=santazhj@gmail.com`
- `OPENAI_API_KEY=<your OpenAI API key>`
- `X_BEARER_TOKEN=<your X API bearer token>`
- `RESEND_API_KEY=<your Resend API key>`
- `EMAIL_FROM=US Monitor <alerts@usmonitor.app>`
- `VAPID_PUBLIC_KEY=<generated public key>`
- `VAPID_PRIVATE_KEY=<generated private key>`
- `VAPID_CONTACT=mailto:alerts@usmonitor.app`
- `USDT_TRC20_ADDRESS=TKFHqMfArpi8wA8kCEEj6rV3HdcM1zfT5g`
- `USDT_ERC20_ADDRESS=0x7c9C0574fa32886F6e6BCc3BD2f5502C4e7F1609`
- `MONTHLY_PRICE_USDT=99`
- `SEND_INITIAL_BACKFILL=false`

Generate VAPID keys locally with:

```powershell
.\.venv\Scripts\python.exe -m app.cli generate-vapid
```

## 3. Add the Custom Domain in Render

In the Render web service:

1. Settings > Custom Domains.
2. Add `usmonitor.app`.
3. Add `www.usmonitor.app` if you want `www` to work too.
4. Copy the DNS records Render shows.

Render will provision HTTPS after DNS resolves.

## 4. Set Dynadot DNS

In Dynadot:

1. My Domains > Manage Domains > `usmonitor.app`.
2. DNS Settings.
3. Use Dynadot DNS unless you move DNS to Cloudflare.
4. Add the records Render gives you.

Typical Render setup:

- `www` as a `CNAME` pointing to your Render service hostname.
- Root/apex `usmonitor.app` as the root record Render asks for. Use the exact
  record type/value Render displays because root-domain support depends on the
  DNS provider.

## 5. Configure Resend for Login Email

In Resend:

1. Add domain `usmonitor.app`.
2. Add the DNS records Resend gives you in Dynadot.
3. Wait for verification.
4. Set `EMAIL_FROM=US Monitor <alerts@usmonitor.app>`.

Alerts still use PWA push. Email is only for magic-link login and account
messages.

## 6. Production Smoke Test

After DNS and deploy:

1. Open `https://usmonitor.app`.
2. Sign in as the admin email.
3. Create an invite.
4. Sign in with a friend email using that invite.
5. Confirm the pending payment in `/admin`.
6. Add the site to iPhone home screen.
7. Enable push and send a test push.
8. Trigger `/admin` > immediate poll.

If `X_BEARER_TOKEN` is missing, the poll job will safely skip instead of
failing.
