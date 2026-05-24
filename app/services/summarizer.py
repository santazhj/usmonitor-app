from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.config import Settings
from app.models import XPost


class SummaryOutput(BaseModel):
    title: str = Field(max_length=120)
    notification_text: str = Field(max_length=160)
    bullets: list[str] = Field(default_factory=list, max_length=5)
    tickers: list[str] = Field(default_factory=list, max_length=12)
    why_it_matters: str = Field(max_length=500)
    risks: list[str] = Field(default_factory=list, max_length=4)
    source_url: str


TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")


def fallback_summary(post: XPost, model: str = "fallback") -> SummaryOutput:
    text = " ".join(post.text.split())
    compact = text[:130] + ("..." if len(text) > 130 else "")
    tickers = sorted({match.upper() for match in TICKER_RE.findall(text)})
    return SummaryOutput(
        title="Serenity 新帖提醒",
        notification_text=f"@{post.author_handle}: {compact}",
        bullets=[compact],
        tickers=tickers,
        why_it_matters="这是监控源发布的新原创内容；当前为开发模式摘要，需要人工复核重点。",
        risks=["未调用模型生成深度摘要", "不构成投资建议"],
        source_url=post.url,
    )


def summarize_post(settings: Settings, post: XPost) -> tuple[SummaryOutput, str]:
    if not settings.openai_api_key:
        return fallback_summary(post), "fallback"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.parse(
            model=settings.openai_summary_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "你是 Serenity Alerts 的中文情报摘要器。输出简体中文，"
                        "只提炼信息、逻辑和风险，不给买卖指令、仓位建议或收益承诺。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"监控源: @{post.author_handle}\n"
                        f"原帖链接: {post.url}\n"
                        f"原帖正文:\n{post.text}"
                    ),
                },
            ],
            text_format=SummaryOutput,
        )
        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                parsed = getattr(item, "parsed", None)
                if parsed:
                    parsed.source_url = post.url
                    return parsed, settings.openai_summary_model
        return fallback_summary(post), "fallback-unparsed"
    except Exception:
        return fallback_summary(post), "fallback-error"
