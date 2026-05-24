from app.config import Settings


def test_openrouter_settings_are_configurable():
    settings = Settings(
        openai_api_key="sk-or-test",
        openai_base_url="https://openrouter.ai/api/v1",
        openai_summary_model="openai/gpt-4o-mini",
        openai_http_referer="https://usmonitor.app",
        openai_app_title="US Monitor",
    )

    assert settings.openai_base_url == "https://openrouter.ai/api/v1"
    assert settings.openai_summary_model == "openai/gpt-4o-mini"
    assert settings.openai_http_referer == "https://usmonitor.app"
    assert settings.openai_app_title == "US Monitor"
