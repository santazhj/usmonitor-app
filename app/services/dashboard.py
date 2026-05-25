from __future__ import annotations

from typing import Any

from app.models import WatchlistMention
from app.models import utcnow
from app.services.market_data import MarketDataResult


def row(
    ticker: str,
    company: str,
    region: str,
    ai_layer: str,
    role: str,
    latest_signal: str,
    tier: str,
    focus: str,
) -> dict:
    return {
        "ticker": ticker,
        "company": company,
        "region": region,
        "ai_layer": ai_layer,
        "role": role,
        "latest_signal": latest_signal,
        "tier": tier,
        "focus": focus,
    }


WATCHLIST_CATEGORIES: list[dict] = [
    {
        "slug": "capex",
        "label": "Cloud CAPEX",
        "description": "Demand-side anchors that drive the full AI factory order book.",
        "rows": [
            row(
                "MSFT",
                "Microsoft",
                "US",
                "Cloud CAPEX",
                "Azure AI demand anchor",
                "Watch AI revenue run-rate, Azure growth, and capex discipline",
                "Demand anchor",
                "High liquidity",
            ),
            row(
                "GOOGL",
                "Alphabet",
                "US",
                "Cloud/TPU",
                "TPU, Google Cloud, and internal model infrastructure",
                "Watch cloud backlog, TPU scale, and capex trajectory",
                "Demand anchor",
                "High liquidity",
            ),
            row(
                "AMZN",
                "Amazon",
                "US",
                "Cloud/ASIC",
                "AWS, Trainium, and hyperscale infrastructure demand",
                "Watch AWS growth, Trainium commitments, and data-center capex",
                "Demand anchor",
                "High liquidity",
            ),
            row(
                "META",
                "Meta Platforms",
                "US",
                "AI Factory",
                "Large AI infrastructure spender",
                "Watch 2026 capex guidance and monetization pressure",
                "Demand anchor",
                "High liquidity",
            ),
            row(
                "ORCL",
                "Oracle",
                "US",
                "GPU Cloud",
                "AI cloud capacity and GPU infrastructure supplier",
                "Watch AI cloud backlog and customer concentration",
                "Demand anchor",
                "High attention",
            ),
            row(
                "NBIS",
                "Nebius Group",
                "US",
                "AI Cloud",
                "High-beta AI cloud capacity provider",
                "Watch hyperscaler contracts and GPU utilization",
                "High elasticity",
                "High attention",
            ),
        ],
    },
    {
        "slug": "compute-network",
        "label": "Compute & Network",
        "description": "GPU, ASIC, Ethernet, SerDes, and rack-scale connectivity.",
        "rows": [
            row(
                "NVDA",
                "NVIDIA",
                "US",
                "GPU/Networking",
                "AI rack-scale platform reference asset",
                "Watch data-center networking growth vs compute growth",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "AMD",
                "Advanced Micro Devices",
                "US",
                "GPU/CPU",
                "Alternative accelerator and server CPU supplier",
                "Watch MI-series adoption and hyperscaler attach",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "AVGO",
                "Broadcom",
                "US",
                "Custom ASIC/Networking",
                "Core beneficiary of hyperscaler custom silicon",
                "Watch AI revenue, XPU projects, and networking mix",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "MRVL",
                "Marvell Technology",
                "US",
                "Custom Silicon/Optics",
                "Custom silicon, DSP, and electro-optics bridge",
                "Watch custom silicon backlog and 1.6T DSP ramp",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "ANET",
                "Arista Networks",
                "US",
                "AI Ethernet",
                "Cloud AI spine/leaf switching supplier",
                "Watch 800G/1.6T switching cycles and cloud concentration",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "ALAB",
                "Astera Labs",
                "US",
                "PCIe/CXL",
                "AI server retimer and rack connectivity exposure",
                "Watch connectivity attach rate and valuation risk",
                "High elasticity",
                "High attention",
            ),
            row(
                "CRDO",
                "Credo Technology",
                "US",
                "AEC/SerDes",
                "High-speed connectivity and active electrical cable exposure",
                "Watch 800G/1.6T AEC penetration and customer concentration",
                "High elasticity",
                "High attention",
            ),
            row(
                "SMCI",
                "Super Micro Computer",
                "US",
                "AI Servers",
                "Rack-scale AI server integration proxy",
                "Watch gross margin, shipment timing, and customer quality",
                "Industry reference",
                "High attention",
            ),
            row(
                "DELL",
                "Dell Technologies",
                "US",
                "AI Servers",
                "Enterprise AI server channel",
                "Watch AI server backlog and margin conversion",
                "Industry reference",
                "High liquidity",
            ),
        ],
    },
    {
        "slug": "foundry-test",
        "label": "Foundry & Test",
        "description": "Advanced nodes, EUV, process control, and AI chip test bottlenecks.",
        "rows": [
            row(
                "TSM",
                "TSMC",
                "Taiwan",
                "Foundry/CoWoS",
                "Systemic chokepoint for AI accelerators and advanced packaging",
                "Watch N2/A16, CoWoS expansion, and HPC wafer demand",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "ASML",
                "ASML",
                "Netherlands",
                "EUV",
                "Upstream chokepoint for advanced logic and DRAM EUV",
                "Watch High-NA/EUV demand and export restriction impact",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "AMAT",
                "Applied Materials",
                "US",
                "Equipment",
                "Deposition, etch, and packaging equipment exposure",
                "Watch GAA and advanced packaging capex",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "LRCX",
                "Lam Research",
                "US",
                "Equipment",
                "Etch/deposition exposure to memory and advanced nodes",
                "Watch memory capex recovery and AI DRAM intensity",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "KLAC",
                "KLA",
                "US",
                "Inspection/Metrology",
                "Yield-control beneficiary for advanced nodes and packaging",
                "Watch inspection intensity as process complexity rises",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "6857.T",
                "Advantest",
                "Japan",
                "AI Chip Test",
                "SoC, HBM, and AI accelerator testing bottleneck",
                "Watch AI test time, HBM complexity, and order momentum",
                "Core chokepoint",
                "Global focus",
            ),
            row(
                "BESI.AS",
                "BESI",
                "Netherlands",
                "Hybrid Bonding",
                "High-beta hybrid bonding equipment exposure",
                "Watch HBM4, SoIC, and 3D stacking order conversion",
                "High elasticity",
                "Global focus",
            ),
        ],
    },
    {
        "slug": "memory-storage",
        "label": "Memory & Storage",
        "description": "HBM, server DRAM, eSSD, NAND controllers, and memory-cycle leverage.",
        "rows": [
            row(
                "MU",
                "Micron",
                "US",
                "HBM/DRAM/eSSD",
                "US-listed core HBM and AI memory exposure",
                "Watch HBM4 ramp, gross margin, and supply discipline",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "000660.KS",
                "SK hynix",
                "Korea",
                "HBM",
                "Leading HBM supplier with strong financial validation",
                "Watch HBM4 contracts, ASP, and long-term supply agreements",
                "Core chokepoint",
                "Global focus",
            ),
            row(
                "005930.KS",
                "Samsung Electronics",
                "Korea",
                "HBM/DRAM/Foundry",
                "HBM catch-up and memory-cycle reference asset",
                "Watch HBM4 qualification and foundry customer progress",
                "Industry reference",
                "Global focus",
            ),
            row(
                "SNDK",
                "SanDisk",
                "US",
                "NAND/eSSD",
                "AI storage and NAND-cycle leverage",
                "Watch eSSD demand and NAND pricing discipline",
                "High elasticity",
                "High attention",
            ),
            row(
                "SIMO",
                "Silicon Motion",
                "US",
                "NAND Controllers",
                "Controller exposure to SSD and embedded storage demand",
                "Watch AI storage cycle and controller ASP",
                "High elasticity",
                "Medium liquidity",
            ),
            row(
                "EWY",
                "iShares MSCI South Korea ETF",
                "US ETF",
                "Korea Memory Basket",
                "Liquid proxy for SK hynix and Samsung exposure",
                "Watch Korea memory cycle and HBM share shifts",
                "Proxy",
                "High liquidity",
            ),
        ],
    },
    {
        "slug": "packaging-substrate",
        "label": "Packaging & Substrate",
        "description": "CoWoS, ABF, IC substrate, advanced PCB, and packaging materials.",
        "rows": [
            row(
                "4062.T",
                "Ibiden",
                "Japan",
                "ABF Substrate",
                "High-end IC substrate exposure for AI GPU/ASIC packages",
                "Watch ABF capacity, customer mix, and ASP cycle",
                "Core chokepoint",
                "Global focus",
            ),
            row(
                "3037.TW",
                "Unimicron",
                "Taiwan",
                "ABF/PCB",
                "AI server PCB and high-layer substrate exposure",
                "Watch yield, pricing, and Taiwan AI-chain demand",
                "Validation",
                "Global focus",
            ),
            row(
                "2802.T",
                "Ajinomoto",
                "Japan",
                "ABF Film",
                "Hidden material bottleneck in high-end substrates",
                "Watch ABF spec upgrades and material mix contribution",
                "Industry reference",
                "Global focus",
            ),
            row(
                "ATS.VI",
                "AT&S",
                "Austria",
                "IC Substrate",
                "High-beta substrate and advanced PCB supplier",
                "Watch leverage, depreciation load, and AI/HPC order quality",
                "Validation",
                "Global focus",
            ),
            row(
                "AEHR",
                "Aehr Test Systems",
                "US",
                "Wafer-Level Test",
                "Small-cap test exposure to SiC, GaN, and photonics",
                "Watch real AI-related orders vs narrative momentum",
                "Validation",
                "High attention",
            ),
        ],
    },
    {
        "slug": "optical",
        "label": "Optical & Photonics",
        "description": "800G/1.6T optics, lasers, InP, SOI, GaAs, CPO/LRO, and optical modules.",
        "rows": [
            row(
                "COHR",
                "Coherent",
                "US",
                "Lasers/Transceivers",
                "Institutional optical-chain asset",
                "Watch AI optics agreements, 800G/1.6T, and margin recovery",
                "High elasticity",
                "High liquidity",
            ),
            row(
                "LITE",
                "Lumentum",
                "US",
                "Lasers/Optical Components",
                "Laser and optical component exposure to AI datacom",
                "Watch datacom recovery and customer concentration",
                "High elasticity",
                "High liquidity",
            ),
            row(
                "FN",
                "Fabrinet",
                "US",
                "Optical Manufacturing",
                "Optical module manufacturing capacity proxy",
                "Watch 800G/1.6T customer ramp and margin ceiling",
                "High elasticity",
                "High liquidity",
            ),
            row(
                "GLW",
                "Corning",
                "US",
                "Fiber/Advanced Optics",
                "Large-cap optical material reference asset",
                "Watch data-center fiber demand and AI optics partnerships",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "AAOI",
                "Applied Optoelectronics",
                "US",
                "Optical Modules",
                "High-attention AI optics beta",
                "Watch 800G/1.6T shipments and customer concentration",
                "High elasticity",
                "High attention",
            ),
            row(
                "AXTI",
                "AXT",
                "US",
                "InP/GaAs Substrates",
                "Serenity-style bottom-layer photonics material exposure",
                "Watch InP demand, export controls, and customer validation",
                "High elasticity",
                "High attention",
            ),
            row(
                "SIVE.ST",
                "Sivers Semiconductors",
                "Sweden",
                "DFB Laser/CPO",
                "Small-cap LRO/CPO light-source exposure",
                "Watch Jabil 1.6T LRO progress and financing risk",
                "High elasticity",
                "Niche/global",
            ),
            row(
                "SOI.PA",
                "Soitec",
                "France",
                "SOI Substrate",
                "Silicon photonics and SOI material exposure",
                "Watch CPO adoption and RF-SOI recovery",
                "High elasticity",
                "Global focus",
            ),
            row(
                "IQE.L",
                "IQE",
                "UK",
                "Epitaxy",
                "Compound semiconductor epitaxy exposure",
                "Watch photonics demand, profitability, and financing risk",
                "Validation",
                "Niche/global",
            ),
            row(
                "TSEM",
                "Tower Semiconductor",
                "US/Israel",
                "Specialty Foundry",
                "Analog and silicon photonics foundry exposure",
                "Watch AI purity and specialty foundry demand",
                "Validation",
                "Medium liquidity",
            ),
            row(
                "300502.SZ",
                "Eoptolink",
                "China",
                "Optical Transceivers",
                "China 800G/1.6T optical module exposure",
                "Watch export constraints, overseas customers, and valuation",
                "Validation",
                "Global focus",
            ),
            row(
                "300308.SZ",
                "Zhongji Innolight",
                "China",
                "Optical Transceivers",
                "High-attention China optical module supplier",
                "Watch 800G/1.6T ramp, customer concentration, and policy risk",
                "Validation",
                "Global focus",
            ),
        ],
    },
    {
        "slug": "power-cooling",
        "label": "Power & Cooling",
        "description": "Switchgear, UPS, liquid cooling, thermal systems, and onsite power.",
        "rows": [
            row(
                "VRT",
                "Vertiv",
                "US",
                "Power/Thermal",
                "Direct AI data-center power and cooling bottleneck",
                "Watch backlog, liquid cooling, and delivery execution",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "ETN",
                "Eaton",
                "US",
                "Electrical Equipment",
                "Switchgear, transformer, and power distribution exposure",
                "Watch data-center electrical backlog and capacity release",
                "Core chokepoint",
                "High liquidity",
            ),
            row(
                "SU.PA",
                "Schneider Electric",
                "France",
                "Power Management",
                "European core data-center electrification asset",
                "Watch AI data-center demand and euro-cycle exposure",
                "Industry reference",
                "Global focus",
            ),
            row(
                "NVT",
                "nVent",
                "US",
                "Electrical Enclosures",
                "Electrical protection and enclosure content exposure",
                "Watch data-center content per rack and industrial cycle risk",
                "Industry reference",
                "Medium liquidity",
            ),
            row(
                "MOD",
                "Modine",
                "US",
                "Thermal Management",
                "Liquid cooling and heat rejection high-beta exposure",
                "Watch CDU, cold plate, and data-center cooling orders",
                "Validation",
                "High attention",
            ),
            row(
                "BE",
                "Bloom Energy",
                "US",
                "Onsite Power",
                "Fuel-cell and onsite power optionality for data centers",
                "Watch signed power contracts and financing quality",
                "Validation",
                "High attention",
            ),
            row(
                "CEG",
                "Constellation Energy",
                "US",
                "Clean Power",
                "Large-scale power supplier for data-center demand",
                "Watch nuclear/data-center power contracts",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "GEV",
                "GE Vernova",
                "US",
                "Grid/Power",
                "Grid equipment and electrification backlog proxy",
                "Watch grid equipment demand and margin execution",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "PWR",
                "Quanta Services",
                "US",
                "Grid Buildout",
                "Transmission and power infrastructure construction proxy",
                "Watch utility and data-center grid backlog",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "XLU",
                "Utilities Select Sector SPDR Fund",
                "US ETF",
                "Utilities Basket",
                "Liquid ETF proxy for AI power theme",
                "Watch power demand narrative vs utility rate-cycle risk",
                "Proxy",
                "High liquidity",
            ),
        ],
    },
    {
        "slug": "software-data",
        "label": "Software & Data",
        "description": "High-attention AI application and data-platform names for comparison.",
        "rows": [
            row(
                "PLTR",
                "Palantir",
                "US",
                "AI Platform",
                "Enterprise AI workflow and government AI exposure",
                "Watch AIP adoption, valuation, and operating leverage",
                "High attention",
                "High liquidity",
            ),
            row(
                "SNOW",
                "Snowflake",
                "US",
                "Data Cloud",
                "Enterprise data platform feeding AI workloads",
                "Watch consumption growth and AI product monetization",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "DDOG",
                "Datadog",
                "US",
                "Observability",
                "Cloud and AI workload observability exposure",
                "Watch AI workload growth and net retention",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "CRWD",
                "CrowdStrike",
                "US",
                "Security",
                "AI-era endpoint and cloud security platform",
                "Watch platform consolidation and AI security demand",
                "Industry reference",
                "High liquidity",
            ),
            row(
                "RDDT",
                "Reddit",
                "US",
                "Data/Attention",
                "High-attention data licensing and social platform asset",
                "Watch data licensing revenue and ad monetization",
                "High attention",
                "High liquidity",
            ),
            row(
                "FIG",
                "Figma",
                "US",
                "Design Software",
                "Product design collaboration and AI workflow exposure",
                "Watch enterprise adoption and AI design-tool competition",
                "High attention",
                "High attention",
            ),
        ],
    },
]

