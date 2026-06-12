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
    positive_tickers: list[str] = Field(default_factory=list, max_length=12)
    why_it_matters: str = Field(max_length=500)
    risks: list[str] = Field(default_factory=list, max_length=4)
    source_url: str


TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")
POSITIVE_RE = re.compile(
    r"\b(long|bullish|buy|buying|own|owned|winner|beneficiary|upside|"
    r"attractive|undervalued|breakout|accumulate|compounder|positive|"
    r"outperform|re-rate|rerate|early)\b|"
    r"(看好|正面|受益|低估|上行|多头|买入|赢家|弹性|催化|重估)",
    re.IGNORECASE,
)


def normalize_ticker(value: str) -> str:
    return value.strip().lstrip("$").upper()


def positive_tickers_from_text(text: str, tickers: list[str]) -> list[str]:
    normalized = sorted({normalize_ticker(ticker) for ticker in tickers if ticker})
    if not normalized:
        return []
    if POSITIVE_RE.search(text or ""):
        return normalized
    return []


def _compact(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    return text[:limit] + ("..." if len(text) > limit else "")


def fallback_summary(post: XPost, model: str = "fallback") -> SummaryOutput:
    text = " ".join(post.text.split())
    tickers = sorted({match.upper() for match in TICKER_RE.findall(text)})
    positive_tickers = positive_tickers_from_text(text, tickers)
    compact = _compact(text, 118)
    body = _compact(f"@{post.author_handle}: {compact}", 160)
    primary = f"${tickers[0]}" if tickers else "监控源"
    return SummaryOutput(
        title=f"{primary} 新原帖提醒",
        notification_text=body,
        bullets=[compact] if compact else [],
        tickers=tickers,
        positive_tickers=positive_tickers,
        why_it_matters="监控源发布了新的原创内容；当前为自动回退摘要，需要结合原文复核重点。",
        risks=["未调用模型生成深度摘要。", "不构成投资建议"],
        source_url=post.url,
    )


def _client_kwargs(settings: Settings) -> dict:
    kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    headers = {}
    if settings.openai_http_referer:
        headers["HTTP-Referer"] = settings.openai_http_referer
    if settings.openai_app_title:
        headers["X-OpenRouter-Title"] = settings.openai_app_title
    if headers:
        kwargs["default_headers"] = headers
    return kwargs


def summarize_post(settings: Settings, post: XPost) -> tuple[SummaryOutput, str]:
    if not settings.openai_api_key:
        return fallback_summary(post), "fallback"

    try:
        from openai import OpenAI

        client = OpenAI(**_client_kwargs(settings))
        response = client.responses.parse(
            model=settings.openai_summary_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "你是 US Monitor 的中文金融情报摘要器。"
                        "输出简体中文，只提炼信息、逻辑、风险，不给买卖指令、仓位建议或收益承诺。"
                        "tickers 字段列出原帖明确提到的证券代码。"
                        "positive_tickers 只列出作者明确正面评价、看好、做多、认为受益或给出建设性 bullish 分析的代码；"
                        "排除仅用于比较、风险提示、负面或中性提到的代码。"
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
