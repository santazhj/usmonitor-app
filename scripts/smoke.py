from __future__ import annotations

import httpx
from dotenv import load_dotenv
import os

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    load_dotenv()
    admin_email = os.getenv("ADMIN_EMAILS", "admin@example.com").split(",")[0].strip()
    with httpx.Client(base_url=BASE_URL, follow_redirects=False) as client:
        config = client.get("/api/config")
        config.raise_for_status()
        print("config", config.status_code)

        auth = client.post("/api/auth/request", json={"email": admin_email})
        auth.raise_for_status()
        link = auth.json()["dev_magic_link"]
        verify_path = link.split("http://localhost:8000")[-1]
        verify = client.get(verify_path)
        print("verify", verify.status_code)

        me = client.get("/api/me")
        me.raise_for_status()
        print("me", me.json()["email"], "admin=", me.json()["is_admin"])

        overview = client.get("/api/admin/overview")
        overview.raise_for_status()
        print("overview", overview.json()["counts"])

        poll = client.post("/api/admin/poll")
        poll.raise_for_status()
        print("poll", poll.json())


if __name__ == "__main__":
    main()
