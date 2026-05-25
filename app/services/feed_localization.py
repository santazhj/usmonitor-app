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

LOCALIZATION_CACHE_KEY = "feed_zh_v4"
LOCALIZATION_ROOT_KEY = "_serenity_localizations"
TICKER_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,9})")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
URL_RE = re.compile(r"https?://\S+")
HANDLE_RE = re.compile(r"@\w+:?\s*")
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
GENERIC_TITLE_RE = re.compile(
    r"(serenity|alerts?|新帖|提醒|总结|summary|new post)",
    re.IGNORECASE,
)


class FeedLocalizationItem(BaseModel):
    id: str
    title: str = Field(max_length=40)
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
    }
    raw_json[LOCALIZATION_ROOT_KEY] = root
    summary.post.raw_json = raw_json


def existing_chinese_payload(summary: AlertSummary) -> dict[str, Any] | None:
    if not has_chinese(summary.notification_text or ""):
        return None
    if not title_quality_ok(summary.title):
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
    dotted_bases = {ticker.split(".", 1)[0] for ticker in found if "." in ticker}
    found = {ticker for ticker in found if "." in ticker or ticker not in dotted_bases}
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
    ]
    for word in allowed:
        stripped = re.sub(rf"\b{re.escape(word)}\b", " ", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\b[A-Z]{2,10}\b", " ", stripped)
    stripped = re.sub(r"\b[A-Z][A-Za-z]{2,24}\b", " ", stripped)
    return stripped


def payload_quality_ok(payload: dict[str, Any]) -> bool:
    if not title_quality_ok(str(payload.get("title") or "")):
        return False
    text = " ".join(
        [
            str(payload.get("notification_text") or ""),
            " ".join(str(item) for item in payload.get("bullets") or []),
            str(payload.get("why_it_matters") or ""),
        ]
    )
    if not has_chinese(text):
        return False
    stripped = allowed_english_stripped(text)
    if ENGLISH_RESIDUE_RE.search(stripped):
        return False
    if COMMON_ENGLISH_WORD_RE.search(stripped):
        return False
    latin_letters = len(re.findall(r"[A-Za-z]", stripped))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return cjk_chars > 0 and latin_letters / max(cjk_chars, 1) < 0.08


def title_quality_ok(title: str) -> bool:
    title = " ".join((title or "").split())
    if not title or len(title) > 40:
        return False
    if URL_RE.search(title) or "@" in title:
        return False
    if GENERIC_TITLE_RE.search(title):
        return False
    if not has_chinese(title):
        return False
    return len(re.findall(r"[\u4e00-\u9fff]", title)) >= 4


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
    title = fallback_zh_title(text, tickers)
    notification = f"作者这条帖子的意思是（涉及 {ticker_text}）：{restatement}"
    bullets = [f"涉及标的：{ticker_text}", "含义：这是原帖语义的中文转述，等待模型生成更精确版本。"]
    return {
        "title": title,
        "notification_text": notification[:420],
        "bullets": bullets[:3],
        "why_it_matters": "中文 feed 会优先使用模型翻译原帖全段意思；模型暂不可用时显示这版临时中文转述。",
    }


def fallback_zh_title(text: str, tickers: list[str]) -> str:
    primary = f"${tickers[0]}" if tickers else "相关标的"
    lower = text.lower()
    if any(word in lower for word in ["valuation", "valued", "undervalued", "cheap"]):
        return f"{primary} 估值线索更新"
    if any(word in lower for word in ["institutional inflow", "index inclusion", "vanguard", "blackrock", "msci", "nasdaq"]):
        return f"{primary} 机构资金催化"
    if any(word in lower for word in ["beneficiary", "benefit", "winner"]):
        return f"{primary} 受益逻辑更新"
    if any(word in lower for word in ["netflix special", "deserve my own"]):
        return f"{primary} 成功案例调侃"
    if any(word in lower for word in ["subscribe", "followers", "thank"]):
        return "订阅人数进展"
    if tickers:
        return f"{primary} 观点更新"
    return "市场观点更新"


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
        "中文要像中国投资者日常会说的话，顺口、自然，不要翻译腔。"
        "保留股票代码、关键公司名、语气和因果关系；链接可概括为“附了链接”。"
        "不要写“原帖提到”、不要说“需要结合原帖”、不要让用户自己去看原帖。"
        "title 必须是对整条帖子的短标题，8-22 个中文字符，像财经快讯标题；"
        "可以包含核心 ticker，但禁止使用“Serenity 新帖提醒”“总结”“新帖”等泛化标题。"
        "除了股票代码、公司名、指数名、机构名之外，禁止保留英文句子或英文短语。"
        "如果原文有 'we are about to see'，要译成“接下来可能会看到”。"
        "如果原文有 'This is what it is like'，要译成“这就是这种阶段通常会发生的事情”。"
        "不要输出买卖建议、仓位建议或收益承诺。"
        "notification_text 用自然中文，120-320 个中文字符；短帖可以更短。"
        "bullets 最多 3 条，用中文提炼核心含义。"
    )
    use_responses_api = "openrouter.ai" not in settings.openai_base_url.lower()
    if use_responses_api:
        try:
            from openai import OpenAI

            client = OpenAI(**_client_kwargs(settings))
            response = client.responses.parse(
                model=_translation_model(settings),
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            "请按原 id 返回。每条 notification_text 要直接复述作者整段话的中文意思，"
                            "不是关键词摘要；每条 title 要概括全篇重点，不要固定模板标题。\n"
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
        except Exception as exc:
            logger.warning("Responses feed localization failed: %s", exc.__class__.__name__)

    try:
        from openai import OpenAI

        client = OpenAI(**_client_kwargs(settings))
        response = client.chat.completions.create(
            model=_translation_model(settings),
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "请返回严格 JSON，格式为 "
                        '{"items":[{"id":"...","title":"...","notification_text":"...",'
                        '"bullets":["..."],"why_it_matters":"..."}]}。'
                        "再次强调：notification_text 必须是中国用户能直接读懂的自然中文，"
                        "不得残留英文句子或英文短语；title 必须是智能短标题，不得写 Serenity 新帖提醒。"
                        f"\n需要处理的 items:\n{json.dumps(items, ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        parsed = FeedLocalizationBatch.model_validate(data)
        return _validated_payloads(parsed.items)
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