DYNAMIC_CATEGORY = {
    "slug": "serenity-alert",
    "label": "Serenity Adds",
    "description": "Tickers added from positive Serenity X-source analysis.",
}


def dashboard_tickers() -> list[str]:
    return [
        item["ticker"]
        for category in WATCHLIST_CATEGORIES
        for item in category["rows"]
    ]


def static_rows() -> list[dict]:
    return [
        {
            **item,
            "category": category["slug"],
            "category_label": category["label"],
        }
        for category in WATCHLIST_CATEGORIES
        for item in category["rows"]
    ]


def static_ticker_set() -> set[str]:
    return {item["ticker"] for item in static_rows()}


def mention_rows(mentions: list[WatchlistMention]) -> list[dict]:
    existing = static_ticker_set()
    rows = []
    seen = set()
    for mention in mentions:
        ticker = mention.ticker.upper()
        if ticker in existing or ticker in seen:
            continue
        seen.add(ticker)
        rows.append(
            row(
                ticker,
                mention.company or ticker,
                "Global",
                "Serenity Alert",
                "Positive source mention",
                mention.reason or "Added from a constructive Serenity X-source post",
                "Serenity positive",
                "Source driven",
            )
            | {
                "source_url": mention.source_url,
                "source_added_at": mention.created_at.isoformat(),
                "category": DYNAMIC_CATEGORY["slug"],
                "category_label": DYNAMIC_CATEGORY["label"],
            }
        )
    return rows


