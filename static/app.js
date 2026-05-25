const authView = document.querySelector("#authView");
const memberView = document.querySelector("#memberView");
const loginForm = document.querySelector("#loginForm");
const loginMessage = document.querySelector("#loginMessage");
const accountEmail = document.querySelector("#accountEmail");
const subscriptionState = document.querySelector("#subscriptionState");
const pushStatus = document.querySelector("#pushStatus");
const enablePushBtn = document.querySelector("#enablePushBtn");
const testPushBtn = document.querySelector("#testPushBtn");
const paymentBox = document.querySelector("#paymentBox");
const listBox = document.querySelector("#listBox");
const feedBox = document.querySelector("#feedBox");
const logoutBtn = document.querySelector("#logoutBtn");
const adminLink = document.querySelector("#adminLink");
const planBadge = document.querySelector("#planBadge");
const languageToggle = document.querySelector("#languageToggle");
const dashboardMetrics = document.querySelector("#dashboardMetrics");
const categoryTabs = document.querySelector("#categoryTabs");
const dashboardRows = document.querySelector("#dashboardRows");
const sourceStatus = document.querySelector("#sourceStatus");
const dataStatus = document.querySelector("#dataStatus");
const lastUpdated = document.querySelector("#lastUpdated");
const refreshLabel = document.querySelector("#refreshLabel");
const dashboardSearch = document.querySelector("#dashboardSearch");
const tableStatus = document.querySelector("#tableStatus");
const tickerDrawer = document.querySelector("#tickerDrawer");
const drawerClose = document.querySelector("#drawerClose");
const drawerBody = document.querySelector("#drawerBody");

const LANGUAGE_KEY = "usmonitor.language";
const CATEGORY_KEY = "usmonitor.dashboard.category";
const SEARCH_KEY = "usmonitor.dashboard.search";
const SORT_FIELD_KEY = "usmonitor.dashboard.sortField";
const SORT_DIRECTION_KEY = "usmonitor.dashboard.sortDirection";
const VISITOR_KEY = "usmonitor.visitorId";
const DEFAULT_LANGUAGE = "zh";
const DEFAULT_SORT_FIELD = "dollar_volume";
const DEFAULT_SORT_DIRECTION = "desc";

