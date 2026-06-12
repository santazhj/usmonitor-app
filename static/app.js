const els = {
  logoutBtn: document.querySelector("#logoutBtn"),
  adminLink: document.querySelector("#adminLink"),
  languageToggle: document.querySelector("#languageToggle"),
  dashboardMetrics: document.querySelector("#dashboardMetrics"),
  intelPanel: document.querySelector("#intelPanel"),
  categoryTabs: document.querySelector("#categoryTabs"),
  dashboardRows: document.querySelector("#dashboardRows"),
  sourceStatus: document.querySelector("#sourceStatus"),
  dataStatus: document.querySelector("#dataStatus"),
  lastUpdated: document.querySelector("#lastUpdated"),
  refreshLabel: document.querySelector("#refreshLabel"),
  dashboardSearch: document.querySelector("#dashboardSearch"),
  rowQualityFilter: document.querySelector("#rowQualityFilter"),
  tableStatus: document.querySelector("#tableStatus"),
  clearFiltersBtn: document.querySelector("#clearFiltersBtn"),
  feedBox: document.querySelector("#feedBox"),
  tickerDrawer: document.querySelector("#tickerDrawer"),
  drawerClose: document.querySelector("#drawerClose"),
  drawerBody: document.querySelector("#drawerBody")
};

const LANGUAGE_KEY = "usmonitor.language";
const CATEGORY_KEY = "usmonitor.dashboard.category";
const SEARCH_KEY = "usmonitor.dashboard.search";
const SORT_FIELD_KEY = "usmonitor.dashboard.sortField";
const SORT_DIRECTION_KEY = "usmonitor.dashboard.sortDirection";
const QUALITY_KEY = "usmonitor.dashboard.quality";
const FEED_FILTER_KEY = "usmonitor.feed.filter";
const READ_ALERTS_KEY = "usmonitor.feed.read";
const SAVED_ALERTS_KEY = "usmonitor.feed.saved";
const VISITOR_KEY = "usmonitor.visitorId";

const DEFAULT_SORT_FIELD = "dollar_volume";
const DEFAULT_SORT_DIRECTION = "desc";

const state = {
  language: localStorage.getItem(LANGUAGE_KEY) || "zh",
  category: localStorage.getItem(CATEGORY_KEY) || "all",
  search: localStorage.getItem(SEARCH_KEY) || "",
  quality: localStorage.getItem(QUALITY_KEY) || "all",
  sortField: localStorage.getItem(SORT_FIELD_KEY) || DEFAULT_SORT_FIELD,
  sortDirection: localStorage.getItem(SORT_DIRECTION_KEY) || DEFAULT_SORT_DIRECTION,
  feedFilter: localStorage.getItem(FEED_FILTER_KEY) || "all",
  readAlerts: readSet(READ_ALERTS_KEY),
  savedAlerts: readSet(SAVED_ALERTS_KEY),
  dashboard: null,
  dashboardError: "",
  feed: [],
  user: null,
  drawerTicker: "",
  candlePeriod: "day",
  candleRequestId: 0
};

const CANDLE_PERIODS = [
  { key: "intraday", zh: "日内", en: "Intra" },
  { key: "day", zh: "日K", en: "Day" },
  { key: "week", zh: "周K", en: "Week" },
  { key: "month", zh: "月K", en: "Month" },
  { key: "year", zh: "年K", en: "Year" }
];

const COPY = {
  zh: {
    "brand.subtitle": "AI 产业链情报终端",
    "nav.dashboard": "看板",
    "nav.alerts": "情报",
    "nav.account": "账户",
    "nav.logout": "退出",
    "hero.eyebrow": "AI Infrastructure",
    "hero.title": "美股 AI 产业链监控",
    "hero.lede": "按云资本开支、算力网络、晶圆制造、存储、封装、光互连、电力冷却和软件数据分层跟踪核心标的。",
    "status.label": "数据状态",
    "filters.title": "产业链分组",
    "filters.clear": "清空",
    "sources.title": "数据源",
    "search.placeholder": "搜索 ticker、公司、AI 角色",
    "quality.all": "全部",
    "quality.live": "有行情",
    "quality.missing": "缺行情",
    "table.title": "产业链标的矩阵",
    "table.ticker": "标的",
    "table.price": "最新价",
    "table.change": "% 涨跌",
    "table.dollarVolume": "成交额",
    "table.marketCap": "市值",
    "table.pe": "PE",
    "table.layer": "分层",
    "table.role": "AI 角色",
    "table.source": "数据",
    "alerts.title": "最新情报",
    "alerts.all": "全部",
    "alerts.unread": "未读",
    "alerts.saved": "收藏",
    "alerts.loading": "正在加载情报...",
    "alerts.empty": "暂无情报。",
    "alerts.failed": "情报加载失败，请稍后刷新。",
    "alerts.read": "已读",
    "alerts.markRead": "标为已读",
    "alerts.save": "收藏",
    "alerts.unsave": "取消收藏",
    "alerts.source": "原文",
    "tabs.all": "全部",
    "metrics.tracked": "标的数",
    "metrics.priced": "行情覆盖",
    "metrics.core": "核心瓶颈",
    "metrics.attention": "高关注",
    "metrics.updated": "最近刷新",
    "metrics.detail.tracked": "当前产业链矩阵标的",
    "metrics.detail.priced": "{priced}/{total} 有行情",
    "metrics.detail.core": "供应链核心约束层",
    "metrics.detail.attention": "高流动性或高关注标的",
    "metrics.detail.updated": "接口生成时间",
    "intel.eyebrow": "AI Situation",
    "intel.title": "AI 产业链态势屏",
    "intel.summary": "基于行情、成交额和情报流生成的实时观察层。",
    "intel.focus": "当前主线",
    "intel.pressure": "压力点",
    "intel.breadth": "行情覆盖",
    "intel.map": "产业链热力地图",
    "intel.movers": "异动标的",
    "intel.avgChange": "平均涨跌",
    "intel.volume": "成交额",
    "intel.upDown": "上涨/下跌",
    "intel.covered": "{priced}/{total} 有行情",
    "intel.noData": "等待行情",
    "intel.open": "查看",
    "dashboard.refreshTarget": "{seconds}s 刷新目标",
    "dashboard.rowsShown": "显示 {shown}/{total}，排序：{sort}",
    "dashboard.noRows": "没有匹配的标的。",
    "dashboard.loadFailed": "看板加载失败",
    "status.market_live": "行情在线",
    "status.provider_error": "行情异常",
    "status.provider_pending": "等待行情",
    "row.live": "实时/收盘",
    "row.missing": "缺数",
    "row.stale": "陈旧",
    "drawer.market": "市场数据",
    "drawer.position": "产业链定位",
    "drawer.signal": "最新线索",
    "drawer.range": "日内区间",
    "drawer.chart": "K 线图",
    "chart.loading": "正在加载 K 线...",
    "chart.empty": "暂无 K 线数据",
    "chart.failed": "K 线加载失败",
    "chart.candles": "{count} 根 K 线",
    "drawer.source": "查看来源",
    "drawer.noSource": "暂无来源",
    "sort.ticker": "标的",
    "sort.price": "最新价",
    "sort.change_percent": "% 涨跌",
    "sort.dollar_volume": "成交额",
    "sort.market_cap": "市值",
    "sort.pe_ratio": "PE",
    "sort.category_label": "分层"
  },
  en: {
    "brand.subtitle": "AI supply-chain intelligence terminal",
    "nav.dashboard": "Dashboard",
    "nav.alerts": "Alerts",
    "nav.account": "Account",
    "nav.logout": "Sign out",
    "hero.eyebrow": "AI Infrastructure",
    "hero.title": "US AI Supply Chain Monitor",
    "hero.lede": "Track AI infrastructure names by cloud capex, compute, foundry, memory, packaging, optics, power, and software layers.",
    "status.label": "Data status",
    "filters.title": "Supply-chain layers",
    "filters.clear": "Clear",
    "sources.title": "Sources",
    "search.placeholder": "Search ticker, company, AI role",
    "quality.all": "All",
    "quality.live": "Priced",
    "quality.missing": "Missing",
    "table.title": "Supply-chain ticker matrix",
    "table.ticker": "Ticker",
    "table.price": "Last",
    "table.change": "% Chg",
    "table.dollarVolume": "$ Vol",
    "table.marketCap": "Mkt Cap",
    "table.pe": "PE",
    "table.layer": "Layer",
    "table.role": "AI Role",
    "table.source": "Data",
    "alerts.title": "Latest Intelligence",
    "alerts.all": "All",
    "alerts.unread": "Unread",
    "alerts.saved": "Saved",
    "alerts.loading": "Loading alerts...",
    "alerts.empty": "No alerts yet.",
    "alerts.failed": "Alerts could not be loaded. Please refresh later.",
    "alerts.read": "Read",
    "alerts.markRead": "Mark read",
    "alerts.save": "Save",
    "alerts.unsave": "Unsave",
    "alerts.source": "Source",
    "tabs.all": "All",
    "metrics.tracked": "Tickers",
    "metrics.priced": "Priced",
    "metrics.core": "Core Chokepoints",
    "metrics.attention": "High Attention",
    "metrics.updated": "Updated",
    "metrics.detail.tracked": "Current supply-chain matrix",
    "metrics.detail.priced": "{priced}/{total} priced",
    "metrics.detail.core": "Supply constraint layers",
    "metrics.detail.attention": "High-liquidity or high-attention names",
    "metrics.detail.updated": "API generation time",
    "intel.eyebrow": "AI Situation",
    "intel.title": "AI Supply-Chain Situation Screen",
    "intel.summary": "A live operating layer generated from market data, dollar volume, and intelligence flow.",
    "intel.focus": "Current Focus",
    "intel.pressure": "Pressure Point",
    "intel.breadth": "Price Coverage",
    "intel.map": "Supply-Chain Heat Map",
    "intel.movers": "Active Movers",
    "intel.avgChange": "Avg Change",
    "intel.volume": "$ Volume",
    "intel.upDown": "Up/Down",
    "intel.covered": "{priced}/{total} priced",
    "intel.noData": "Waiting for market data",
    "intel.open": "Open",
    "dashboard.refreshTarget": "{seconds}s refresh target",
    "dashboard.rowsShown": "Showing {shown}/{total}, sorted by {sort}",
    "dashboard.noRows": "No matching tickers.",
    "dashboard.loadFailed": "Dashboard failed to load",
    "status.market_live": "Market live",
    "status.provider_error": "Provider error",
    "status.provider_pending": "Provider pending",
    "row.live": "Live/close",
    "row.missing": "Missing",
    "row.stale": "Stale",
    "drawer.market": "Market Data",
    "drawer.position": "Supply-chain Position",
    "drawer.signal": "Latest Signal",
    "drawer.range": "Daily Range",
    "drawer.chart": "Candlestick Chart",
    "chart.loading": "Loading candles...",
    "chart.empty": "No candle data",
    "chart.failed": "Candles failed to load",
    "chart.candles": "{count} candles",
    "drawer.source": "View Source",
    "drawer.noSource": "No source",
    "sort.ticker": "Ticker",
    "sort.price": "Last",
    "sort.change_percent": "% Chg",
    "sort.dollar_volume": "$ Vol",
    "sort.market_cap": "Market Cap",
    "sort.pe_ratio": "PE",
    "sort.category_label": "Layer"
  }
};