def latest_mention_by_ticker(mentions: list[WatchlistMention]) -> dict[str, WatchlistMention]:
    latest = {}
    for mention in mentions:
        ticker = mention.ticker.upper()
        if ticker not in latest:
            latest[ticker] = mention
    return latest


def _market_payload(item: dict, market_rows: dict[str, dict[str, Any]]) -> dict:
    market = market_rows.get(item["ticker"], {})
    return {
        "price": market.get("price"),
        "change": market.get("change"),
        "change_percent": market.get("change_percent"),
        "volume": market.get("volume"),
        "dollar_volume": market.get("dollar_volume"),
        "market_cap": market.get("market_cap"),
        "pe_ratio": market.get("pe_ratio"),
        "revenue_growth": None,
        "market_updated_at": market.get("updated_at"),
        "market_provider": market.get("provider"),
        "currency": market.get("currency"),
        "exchange": market.get("exchange"),
    }


def get_dashboard_snapshot(
    market_data: MarketDataResult | None = None,
    extra_rows: list[dict] | None = None,
    positive_mentions: list[WatchlistMention] | None = None,
) -> dict:
    market_rows = market_data.rows if market_data else {}
    extra_rows = extra_rows or []
    positive_mentions = positive_mentions or []
    mentions_by_ticker = latest_mention_by_ticker(positive_mentions)
    base_rows = []
    for item in static_rows():
        mention = mentions_by_ticker.get(item["ticker"])
        if mention:
            item = {
                **item,
                "latest_signal": mention.reason or item["latest_signal"],
                "source_url": mention.source_url,
                "source_added_at": mention.created_at.isoformat(),
            }
        base_rows.append(item)

    rows = [
        {
            **item,
            **_market_payload(item, market_rows),
        }
        for item in [*base_rows, *extra_rows]
    ]
    core_count = sum(1 for item in rows if item["tier"] == "Core chokepoint")
    high_attention_count = sum(
        1
        for item in rows
        if item["focus"] in {"High liquidity", "High attention"}
    )
    if market_data and market_data.status == "live":
        data_status = "market_live"
        data_status_label = "Market data live"
        market_status = "live"
        market_detail = market_data.detail
    elif market_data and market_data.status == "error":
        data_status = "provider_error"
        data_status_label = "Market data provider error"
        market_status = "error"
        market_detail = market_data.detail
    else:
        data_status = "provider_pending"
        data_status_label = "Market data provider pending"
        market_status = "pending"
        market_detail = "Provider adapter is not connected yet."

    return {
        "generated_at": utcnow().isoformat(),
        "refresh_interval_seconds": 15,
        "data_status": data_status,
        "data_status_label": data_status_label,
        "disclaimer": "Information dashboard only. Not investment advice.",
        "metrics": {
            "tracked_tickers": len(rows),
            "categories": len(WATCHLIST_CATEGORIES),
            "core_chokepoints": core_count,
            "high_attention": high_attention_count,
            "priced_tickers": len(market_rows),
        },
        "source_status": [
            {
                "name": "Serenity Alert",
                "status": "live",
                "detail": "X original-post monitor is deployed.",
            },
            {
                "name": "AI chokepoint map",
                "status": "live",
                "detail": "Dashboard taxonomy is seeded from the AI supply-chain report.",
            },
            {
                "name": "Market data",
                "status": market_status,
                "detail": market_detail,
                "provider": market_data.provider if market_data else "Massive",
                "loaded_tickers": market_data.loaded_count if market_data else 0,
                "eligible_tickers": market_data.eligible_count if market_data else 0,
                "fundamentals_loaded": market_data.fundamentals_loaded_count
                if market_data
                else 0,
            },
            {
                "name": "Fundamentals",
                "status": "pending",
                "detail": "Daily cache will be enabled with the market data provider.",
            },
        ],
        "categories": [
            {
                "slug": category["slug"],
                "label": category["label"],
                "description": category["description"],
                "count": len(category["rows"]),
            }
            for category in WATCHLIST_CATEGORIES
        ]
        + (
            [
                {
                    **DYNAMIC_CATEGORY,
                    "count": len(extra_rows),
                }
            ]
            if extra_rows
            else []
        ),
        "rows": rows,
    }
