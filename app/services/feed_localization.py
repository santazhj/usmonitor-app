from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AlertSummary


logger = logging.getLogger(__name__)

LOCALIZATION_CACHE_KEY = "feed_zh_v5"
LOCALIZATION_ROOT_KEY = "_serenity_localizations"
TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
URL_RE = re.compile(r"https?://\S+")
HANDLE_RE = re.compile(r"@\w+:?\s*")
MOJIBAKE_RE = re.compile(r"(杩|鎴|鐪|浠|鈥|檚|锛|銆|€\?)")
ENGLISH_RESIDUE_RE = re.compile(
    r"\b("
    r"we(?:'re| are) about to see|this is what it'?s like|did you listen|"
    r"for people trying|valuation analysis|institutional inflow|"
    r"index inclusion|deserve my own|netflix special|both vanguard|"
    r"maybe for the first time|then,? couple that|with even more|"
    r"about to see|trying to do|are probably valued"
    r")\b",
    re.IGNORECASE,
)
COMMON_ENGLISH_WORD_RE = re.compile(
    r"\b(the|and|or|with|from|after|before|about|trying|people|see|"
    r"probably|valued|early|inflow|entering|first|time|then|both|maybe|"
    r"this|what|like|deserve|special|listen|anon)\b",
    re.IGNORECASE,
)


class FeedLocalizationItem(BaseModel):
    id: str
    title: str = Field(max_length=40)
    notification_text: str = Field(max_length=500)
    bullets: list[str] = Field(default_factory=list, max_length=3)
    why_it_matters: str = Field(max_length=400)
    risks: list[str] = Field(default_factory=list, max_length=3)


class FeedLocalizationBatch(BaseModel):
    items: list[FeedLocalizationItem]


def has_chinese(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def has_mojibake(text: str) -> bool:
    return bool(MOJIBAKE_RE.search(text or ""))


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
    return payload if required <= set(payload) and payload_quality_ok(payload) else None


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
        "risks": list(payload.get("risks") or [])[:3],
    }
    raw_json[LOCALIZATION_ROOT_KEY] = root
    summary.post.raw_json = raw_json


def existing_chinese_payload(summary: AlertSummary) -> dict[str, Any] | None:
    text = " ".join(
        [
            summary.title or "",
            summary.notification_text or "",
            " ".join(summary.bullets or []),
            summary.why_it_matters or "",
            " ".join(summary.risks or []),
        ]
    )
    if has_mojibake(text) or not has_chinese(text):
        return None
    if not title_quality_ok(summary.title):
        return None
    return {
        "title": summary.title,
        "notification_text": summary.notification_text,
        "bullets": summary.bullets or [],
        "why_it_matters": summary.why_it_matters or "",
        "risks": summary.risks or [],
    }


def _tickers(text: str, fallback: list[str] | None = None) -> list[str]:
    found = {match.upper() for match in TICKER_RE.findall(text or "")}
    found.update(
        str(ticker).strip().lstrip("$").upper()
        for ticker in fallback or []
        if ticker
    )
    dotted_bases = {ticker.split(".", 1)[0] for ticker in found if "." in ticker}
    found = {ticker for ticker in found if "." in ticker or ticker not in dotted_bases}
    return sorted(found)


def clean_source(text: str) -> str:
    text = URL_RE.sub("", text or "")
    text = HANDLE_RE.sub("", text)
    return " ".join(text.split()).strip()


def payload_quality_ok(payload: dict[str, Any]) -> bool:
    title = str(payload.get("title") or "")
    text = " ".join(
        [
            title,
            str(payload.get("notification_text") or ""),
            " ".join(str(item) for item in payload.get("bullets") or []),
            str(payload.get("why_it_matters") or ""),
            " ".join(str(item) for item in payload.get("risks") or []),
        ]
    )
    if not title_quality_ok(title) or not has_chinese(text) or has_mojibake(text):
        return False
    stripped = allowed_english_stripped(text)
    if ENGLISH_RESIDUE_RE.search(stripped):
        return False
    if COMMON_ENGLISH_WORD_RE.search(stripped):
        return False
    return True