const ZH_CATEGORY_LABELS = {
  all: "全部",
  capex: "云资本开支",
  "compute-network": "算力与网络",
  "foundry-test": "晶圆制造与测试",
  "memory-storage": "存储",
  "packaging-substrate": "封装与基板",
  optical: "光通信与光子",
  "power-cooling": "电力与冷却",
  "software-data": "软件与数据",
  "serenity-alert": "Serenity 新增",
  "Cloud CAPEX": "云资本开支",
  "Compute & Network": "算力与网络",
  "Foundry & Test": "晶圆制造与测试",
  "Memory & Storage": "存储",
  "Packaging & Substrate": "封装与基板",
  "Optical & Photonics": "光通信与光子",
  "Power & Cooling": "电力与冷却",
  "Software & Data": "软件与数据",
  "Serenity Adds": "Serenity 新增"
};

const ZH_LAYER_LABELS = {
  "Cloud CAPEX": "云资本开支",
  "Cloud/TPU": "云/TPU",
  "Cloud/ASIC": "云/ASIC",
  "AI Factory": "AI 工厂",
  "GPU Cloud": "GPU 云",
  "AI Cloud": "AI 云",
  "GPU/Networking": "GPU/网络",
  "GPU/CPU": "GPU/CPU",
  "Custom ASIC/Networking": "定制 ASIC/网络",
  "Custom Silicon/Optics": "定制芯片/光通信",
  "AI Ethernet": "AI 以太网",
  "PCIe/CXL": "PCIe/CXL",
  "AEC/SerDes": "AEC/SerDes",
  "AI Servers": "AI 服务器",
  "Foundry/CoWoS": "晶圆代工/CoWoS",
  EUV: "EUV 光刻",
  Equipment: "半导体设备",
  "Inspection/Metrology": "检测/量测",
  "AI Chip Test": "AI 芯片测试",
  "Hybrid Bonding": "混合键合",
  "HBM/DRAM/eSSD": "HBM/DRAM/eSSD",
  HBM: "HBM",
  "HBM/DRAM/Foundry": "HBM/DRAM/代工",
  "NAND/eSSD": "NAND/eSSD",
  "NAND Controllers": "NAND 控制器",
  "Korea Memory Basket": "韩国存储组合",
  "ABF Substrate": "ABF 基板",
  "ABF/PCB": "ABF/PCB",
  "ABF Film": "ABF 膜",
  "IC Substrate": "IC 基板",
  "Wafer-Level Test": "晶圆级测试",
  "Lasers/Transceivers": "激光器/收发器",
  "Lasers/Optical Components": "激光器/光组件",
  "Optical Manufacturing": "光模块制造",
  "Fiber/Advanced Optics": "光纤/先进光学",
  "Optical Modules": "光模块",
  "InP/GaAs Substrates": "InP/GaAs 基板",
  "DFB Laser/CPO": "DFB 激光器/CPO",
  "SOI Substrate": "SOI 基板",
  Epitaxy: "外延",
  "Specialty Foundry": "特色工艺代工",
  "Power/Thermal": "电力/热管理",
  "Electrical Equipment": "电气设备",
  "Power Management": "电力管理",
  "Electrical Enclosures": "电气保护/机柜",
  "Thermal Management": "热管理",
  "Onsite Power": "现场供电",
  "Clean Power": "清洁电力",
  "Grid/Power": "电网/电力",
  "Grid Buildout": "电网建设",
  "Utilities Basket": "公用事业组合",
  "AI Platform": "AI 平台",
  "Data Cloud": "数据云",
  Observability: "可观测性",
  Security: "安全",
  "Data/Attention": "数据/注意力",
  "Design Software": "设计软件",
  "Serenity Alert": "Serenity 新增"
};

