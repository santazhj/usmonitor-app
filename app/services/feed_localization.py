from __future__ import annotations

import re
import json
import logging
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AlertSummary


logger = logging.getLogger(__name__)

LOCALIZATION_CACHE_KEY = "feed_zh_v2"
LOCALIZATION_ROOT_KEY = "_serenity_localizations"
TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
URL_RE = re.compile(r"https?://\S+")
HANDLE_RE = re.compile(r"@\w+:?\s*")


class FeedLocalizationItem(BaseModel):
    id: str
    title: str = Field(max_length=120)
    notification_text: str = Field(max_length=500)
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
    if not has_chinese(summary.notification_text or ""):
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


def clean_source_for_translation(text: str) -> str:
    text = URL_RE.sub("", text or "")
    text = HANDLE_RE.sub("", text)
    return " ".join(text.split()).strip()


def rough_translate_fallback(text: str) -> str:
    cleaned = clean_source_for_translation(text)
    replacements = [
        ("For people trying to do valuation analysis on", "如果想对"),
        ("valuation analysis", "估值分析"),
        ("are probably valued", "大概率估值在"),
        ("probably", "大概"),
        ("I think I deserve my own Netflix special after", "作者开玩笑说，经历"),
        ("Did you listen anon?", "之前提醒过了，你注意到了吗？"),
        ("is extremely early", "还处在非常早期"),
        ("We're about to see", "接下来可能会看到"),
        ("a ton of institutional inflow", "大量机构资金流入"),
        ("institutional inflow", "机构资金流入"),
        ("is the largest beneficiary", "是最大的受益者"),
        ("brand new events this weekend", "这个周末的新催化"),
        ("index inclusion", "指数纳入"),
        ("Blackrock", "贝莱德"),
        ("Vanguard", "先锋"),
        ("MSCI", "MSCI"),
        ("NASDAQ", "纳斯达克"),
        ("Nasdaq", "纳斯达克"),
        ("beneficiary", "受益者"),
        ("extremely early", "非常早期"),
        ("early", "早期"),
        ("after", "之后"),
        ("and", "和"),
        ("or", "或"),
        ("as", "作为"),
        ("on", "关于"),
    ]
    translated = cleaned
    for source, target in replacements:
        translated = translated.replace(source, target)
    return translated


def fallback_zh_payload(summary: AlertSummary) -> dict[str, Any]:
    text = clean_source_for_translation(source_text(summary))
    tickers = _tickers(text, summary.tickers)
    ticker_text = "、".join(f"${ticker}" for ticker in tickers) if tickers else "相关标的"
    restatement = rough_translate_fallback(text)
    notification = f"作者这条帖子的意思是（涉及 {ticker_text}）：{restatement}"
    bullets = [f"涉及标的：{ticker_text}", "含义：这是原帖语义的中文转述，等待模型生成更精确版本。"]
    return {
        "title": "Serenity 新帖提醒",
        "notification_text": notification[:420],
        "bullets": bullets[:3],
        "why_it_matters": "中文 feed 会优先使用模型翻译原帖全段意思；模型暂不可用时显示这版临时中文转述。",
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
        "任务不是抽关键词，而是把每条 X 原帖的全段意思直接翻译/转述给中文用户。"
        "用户不懂英文，所以 notification_text 必须让用户不看原帖也能理解作者完整表达。"
        "保留股票代码、关键公司名、语气和因果关系；链接可概括为“附了链接”。"
        "不要写“原帖提到”、不要说“需要结合原帖”、不要让用户自己去看原帖。"
        "不要输出买卖建议、仓位建议或收益承诺。"
        "notification_text 用自然中文，180-320 个中文字符；短帖可以更短。"
        "bullets 最多 3 条，用中文提炼核心含义。"
    )
    use_responses_api = "openrouter.ai" not in settings.openai_base_url.lower()
    if use_responses_api:
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
                        "content": (
                            "请按原 id 返回。每条 notification_text 要直接复述作者整段话的中文意思，"
                            "不是关键词摘要。\n"
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
            return {
                item.id: {
                    "title": item.title,
                    "notification_text": item.notification_text,
                    "bullets": item.bullets,
                    "why_it_matters": item.why_it_matters,
                }
                for item in parsed_items
            }
        except Exception as exc:
            logger.warning("Responses feed localization failed: %s", exc.__class__.__name__)

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
    except Exception as exc:
        logger.warning("Chat feed localization failed: %s", exc.__class__.__name__)
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
        if summary.id in generated:
            cache_zh(summary, payload)
    if generated:
        db.commit()
    return localized
