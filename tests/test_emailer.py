import asyncio

import pytest

from app.config import Settings
from app.services.emailer import send_magic_link


def test_magic_link_is_returned_only_for_local_development():
    settings = Settings(base_url="http://localhost:8000", resend_api_key="")

    result = asyncio.run(send_magic_link(settings, "user@example.com", "http://link"))

    assert result["dev_magic_link"] == "http://link"


def test_missing_resend_key_fails_closed_in_production():
    settings = Settings(base_url="https://usmonitor.app", resend_api_key="")

    with pytest.raises(RuntimeError):
        asyncio.run(send_magic_link(settings, "user@example.com", "https://link"))