def allowed_english_stripped(text: str) -> str:
    stripped = re.sub(r"\$[A-Za-z][A-Za-z0-9.]{0,9}", " ", text or "")
    allowed = [
        "BlackRock",
        "Blackrock",
        "Vanguard",
        "MSCI",
        "NASDAQ",
        "Nasdaq",
        "S&P",
        "Netflix",
        "X",
        "AI",
        "CPO",
        "LRO",
        "HBM",
        "GPU",
        "ASIC",
        "Ayar",
        "Celestial",
        "Lightmatter",
        "Lighthorse",
        "Poet",
        "TFLN",
        "Sivers",
    ]
    for word in allowed:
        stripped = re.sub(rf"\b{re.escape(word)}\b", " ", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\b[A-Z]{2,10}\b", " ", stripped)
    stripped = re.sub(r"\b[A-Z][A-Za-z]{2,24}\b", " ", stripped)
    return stripped


def title_quality_ok(title: str) -> bool:
    title = " ".join((title or "").split())
    if not title or len(title) > 40:
        return False
    if URL_RE.search(title) or "@" in title:
        return False
    if re.search(r"(serenity|alerts?|summary|new post|新帖提醒)", title, re.I):
        return False
    return has_chinese(title) and not has_mojibake(title)


def fallback_zh_title(text: str, tickers: list[str]) -> str:
    primary = f"${tickers[0]}" if tickers else "监控源"
    lower = text.lower()
    if any(word in lower for word in ["valuation", "valued", "undervalued", "cheap"]):
        return f"{primary} 估值线索更新"
    if any(word in lower for word in ["inflow", "index inclusion", "vanguard", "blackrock", "msci", "nasdaq"]):
        return f"{primary} 机构资金催化"
    if any(word in lower for word in ["beneficiary", "benefit", "winner"]):
        return f"{primary} 受益逻辑更新"
    if any(word in lower for word in ["cpo", "optical", "photonics", "800g", "1.6t"]):
        return f"{primary} 光互连线索更新"
    if any(word in lower for word in ["hbm", "memory", "dram"]):
        return f"{primary} 存储链线索更新"
    if tickers:
        return f"{primary} 观点更新"
    return "市场观点更新"


def fallback_zh_payload(summary: AlertSummary) -> dict[str, Any]:
    text = clean_source(source_text(summary))
    tickers = _tickers(text, summary.tickers)
    ticker_text = "、".join(f"${ticker}" for ticker in tickers) if tickers else "相关标的"
    compact = rough_translate_fallback(text, tickers)
    return {
        "title": fallback_zh_title(text, tickers),
        "notification_text": (
            f"监控源发布了新的原创内容，涉及 {ticker_text}。"
            f"模型暂时不可用，以下为规则回退摘要：{compact}"
        )[:480],
        "bullets": [
            f"涉及标的：{ticker_text}",
            "这是模型不可用时的回退摘要，原文链接应作为最终复核来源。",
        ],
        "why_it_matters": "这条内容来自已监控来源，可能影响相关标的的产业链叙事、资金关注度或事件催化。",
        "risks": ["模型未生成深度中文摘要。", "仅供信息参考，不构成投资建议。"],
    }


def rough_translate_fallback(text: str, tickers: list[str]) -> str:
    lower = text.lower()
    primary = f"${tickers[0]}" if tickers else "相关标的"
    if "institutional inflow" in lower or "index inclusion" in lower:
        return (
            f"作者认为 {primary} 仍处在非常早期，接下来可能看到 BlackRock、"
            "Vanguard、MSCI、Nasdaq 等机构资金流入以及指数相关资金流入。"
        )
    if any(word in lower for word in ["valuation", "valued", "undervalued", "cheap"]):
        return f"作者围绕 {primary} 的估值和潜在低估逻辑展开讨论，需要结合原文和基本面复核。"
    if any(word in lower for word in ["beneficiary", "benefit", "winner"]):
        return f"作者强调 {primary} 可能是相关产业趋势的受益标的，需要复核事件和订单证据。"
    compact = text[:220] + ("..." if len(text) > 220 else "")
    return f"原文关键信息保留如下，需人工复核：{compact}"


def _client_kwargs(settings: Settings) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
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


def _translation_model(settings: Settings) -> str:
    return settings.openai_translation_model or settings.openai_summary_model


def _validated_payloads(items: list[FeedLocalizationItem]) -> dict[str, dict[str, Any]]:
    valid: dict[str, dict[str, Any]] = {}
    for item in items:
        payload = {
            "title": item.title,
            "notification_text": item.notification_text,
            "bullets": item.bullets,
            "why_it_matters": item.why_it_matters,
            "risks": item.risks,
        }
        if payload_quality_ok(payload):
            valid[item.id] = payload
        else:
            logger.warning("Rejected low-quality feed localization for %s", item.id)
    return valid


def generate_zh_batch(
    settings: Settings, summaries: list[AlertSummary]
) -> dict[str, dict[str, Any]]:
    if not settings.openai_api_key or not summaries:
        return {}
    items = [
        {
            "id": summary.id,
            "author": summary.post.author_handle if summary.post else "source",
            "source_url": summary.source_url,
            "tickers": summary.tickers or [],
            "text": source_text(summary),
        }
        for summary in summaries
    ]
    system_prompt = (
        "你是 US Monitor 的中文金融情报翻译器。任务是把每条 X 原帖的完整意思转成自然简体中文，"
        "让中文用户不看原帖也能理解作者表达。保留股票代码、公司名、因果关系和语气；不要给买卖建议、"
        "仓位建议或收益承诺。title 写成 8-22 个中文字符的财经快讯标题，不要使用泛化标题。"
    )
    try:
        from openai import OpenAI

        client = OpenAI(**_client_kwargs(settings))
        if "openrouter.ai" not in settings.openai_base_url.lower():
            response = client.responses.parse(
                model=_translation_model(settings),
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "请按 id 返回。每条 notification_text 用自然中文，120-320 个中文字符；"
                            "bullets 最多 3 条；risks 最多 3 条。\n"
                            f"{json.dumps(items, ensure_ascii=False)}"
                        ),
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
            return _validated_payloads(parsed_items)

        response = client.chat.completions.create(
            model=_translation_model(settings),
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "请返回严格 JSON，格式为 "
                        '{"items":[{"id":"...","title":"...","notification_text":"...",'
                        '"bullets":["..."],"why_it_matters":"...","risks":["..."]}]}。\n'
                        f"{json.dumps(items, ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content or "{}")
        parsed = FeedLocalizationBatch.model_validate(data)
        return _validated_payloads(parsed.items)
    except Exception as exc:
        logger.warning("Feed localization failed: %s", exc.__class__.__name__)
        return {}


def localize_feed_for_zh(
    settings: Settings,
    db: Session,
    summaries: list[AlertSummary],
    *,
    generate: bool = True,
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

    generated = generate_zh_batch(settings, pending) if generate else {}
    for summary in pending:
        payload = generated.get(summary.id) or fallback_zh_payload(summary)
        localized[summary.id] = payload
        if summary.id in generated:
            cache_zh(summary, payload)
    if generated:
        db.commit()
    return localized
