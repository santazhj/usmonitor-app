from __future__ import annotations

import re
import json
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AlertSummary


LOCALIZATION_CACHE_KEY = "feed_zh_v1"
LOCALIZATION_ROOT_KEY = "_serenity_localizations"
TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
URL_RE = re.compile(r"https?://\S+")


class FeedLocalizationItem(BaseModel):
    id: str
    title: str = Field(max_length=120)
    notification_text: str = Field(max_length=220)
    bullets: list[str] = Field(default_factory=list, max_length=3)
    why_it_matters: str = Field(max_length=400)


class FeedLocalizationBatch(BaseModel):
    items: list[FeedLocalizationItem]


def has_chinese(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def source_text(summary: AlertSummary) -> str:
    if summary.post and summary.post.text:
        return summary.post.text
    return summary.notification_text or ""


def _cache_payload(raw_json: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(raw_json, dict):
        return None
    root = raw_json.get(LOCALIZATION_ROOT_KEY)
    if not isinstance(root, dict):
        return None
    payload = root.get(LOCALIZATION_CACHE_KEY)
    return payload if isinstance(payload, dict) else None


def cached_zh(summary: AlertSummary) -> dict[str, Any] | None:
    payload = _cache_payload(summary.post.raw_json if summary.post else None)
    if not payload:
        return None
    required = {"title", "notification_text", "bullets", "why_it_matters"}
    return payload if required <= set(payload) else None


def cache_zh(summary: AlertSummary, payload: dict[str, Any]) -> None:
    if not summary.post:
        return
    raw_json = dict(summary.post.raw_json or {})
    root = dict(raw_json.get(LOCALIZATION_ROOT_KEY) or {})
    root[LOCALIZATION_CACHE_KEY] = {
        "title": str(payload.get("title") or ""),
        "notification_text": str(payload.get("notification_text") or ""),
        "bullets": list(payload.get("bullets") or [])[:3],
        "why_it_matters": str(payload.get("why_it_matters") or ""),
    }
    raw_json[LOCALIZATION_ROOT_KEY] = root
    summary.post.raw_json = raw_json


def existing_chinese_payload(summary: AlertSummary) -> dict[str, Any] | None:
    text = " ".join(
        [
            summary.title or "",
            summary.notification_text or "",
            summary.why_it_matters or "",
            " ".join(summary.bullets or []),
        ]
    )
    if not has_chinese(text):
        return None
    return {
        "title": summary.title,
        "notification_text": summary.notification_text,
        "bullets": summary.bullets or [],
        "why_it_matters": summary.why_it_matters or "",
    }


def _tickers(text: str, fallback: list[str] | None = None) -> list[str]:
    found = {match.upper() for match in TICKER_RE.findall(text or "")}
    found.update(str(ticker).strip().lstrip("$").upper() for ticker in fallback or [] if ticker)
    return sorted(found)


def _keyword_points(text: str) -> list[str]:
    lower = text.lower()
    points = []
    keyword_map = [
        (("valuation", "valued", "undervalued", "cheap"), "估值或低估逻辑"),
        (("beneficiary", "benefit", "winner"), "潜在受益标的"),
        (("index inclusion", "nasdaq", "msci", "vanguard", "blackrock"), "指数纳入或机构资金流"),
        (("institutional inflow", "inflow"), "机构资金流入预期"),
        (("early", "extremely early"), "行情或基本面仍处早期阶段的判断"),
        (("netflix special", "deserve my own"), "作者用调侃语气强调关注度"),
        (("lightmatter", "celestial", "ayar", "lighthorse"), "硅光或光互连可比公司线索"),
        (("subscribe", "followers", "thank"), "账号运营或订阅进展"),
    ]
    for keywords, label in keyword_map:
        if any(keyword in lower for keyword in keywords):
            points.append(label)
    return points[:3]


def fallback_zh_payload(summary: AlertSummary) -> dict[str, Any]:
    text = URL_RE.sub("", source_text(summary)).strip()
    tickers = _tickers(text, summary.tickers)
    points = _keyword_points(text)
    ticker_text = "、".join(f"${ticker}" for ticker in tickers) if tickers else "相关标的"
    if points:
        point_text = "，重点是" + "、".join(points)
    else:
        point_text = "，需要结合原帖上下文判断重点"
    notification = f"@{summary.post.author_handle if summary.post else 'aleabitoreddit'}：原帖提到 {ticker_text}{point_text}。"
    bullets = [f"涉及标的：{ticker_text}"]
    bullets.extend(f"关注点：{point}" for point in points)
    return {
        "title": "Serenity 新帖提醒",
        "notification_text": notification[:180],
        "bullets": bullets[:3],
        "why_it_matters": "这是基于原帖正文生成的中文化摘要；仅用于情报浏览，不构成投资建议。",
    }


def _client_kwargs(settings: Settings) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    default_headers = {}
    if settings.openai_http_referer:
        default_headers["HTTP-Referer"] = settings.openai_http_referer
    if settings.openai_app_title:
        default_headers["X-OpenRouter-Title"] = settings.openai_app_title
    if default_headers:
        kwargs["default_headers"] = default_headers
    return kwargs


def generate_zh_batch(
    settings: Settings, summaries: list[AlertSummary]
) -> dict[str, dict[str, Any]]:
    if not settings.openai_api_key or not summaries:
        return {}
    items = [
        {
            "id": summary.id,
            "author": summary.post.author_handle if summary.post else "aleabitoreddit",
            "source_url": summary.source_url,
            "tickers": summary.tickers or [],
            "text": source_text(summary),
        }
        for summary in summaries
    ]
    system_prompt = (
        "你是 US Monitor 的中文金融情报翻译器。"
        "把每条 X 原帖翻译并压缩成简体中文 feed 卡片。"
        "保留股票代码、关键公司名和链接含义，不输出买卖建议、仓位建议或收益承诺。"
        "notification_text 要适合右侧栏阅读，不超过 120 个中文字符。"
        "bullets 最多 3 条，每条必须是中文。"
    )
    try:
        from openai import OpenAI

        client = OpenAI(**_client_kwargs(settings))
        response = client.responses.parse(
            model=settings.openai_summary_model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"请处理这些 feed items，按原 id 返回：\n{items}",
                },
            ],
            text_format=FeedLocalizationBatch,
        )
        parsed_items: list[FeedLocalizationItem] = []
        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                parsed = getattr(item, "parsed", None)
                if parsed:
                    parsed_items = parsed.items
                    break
        return {
            item.id: {
                "title": item.title,
                "notification_text": item.notification_text,
                "bullets": item.bullets,
                "why_it_matters": item.why_it_matters,
            }
            for item in parsed_items
        }
    except Exception:
        pass

    try:
        from openai import OpenAI

        client = OpenAI(**_client_kwargs(settings))
        response = client.chat.completions.create(
            model=settings.openai_summary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "请返回严格 JSON，格式为 "
                        '{"items":[{"id":"...","title":"...","notification_text":"...",'
                        '"bullets":["..."],"why_it_matters":"..."}]}。'
                        f"\n需要处理的 items:\n{json.dumps(items, ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        parsed = FeedLocalizationBatch.model_validate(data)
        return {
            item.id: {
                "title": item.title,
                "notification_text": item.notification_text,
                "bullets": item.bullets,
                "why_it_matters": item.why_it_matters,
            }
            for item in parsed.items
        }
    except Exception:
        return {}


def localize_feed_for_zh(
    settings: Settings, db: Session, summaries: list[AlertSummary]
) -> dict[str, dict[str, Any]]:
    localized: dict[str, dict[str, Any]] = {}
    pending: list[AlertSummary] = []
    for summary in summaries:
        cached = cached_zh(summary)
        if cached:
            localized[summary.id] = cached
            continue
        existing = existing_chinese_payload(summary)
        if existing:
            localized[summary.id] = existing
            continue
        pending.append(summary)

    generated = generate_zh_batch(settings, pending)
    for summary in pending:
        payload = generated.get(summary.id) or fallback_zh_payload(summary)
        localized[summary.id] = payload
        cache_zh(summary, payload)
    if pending:
        db.commit()
    return localized