const ZH_COMPANY_BY_TICKER = {
  "000660.KS": "SK 海力士",
  "005930.KS": "三星电子",
  "2802.T": "味之素",
  "3037.TW": "欣兴电子",
  "4062.T": "揖斐电",
  "6857.T": "爱德万测试",
  AAOI: "应用光电",
  AEHR: "Aehr 测试系统",
  ALAB: "Astera Labs",
  AMAT: "应用材料",
  AMD: "AMD",
  AMZN: "亚马逊",
  ANET: "Arista 网络",
  ASML: "阿斯麦",
  "ATS.VI": "奥特斯",
  AVGO: "博通",
  AXTI: "AXT",
  BE: "Bloom Energy",
  "BESI.AS": "BESI",
  CEG: "星座能源",
  COHR: "相干公司",
  CRDO: "Credo 科技",
  CRWD: "CrowdStrike",
  DDOG: "Datadog",
  DELL: "戴尔科技",
  ETN: "伊顿",
  EWY: "韩国 MSCI ETF",
  FIG: "Figma",
  FN: "Fabrinet",
  GEV: "GE Vernova",
  GLW: "康宁",
  GOOGL: "Alphabet/谷歌",
  IQE: "IQE",
  "IQE.L": "IQE",
  KLAC: "科磊",
  LITE: "Lumentum",
  LRCX: "泛林集团",
  META: "Meta",
  MOD: "Modine 制造",
  MRVL: "Marvell",
  MSFT: "微软",
  MU: "美光",
  NBIS: "Nebius",
  NVDA: "英伟达",
  NVT: "nVent",
  ORCL: "甲骨文",
  PLTR: "Palantir",
  PWR: "Quanta Services",
  RDDT: "Reddit",
  SIMO: "慧荣科技",
  SMCI: "超微电脑",
  SNDK: "闪迪",
  "SIVE.ST": "Sivers Semiconductors",
  SNOW: "Snowflake",
  "SOI.PA": "Soitec",
  "SU.PA": "施耐德电气",
  TSEM: "Tower Semiconductor",
  TSM: "台积电",
  VRT: "维谛技术",
  XLU: "公用事业 ETF"
};

const ZH_ROLE_LABELS = {
  "Azure AI demand anchor": "Azure AI 需求锚点",
  "TPU, Google Cloud, and internal model infrastructure": "TPU、Google Cloud 与内部模型基础设施",
  "AWS, Trainium, and hyperscale infrastructure demand": "AWS、Trainium 与超大规模基建需求",
  "Large AI infrastructure spender": "大型 AI 基建投入方",
  "AI cloud capacity and GPU infrastructure supplier": "AI 云容量与 GPU 基建设施供应商",
  "High-beta AI cloud capacity provider": "高弹性 AI 云算力供应商",
  "AI rack-scale platform reference asset": "AI 整机柜平台标杆",
  "Alternative accelerator and server CPU supplier": "替代加速器与服务器 CPU 供应商",
  "Core beneficiary of hyperscaler custom silicon": "超大规模定制芯片核心受益方",
  "Custom silicon, DSP, and electro-optics bridge": "定制芯片、DSP 与电光互联桥梁",
  "Cloud AI spine/leaf switching supplier": "云端 AI 交换机供应商",
  "AI server retimer and rack connectivity exposure": "AI 服务器 Retimer 与机柜互联标的",
  "High-speed connectivity and active electrical cable exposure": "高速互联与 AEC 标的",
  "Rack-scale AI server integration proxy": "AI 整机柜服务器集成代表",
  "Enterprise AI server channel": "企业 AI 服务器渠道",
  "Systemic chokepoint for AI accelerators and advanced packaging": "AI 加速器与先进封装系统级瓶颈",
  "Upstream chokepoint for advanced logic and DRAM EUV": "先进逻辑与 DRAM EUV 上游瓶颈",
  "Deposition, etch, and packaging equipment exposure": "沉积、刻蚀与封装设备标的",
  "Etch/deposition exposure to memory and advanced nodes": "存储与先进制程刻蚀/沉积标的",
  "Yield-control beneficiary for advanced nodes and packaging": "先进制程与封装良率控制受益方",
  "SoC, HBM, and AI accelerator testing bottleneck": "SoC、HBM 与 AI 加速器测试瓶颈",
  "High-beta hybrid bonding equipment exposure": "高弹性混合键合设备标的",
  "US-listed core HBM and AI memory exposure": "美股核心 HBM 与 AI 存储标的",
  "Leading HBM supplier with strong financial validation": "财务验证较强的 HBM 龙头",
  "HBM catch-up and memory-cycle reference asset": "HBM 追赶与存储周期代表",
  "AI storage and NAND-cycle leverage": "AI 存储与 NAND 周期弹性",
  "Controller exposure to SSD and embedded storage demand": "SSD 与嵌入式存储控制器标的",
  "Liquid proxy for SK hynix and Samsung exposure": "SK 海力士与三星的流动性代理",
  "High-end IC substrate exposure for AI GPU/ASIC packages": "AI GPU/ASIC 高端 IC 基板标的",
  "AI server PCB and high-layer substrate exposure": "AI 服务器 PCB 与高层板标的",
  "Hidden material bottleneck in high-end substrates": "高端基板隐性材料瓶颈",
  "High-beta substrate and advanced PCB supplier": "高弹性基板与先进 PCB 供应商",
  "Small-cap test exposure to SiC, GaN, and photonics": "SiC、GaN 与光子测试小盘标的",
  "Institutional optical-chain asset": "机构级光通信链标的",
  "Laser and optical component exposure to AI datacom": "AI 数据通信激光与光组件标的",
  "Optical module manufacturing capacity proxy": "光模块制造产能代理",
  "Large-cap optical material reference asset": "大盘光学材料代表",
  "High-attention AI optics beta": "高关注 AI 光通信弹性标的",
  "Serenity-style bottom-layer photonics material exposure": "底层光子材料标的",
  "Small-cap LRO/CPO light-source exposure": "LRO/CPO 光源小盘标的",
  "Silicon photonics and SOI material exposure": "硅光与 SOI 材料标的",
  "Compound semiconductor epitaxy exposure": "化合物半导体外延标的",
  "Analog and silicon photonics foundry exposure": "模拟与硅光代工标的",
  "Direct AI data-center power and cooling bottleneck": "AI 数据中心电力与冷却直接瓶颈",
  "Switchgear, transformer, and power distribution exposure": "开关设备、变压器与配电标的",
  "European core data-center electrification asset": "欧洲数据中心电气化核心标的",
  "Electrical protection and enclosure content exposure": "电气保护与机柜内容标的",
  "Liquid cooling and heat rejection high-beta exposure": "液冷与散热高弹性标的",
  "Fuel-cell and onsite power optionality for data centers": "数据中心燃料电池与现场供电期权",
  "Large-scale power supplier for data-center demand": "数据中心需求的大型电力供应商",
  "Grid equipment and electrification backlog proxy": "电网设备与电气化订单代理",
  "Transmission and power infrastructure construction proxy": "输电与电力基础设施建设代理",
  "Liquid ETF proxy for AI power theme": "AI 电力主题流动性 ETF 代理",
  "Enterprise AI workflow and government AI exposure": "企业 AI 工作流与政府 AI 标的",
  "Enterprise data platform feeding AI workloads": "支撑 AI 工作负载的企业数据平台",
  "Cloud and AI workload observability exposure": "云与 AI 工作负载可观测性标的",
  "AI-era endpoint and cloud security platform": "AI 时代终端与云安全平台",
  "High-attention data licensing and social platform asset": "高关注数据授权与社交平台标的",
  "Product design collaboration and AI workflow exposure": "产品设计协作与 AI 工作流标的",
  "Positive source mention": "正向来源提及"
};

