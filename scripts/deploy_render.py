from __future__ import annotations

import argparse
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "https://api.render.com/v1"

REPO_URL = "https://github.com/santazhj/usmonitor-app"
APP_BASE_URL = "https://usmonitor.app"
WEB_SERVICE_NAME = "usmonitor-app"
CRON_SERVICE_NAME = "usmonitor-poll"
POSTGRES_NAME = "usmonitor-db"
REGION = "singapore"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def load_settings() -> dict[str, str]:
    merged: dict[str, str] = {}
    merged.update(load_env_file(ROOT / ".env"))
    merged.update(load_env_file(ROOT / ".env.deploy"))
    merged.update({key: value for key, value in os.environ.items() if value})
    return merged


def require(settings: dict[str, str], names: list[str]) -> None:
    missing = [name for name in names if not settings.get(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required values in .env.deploy: {joined}")


class RenderAPI:
    def __init__(self, api_key: str):
        self.client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Render API {method} {path} failed: "
                f"{response.status_code} {response.text}"
            )
        if not response.content:
            return None
        return response.json()

    def list_paginated(
        self, path: str, params: dict[str, str], item_key: str
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor = ""
        while True:
            query = dict(params)
            query["limit"] = "100"
            if cursor:
                query["cursor"] = cursor
            page = self.request("GET", path, params=query)
            if not page:
                break
            for entry in page:
                items.append(entry.get(item_key, entry))
            cursor = page[-1].get("cursor", "") if isinstance(page[-1], dict) else ""
            if not cursor:
                break
        return items

    def service_env_vars(self, service_id: str) -> dict[str, str]:
        entries = self.request("GET", f"/services/{service_id}/env-vars")
        values: dict[str, str] = {}
        for entry in entries:
            env_var = entry.get("envVar", entry)
            key = env_var.get("key")
            value = env_var.get("value")
            if key and value is not None:
                values[key] = value
        return values


def choose_owner(api: RenderAPI, settings: dict[str, str]) -> str:
    if settings.get("RENDER_OWNER_ID"):
        return settings["RENDER_OWNER_ID"]

    owners = api.request("GET", "/owners")
    unwrapped = [entry.get("owner", entry) for entry in owners]
    preferred_email = settings.get("RENDER_OWNER_EMAIL", "santazhj@gmail.com").lower()
    matching = [
        owner
        for owner in unwrapped
        if owner.get("email", "").lower() == preferred_email
    ]
    if len(matching) == 1:
        return matching[0]["id"]
    if len(unwrapped) == 1:
        return unwrapped[0]["id"]

    print("Multiple Render owners found. Add RENDER_OWNER_ID to .env.deploy:")
    for owner in unwrapped:
        print(f"- {owner.get('id')} {owner.get('name')} {owner.get('email')}")
    raise SystemExit(2)


def existing_postgres(api: RenderAPI, owner_id: str) -> dict[str, Any] | None:
    matches = api.list_paginated(
        "/postgres",
        {"ownerId": owner_id, "name": POSTGRES_NAME, "region": REGION},
        "postgres",
    )
    return matches[0] if matches else None


def ensure_postgres(api: RenderAPI, owner_id: str) -> dict[str, Any]:
    postgres = existing_postgres(api, owner_id)
    if postgres:
        print(f"Using existing Postgres: {postgres['name']} ({postgres['id']})")
        return postgres

    print("Creating Render Postgres...")
    return api.request(
        "POST",
        "/postgres",
        json={
            "name": POSTGRES_NAME,
            "ownerId": owner_id,
            "plan": "basic_256mb",
            "region": REGION,
            "version": "17",
            "databaseName": "usmonitor",
            "databaseUser": "usmonitor",
        },
    )


def wait_for_database_url(api: RenderAPI, postgres_id: str) -> str:
    print("Waiting for Postgres connection info...")
    for _ in range(60):
        try:
            info = api.request("GET", f"/postgres/{postgres_id}/connection-info")
            url = info.get("internalConnectionString")
            if url:
                return url
        except RuntimeError:
            pass
        time.sleep(10)
    raise TimeoutError("Postgres connection info was not available after 10 minutes")


def env_list(values: dict[str, str]) -> list[dict[str, str]]:
    return [{"key": key, "value": value} for key, value in values.items()]


def service_by_name(
    api: RenderAPI, owner_id: str, name: str, service_type: str
) -> dict[str, Any] | None:
    services = api.list_paginated(
        "/services",
        {"ownerId": owner_id, "name": name, "type": service_type},
        "service",
    )
    return services[0] if services else None


def ensure_service(
    api: RenderAPI,
    owner_id: str,
    name: str,
    service_type: str,
    details: dict[str, Any],
    env: dict[str, str],
    autodeploy: str = "yes",
) -> dict[str, Any]:
    existing = service_by_name(api, owner_id, name, service_type)
    if existing:
        print(f"Using existing service: {name} ({existing['id']})")
        api.request("PUT", f"/services/{existing['id']}/env-vars", json=env_list(env))
        return existing

    print(f"Creating service: {name}...")
    created = api.request(
        "POST",
        "/services",
        json={
            "type": service_type,
            "name": name,
            "ownerId": owner_id,
            "repo": REPO_URL,
            "branch": "main",
            "autoDeploy": autodeploy,
            "envVars": env_list(env),
            "serviceDetails": details,
        },
    )
    return created.get("service", created)


def trigger_deploy(api: RenderAPI, service_id: str) -> None:
    api.request("POST", f"/services/{service_id}/deploys", json={"clearCache": "do_not_clear"})


def add_custom_domain(api: RenderAPI, service_id: str, domain: str) -> None:
    existing = api.request("GET", f"/services/{service_id}/custom-domains")
    domains = [entry.get("customDomain", entry).get("name") for entry in existing]
    if domain in domains:
        print(f"Custom domain already exists: {domain}")
        return
    print(f"Adding custom domain: {domain}")
    api.request("POST", f"/services/{service_id}/custom-domains", json={"name": domain})


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy US Monitor to Render.")
    parser.add_argument(
        "--skip-domains",
        action="store_true",
        help="Create services without adding usmonitor.app custom domains.",
    )
    args = parser.parse_args()

    settings = load_settings()
    require(
        settings,
        [
            "RENDER_API_KEY",
            "OPENAI_API_KEY",
            "X_BEARER_TOKEN",
            "RESEND_API_KEY",
            "VAPID_PUBLIC_KEY",
            "VAPID_PRIVATE_KEY",
            "USDT_TRC20_ADDRESS",
            "USDT_ERC20_ADDRESS",
        ],
    )

    api = RenderAPI(settings["RENDER_API_KEY"])
    owner_id = choose_owner(api, settings)
    postgres = ensure_postgres(api, owner_id)
    database_url = wait_for_database_url(api, postgres["id"])

    existing_web = service_by_name(api, owner_id, WEB_SERVICE_NAME, "web_service")
    existing_web_env = api.service_env_vars(existing_web["id"]) if existing_web else {}

    secret_key = (
        settings.get("SECRET_KEY")
        or existing_web_env.get("SECRET_KEY")
        or secrets.token_urlsafe(48)
    )
    job_secret = (
        settings.get("JOB_SECRET")
        or existing_web_env.get("JOB_SECRET")
        or secrets.token_urlsafe(32)
    )
    vapid_contact = settings.get("VAPID_CONTACT", "mailto:alerts@usmonitor.app")

    common = {
        "DATABASE_URL": database_url,
        "PYTHON_VERSION": "3.12.8",
        "APP_BASE_URL": APP_BASE_URL,
        "OPENAI_API_KEY": settings["OPENAI_API_KEY"],
        "OPENAI_BASE_URL": settings.get("OPENAI_BASE_URL", ""),
        "OPENAI_SUMMARY_MODEL": settings.get("OPENAI_SUMMARY_MODEL", "gpt-5.4-mini"),
        "OPENAI_TRANSLATION_MODEL": settings.get(
            "OPENAI_TRANSLATION_MODEL",
            settings.get("OPENAI_SUMMARY_MODEL", "gpt-5.4-mini"),
        ),
        "OPENAI_HTTP_REFERER": settings.get("OPENAI_HTTP_REFERER", APP_BASE_URL),
        "OPENAI_APP_TITLE": settings.get("OPENAI_APP_TITLE", "US Monitor"),
        "X_BEARER_TOKEN": settings["X_BEARER_TOKEN"],
        "X_ALEABITOREDDIT_USER_ID": settings.get("X_ALEABITOREDDIT_USER_ID", ""),
        "VAPID_PUBLIC_KEY": settings["VAPID_PUBLIC_KEY"],
        "VAPID_PRIVATE_KEY": settings["VAPID_PRIVATE_KEY"],
        "VAPID_CONTACT": vapid_contact,
        "SEND_INITIAL_BACKFILL": settings.get("SEND_INITIAL_BACKFILL", "false"),
    }
    web_env = {
        **common,
        "SECRET_KEY": secret_key,
        "ADMIN_EMAILS": settings.get("ADMIN_EMAILS", "santazhj@gmail.com"),
        "RESEND_API_KEY": settings["RESEND_API_KEY"],
        "EMAIL_FROM": settings.get("EMAIL_FROM", "US Monitor <alerts@usmonitor.app>"),
        "USDT_TRC20_ADDRESS": settings["USDT_TRC20_ADDRESS"],
        "USDT_ERC20_ADDRESS": settings["USDT_ERC20_ADDRESS"],
        "MONTHLY_PRICE_USDT": settings.get("MONTHLY_PRICE_USDT", "99"),
        "JOB_SECRET": job_secret,
    }

    web = ensure_service(
        api,
        owner_id,
        WEB_SERVICE_NAME,
        "web_service",
        {
            "runtime": "python",
            "plan": "starter",
            "region": REGION,
            "healthCheckPath": "/api/config",
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
            },
        },
        web_env,
    )

    cron = ensure_service(
        api,
        owner_id,
        CRON_SERVICE_NAME,
        "cron_job",
        {
            "runtime": "python",
            "plan": "starter",
            "region": REGION,
            "schedule": "*/15 * * * *",
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python -m app.jobs.poll_sources",
            },
        },
        common,
        autodeploy="no",
    )

    if not args.skip_domains:
        add_custom_domain(api, web["id"], "usmonitor.app")
        add_custom_domain(api, web["id"], "www.usmonitor.app")

    trigger_deploy(api, web["id"])

    service_url = web.get("serviceDetails", {}).get("url", "")
    service_host = service_url.removeprefix("https://").removeprefix("http://").rstrip("/")
    if not service_host:
        service_host = f"{web.get('slug', WEB_SERVICE_NAME)}.onrender.com"

    print("\nRender resources are ready or deploying.")
    print(f"Web service: {web.get('dashboardUrl', web['id'])}")
    print(f"Cron job: {cron.get('dashboardUrl', cron['id'])}")
    print("\nDynadot DNS records to add:")
    print("- A     @    216.24.57.1")
    print(f"- CNAME www  {service_host}")
    print("\nRemove any AAAA records for usmonitor.app before verifying in Render.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