const COPY = {
  zh: {
    "app.title": "US Monitor",
    "nav.dashboard": "看板",
    "nav.alerts": "情报",
    "nav.account": "账户",
    "nav.logout": "退出",
    "plan.loading": "检查权限",
    "plan.vip": "VIP 版本",
    "plan.free": "普通版本",
    "plan.vipTitle": "当前账户已开通 VIP 权限",
    "plan.freeTitle": "当前为普通版本",
    "hero.eyebrow": "AI 基础设施",
    "hero.title": "美股 AI 产业链终端",
    "hero.lede":
      "按算力、半导体、光互连、电力和软件分层跟踪核心标的，聚焦价格、流动性和产业链瓶颈。",
    "dashboard.refreshTarget": "{seconds}s 刷新目标",
    "dashboard.updated": "更新于 {date}",
    "dashboard.unavailable": "看板暂不可用",
    "dashboard.rowsShown": "显示 {shown}/{total} 个标的，排序：{sort}",
    "dashboard.noRows": "没有匹配的标的。",
    "metrics.tracked": "已跟踪",
    "metrics.market": "行情状态",
    "metrics.priced": "有行情",
    "metrics.fundamentals": "基本面",
    "metrics.core": "核心瓶颈",
    "metrics.attention": "高关注",
    "search.label": "搜索",
    "search.placeholder": "Ticker、公司、AI 角色",
    "tabs.all": "全部",
    "table.ticker": "代码",
    "table.price": "价格",
    "table.change": "% 涨跌",
    "table.marketCap": "市值",
    "table.dollarVolume": "交易额",
    "table.pe": "PE",
    "table.aiRole": "AI 角色",
    "table.latestSignal": "最新观察",
    "table.pending": "待接入",
    "sort.ticker": "代码",
    "sort.price": "价格",
    "sort.change_percent": "% 涨跌",
    "sort.market_cap": "市值",
    "sort.dollar_volume": "交易额",
    "sort.pe_ratio": "PE",
    "drawer.market": "行情",
    "drawer.aiRole": "AI 角色",
    "drawer.latestSignal": "最新观察",
    "drawer.positioning": "产业链定位",
    "drawer.updated": "行情更新",
    "drawer.source": "来源",
    "rail.sourceEyebrow": "数据源状态",
    "rail.sourceTitle": "数据状态",
    "rail.alertsEyebrow": "提醒",
    "rail.alertsTitle": "最新情报",
    "alerts.signedOut": "登录后查看完整 alert feed。",
    "alerts.empty": "暂无提醒。",
    "alerts.viewSource": "查看原帖",
    "auth.eyebrow": "邮箱注册",
    "auth.title": "邮箱注册 / 登录",
    "auth.email": "邮箱",
    "auth.submit": "发送登录链接",
    "auth.sending": "发送中...",
    "auth.devLink": "开发模式链接：",
    "auth.openLogin": "打开登录",
    "auth.sent": "登录链接已发送。",
    "auth.failed": "登录失败，请检查邮箱。",
    "account.eyebrow": "账户",
    "account.active": "已开通",
    "account.admin": "管理员权限已开通",
    "account.noExpiry": "无固定到期日",
    "account.pending": "普通版本",
    "account.waiting": "高级服务未开通",
    "push.eyebrow": "推送",
    "push.title": "iPhone PWA 推送",
    "push.enable": "开启推送",
    "push.test": "测试推送",
    "push.unsupported": "当前浏览器不支持 Web Push。",
    "push.installed": "已在主屏幕模式运行，可以授权通知。",
    "push.installFirst": "iPhone 需要先添加到主屏幕，再授权通知。",
    "push.noVapid": "VAPID 公钥未配置。",
    "push.denied": "通知权限未开启。",
    "push.enabled": "推送已开启。",
    "push.testing": "发送测试中...",
    "push.testDone": "测试完成，{sent} 成功，{failed} 失败。",
    "payment.eyebrow": "付款",
    "payment.title": "升级会员：99 USDT / 月",
    "payment.adminBypass": "管理员访问已开通，无需付款。",
    "payment.memberActive": "会员服务已开通，到期前无需再次付款。",
    "payment.amount": "金额",
    "payment.month": "月",
    "payment.noteCode": "备注码",
    "payment.missing": "未配置",
    "lists.eyebrow": "列表",
    "lists.title": "订阅列表",
    "lists.active": "已开通",
    "lists.locked": "高级会员",
    "terms.eyebrow": "定位",
    "terms.title": "情报摘要，不是交易建议",
    "terms.body":
      "邮箱可直接注册免费版。高级 alert 和推送权限需付款，或由后台手动开通会员。"
  },
  en: {
    "app.title": "US Monitor",
    "nav.dashboard": "Dashboard",
    "nav.alerts": "Alerts",
    "nav.account": "Account",
    "nav.logout": "Sign out",
    "plan.loading": "Checking access",
    "plan.vip": "VIP version",
    "plan.free": "Free version",
    "plan.vipTitle": "This account has VIP access.",
    "plan.freeTitle": "This account is on the free version.",
    "hero.eyebrow": "AI Infrastructure",
    "hero.title": "US AI Supply Chain Terminal",
    "hero.lede":
      "A compact AI supply-chain terminal grouped by compute, semiconductors, optical links, power, and software.",
    "dashboard.refreshTarget": "{seconds}s refresh target",
    "dashboard.updated": "Updated {date}",
    "dashboard.unavailable": "Dashboard unavailable",
    "dashboard.rowsShown": "Showing {shown}/{total} tickers, sorted by {sort}",
    "dashboard.noRows": "No matching tickers.",
    "metrics.tracked": "Tracked",
    "metrics.market": "Market",
    "metrics.priced": "Priced",
    "metrics.fundamentals": "Fundamentals",
    "metrics.core": "Core Chokepoints",
    "metrics.attention": "High Attention",
    "search.label": "Search",
    "search.placeholder": "Ticker, company, AI role",
    "tabs.all": "All",
    "table.ticker": "Ticker",
    "table.price": "Price",
    "table.change": "% Chg",
    "table.marketCap": "Mkt Cap",
    "table.dollarVolume": "Dollar Vol",
    "table.pe": "PE",
    "table.aiRole": "AI Role",
    "table.latestSignal": "Latest Signal",
    "table.pending": "Pending",
    "sort.ticker": "Ticker",
    "sort.price": "Price",
    "sort.change_percent": "% Chg",
    "sort.market_cap": "Market Cap",
    "sort.dollar_volume": "Dollar Vol",
    "sort.pe_ratio": "PE",
    "drawer.market": "Market",
    "drawer.aiRole": "AI Role",
    "drawer.latestSignal": "Latest Signal",
    "drawer.positioning": "Supply-chain position",
    "drawer.updated": "Market updated",
    "drawer.source": "Source",
    "rail.sourceEyebrow": "Source Status",
    "rail.sourceTitle": "Data Status",
    "rail.alertsEyebrow": "Alerts",
    "rail.alertsTitle": "Latest Intelligence",
    "alerts.signedOut": "Sign in to view the full alert feed.",
    "alerts.empty": "No alerts yet.",
    "alerts.viewSource": "View source post",
    "auth.eyebrow": "Email Access",
    "auth.title": "Sign up or sign in with email",
    "auth.email": "Email",
    "auth.submit": "Send login link",
    "auth.sending": "Sending...",
    "auth.devLink": "Development link: ",
    "auth.openLogin": "Open login",
    "auth.sent": "Login link sent.",
    "auth.failed": "Login failed. Check your email.",
    "account.eyebrow": "Account",
    "account.active": "Active",
    "account.admin": "Admin access active",
    "account.noExpiry": "No fixed expiry",
    "account.pending": "Free version",
    "account.waiting": "Premium not active",
    "push.eyebrow": "Push",
    "push.title": "iPhone PWA Push",
    "push.enable": "Enable push",
    "push.test": "Test push",
    "push.unsupported": "This browser does not support Web Push.",
    "push.installed": "Running from the home screen. Notification permission can be granted.",
    "push.installFirst": "On iPhone, add the app to the home screen before enabling notifications.",
    "push.noVapid": "VAPID public key is not configured.",
    "push.denied": "Notification permission was not granted.",
    "push.enabled": "Push is enabled.",
    "push.testing": "Sending test...",
    "push.testDone": "Test complete: {sent} sent, {failed} failed.",
    "payment.eyebrow": "Payment",
    "payment.title": "Upgrade: 99 USDT / month",
    "payment.adminBypass": "Admin access is active. No payment required.",
    "payment.memberActive": "Premium is active. No payment is required before expiry.",
    "payment.amount": "Amount",
    "payment.month": "month",
    "payment.noteCode": "Note code",
    "payment.missing": "Not configured",
    "lists.eyebrow": "Lists",
    "lists.title": "Subscribed Lists",
    "lists.active": "Active",
    "lists.locked": "Premium",
    "terms.eyebrow": "Positioning",
    "terms.title": "Intelligence summaries, not trading advice",
    "terms.body":
      "Anyone can sign up for a free account with email. Premium alerts and push access require payment or manual admin activation."
  }
};

const CATEGORY_ZH = {
  "Cloud CAPEX": "云 CAPEX",
  "Compute & Network": "算力与网络",
  "Foundry & Test": "晶圆代工与测试",
  "Memory & Storage": "内存与存储",
  "Packaging & Substrate": "先进封装与载板",
  "Optical & Photonics": "光互连与光子",
  "Power & Cooling": "电力与冷却",
  "Software & Data": "软件与数据",
  "Serenity Adds": "Serenity 动态加入"
};

