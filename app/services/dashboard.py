from __future__ import annotations

from app.models import utcnow


WATCHLIST_CATEGORIES: list[dict] = [
    {
        "slug": "compute",
        "label": "Compute",
        "description": "GPU, accelerator, and AI server demand.",
        "rows": [
            {
                "ticker": "NVDA",
                "company": "NVIDIA",
                "region": "US",
                "ai_layer": "GPU",
                "role": "Training and inference accelerator leader",
                "latest_signal": "Core AI capex beneficiary",
            },
            {
                "ticker": "AMD",
                "company": "Advanced Micro Devices",
                "region": "US",
                "ai_layer": "GPU",
                "role": "Alternative accelerator supplier",
                "latest_signal": "MI-series adoption watch",
            },
            {
                "ticker": "SMCI",
                "company": "Super Micro Computer",
                "region": "US",
                "ai_layer": "Servers",
                "role": "AI server integration",
                "latest_signal": "Rack-scale deployment proxy",
            },
            {
                "ticker": "DELL",
                "company": "Dell Technologies",
                "region": "US",
                "ai_layer": "Servers",
                "role": "Enterprise AI server channel",
                "latest_signal": "Backlog and margin mix watch",
            },
            {
                "ticker": "HPE",
                "company": "Hewlett Packard Enterprise",
                "region": "US",
                "ai_layer": "Servers",
                "role": "Enterprise and HPC infrastructure",
                "latest_signal": "AI systems pipeline watch",
            },
        ],
    },
    {
        "slug": "semis",
        "label": "Semiconductors",
        "description": "Foundry, memory, packaging, and chip equipment.",
        "rows": [
            {
                "ticker": "TSM",
                "company": "TSMC",
                "region": "Taiwan",
                "ai_layer": "Foundry",
                "role": "Advanced-node manufacturing",
                "latest_signal": "CoWoS and N3/N2 capacity watch",
            },
            {
                "ticker": "ASML",
                "company": "ASML",
                "region": "Netherlands",
                "ai_layer": "Equipment",
                "role": "EUV lithography bottleneck",
                "latest_signal": "Advanced-node capex proxy",
            },
            {
                "ticker": "AVGO",
                "company": "Broadcom",
                "region": "US",
                "ai_layer": "ASIC/Networking",
                "role": "Custom silicon and switching",
                "latest_signal": "Hyperscaler custom ASIC exposure",
            },
            {
                "ticker": "MU",
                "company": "Micron",
                "region": "US",
                "ai_layer": "HBM/DRAM",
                "role": "AI memory supplier",
                "latest_signal": "HBM pricing and supply watch",
            },
            {
                "ticker": "AMAT",
                "company": "Applied Materials",
                "region": "US",
                "ai_layer": "Equipment",
                "role": "Wafer fabrication equipment",
                "latest_signal": "Foundry and memory capex proxy",
            },
            {
                "ticker": "LRCX",
                "company": "Lam Research",
                "region": "US",
                "ai_layer": "Equipment",
                "role": "Etch and deposition equipment",
                "latest_signal": "Memory recovery proxy",
            },
        ],
    },
    {
        "slug": "power",
        "label": "Power & Cooling",
        "description": "Power, thermal, data-center infrastructure.",
        "rows": [
            {
                "ticker": "VRT",
                "company": "Vertiv",
                "region": "US",
                "ai_layer": "Cooling/Power",
                "role": "Data-center thermal and power systems",
                "latest_signal": "Liquid cooling demand watch",
            },
            {
                "ticker": "ETN",
                "company": "Eaton",
                "region": "US",
                "ai_layer": "Power",
                "role": "Electrical equipment and power distribution",
                "latest_signal": "Grid upgrade proxy",
            },
            {
                "ticker": "PWR",
                "company": "Quanta Services",
                "region": "US",
                "ai_layer": "Grid",
                "role": "Power infrastructure buildout",
                "latest_signal": "Transmission backlog watch",
            },
            {
                "ticker": "CEG",
                "company": "Constellation Energy",
                "region": "US",
                "ai_layer": "Power",
                "role": "Nuclear and clean power supplier",
                "latest_signal": "Data-center power contract watch",
            },
            {
                "ticker": "GEV",
                "company": "GE Vernova",
                "region": "US",
                "ai_layer": "Grid/Power",
                "role": "Grid and power equipment",
                "latest_signal": "Electrification backlog proxy",
            },
        ],
    },
    {
        "slug": "cloud",
        "label": "Cloud",
        "description": "Hyperscalers funding the AI infrastructure cycle.",
        "rows": [
            {
                "ticker": "MSFT",
                "company": "Microsoft",
                "region": "US",
                "ai_layer": "Cloud",
                "role": "Azure AI and OpenAI distribution",
                "latest_signal": "AI capex and cloud margin watch",
            },
            {
                "ticker": "GOOGL",
                "company": "Alphabet",
                "region": "US",
                "ai_layer": "Cloud/TPU",
                "role": "Google Cloud and TPU stack",
                "latest_signal": "TPU and Gemini monetization watch",
            },
            {
                "ticker": "AMZN",
                "company": "Amazon",
                "region": "US",
                "ai_layer": "Cloud",
                "role": "AWS AI infrastructure",
                "latest_signal": "AWS growth and capex intensity watch",
            },
            {
                "ticker": "META",
                "company": "Meta Platforms",
                "region": "US",
                "ai_layer": "Model/Infra",
                "role": "Large-scale AI infra spender",
                "latest_signal": "Open model and capex cycle watch",
            },
            {
                "ticker": "ORCL",
                "company": "Oracle",
                "region": "US",
                "ai_layer": "Cloud",
                "role": "GPU cloud capacity supplier",
                "latest_signal": "AI cloud backlog watch",
            },
        ],
    },
    {
        "slug": "software",
        "label": "Software",
        "description": "Enterprise AI adoption and monetization layer.",
        "rows": [
            {
                "ticker": "PLTR",
                "company": "Palantir",
                "region": "US",
                "ai_layer": "AI Platform",
                "role": "Enterprise AI workflow platform",
                "latest_signal": "AIP adoption and valuation watch",
            },
            {
                "ticker": "SNOW",
                "company": "Snowflake",
                "region": "US",
                "ai_layer": "Data Cloud",
                "role": "AI data infrastructure",
                "latest_signal": "Consumption and Cortex AI watch",
            },
            {
                "ticker": "DDOG",
                "company": "Datadog",
                "region": "US",
                "ai_layer": "Observability",
                "role": "Cloud and AI workload monitoring",
                "latest_signal": "AI-native workload growth proxy",
            },
            {
                "ticker": "CRWD",
                "company": "CrowdStrike",
                "region": "US",
                "ai_layer": "Security",
                "role": "AI-era endpoint and cloud security",
                "latest_signal": "Platform consolidation watch",
            },
            {
                "ticker": "CRM",
                "company": "Salesforce",
                "region": "US",
                "ai_layer": "Enterprise Apps",
                "role": "AI agents in enterprise workflows",
                "latest_signal": "Agentforce adoption watch",
            },
        ],
    },
    {
        "slug": "robotics",
        "label": "Robotics",
        "description": "Physical AI, automation, and edge compute exposure.",
        "rows": [
            {
                "ticker": "TSLA",
                "company": "Tesla",
                "region": "US",
                "ai_layer": "Physical AI",
                "role": "Autonomy and humanoid optionality",
                "latest_signal": "Robotaxi and Optimus milestones",
            },
            {
                "ticker": "ISRG",
                "company": "Intuitive Surgical",
                "region": "US",
                "ai_layer": "Robotics",
                "role": "Robotic surgery platform",
                "latest_signal": "Procedure growth and system placements",
            },
            {
                "ticker": "TER",
                "company": "Teradyne",
                "region": "US",
                "ai_layer": "Automation/Test",
                "role": "Semiconductor test and industrial automation",
                "latest_signal": "AI chip test cycle proxy",
            },
            {
                "ticker": "ROK",
                "company": "Rockwell Automation",
                "region": "US",
                "ai_layer": "Industrial Automation",
                "role": "Factory automation stack",
                "latest_signal": "Manufacturing automation cycle watch",
            },
        ],
    },
]


def get_dashboard_snapshot() -> dict:
    rows = [
        {**row, "category": category["slug"], "category_label": category["label"]}
        for category in WATCHLIST_CATEGORIES
        for row in category["rows"]
    ]
    return {
        "generated_at": utcnow().isoformat(),
        "refresh_interval_seconds": 15,
        "data_status": "provider_pending",
        "data_status_label": "Market data provider pending",
        "disclaimer": "Information dashboard only. Not investment advice.",
        "metrics": {
            "tracked_tickers": len(rows),
            "categories": len(WATCHLIST_CATEGORIES),
            "live_prices": 0,
            "alert_sources": 1,
        },
        "source_status": [
            {
                "name": "Serenity Alert",
                "status": "live",
                "detail": "X original-post monitor is deployed.",
            },
            {
                "name": "Market data",
                "status": "pending",
                "detail": "Provider adapter is not connected yet.",
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
        ],
        "rows": rows,
    }