function zhLookup(value, dictionary) {
  if (state.language !== "zh" || !value) return value || "";
  return dictionary[value] || value;
}

function displayCompany(row) {
  if (state.language !== "zh") return row.company || "";
  return ZH_COMPANY_BY_TICKER[row.ticker] || row.company || "";
}

function displayLayer(row) {
  const category = ZH_CATEGORY_LABELS[row.category] || ZH_CATEGORY_LABELS[row.category_label];
  if (state.language === "zh" && category) return category;
  return row.category_label || row.ai_layer || "--";
}

function displayAiLayer(row) {
  return zhLookup(row.ai_layer, ZH_LAYER_LABELS) || "--";
}

function displayRole(row) {
  return zhLookup(row.role, ZH_ROLE_LABELS) || "--";
}

function displayCategoryItem(item) {
  if (state.language !== "zh") return item.label;
  return ZH_CATEGORY_LABELS[item.slug] || ZH_CATEGORY_LABELS[item.label] || item.label;
}

const ZH_SOURCE_LABELS = {
  "Serenity Alert": "Serenity 情报",
  "AI chokepoint map": "AI 瓶颈图谱",
  "Market data": "行情数据",
  Fundamentals: "基本面",
  live: "在线",
  pending: "等待",
  error: "异常",
  "X original-post monitor is deployed.": "X 原始帖监控已部署。",
  "Dashboard taxonomy is seeded from the AI supply-chain report.": "产业链分层来自 AI 供应链图谱。",
  "Provider adapter is not connected yet.": "行情适配器等待连接。"
};

function displaySourceText(value) {
  if (state.language !== "zh" || !value) return value || "";
  if (value.startsWith("Massive full-market snapshot connected.")) {
    return value
      .replace("Massive full-market snapshot connected.", "全市场行情已连接。")
      .replace("U.S. tickers populated.", "个美股标的有行情。")
      .replace("Fundamentals populated for", "基本面覆盖")
      .replace("priced tickers.", "个有行情标的。")
      .replace("Yahoo Chart fallback populated", "全球补充行情覆盖")
      .replace("missing/global tickers.", "个缺失/全球标的。")
      .replace("Yahoo Quote fundamentals populated", "补充基本面覆盖")
      .replace("market-cap/PE rows.", "行市值/PE。")
      .replaceAll("Massive", "行情源")
      .replaceAll("Yahoo Chart", "补充行情")
      .replaceAll("Yahoo Quote", "补充基本面");
  }
  if (value.startsWith("Low-frequency market cap and PE cache populated for")) {
    return value
      .replace("Low-frequency market cap and PE cache populated for", "低频市值和 PE 缓存已覆盖")
      .replace("tickers.", "个标的。");
  }
  return ZH_SOURCE_LABELS[value] || value;
}

function t(key, params = {}) {
  let value = COPY[state.language]?.[key] || COPY.zh[key] || key;
  Object.entries(params).forEach(([name, replacement]) => {
    value = value.replaceAll(`{${name}}`, replacement);
  });
  return value;
}

function readSet(key) {
  try {
    return new Set(JSON.parse(localStorage.getItem(key) || "[]"));
  } catch {
    return new Set();
  }
}