const VALUE_ZH = {
  "Demand-side anchors that drive the full AI factory order book.":
    "驱动整条 AI 工厂订单链的需求端锚点。",
  "GPU, ASIC, Ethernet, SerDes, and rack-scale connectivity.":
    "GPU、ASIC、以太网、SerDes 与机架级连接。",
  "Advanced nodes, EUV, process control, and AI chip test bottlenecks.":
    "先进制程、EUV、过程控制与 AI 芯片测试瓶颈。",
  "HBM, server DRAM, eSSD, NAND controllers, and memory-cycle leverage.":
    "HBM、服务器 DRAM、eSSD、NAND 控制器和内存周期弹性。",
  "CoWoS, ABF, IC substrate, advanced PCB, and packaging materials.":
    "CoWoS、ABF、IC 载板、高阶 PCB 与封装材料。",
  "800G/1.6T optics, lasers, InP, SOI, GaAs, CPO/LRO, and optical modules.":
    "800G/1.6T 光模块、激光器、InP、SOI、GaAs、CPO/LRO 与光模块。",
  "Switchgear, UPS, liquid cooling, thermal systems, and onsite power.":
    "开关设备、UPS、液冷、热管理系统与现场电力。",
  "High-attention AI application and data-platform names for comparison.":
    "用于对照的高关注 AI 应用与数据平台标的。",
  "Tickers added from positive Serenity X-source analysis.":
    "来自 Serenity X 来源正面分析后动态加入的标的。",
  "Market data provider pending": "行情数据源待接入",
  "Market data live": "行情数据已接入",
  "Market data provider error": "行情数据源错误",
  "Information dashboard only. Not investment advice.": "仅作信息看板，不构成投资建议。",
  "Demand anchor": "需求锚点",
  "Industry reference": "产业参考",
  "Core chokepoint": "核心瓶颈",
  "High elasticity": "高弹性",
  "Validation": "验证中",
  "Proxy": "代理标的",
  "High attention": "高关注",
  "High liquidity": "高流动性",
  "Medium liquidity": "中等流动性",
  "Global focus": "全球关注",
  "Niche/global": "小众/全球",
  "Serenity positive": "Serenity 正面提及",
  "Source driven": "来源驱动",
  "Positive source mention": "来源正面提及",
  "Added from a constructive Serenity X-source post": "来自 Serenity X 来源的建设性正面帖子",
  "live": "已上线",
  "pending": "待接入",
  "error": "错误",
  "Serenity Alert": "Serenity Alert",
  "X original-post monitor is deployed.": "X 原创帖监控已上线。",
  "AI chokepoint map": "AI 瓶颈地图",
  "Dashboard taxonomy is seeded from the AI supply-chain report.":
    "看板分类已基于 AI 产业链报告初始化。",
  "Market data": "行情数据",
  "Provider adapter is not connected yet.": "行情源适配器尚未接入。",
  Fundamentals: "基本面数据",
  "Daily cache will be enabled with the market data provider.":
    "接入行情源后会启用每日基本面缓存。",
  "Curated AI supply-chain and market intelligence from selected X sources.":
    "来自精选 X 来源的 AI 产业链和市场情报。"
};

const ROW_ZH = {
  MSFT: ["云 CAPEX", "Azure AI 需求锚点", "关注 AI 收入运行率、Azure 增速和资本开支纪律"],
  GOOGL: ["云/TPU", "TPU、Google Cloud 与内部模型基础设施", "关注云 backlog、TPU 规模和 CAPEX 轨迹"],
  AMZN: ["云/ASIC", "AWS、Trainium 与超大规模基础设施需求", "关注 AWS 增速、Trainium 承诺和数据中心资本开支"],
  META: ["AI 工厂", "大型 AI 基础设施支出方", "关注 2026 CAPEX 指引和商业化压力"],
  ORCL: ["GPU 云", "AI 云容量和 GPU 基础设施供应商", "关注 AI 云 backlog 和客户集中度"],
  NBIS: ["AI 云", "高 beta AI 云容量供应商", "关注超大客户合约和 GPU 利用率"],
  NVDA: ["GPU/网络", "AI 机架级平台参考资产", "关注数据中心网络增速相对计算业务的变化"],
  AMD: ["GPU/CPU", "替代加速器和服务器 CPU 供应商", "关注 MI 系列采用率和超大客户绑定"],
  AVGO: ["定制 ASIC/网络", "超大客户定制芯片的核心受益者", "关注 AI 收入、XPU 项目和网络业务占比"],
  MRVL: ["定制芯片/光互连", "连接定制芯片、DSP 与电光互连的桥梁", "关注定制芯片 backlog 和 1.6T DSP 放量"],
  ANET: ["AI 以太网", "云端 AI spine/leaf 交换机供应商", "关注 800G/1.6T 交换周期和云客户集中度"],
  ALAB: ["PCIe/CXL", "AI 服务器 retimer 和机架连接受益标的", "关注连接器件 attach rate 和估值风险"],
  CRDO: ["AEC/SerDes", "高速连接和主动电缆受益标的", "关注 800G/1.6T AEC 渗透率和客户集中度"],
  SMCI: ["AI 服务器", "机架级 AI 服务器集成代理标的", "关注毛利率、出货节奏和客户质量"],
  DELL: ["AI 服务器", "企业 AI 服务器渠道", "关注 AI 服务器 backlog 和利润率转化"],
  TSM: ["晶圆代工/CoWoS", "AI 加速器和先进封装的系统性瓶颈", "关注 N2/A16、CoWoS 扩产和 HPC 晶圆需求"],
  ASML: ["EUV", "先进逻辑和 DRAM EUV 的上游瓶颈", "关注 High-NA/EUV 需求和出口管制影响"],
  AMAT: ["设备", "沉积、刻蚀和先进封装设备敞口", "关注 GAA 和先进封装资本开支"],
  LRCX: ["设备", "面向内存和先进制程的刻蚀/沉积设备敞口", "关注内存资本开支复苏和 AI DRAM 强度"],
  KLAC: ["检测/量测", "先进制程和先进封装的良率控制受益者", "关注工艺复杂度上升带来的检测强度"],
  "6857.T": ["AI 芯片测试", "SoC、HBM 和 AI 加速器测试瓶颈", "关注 AI 测试时间、HBM 复杂度和订单动能"],
  "BESI.AS": ["混合键合", "高 beta 混合键合设备敞口", "关注 HBM4、SoIC 和 3D 堆叠订单转化"],
  MU: ["HBM/DRAM/eSSD", "美股核心 HBM 和 AI 内存敞口", "关注 HBM4 放量、毛利率和供给纪律"],
  "000660.KS": ["HBM", "财务验证较强的领先 HBM 供应商", "关注 HBM4 合约、ASP 和长期供货协议"],
  "005930.KS": ["HBM/DRAM/晶圆代工", "HBM 追赶者和内存周期参考资产", "关注 HBM4 认证和晶圆代工客户进展"],
  SNDK: ["NAND/eSSD", "AI 存储和 NAND 周期弹性", "关注 eSSD 需求和 NAND 定价纪律"],
  SIMO: ["NAND 控制器", "SSD 和嵌入式存储需求的控制器敞口", "关注 AI 存储周期和控制器 ASP"],
  EWY: ["韩国内存篮子", "SK hynix 和 Samsung 敞口的流动性代理", "关注韩国内存周期和 HBM 份额变化"],
  "4062.T": ["ABF 载板", "AI GPU/ASIC 高端封装载板敞口", "关注 ABF 产能、客户结构和 ASP 周期"],
  "3037.TW": ["ABF/PCB", "AI 服务器 PCB 和高层数载板敞口", "关注良率、定价和台湾 AI 链需求"],
  "2802.T": ["ABF 薄膜", "高端载板中的隐性材料瓶颈", "关注 ABF 规格升级和材料组合贡献"],
  "ATS.VI": ["IC 载板", "高 beta 载板和先进 PCB 供应商", "关注杠杆、折旧压力和 AI/HPC 订单质量"],
  AEHR: ["晶圆级测试", "SiC、GaN 和光子方向的小盘测试敞口", "关注真实 AI 相关订单与叙事动能的差异"],
  COHR: ["激光器/收发器", "机构型光互连产业链资产", "关注 AI 光学协议、800G/1.6T 和利润率修复"],
  LITE: ["激光器/光学组件", "AI 数据通信中的激光器和光组件敞口", "关注 datacom 复苏和客户集中度"],
  FN: ["光模块制造", "光模块制造产能代理标的", "关注 800G/1.6T 客户放量和利润率上限"],
  GLW: ["光纤/先进光学", "大盘光学材料参考资产", "关注数据中心光纤需求和 AI 光学合作"],
  AAOI: ["光模块", "高关注 AI 光模块 beta", "关注 800G/1.6T 出货和客户集中度"],
  AXTI: ["InP/GaAs 衬底", "Serenity 风格底层光子材料敞口", "关注 InP 需求、出口管制和客户验证"],
  "SIVE.ST": ["DFB 激光器/CPO", "小盘 LRO/CPO 光源敞口", "关注 Jabil 1.6T LRO 进展和融资风险"],
  "SOI.PA": ["SOI 衬底", "硅光和 SOI 材料敞口", "关注 CPO 采用率和 RF-SOI 复苏"],
  "IQE.L": ["外延", "化合物半导体外延敞口", "关注光子需求、盈利能力和融资风险"],
  TSEM: ["特色晶圆代工", "模拟和硅光晶圆代工敞口", "关注 AI 纯度和特色代工需求"],
  VRT: ["电力/热管理", "AI 数据中心电力和冷却的直接瓶颈", "关注 backlog、液冷和交付执行"],
  ETN: ["电气设备", "开关设备、变压器和配电敞口", "关注数据中心电气 backlog 和产能释放"],
  "SU.PA": ["电力管理", "欧洲核心数据中心电气化资产", "关注 AI 数据中心需求和欧洲周期敞口"],
  NVT: ["电气箱体", "电气保护和箱体内容量敞口", "关注每机架内容量和工业周期风险"],
  MOD: ["热管理", "液冷和散热高 beta 敞口", "关注 CDU、冷板和数据中心冷却订单"],
  BE: ["现场电力", "数据中心燃料电池和现场电力可选项", "关注已签电力合约和融资质量"],
  CEG: ["清洁电力", "面向数据中心需求的大型电力供应商", "关注核电/数据中心电力合约"],
  GEV: ["电网/电力", "电网设备和电气化 backlog 代理", "关注电网设备需求和利润率执行"],
  PWR: ["电网建设", "输电和电力基础设施施工代理", "关注公用事业和数据中心电网 backlog"],
  XLU: ["公用事业篮子", "AI 电力主题的流动性 ETF 代理", "关注电力需求叙事与公用事业利率周期风险"],
  PLTR: ["AI 平台", "企业 AI 工作流和政府 AI 敞口", "关注 AIP 采用、估值和经营杠杆"],
  SNOW: ["数据云", "服务 AI 工作负载的企业数据平台", "关注 consumption 增长和 AI 产品商业化"],
  DDOG: ["可观测性", "云和 AI 工作负载可观测性敞口", "关注 AI 工作负载增长和净留存"],
  CRWD: ["安全", "AI 时代端点和云安全平台", "关注平台整合和 AI 安全需求"],
  RDDT: ["数据/注意力", "高关注数据授权和社交平台资产", "关注数据授权收入和广告变现"],
  FIG: ["设计软件", "产品设计协作和 AI 工作流敞口", "关注企业采用和 AI 设计工具竞争"]
};

const COMPANY_ZH = {
  MSFT: "微软",
  GOOGL: "谷歌母公司",
  AMZN: "亚马逊",
  META: "Meta平台公司",
  ORCL: "甲骨文",
  NBIS: "内比乌斯集团",
  NVDA: "英伟达",
  AMD: "超威半导体",
  AVGO: "博通",
  MRVL: "迈威尔科技",
  ANET: "阿里斯塔网络",
  ALAB: "阿斯特拉实验室",
  CRDO: "科瑞多科技",
  SMCI: "超微电脑",
  DELL: "戴尔科技",
  TSM: "台积电",
  ASML: "阿斯麦",
  AMAT: "应用材料",
  LRCX: "泛林集团",
  KLAC: "科磊",
  "6857.T": "爱德万测试",
  "BESI.AS": "贝思半导体",
  MU: "美光科技",
  "000660.KS": "SK海力士",
  "005930.KS": "三星电子",
  SNDK: "闪迪",
  SIMO: "慧荣科技",
  EWY: "韩国股票ETF",
  "4062.T": "揖斐电",
  "3037.TW": "欣兴电子",
  "2802.T": "味之素",
  "ATS.VI": "奥特斯",
  AEHR: "艾尔测试系统",
  COHR: "相干公司",
  LITE: "朗美通",
  FN: "法布里内特",
  GLW: "康宁",
  AAOI: "应用光电",
  AXTI: "AXT材料",
  "SIVE.ST": "西弗斯半导体",
  "SOI.PA": "索泰克",
  "IQE.L": "IQE外延",
  TSEM: "高塔半导体",
  VRT: "维谛技术",
  ETN: "伊顿",
  "SU.PA": "施耐德电气",
  NVT: "恩伟特",
  MOD: "摩丁制造",
  BE: "布鲁姆能源",
  CEG: "星座能源",
  GEV: "GE能源科技",
  PWR: "昆塔服务",
  XLU: "公用事业精选行业基金",
  PLTR: "帕兰提尔",
  SNOW: "雪花",
  DDOG: "数据狗",
  CRWD: "众击安全",
  RDDT: "红迪",
  FIG: "菲格玛"
};