function writeSet(key, set) {
  localStorage.setItem(key, JSON.stringify([...set]));
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
    ...options
  });
  if (!response.ok) {
    const text = await response.text();
    const error = new Error(text || "Request failed");
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return new Intl.NumberFormat(state.language === "zh" ? "zh-Hans" : "en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(number);
}

function formatCompact(value, prefix = "") {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  const abs = Math.abs(number);
  const locale = state.language === "zh" ? "zh-Hans" : "en-US";
  if (abs >= 1_000_000_000_000) return `${prefix}${formatNumber(number / 1_000_000_000_000, 2)}T`;
  if (abs >= 1_000_000_000) return `${prefix}${formatNumber(number / 1_000_000_000, 2)}B`;
  if (abs >= 1_000_000) return `${prefix}${formatNumber(number / 1_000_000, 2)}M`;
  return `${prefix}${new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(number)}`;
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  const sign = number > 0 ? "+" : "";
  return `${sign}${formatNumber(number, 2)}%`;
}

function parseApiDate(value) {
  if (!value) return null;
  const text = String(value);
  const hasTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(text);
  const normalized = hasTimezone ? text : `${text}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDateTime(value) {
  const date = parseApiDate(value);
  if (!date) return "--";
  return date.toLocaleString(state.language === "zh" ? "zh-Hans" : "en-US", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short"
  });
}

function rowStatus(row) {
  const labels = state.language === "zh"
    ? { live: "实时", close: "收盘", missing: "缺失" }
    : { live: "Live", close: "Close", missing: "Missing" };
  if (!Number.isFinite(Number(row.price))) return { key: "missing", label: labels.missing };
  if (row.price_mode === "live") return { key: "live", label: labels.live };
  if (row.price_mode === "close") return { key: "stale", label: labels.close };
  const updated = parseApiDate(row.market_updated_at);
  if (updated && Date.now() - updated.getTime() > 1000 * 60 * 60 * 36) {
    return { key: "stale", label: labels.close };
  }
  return { key: "live", label: labels.live };
}

function candlePeriodLabel(periodKey) {
  const period = CANDLE_PERIODS.find((item) => item.key === periodKey);
  if (!period) return periodKey;
  return state.language === "zh" ? period.zh : period.en;
}

function formatCandleTimestamp(value, period) {
  const date = parseApiDate(value);
  if (!date) return "--";
  const locale = state.language === "zh" ? "zh-Hans" : "en-US";
  if (period === "intraday") {
    return date.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  }
  if (period === "year") {
    return date.toLocaleDateString(locale, { year: "numeric" });
  }
  return date.toLocaleDateString(locale, { month: "2-digit", day: "2-digit" });
}

function setCandleStatus(message, tone = "muted") {
  const status = document.querySelector("#candleStatus");
  if (!status) return;
  status.textContent = message;
  status.dataset.tone = tone;
  status.classList.remove("hidden");
}

async function loadCandles(ticker, period) {
  state.candlePeriod = period;
  const requestId = ++state.candleRequestId;
  document.querySelectorAll("[data-candle-period]").forEach((button) => {
    button.classList.toggle("active", button.dataset.candlePeriod === period);
  });
  const meta = document.querySelector("#candleMeta");
  if (meta) meta.textContent = candlePeriodLabel(period);
  setCandleStatus(t("chart.loading"));

  try {
    const data = await api(`/api/market/candles/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period)}`);
    if (requestId !== state.candleRequestId || ticker !== state.drawerTicker) return;
    renderCandleChart(data);
  } catch {
    if (requestId !== state.candleRequestId) return;
    const canvas = document.querySelector("#candleChart");
    if (canvas) {
      const context = canvas.getContext("2d");
      context?.clearRect(0, 0, canvas.width, canvas.height);
    }
    if (meta) meta.textContent = candlePeriodLabel(period);
    setCandleStatus(t("chart.failed"), "warn");
  }
}

function renderCandleChart(data) {
  const rows = (data?.candles || []).filter((row) => (
    Number.isFinite(Number(row.open))
    && Number.isFinite(Number(row.high))
    && Number.isFinite(Number(row.low))
    && Number.isFinite(Number(row.close))
  ));
  const canvas = document.querySelector("#candleChart");
  const meta = document.querySelector("#candleMeta");
  if (meta) {
    meta.textContent = rows.length
      ? `${candlePeriodLabel(data.period)} · ${t("chart.candles", { count: rows.length })}`
      : candlePeriodLabel(data.period);
  }
  if (!canvas || !rows.length) {
    setCandleStatus(t("chart.empty"), "warn");
    return;
  }
  drawCandles(canvas, rows, data.period);
  document.querySelector("#candleStatus")?.classList.add("hidden");
}

function drawCandles(canvas, rows, period) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor(rect.width));
  const height = Math.max(220, Math.floor(rect.height));
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const margin = { top: 16, right: 16, bottom: 34, left: 58 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const highs = rows.map((row) => Number(row.high));
  const lows = rows.map((row) => Number(row.low));
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const pricePadding = (maxPrice - minPrice || maxPrice || 1) * 0.08;
  const topPrice = maxPrice + pricePadding;
  const bottomPrice = minPrice - pricePadding;
  const yFor = (price) => margin.top + ((topPrice - price) / (topPrice - bottomPrice)) * plotHeight;
  const xFor = (index) => margin.left + (rows.length === 1 ? plotWidth / 2 : (index / (rows.length - 1)) * plotWidth);

  ctx.font = "11px JetBrains Mono, Consolas, monospace";
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(244, 244, 245, 0.08)";
  ctx.fillStyle = "rgba(161, 161, 170, 0.9)";
  for (let index = 0; index <= 4; index += 1) {
    const y = margin.top + (plotHeight / 4) * index;
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(width - margin.right, y);
    ctx.stroke();
    const price = topPrice - ((topPrice - bottomPrice) / 4) * index;
    ctx.fillText(formatNumber(price, 2), 8, y + 4);
  }

  const candleWidth = Math.max(2, Math.min(10, (plotWidth / rows.length) * 0.58));
  rows.forEach((row, index) => {
    const open = Number(row.open);
    const high = Number(row.high);
    const low = Number(row.low);
    const close = Number(row.close);
    const up = close >= open;
    const color = up ? "#34d399" : "#fb7185";
    const x = xFor(index);
    const yHigh = yFor(high);
    const yLow = yFor(low);
    const yOpen = yFor(open);
    const yClose = yFor(close);
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(2, Math.abs(yClose - yOpen));
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, yHigh);
    ctx.lineTo(x, yLow);
    ctx.stroke();
    ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
  });

  ctx.fillStyle = "rgba(161, 161, 170, 0.85)";
  const first = rows[0];
  const last = rows[rows.length - 1];
  ctx.fillText(formatCandleTimestamp(first.timestamp, period), margin.left, height - 10);
  const lastLabel = formatCandleTimestamp(last.timestamp, period);
  const lastWidth = ctx.measureText(lastLabel).width;
  ctx.fillText(lastLabel, width - margin.right - lastWidth, height - 10);
  ctx.fillStyle = "#e4e4e7";
  const closeLabel = `C ${formatNumber(last.close, 2)}`;
  const closeWidth = ctx.measureText(closeLabel).width;
  ctx.fillText(closeLabel, width - margin.right - closeWidth, margin.top + 12);
}

function sortValue(row, field) {
  const value = row[field];
  if (field === "ticker" || field === "category_label") return String(value || "");
  const number = Number(value);
  return Number.isFinite(number) ? number : Number.NEGATIVE_INFINITY;
}

function currentRows() {
  const rows = [...(state.dashboard?.rows || [])];
  const search = state.search.trim().toLowerCase();
  return rows
    .filter((row) => state.category === "all" || row.category === state.category)
    .filter((row) => {
      const quality = rowStatus(row).key;
      if (state.quality === "live") return quality !== "missing";
      if (state.quality === "missing") return quality === "missing";
      return true;
    })
    .filter((row) => {
      if (!search) return true;
      return [
        row.ticker,
        row.company,
        row.category_label,
        row.ai_layer,
        row.role,
        row.latest_signal,
        displayCompany(row),
        displayLayer(row),
        displayAiLayer(row),
        displayRole(row)
      ]
        .join(" ")
        .toLowerCase()
        .includes(search);
    })
    .sort((a, b) => {
      const av = sortValue(a, state.sortField);
      const bv = sortValue(b, state.sortField);
      let result = typeof av === "string" ? av.localeCompare(bv) : av - bv;
      if (state.sortDirection === "desc") result *= -1;
      return result;
    });
}

function pricedDashboardRows() {
  return (state.dashboard?.rows || []).filter((row) => Number.isFinite(Number(row.price)));
}

function categoryStats() {
  const categories = state.dashboard?.categories || [];
  const rows = state.dashboard?.rows || [];
  const stats = categories.map((category) => {
    const categoryRows = rows.filter((row) => row.category === category.slug);
    const priced = categoryRows.filter((row) => Number.isFinite(Number(row.price)));
    const changes = priced.map((row) => Number(row.change_percent)).filter(Number.isFinite);
    const volume = priced.reduce((sum, row) => sum + (Number(row.dollar_volume) || 0), 0);
    const avgChange = changes.length ? changes.reduce((sum, value) => sum + value, 0) / changes.length : null;
    const up = changes.filter((value) => value > 0).length;
    const down = changes.filter((value) => value < 0).length;
    const leader = [...priced].sort((a, b) => (Number(b.dollar_volume) || 0) - (Number(a.dollar_volume) || 0))[0];
    return {
      slug: category.slug,
      label: displayCategoryItem(category),
      count: categoryRows.length,
      priced: priced.length,
      avgChange,
      volume,
      up,
      down,
      leader
    };
  });
  const maxVolume = Math.max(...stats.map((item) => item.volume), 1);
  return stats.map((item) => ({
    ...item,
    heat: Math.max(
      12,
      Math.min(100, (item.volume / maxVolume) * 68 + Math.min(32, Math.abs(item.avgChange || 0) * 3.2))
    )
  }));
}

function formatAvgChange(value) {
  return value === null || value === undefined ? "--" : formatPercent(value);
}

function renderIntelPanel() {
  if (!els.intelPanel) return;
  if (state.dashboardError) {
    els.intelPanel.innerHTML = "";
    return;
  }
  const rows = state.dashboard?.rows || [];
  const pricedRows = pricedDashboardRows();
  const stats = categoryStats();
  if (!rows.length) {
    els.intelPanel.innerHTML = `
      <article class="intel-command-card">
        <span class="eyebrow">${escapeHtml(t("intel.eyebrow"))}</span>
        <h2>${escapeHtml(t("intel.title"))}</h2>
        <p>${escapeHtml(t("intel.noData"))}</p>
      </article>`;
    return;
  }

  const focus = [...stats].filter((item) => item.priced).sort((a, b) => b.volume - a.volume)[0];
  const pressure = [...stats]
    .filter((item) => item.avgChange !== null)
    .sort((a, b) => (a.avgChange ?? 0) - (b.avgChange ?? 0))[0];
  const total = rows.length;
  const coverage = total ? Math.round((pricedRows.length / total) * 100) : 0;
  const movers = [...pricedRows]
    .filter((row) => Number.isFinite(Number(row.change_percent)))
    .sort((a, b) => Math.abs(Number(b.change_percent)) - Math.abs(Number(a.change_percent)))
    .slice(0, 5);

  els.intelPanel.innerHTML = `
    <article class="intel-command-card">
      <span class="eyebrow">${escapeHtml(t("intel.eyebrow"))}</span>
      <h2>${escapeHtml(t("intel.title"))}</h2>
      <p>${escapeHtml(t("intel.summary"))}</p>
      <div class="intel-signal-grid">
        ${intelSignalBlock(t("intel.focus"), focus?.label || "--", focus ? `${formatAvgChange(focus.avgChange)} · ${formatCompact(focus.volume, "$")}` : "--", "focus")}
        ${intelSignalBlock(t("intel.pressure"), pressure?.label || "--", pressure ? `${formatAvgChange(pressure.avgChange)} · ${pressure.up}/${pressure.down}` : "--", "pressure")}
        ${intelSignalBlock(t("intel.breadth"), `${coverage}%`, t("intel.covered", { priced: pricedRows.length, total }), "breadth")}
      </div>
    </article>

    <article class="intel-map-card">
      <div class="intel-card-head">
        <span>${escapeHtml(t("intel.map"))}</span>
        <small>${escapeHtml(t("intel.avgChange"))}</small>
      </div>
      <div class="heat-map">
        ${stats
          .map((item) => {
            const tone = (item.avgChange || 0) >= 0 ? "up" : "down";
            const active = state.category === item.slug ? "active" : "";
            const heatOpacity = (0.06 + item.heat / 580).toFixed(3);
            return `
              <button class="heat-node ${tone} ${active}" style="--heat:${item.heat.toFixed(0)}%; --heat-opacity:${heatOpacity}" data-intel-category="${escapeHtml(item.slug)}" type="button">
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(formatAvgChange(item.avgChange))}</strong>
                <small>${escapeHtml(item.priced)}/${escapeHtml(item.count)} · ${escapeHtml(formatCompact(item.volume, "$"))}</small>
                <i><b style="width:${item.heat.toFixed(0)}%"></b></i>
              </button>`;
          })
          .join("")}
      </div>
    </article>

    <article class="intel-movers-card">
      <div class="intel-card-head">
        <span>${escapeHtml(t("intel.movers"))}</span>
        <small>${escapeHtml(t("intel.volume"))}</small>
      </div>
      <div class="mover-list">
        ${movers
          .map((row) => {
            const change = Number(row.change_percent);
            const tone = change >= 0 ? "up" : "down";
            return `
              <button class="mover-row ${tone}" data-intel-ticker="${escapeHtml(row.ticker)}" type="button">
                <span>
                  <strong>${escapeHtml(row.ticker)}</strong>
                  <small>${escapeHtml(displayCompany(row))}</small>
                </span>
                <em>${escapeHtml(formatPercent(row.change_percent))}</em>
                <b>${escapeHtml(formatCompact(row.dollar_volume, "$"))}</b>
              </button>`;
          })
          .join("")}
      </div>
    </article>`;
}

function intelSignalBlock(label, value, detail, tone) {
  return `
    <section class="intel-signal ${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(detail)}</small>
    </section>`;
}

function applyCopy() {
  document.documentElement.lang = state.language === "zh" ? "zh-Hans" : "en";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    if (element.tagName === "OPTION") element.textContent = t(element.dataset.i18n);
  });
  els.languageToggle.textContent = state.language === "zh" ? "EN" : "中文";
}

function renderMetrics() {
  const snapshot = state.dashboard;
  const metrics = snapshot?.metrics || {};
  const total = metrics.tracked_tickers || snapshot?.rows?.length || 0;
  const generatedAt = snapshot?.generated_at;
  const cards = [
    {
      label: t("metrics.tracked"),
      value: total || "--",
      detail: t("metrics.detail.tracked"),
      icon: "◇"
    },
    {
      label: t("metrics.priced"),
      value: `${metrics.priced_tickers || 0}/${total || 0}`,
      detail: t("metrics.detail.priced", { priced: metrics.priced_tickers || 0, total: total || 0 }),
      icon: "●"
    },
    {
      label: t("metrics.core"),
      value: metrics.core_chokepoints ?? "--",
      detail: t("metrics.detail.core"),
      icon: "◆"
    },
    {
      label: t("metrics.attention"),
      value: metrics.high_attention ?? "--",
      detail: t("metrics.detail.attention"),
      icon: "▲"
    },
    {
      label: t("metrics.updated"),
      value: generatedAt ? formatDateTime(generatedAt) : "--",
      detail: t("metrics.detail.updated"),
      icon: "↻"
    }
  ];
  els.dashboardMetrics.innerHTML = cards
    .map(
      (card) => `
        <article class="terminal-kpi">
          <div>
            <span>${escapeHtml(card.label)}</span>
            <strong>${escapeHtml(card.value)}</strong>
            <small>${escapeHtml(card.detail)}</small>
          </div>
          <i>${escapeHtml(card.icon)}</i>
        </article>`
    )
    .join("");
}

function renderCategories() {
  const categories = state.dashboard?.categories || [];
  const allCount = state.dashboard?.rows?.length || 0;
  const items = [{ slug: "all", label: t("tabs.all"), count: allCount }, ...categories];
  els.categoryTabs.innerHTML = items
    .map(
      (item) => `
        <button class="${state.category === item.slug ? "active" : ""}" data-category="${escapeHtml(item.slug)}" type="button">
          <span>${escapeHtml(displayCategoryItem(item))}</span>
          <strong>${escapeHtml(item.count ?? "")}</strong>
        </button>`
    )
    .join("");
}

function renderSources() {
  const sources = state.dashboard?.source_status || [];
  els.sourceStatus.innerHTML = sources
    .map(
      (item) => `
        <article class="terminal-source ${escapeHtml(item.status || "pending")}">
          <span>${escapeHtml(displaySourceText(item.name))}</span>
          <strong>${escapeHtml(displaySourceText(item.status || "pending"))}</strong>
          <small>${escapeHtml(displaySourceText(item.detail || ""))}</small>
        </article>`
    )
    .join("");
}

function renderStatus() {
  const snapshot = state.dashboard;
  if (state.dashboardError) {
    els.dataStatus.textContent = t("dashboard.loadFailed");
    els.lastUpdated.textContent = "--";
    els.refreshLabel.textContent = "Start backend at http://127.0.0.1:8000";
    return;
  }
  const status = snapshot?.data_status || "provider_pending";
  els.dataStatus.textContent = t(`status.${status}`) || snapshot?.data_status_label || status;
  els.lastUpdated.textContent = snapshot?.generated_at ? formatDateTime(snapshot.generated_at) : "--";
  els.refreshLabel.textContent = snapshot?.refresh_interval_seconds
    ? t("dashboard.refreshTarget", { seconds: snapshot.refresh_interval_seconds })
    : "--";
}

function renderTable() {
  if (state.dashboardError) {
    els.dashboardRows.innerHTML = `<div class="terminal-empty-row">${escapeHtml(state.dashboardError)}</div>`;
    els.tableStatus.textContent = state.dashboardError;
    return;
  }
  const rows = currentRows();
  const total = state.dashboard?.rows?.length || 0;
  if (!rows.length) {
    els.dashboardRows.innerHTML = `<div class="terminal-empty-row">${escapeHtml(t("dashboard.noRows"))}</div>`;
  } else {
    els.dashboardRows.innerHTML = rows
      .map((row) => {
        const status = rowStatus(row);
        const change = Number(row.change_percent);
        const tone = Number.isFinite(change) && change > 0 ? "up" : Number.isFinite(change) && change < 0 ? "down" : "flat";
        return `
          <article class="terminal-table-row terminal-data-row" role="row" tabindex="0" data-ticker="${escapeHtml(row.ticker)}">
            <div class="ticker-cell sticky-col">
              <strong>${escapeHtml(row.ticker)}</strong>
              <small>${escapeHtml(displayCompany(row))}</small>
            </div>
            <div class="number-cell">${escapeHtml(formatNumber(row.price, 2))}</div>
            <div class="number-cell ${tone}">${escapeHtml(formatPercent(row.change_percent))}</div>
            <div class="number-cell">${escapeHtml(formatCompact(row.dollar_volume, "$"))}</div>
            <div class="number-cell">${escapeHtml(formatCompact(row.market_cap, "$"))}</div>
            <div class="number-cell">${escapeHtml(row.pe_note || formatNumber(row.pe_ratio, 1))}</div>
            <div><span class="soft-badge">${escapeHtml(displayLayer(row))}</span></div>
            <div class="role-cell">
              <strong>${escapeHtml(displayRole(row))}</strong>
            </div>
            <div class="source-cell">
              <span class="data-badge ${escapeHtml(status.key)}">${escapeHtml(status.label)}</span>
            </div>
          </article>`;
      })
      .join("");
  }

  els.tableStatus.textContent = t("dashboard.rowsShown", {
    shown: rows.length,
    total,
    sort: t(`sort.${state.sortField}`)
  });

  document.querySelectorAll(".table-sort").forEach((button) => {
    const active = button.dataset.sort === state.sortField;
    button.classList.toggle("active", active);
    button.dataset.direction = active ? state.sortDirection : "";
  });
}

function renderFeed() {
  const items = state.feed.filter((item) => {
    if (state.feedFilter === "unread") return !state.readAlerts.has(item.id);
    if (state.feedFilter === "saved") return state.savedAlerts.has(item.id);
    return true;
  });
  document.querySelectorAll("[data-feed-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.feedFilter === state.feedFilter);
  });
  if (!items.length) {
    els.feedBox.innerHTML = `<p class="empty">${escapeHtml(t("alerts.empty"))}</p>`;
    return;
  }
  els.feedBox.innerHTML = items
    .map((item) => {
      const read = state.readAlerts.has(item.id);
      const saved = state.savedAlerts.has(item.id);
      const tickers = (item.tickers || []).slice(0, 6);
      return `
        <article class="terminal-feed-card ${read ? "read" : ""}" data-alert-id="${escapeHtml(item.id)}">
          <div class="feed-card-head">
            <strong>${escapeHtml(item.title || "Untitled")}</strong>
            <time>${escapeHtml(formatDateTime(item.created_at))}</time>
          </div>
          <p>${escapeHtml(item.notification_text || "")}</p>
          <div class="feed-tickers">
            ${tickers.map((ticker) => `<button type="button" data-feed-ticker="${escapeHtml(ticker)}">$${escapeHtml(ticker)}</button>`).join("")}
          </div>
          <div class="feed-actions">
            <button type="button" data-feed-read="${escapeHtml(item.id)}">${escapeHtml(read ? t("alerts.read") : t("alerts.markRead"))}</button>
            <button type="button" data-feed-save="${escapeHtml(item.id)}">${escapeHtml(saved ? t("alerts.unsave") : t("alerts.save"))}</button>
            ${item.source_url ? `<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(t("alerts.source"))}</a>` : ""}
          </div>
        </article>`;
    })
    .join("");
}

function renderAll() {
  applyCopy();
  renderStatus();
  renderMetrics();
  renderIntelPanel();
  renderCategories();
  renderSources();
  renderTable();
  renderFeed();
}

function openDrawer(row) {
  state.drawerTicker = row.ticker;
  const status = rowStatus(row);
  const low = Number(row.low);
  const high = Number(row.high);
  const price = Number(row.price);
  const rangePct = Number.isFinite(low) && Number.isFinite(high) && high > low && Number.isFinite(price)
    ? Math.max(0, Math.min(100, ((price - low) / (high - low)) * 100))
    : null;
  els.drawerBody.innerHTML = `
    <div class="drawer-title">
      <div>
        <span class="eyebrow">${escapeHtml(displayAiLayer(row))}</span>
        <h2 id="drawerTitle">${escapeHtml(row.ticker)} <small>${escapeHtml(displayCompany(row))}</small></h2>
      </div>
      <span class="data-badge ${escapeHtml(status.key)}">${escapeHtml(status.label)}</span>
    </div>
    <div class="drawer-metrics terminal-drawer-grid">
      ${metricBlock(t("table.price"), formatNumber(row.price, 2))}
      ${metricBlock(t("table.change"), formatPercent(row.change_percent))}
      ${metricBlock(t("table.marketCap"), formatCompact(row.market_cap, "$"))}
      ${metricBlock(t("table.pe"), row.pe_note || formatNumber(row.pe_ratio, 1))}
      ${metricBlock(t("table.dollarVolume"), formatCompact(row.dollar_volume, "$"))}
      ${metricBlock(t("table.source"), status.label)}
    </div>
    <section class="drawer-section">
      <h3>${escapeHtml(t("drawer.position"))}</h3>
      <p>${escapeHtml(displayRole(row))}</p>
      <small>${escapeHtml(row.focus || "")} · ${escapeHtml(row.tier || "")}</small>
    </section>
    <section class="drawer-section">
      <h3>${escapeHtml(t("drawer.signal"))}</h3>
      <p>${escapeHtml(row.latest_signal || "--")}</p>
    </section>
    <section class="drawer-section">
      <h3>${escapeHtml(t("drawer.range"))}</h3>
      <div class="range-bar"><i style="left:${rangePct ?? 50}%"></i></div>
      <div class="range-labels">
        <span>L ${escapeHtml(formatNumber(row.low, 2))}</span>
        <span>H ${escapeHtml(formatNumber(row.high, 2))}</span>
      </div>
    </section>
    <section class="drawer-section candle-section">
      <div class="drawer-section-row">
        <h3>${escapeHtml(t("drawer.chart"))}</h3>
        <span id="candleMeta" class="candle-meta">--</span>
      </div>
      <div class="candle-periods">
        ${CANDLE_PERIODS.map((period) => `
          <button class="candle-period-btn ${state.candlePeriod === period.key ? "active" : ""}" data-candle-period="${escapeHtml(period.key)}" type="button">
            ${escapeHtml(state.language === "zh" ? period.zh : period.en)}
          </button>`).join("")}
      </div>
      <div class="candle-chart-wrap">
        <canvas id="candleChart" class="candle-chart" aria-label="${escapeHtml(t("drawer.chart"))}"></canvas>
        <div id="candleStatus" class="candle-status">${escapeHtml(t("chart.loading"))}</div>
      </div>
    </section>
    <section class="drawer-section drawer-actions">
      ${row.source_url ? `<a class="terminal-button" href="${escapeHtml(row.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(t("drawer.source"))}</a>` : `<span class="muted">${escapeHtml(t("drawer.noSource"))}</span>`}
      <span class="muted">${escapeHtml(formatDateTime(row.market_updated_at))}</span>
    </section>`;
  els.tickerDrawer.classList.remove("hidden");
  els.tickerDrawer.setAttribute("aria-hidden", "false");
  loadCandles(row.ticker, state.candlePeriod);
}

function metricBlock(label, value) {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function closeDrawer() {
  state.drawerTicker = "";
  state.candleRequestId += 1;
  els.tickerDrawer.classList.add("hidden");
  els.tickerDrawer.setAttribute("aria-hidden", "true");
}

async function loadUser() {
  try {
    const user = await api("/api/me");
    state.user = user;
    els.logoutBtn.classList.remove("hidden");
    if (user.is_admin) els.adminLink.classList.remove("hidden");
  } catch {
    state.user = null;
  }
}

async function loadDashboard() {
  try {
    state.dashboard = await api("/api/dashboard");
    state.dashboardError = "";
  } catch (error) {
    state.dashboard = null;
    state.dashboardError =
      "Dashboard API failed. Confirm the backend is running at http://127.0.0.1:8000 and open that URL instead of static/index.html.";
  }
}

async function loadFeed() {
  try {
    state.feed = await api(`/api/feed?limit=40&lang=${encodeURIComponent(state.language)}`);
    renderFeed();
  } catch {
    els.feedBox.innerHTML = `<p class="empty">${escapeHtml(t("alerts.failed"))}</p>`;
  }
}

function bindEvents() {
  els.languageToggle.addEventListener("click", async () => {
    state.language = state.language === "zh" ? "en" : "zh";
    localStorage.setItem(LANGUAGE_KEY, state.language);
    await loadFeed();
    renderAll();
  });

  els.logoutBtn.addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    window.location.reload();
  });

  els.dashboardSearch.value = state.search;
  els.dashboardSearch.addEventListener("input", () => {
    state.search = els.dashboardSearch.value;
    localStorage.setItem(SEARCH_KEY, state.search);
    renderTable();
  });

  els.rowQualityFilter.value = state.quality;
  els.rowQualityFilter.addEventListener("change", () => {
    state.quality = els.rowQualityFilter.value;
    localStorage.setItem(QUALITY_KEY, state.quality);
    renderTable();
  });

  els.clearFiltersBtn.addEventListener("click", () => {
    state.category = "all";
    state.search = "";
    state.quality = "all";
    els.dashboardSearch.value = "";
    els.rowQualityFilter.value = "all";
    localStorage.setItem(CATEGORY_KEY, state.category);
    localStorage.setItem(SEARCH_KEY, state.search);
    localStorage.setItem(QUALITY_KEY, state.quality);
    renderAll();
  });

  els.categoryTabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    state.category = button.dataset.category;
    localStorage.setItem(CATEGORY_KEY, state.category);
    renderIntelPanel();
    renderCategories();
    renderTable();
  });

  document.addEventListener("click", (event) => {
    const sortButton = event.target.closest(".table-sort[data-sort]");
    if (sortButton) {
      const field = sortButton.dataset.sort;
      if (state.sortField === field) {
        state.sortDirection = state.sortDirection === "desc" ? "asc" : "desc";
      } else {
        state.sortField = field;
        state.sortDirection = field === "ticker" || field === "category_label" ? "asc" : "desc";
      }
      localStorage.setItem(SORT_FIELD_KEY, state.sortField);
      localStorage.setItem(SORT_DIRECTION_KEY, state.sortDirection);
      renderTable();
      return;
    }

    const intelCategory = event.target.closest("[data-intel-category]");
    if (intelCategory) {
      state.category = intelCategory.dataset.intelCategory;
      localStorage.setItem(CATEGORY_KEY, state.category);
      renderIntelPanel();
      renderCategories();
      renderTable();
      return;
    }

    const intelTicker = event.target.closest("[data-intel-ticker]");
    if (intelTicker) {
      const row = (state.dashboard?.rows || []).find((item) => item.ticker === intelTicker.dataset.intelTicker);
      if (row) openDrawer(row);
      return;
    }

    const rowEl = event.target.closest(".terminal-data-row[data-ticker]");
    if (rowEl) {
      const row = (state.dashboard?.rows || []).find((item) => item.ticker === rowEl.dataset.ticker);
      if (row) openDrawer(row);
      return;
    }

    const candleButton = event.target.closest("[data-candle-period]");
    if (candleButton && state.drawerTicker) {
      loadCandles(state.drawerTicker, candleButton.dataset.candlePeriod);
      return;
    }

    const feedFilter = event.target.closest("[data-feed-filter]");
    if (feedFilter) {
      state.feedFilter = feedFilter.dataset.feedFilter;
      localStorage.setItem(FEED_FILTER_KEY, state.feedFilter);
      renderFeed();
      return;
    }

    const readButton = event.target.closest("[data-feed-read]");
    if (readButton) {
      state.readAlerts.add(readButton.dataset.feedRead);
      writeSet(READ_ALERTS_KEY, state.readAlerts);
      renderFeed();
      return;
    }

    const saveButton = event.target.closest("[data-feed-save]");
    if (saveButton) {
      const id = saveButton.dataset.feedSave;
      if (state.savedAlerts.has(id)) state.savedAlerts.delete(id);
      else state.savedAlerts.add(id);
      writeSet(SAVED_ALERTS_KEY, state.savedAlerts);
      renderFeed();
      return;
    }

    const feedTicker = event.target.closest("[data-feed-ticker]");
    if (feedTicker) {
      state.search = feedTicker.dataset.feedTicker;
      els.dashboardSearch.value = state.search;
      localStorage.setItem(SEARCH_KEY, state.search);
      renderTable();
    }
  });

  els.dashboardRows.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const rowEl = event.target.closest(".terminal-data-row[data-ticker]");
    if (!rowEl) return;
    const row = (state.dashboard?.rows || []).find((item) => item.ticker === rowEl.dataset.ticker);
    if (row) openDrawer(row);
  });

  els.drawerClose.addEventListener("click", closeDrawer);
  els.tickerDrawer.addEventListener("click", (event) => {
    if (event.target.matches("[data-drawer-close]")) closeDrawer();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });
}

function visitorId() {
  let value = localStorage.getItem(VISITOR_KEY);
  if (!value) {
    value = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    localStorage.setItem(VISITOR_KEY, value);
  }
  return value;
}

function sendAnalytics(eventType, durationSeconds = 0) {
  const payload = {
    visitor_id: visitorId(),
    event_type: eventType,
    path: window.location.pathname,
    duration_seconds: Math.round(durationSeconds),
    language: state.language,
    viewport: `${window.innerWidth}x${window.innerHeight}`
  };
  navigator.sendBeacon?.("/api/analytics/event", new Blob([JSON.stringify(payload)], { type: "application/json" }));
}

async function init() {
  applyCopy();
  bindEvents();
  sendAnalytics("pageview");
  loadUser();
  loadFeed();
  await loadDashboard();
  renderAll();
  const startedAt = Date.now();
  window.addEventListener("beforeunload", () => {
    sendAnalytics("heartbeat", (Date.now() - startedAt) / 1000);
  });
}

init();