let appConfig = {};
let dashboardSnapshot = null;
let selectedCategory = localStorage.getItem(CATEGORY_KEY) || "all";
let searchQuery = localStorage.getItem(SEARCH_KEY) || "";
let sortField = localStorage.getItem(SORT_FIELD_KEY) || DEFAULT_SORT_FIELD;
let sortDirection = localStorage.getItem(SORT_DIRECTION_KEY) || DEFAULT_SORT_DIRECTION;
let activeDrawerTicker = null;
let authChecked = false;
let currentUser = null;
let currentLanguage = normalizeLanguage(localStorage.getItem(LANGUAGE_KEY));
let lastEngagementAt = Date.now();

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "include",
    ...options
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) return null;
  return response.json();
}

function getVisitorId() {
  let visitorId = localStorage.getItem(VISITOR_KEY);
  if (!visitorId) {
    visitorId =
      window.crypto?.randomUUID?.() ||
      `v-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(VISITOR_KEY, visitorId);
  }
  return visitorId;
}

function analyticsPayload(eventType, durationSeconds = 0) {
  return {
    visitor_id: getVisitorId(),
    event_type: eventType,
    path: `${location.pathname}${location.hash || ""}`,
    duration_seconds: Math.max(0, Math.round(durationSeconds)),
    language: currentLanguage,
    viewport: `${window.innerWidth}x${window.innerHeight}`
  };
}

function sendAnalytics(eventType, durationSeconds = 0, useBeacon = false) {
  const payload = analyticsPayload(eventType, durationSeconds);
  if (useBeacon && navigator.sendBeacon) {
    const blob = new Blob([JSON.stringify(payload)], {
      type: "application/json"
    });
    navigator.sendBeacon("/api/analytics/event", blob);
    return;
  }
  fetch("/api/analytics/event", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    keepalive: useBeacon,
    body: JSON.stringify(payload)
  }).catch(() => {});
}

function flushEngagement(useBeacon = false) {
  const now = Date.now();
  const seconds = (now - lastEngagementAt) / 1000;
  lastEngagementAt = now;
  if (seconds >= 2) {
    sendAnalytics("heartbeat", seconds, useBeacon);
  }
}

function startAnalytics() {
  sendAnalytics("pageview");
  window.setInterval(() => {
    if (document.visibilityState === "visible") {
      flushEngagement();
    }
  }, 30_000);
  window.addEventListener("hashchange", () => sendAnalytics("pageview"));
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      flushEngagement(true);
    } else {
      lastEngagementAt = Date.now();
    }
  });
  window.addEventListener("pagehide", () => flushEngagement(true));
}

function normalizeLanguage(value) {
  return value === "en" ? "en" : DEFAULT_LANGUAGE;
}

function t(key, vars = {}) {
  const template = COPY[currentLanguage][key] || COPY.en[key] || key;
  return Object.entries(vars).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, value),
    template
  );
}

function localizeValue(value) {
  if (currentLanguage !== "zh") return value;
  return CATEGORY_ZH[value] || VALUE_ZH[value] || value;
}

function localizeRow(row, field) {
  if (currentLanguage !== "zh") return row[field];
  const fields = ["ai_layer", "role", "latest_signal"];
  const rowCopy = ROW_ZH[row.ticker];
  const index = fields.indexOf(field);
  if (rowCopy && index !== -1) return rowCopy[index];
  return localizeValue(row[field]);
}

function localizeCompany(row) {
  if (currentLanguage !== "zh") return row.company;
  return COMPANY_ZH[row.ticker] || row.company;
}

function localizeSourceDetail(source) {
  if (source.name === "Market data") {
    if (source.status === "live") {
      if (currentLanguage !== "zh") return source.detail;
      const provider = source.provider || "";
      const quoteFallback = provider.includes("Yahoo Chart")
        ? "；非美股行情使用 Yahoo Chart fallback"
        : "";
      const fundamentalsFallback = provider.includes("Yahoo Quote")
        ? "；PE/市值使用 Yahoo Quote 低频缓存"
        : "";
      const staticFallback = provider.includes("Static Fundamentals")
        ? "；部分 PE/市值使用静态低频兜底"
        : "";
      return `Massive snapshot 已连接，行情 ${source.loaded_tickers}/${source.eligible_tickers}，基本面 ${source.fundamentals_loaded}/${source.loaded_tickers}${quoteFallback}${fundamentalsFallback}${staticFallback}。`;
    }
    if (source.status === "error") {
      return currentLanguage === "zh"
        ? "Massive snapshot 连接异常，暂未返回可用行情。"
        : source.detail;
    }
  }
  if (source.name === "Fundamentals" && currentLanguage === "zh") {
    if (source.status === "live") {
      const count = source.detail.match(/for (\d+) tickers/)?.[1] || "";
      return count
        ? `PE/市值低频缓存已补全 ${count} 个标的。`
        : "PE/市值低频缓存已接入。";
    }
    return "PE/市值低频缓存等待数据源返回。";
  }
  if (currentLanguage !== "zh") return source.detail;
  if (source.name === "Market data" && source.provider?.includes("Massive")) {
    if (source.status === "live") {
      const fallback = source.provider?.includes("Yahoo")
        ? "；非美股使用 Yahoo Chart 免费 fallback"
        : "";
      return `Massive snapshot 已连接，行情 ${source.loaded_tickers}/${source.eligible_tickers}，基本面 ${source.fundamentals_loaded}/${source.loaded_tickers}${fallback}。`;
    }
    if (source.status === "error") {
      return "Massive snapshot 连接异常，暂未返回可用行情。";
    }
  }
  return localizeValue(source.detail);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function applyStaticCopy() {
  document.documentElement.lang = currentLanguage === "zh" ? "zh-Hans" : "en";
  document.title = t("app.title");
  languageToggle.textContent = currentLanguage === "zh" ? "EN" : "中文";
  languageToggle.setAttribute(
    "aria-label",
    currentLanguage === "zh" ? "Switch to English" : "切换到中文"
  );
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  updatePlanBadge(currentUser);
}

function updatePlanBadge(me) {
  if (!planBadge) return;
  if (!authChecked && !me) {
    planBadge.textContent = t("plan.loading");
    planBadge.dataset.planStatus = "loading";
    planBadge.setAttribute("title", t("plan.loading"));
    return;
  }
  const isVip = Boolean(me?.subscription?.active);
  planBadge.textContent = isVip ? t("plan.vip") : t("plan.free");
  planBadge.dataset.planStatus = isVip ? "vip" : "free";
  planBadge.setAttribute("title", isVip ? t("plan.vipTitle") : t("plan.freeTitle"));
}

function showSignedOut() {
  currentUser = null;
  authChecked = true;
  authView.classList.remove("hidden");
  memberView.classList.add("hidden");
  logoutBtn.classList.add("hidden");
  adminLink.classList.add("hidden");
  updatePlanBadge(null);
}

function showSignedIn(me) {
  currentUser = me;
  authChecked = true;
  authView.classList.add("hidden");
  memberView.classList.remove("hidden");
  logoutBtn.classList.remove("hidden");
  adminLink.classList.toggle("hidden", !me.is_admin);
  updatePlanBadge(me);
}

function moneyAddress(value) {
  return value
    ? `<code>${escapeHtml(value)}</code>`
    : `<span class="muted">${escapeHtml(t("payment.missing"))}</span>`;
}

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleString(
    currentLanguage === "zh" ? "zh-Hans" : "en-US",
    {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    }
  );
}

function formatPrice(value) {
  if (value === null || value === undefined) return "--";
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: Number(value) >= 100 ? 2 : 3,
    maximumFractionDigits: Number(value) >= 100 ? 2 : 4
  });
}

function formatPriceWithCurrency(row) {
  const price = formatPrice(row.price);
  if (price === "--") return price;
  return row.currency && row.currency !== "USD" ? `${price} ${row.currency}` : price;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "--";
  const number = Number(value);
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(2)}%`;
}

function formatCompactNumber(value) {
  if (value === null || value === undefined) return "--";
  return Number(value).toLocaleString("en-US", {
    notation: "compact",
    maximumFractionDigits: 1
  });
}

function formatMarketCap(value) {
  if (value === null || value === undefined) return "--";
  return Number(value).toLocaleString("en-US", {
    notation: "compact",
    maximumFractionDigits: 2
  });
}

function formatRatio(value) {
  if (value === null || value === undefined) return "--";
  return Number(value).toLocaleString("en-US", {
    maximumFractionDigits: 1
  });
}

function formatPERatio(row) {
  if (row.pe_ratio !== null && row.pe_ratio !== undefined) return formatRatio(row.pe_ratio);
  if (row.pe_note) return row.pe_note;
  return "--";
}

function valueClass(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number === 0) return "";
  return number > 0 ? "value-up" : "value-down";
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

async function loadDashboard() {
  dashboardSnapshot = await api("/api/dashboard");
  selectedCategory = selectedCategory || "all";
  renderDashboard();
}

function marketSource(snapshot) {
  return snapshot.source_status.find((source) => source.name === "Market data") || {};
}

function fundamentalsLabel(snapshot) {
  const source = marketSource(snapshot);
  if (source.status === "live" && source.loaded_tickers) {
    return `${source.fundamentals_loaded || 0}/${source.loaded_tickers}`;
  }
  return localizeValue("pending");
}

function sortLabel(field = sortField) {
  return t(`sort.${field}`);
}

function sortDirectionGlyph() {
  return sortDirection === "asc" ? "↑" : "↓";
}

function getSortValue(row, field) {
  if (field === "ticker") return row.ticker || "";
  const value = row[field];
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function compareRows(a, b) {
  const aValue = getSortValue(a, sortField);
  const bValue = getSortValue(b, sortField);
  if (sortField === "ticker") {
    return sortDirection === "asc"
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  }
  if (aValue === null && bValue === null) return a.ticker.localeCompare(b.ticker);
  if (aValue === null) return 1;
  if (bValue === null) return -1;
  return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
}

function rowMatchesSearch(row) {
  const query = searchQuery.trim().toLowerCase();
  if (!query) return true;
  const haystack = [
    row.ticker,
    row.company,
    localizeCompany(row),
    row.category_label,
    row.ai_layer,
    row.role,
    localizeRow(row, "ai_layer"),
    localizeRow(row, "role")
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

function visibleRows(snapshot) {
  const rows =
    selectedCategory === "all"
      ? snapshot.rows
      : snapshot.rows.filter((row) => row.category === selectedCategory);
  return rows.filter(rowMatchesSearch).sort(compareRows);
}

function persistDashboardState() {
  localStorage.setItem(CATEGORY_KEY, selectedCategory);
  localStorage.setItem(SEARCH_KEY, searchQuery);
  localStorage.setItem(SORT_FIELD_KEY, sortField);
  localStorage.setItem(SORT_DIRECTION_KEY, sortDirection);
}

function renderDashboard() {
  const snapshot = dashboardSnapshot;
  if (!snapshot) return;

  if (dashboardSearch && dashboardSearch.value !== searchQuery) {
    dashboardSearch.value = searchQuery;
  }

  refreshLabel.textContent = t("dashboard.refreshTarget", {
    seconds: snapshot.refresh_interval_seconds
  });
  dataStatus.textContent = localizeValue(snapshot.data_status_label);
  lastUpdated.textContent = t("dashboard.updated", {
    date: formatDate(snapshot.generated_at)
  });

  dashboardMetrics.innerHTML = [
    [t("metrics.tracked"), snapshot.metrics.tracked_tickers],
    [t("metrics.priced"), snapshot.metrics.priced_tickers],
    [t("metrics.fundamentals"), fundamentalsLabel(snapshot)],
    [t("metrics.core"), snapshot.metrics.core_chokepoints],
    [t("metrics.attention"), snapshot.metrics.high_attention]
  ]
    .map(
      ([label, value]) => `
        <article>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>`
    )
    .join("");

  document.querySelectorAll(".table-sort").forEach((button) => {
    const active = button.dataset.sort === sortField;
    button.classList.toggle("active", active);
    button.dataset.direction = active ? sortDirectionGlyph() : "";
    button.setAttribute(
      "aria-label",
      `${button.textContent.trim()} ${active ? sortDirectionGlyph() : ""}`.trim()
    );
  });

  const tabs = [
    { slug: "all", label: t("tabs.all"), count: snapshot.rows.length },
    ...snapshot.categories.map((category) => ({
      ...category,
      label: localizeValue(category.label),
      description: localizeValue(category.description)
    }))
  ];
  categoryTabs.innerHTML = tabs
    .map(
      (tab) => `
        <button class="${tab.slug === selectedCategory ? "active" : ""}"
          data-category="${escapeHtml(tab.slug)}"
      title="${escapeHtml(tab.description || tab.label)}"
          type="button">
          <span>${escapeHtml(tab.label)}</span>
          <small>${escapeHtml(tab.count)}</small>
        </button>`
    )
    .join("");

  const rows = visibleRows(snapshot);
  tableStatus.textContent = t("dashboard.rowsShown", {
    shown: rows.length,
    total: snapshot.rows.length,
    sort: `${sortLabel()} ${sortDirectionGlyph()}`
  });

  if (!rows.length) {
    dashboardRows.innerHTML = `<p class="empty-table">${escapeHtml(
      t("dashboard.noRows")
    )}</p>`;
  } else {
    dashboardRows.innerHTML = rows
      .map(
        (row) => `
          <article class="market-row" role="button" tabindex="0" data-ticker="${escapeHtml(row.ticker)}">
            <div class="ticker-cell">
              <strong>${escapeHtml(row.ticker)}</strong>
              <span>${escapeHtml(localizeCompany(row))}</span>
            </div>
            <span class="price-cell">${escapeHtml(formatPriceWithCurrency(row))}</span>
            <span class="change-cell ${escapeHtml(valueClass(row.change_percent))}">
              ${escapeHtml(formatPercent(row.change_percent))}
            </span>
            <span class="number-cell">${escapeHtml(formatMarketCap(row.market_cap))}</span>
            <span class="number-cell">${escapeHtml(formatCompactNumber(row.dollar_volume))}</span>
            <span class="number-cell">${escapeHtml(formatPERatio(row))}</span>
            <span>${escapeHtml(localizeRow(row, "role"))}</span>
          </article>`
      )
      .join("");
    dashboardRows.querySelectorAll(".market-row[data-ticker]").forEach((rowButton) => {
      const openRow = () => {
        renderTickerDrawer(rowButton.dataset.ticker);
      };
      rowButton.addEventListener("click", openRow);
      rowButton.addEventListener("pointerup", openRow);
      rowButton.addEventListener("mouseup", openRow);
      rowButton.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openRow();
        }
      });
    });
  }

  if (activeDrawerTicker) {
    renderTickerDrawer(activeDrawerTicker);
  }

  sourceStatus.innerHTML = snapshot.source_status
    .map(
      (source) => `
        <article class="source-item ${escapeHtml(source.status)}">
          <div>
            <strong>${escapeHtml(localizeValue(source.name))}</strong>
            <span>${escapeHtml(localizeSourceDetail(source))}</span>
          </div>
          <mark>${escapeHtml(localizeValue(source.status))}</mark>
        </article>`
    )
    .join("");
}

function drawerMetric(label, value, className = "") {
  return `
    <article>
      <span>${escapeHtml(label)}</span>
      <strong class="${escapeHtml(className)}">${escapeHtml(value)}</strong>
    </article>`;
}

function renderTickerDrawer(ticker) {
  const row = dashboardSnapshot?.rows.find((item) => item.ticker === ticker);
  if (!row) return;
  activeDrawerTicker = ticker;
  drawerBody.innerHTML = `
    <p class="drawer-kicker">${escapeHtml(localizeValue(row.category_label))}</p>
    <div class="drawer-title">
      <h2 id="drawerTitle">${escapeHtml(row.ticker)}</h2>
      <span>${escapeHtml(localizeCompany(row))}</span>
    </div>
    <div class="drawer-metrics">
      ${drawerMetric(t("table.price"), formatPriceWithCurrency(row))}
      ${drawerMetric(
        t("table.change"),
        formatPercent(row.change_percent),
        valueClass(row.change_percent)
      )}
      ${drawerMetric(t("table.marketCap"), formatMarketCap(row.market_cap))}
      ${drawerMetric(t("table.dollarVolume"), formatCompactNumber(row.dollar_volume))}
      ${drawerMetric(t("table.pe"), formatPERatio(row))}
      ${drawerMetric(t("drawer.updated"), formatDate(row.market_updated_at))}
    </div>
    <section class="drawer-section">
      <span>${escapeHtml(t("drawer.positioning"))}</span>
      <p>${escapeHtml(localizeRow(row, "ai_layer"))}</p>
    </section>
    <section class="drawer-section">
      <span>${escapeHtml(t("drawer.aiRole"))}</span>
      <p>${escapeHtml(localizeRow(row, "role"))}</p>
    </section>
    <section class="drawer-section">
      <span>${escapeHtml(t("drawer.latestSignal"))}</span>
      <p>${escapeHtml(localizeRow(row, "latest_signal"))}</p>
    </section>
    ${
      row.source_url
        ? `<section class="drawer-section">
            <span>${escapeHtml(t("drawer.source"))}</span>
            <p><a href="${escapeHtml(row.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(row.source_url)}</a></p>
          </section>`
        : ""
    }`;
  tickerDrawer.classList.remove("hidden");
  tickerDrawer.setAttribute("aria-hidden", "false");
}

function closeTickerDrawer() {
  activeDrawerTicker = null;
  tickerDrawer.classList.add("hidden");
  tickerDrawer.setAttribute("aria-hidden", "true");
}

async function loadApp(existingMe) {
  appConfig = await api("/api/config");
  const me = existingMe || (await api("/api/me"));
  showSignedIn(me);
  accountEmail.textContent = me.email;

  let subscriptionTitle = t("account.pending");
  let subscriptionDetail = t("account.waiting");
  if (me.is_admin) {
    subscriptionTitle = t("account.admin");
    subscriptionDetail = t("account.noExpiry");
  } else if (me.subscription.active) {
    subscriptionTitle = t("account.active");
    subscriptionDetail = me.subscription.expires_at
      ? new Date(me.subscription.expires_at).toLocaleString(
          currentLanguage === "zh" ? "zh-Hans" : "en-US"
        )
      : t("account.noExpiry");
  }
  subscriptionState.innerHTML = `<strong>${escapeHtml(
    subscriptionTitle
  )}</strong><span>${escapeHtml(subscriptionDetail)}</span>`;

  await Promise.all([loadLists(), loadPayment(), loadFeed()]);
  updatePushStatus();
}

async function loadLists() {
  const lists = await api("/api/lists");
  listBox.innerHTML = lists
    .map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>${escapeHtml(item.name)}</strong>
            <span>${escapeHtml(localizeValue(item.description))}</span>
          </div>
          <mark>${escapeHtml(
            item.subscription_active ? t("lists.active") : t("lists.locked")
          )}</mark>
        </article>`
    )
    .join("");
}

async function loadPayment() {
  const payment = await api("/api/payments/current");
  if (payment.admin_bypass) {
    paymentBox.innerHTML = `
      <p class="status-line">${escapeHtml(t("payment.adminBypass"))}</p>
      <dl>
        <div><dt>TRC20</dt><dd>${moneyAddress(payment.trc20_address)}</dd></div>
        <div><dt>ERC20</dt><dd>${moneyAddress(payment.erc20_address)}</dd></div>
      </dl>`;
    return;
  }
  if (payment.member_active) {
    paymentBox.innerHTML = `
      <p class="status-line">${escapeHtml(t("payment.memberActive"))}</p>
      <dl>
        <div><dt>${escapeHtml(t("account.active"))}</dt><dd>${escapeHtml(
      formatDate(payment.expires_at)
    )}</dd></div>
        <div><dt>TRC20</dt><dd>${moneyAddress(payment.trc20_address)}</dd></div>
        <div><dt>ERC20</dt><dd>${moneyAddress(payment.erc20_address)}</dd></div>
      </dl>`;
    return;
  }
  paymentBox.innerHTML = `
    <dl>
      <div><dt>${escapeHtml(t("payment.amount"))}</dt><dd>${escapeHtml(
    payment.amount_usdt
  )} USDT / ${escapeHtml(t("payment.month"))}</dd></div>
      <div><dt>${escapeHtml(t("payment.noteCode"))}</dt><dd><code>${escapeHtml(
    payment.payment_code
  )}</code></dd></div>
      <div><dt>TRC20</dt><dd>${moneyAddress(payment.trc20_address)}</dd></div>
      <div><dt>ERC20</dt><dd>${moneyAddress(payment.erc20_address)}</dd></div>
    </dl>`;
}

async function loadFeed() {
  const feed = await api(`/api/feed?lang=${encodeURIComponent(currentLanguage)}`);
  if (!feed.length) {
    feedBox.innerHTML = `<p class="empty">${escapeHtml(t("alerts.empty"))}</p>`;
    return;
  }
  feedBox.innerHTML = feed
    .map(
      (item) => `
        <article class="alert-card" id="alert-${escapeHtml(item.id)}">
          <header>
            <h3>${escapeHtml(item.title)}</h3>
            <time>${formatDate(item.created_at)}</time>
          </header>
          <p>${escapeHtml(item.notification_text)}</p>
          <ul>${item.bullets
            .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
            .join("")}</ul>
          <div class="ticker-row">${item.tickers
            .map((ticker) => `<span>${escapeHtml(ticker)}</span>`)
            .join("")}</div>
          <p class="why">${escapeHtml(item.why_it_matters)}</p>
          <a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">
            ${escapeHtml(t("alerts.viewSource"))}
          </a>
          <small>${escapeHtml(item.disclaimer)}</small>
        </article>`
    )
    .join("");
}

function updatePushStatus() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    pushStatus.textContent = t("push.unsupported");
    return;
  }
  const installed =
    window.navigator.standalone === true ||
    window.matchMedia("(display-mode: standalone)").matches;
  pushStatus.textContent = installed ? t("push.installed") : t("push.installFirst");
}

async function enablePush() {
  if (!appConfig.vapid_public_key) {
    pushStatus.textContent = t("push.noVapid");
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    pushStatus.textContent = t("push.denied");
    return;
  }
  const registration = await navigator.serviceWorker.register("/sw.js");
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(appConfig.vapid_public_key)
  });
  await api("/api/push/subscribe", {
    method: "POST",
    body: JSON.stringify({ subscription })
  });
  pushStatus.textContent = t("push.enabled");
}

async function rerenderLanguageSensitiveSections() {
  applyStaticCopy();
  renderDashboard();
  if (currentUser) {
    await loadApp(currentUser);
  } else {
    updatePushStatus();
  }
}

categoryTabs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-category]");
  if (!button) return;
  selectedCategory = button.dataset.category;
  persistDashboardState();
  renderDashboard();
});

dashboardSearch.addEventListener("input", (event) => {
  searchQuery = event.target.value;
  persistDashboardState();
  renderDashboard();
});

document.querySelector(".market-table-header").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-sort]");
  if (!button) return;
  const nextField = button.dataset.sort;
  if (sortField === nextField) {
    sortDirection = sortDirection === "asc" ? "desc" : "asc";
  } else {
    sortField = nextField;
    sortDirection = nextField === "ticker" ? "asc" : "desc";
  }
  persistDashboardState();
  renderDashboard();
});

dashboardRows.addEventListener("click", (event) => {
  const row = event.target.closest(".market-row[data-ticker]");
  if (!row) return;
  renderTickerDrawer(row.dataset.ticker);
});

drawerClose.addEventListener("click", closeTickerDrawer);
tickerDrawer.addEventListener("click", (event) => {
  if (event.target.matches("[data-drawer-close]")) {
    closeTickerDrawer();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !tickerDrawer.classList.contains("hidden")) {
    closeTickerDrawer();
  }
});

languageToggle.addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "en" : "zh";
  localStorage.setItem(LANGUAGE_KEY, currentLanguage);
  rerenderLanguageSensitiveSections();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  loginMessage.textContent = t("auth.sending");
  try {
    const result = await api("/api/auth/request", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(form.entries()))
    });
    loginMessage.innerHTML = result.dev_magic_link
      ? `${escapeHtml(t("auth.devLink"))}<a href="${escapeHtml(
          result.dev_magic_link
        )}">${escapeHtml(t("auth.openLogin"))}</a>`
      : t("auth.sent");
  } catch {
    loginMessage.textContent = t("auth.failed");
  }
});

enablePushBtn.addEventListener("click", enablePush);
testPushBtn.addEventListener("click", async () => {
  pushStatus.textContent = t("push.testing");
  const result = await api("/api/push/test", { method: "POST" });
  pushStatus.textContent = t("push.testDone", {
    sent: result.sent,
    failed: result.failed
  });
});
logoutBtn.addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  location.reload();
});

applyStaticCopy();
startAnalytics();
loadDashboard().catch(() => {
  dataStatus.textContent = t("dashboard.unavailable");
});
window.setInterval(() => {
  loadDashboard().catch(() => {
    dataStatus.textContent = t("dashboard.unavailable");
  });
}, 15_000);

api("/api/me")
  .then(loadApp)
  .catch(() => showSignedOut());
