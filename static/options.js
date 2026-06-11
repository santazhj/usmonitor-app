const AI_CORE_TICKERS = [
  "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "ORCL", "AMD",
  "INTC", "MU", "ARM", "PLTR", "MRVL", "BE", "TEM", "AAOI", "LEU", "RKLB", "MSTR",
  "TSM", "ASML", "AMAT", "LRCX", "KLAC", "SMCI", "LITE", "COHR", "ANET", "VRT"
];

const DEFAULT_TICKERS = AI_CORE_TICKERS;
const DEFAULT_WATCHLISTS = {
  "AI Core": AI_CORE_TICKERS,
  "AI Photonics": [
    "NVDA", "TSM", "MRVL", "AVGO", "LITE", "COHR", "AAOI", "AXTI", "POET", "AEHR",
    "GLW", "JBL", "CIEN", "CRDO", "MTSI", "AMKR", "ONTO", "TSEM", "GFS", "ALAB"
  ],
  "AI Power": [
    "VRT", "ETN", "GEV", "CEG", "VST", "BE", "LEU", "SMR", "OKLO", "BWXT", "CCJ", "PWR", "FIX", "EME"
  ],
  "AI Cloud": [
    "MSFT", "AMZN", "GOOGL", "META", "ORCL", "NVDA", "AMD", "AVGO", "ANET", "DELL",
    "HPE", "SMCI", "VRT", "CRWV", "NBIS", "APLD", "IREN"
  ],
  "AI Speculative": [
    "TEM", "AAOI", "AXTI", "POET", "AEHR", "CRDO", "ALAB", "SNDK", "WDC", "STX",
    "BE", "LEU", "RKLB", "MSTR", "OKLO", "RGTI", "QBTS", "LUNR", "ASTS", "AMBA",
    "OSS", "VPG", "LASR", "VICR", "MP", "WOLF", "NVTS"
  ]
};

const TICKER_NAMES = {
  AAPL: "Apple",
  MSFT: "Microsoft",
  NVDA: "NVIDIA",
  AMZN: "Amazon",
  META: "Meta Platforms",
  GOOGL: "Alphabet",
  TSLA: "Tesla",
  AVGO: "Broadcom",
  ORCL: "Oracle",
  AMD: "Advanced Micro Devices",
  INTC: "Intel",
  MU: "Micron Technology",
  ARM: "Arm Holdings",
  PLTR: "Palantir",
  MRVL: "Marvell Technology",
  BE: "Bloom Energy",
  TEM: "Tempus AI",
  AAOI: "Applied Optoelectronics",
  LEU: "Centrus Energy",
  RKLB: "Rocket Lab",
  MSTR: "Strategy",
  TSM: "Taiwan Semiconductor",
  ASML: "ASML Holding",
  AMAT: "Applied Materials",
  LRCX: "Lam Research",
  KLAC: "KLA",
  SMCI: "Super Micro Computer",
  LITE: "Lumentum",
  COHR: "Coherent",
  ANET: "Arista Networks",
  VRT: "Vertiv",
  BWXT: "BWX Technologies",
  CCJ: "Cameco",
  URG: "Ur-Energy",
  NBIS: "NEBIUS",
  NTRA: "Natera",
  VEEV: "Veeva Systems",
  GH: "Guardant Health",
  GEHC: "GE HealthCare",
  SYK: "Stryker",
  MDT: "Medtronic",
  ISRG: "Intuitive Surgical",
  RXRX: "Recursion Pharma",
  BSX: "Boston Scientific",
  HIMS: "Hims & Hers",
  DIOD: "Diodes"
};

const WATCHLIST_KEY = "usmonitor.options.watchlists";
const WATCHLIST_VERSION = 5;
const SOURCE_KEY = "usmonitor.options.dataSource";
const MAX_EXPIRY_DTE = 365;

const els = {
  quickRefreshBtn: document.querySelector("#quickRefreshBtn"),
  fullScanBtn: document.querySelector("#fullScanBtn"),
  dataSourceSelect: document.querySelector("#dataSourceSelect"),
  optionsAccountLink: document.querySelector("#optionsAccountLink"),
  watchlistSelect: document.querySelector("#watchlistSelect"),
  watchlistTabs: document.querySelector("#watchlistTabs"),
  newListBtn: document.querySelector("#newListBtn"),
  deleteListBtn: document.querySelector("#deleteListBtn"),
  tickerSearch: document.querySelector("#tickerSearch"),
  tickerSuggestions: document.querySelector("#tickerSuggestions"),
  tickerChips: document.querySelector("#tickerChips"),
  tableSearch: document.querySelector("#tableSearch"),
  validFilter: document.querySelector("#validFilter"),
  dteFilter: document.querySelector("#dteFilter"),
  tableStatus: document.querySelector("#tableStatus"),
  scanProgress: document.querySelector("#scanProgress"),
  progressMessage: document.querySelector("#progressMessage"),
  progressMeta: document.querySelector("#progressMeta"),
  progressBar: document.querySelector("#progressBar"),
  progressEvents: document.querySelector("#progressEvents"),
  tableHead: document.querySelector("#optionsTableHead"),
  tableBody: document.querySelector("#optionsTableBody"),
  optionDetail: document.querySelector("#optionDetail"),
  kpiUnderlyings: document.querySelector("#kpiUnderlyings"),
  kpiScope: document.querySelector("#kpiScope"),
  kpiContracts: document.querySelector("#kpiContracts"),
  kpiValid: document.querySelector("#kpiValid"),
  kpiRate: document.querySelector("#kpiRate"),
  kpiRateBar: document.querySelector("#kpiRateBar"),
  kpiBestPer: document.querySelector("#kpiBestPer"),
  kpiIv: document.querySelector("#kpiIv"),
  kpiSpread: document.querySelector("#kpiSpread"),
  kpiRefresh: document.querySelector("#kpiRefresh"),
  kpiMode: document.querySelector("#kpiMode")
};

const columns = [
  { label: "标的", key: "ticker", title: "该行期权对应的正股 ticker。" },
  { label: "合约", title: "同一标的过滤后选出的最佳单个 put 合约。" },
  { label: "期限桶", key: "dte_bucket", title: "用于公平排名的到期期限桶；上方到期日筛选使用具体到期日。" },
  { label: "标签", title: "当前 PER 性价比分档的简短标签。" },
  { label: "Cycle PER", key: "cycle_put_edge_ratio", title: "Cycle PER = 到期收益 / |Delta| × min(Buffer / Expected Move, 2)。比年化 PER 更适合比较月度期权。" },
  { label: "桶排名", key: "bucket_rank", title: "在同一个到期期限桶内，Cycle PER 的百分位排名。" },
  { label: "月度分", key: "monthly_score", title: "月度偏好的综合分，结合桶内排名、质量分和期限偏好，刻意优先 31-75D。" },
  { label: "PER", key: "put_edge_ratio", title: "PER = Bid 年化 / |Delta| × min(Buffer / Expected Move, 2)。流动性和报价新鲜度只做过滤/风险提示，不再进入 PER。" },
  { label: "质量分", key: "score", title: "0-100 综合质量分：加权看收益、下行缓冲、流动性和风险数据，不是收益率。" },
  { label: "现价", key: "spot", title: "计算中使用的最新可用正股价格。" },
  { label: "Bid / Ask", key: "bid", title: "当前或参考的期权买价和卖价。" },
  { label: "权利金", key: "target_credit", title: "目标权利金估算，通常基于买卖价中点并结合报价质量。" },
  { label: "BS", key: "bs_put_price", title: "Black-Scholes 理论价" },
  { label: "权/BS", key: "premium_vs_bs_pct", title: "目标权利金相对 Black-Scholes 理论价的溢价/折价；正数代表市场权利金高于模型价。" },
  { label: "到期收益", key: "expiry_yield", title: "到期收益 = 目标权利金 / 行权价；表示这一单持有到到期且期权归零时，本周期相对行权价的收益。" },
  { label: "天数", key: "dte", title: "从现在到期权到期日的自然日天数。" },
  { label: "年化", key: "ann_yield_bid", title: "按 Bid 权利金、行权价和 DTE 计算的年化收益；过高需要单独看风险。" },
  { label: "报价", title: "报价模式：盘中实时，或休市时的收盘/参考数据。" },
  { label: "展开", title: "展开该标的下排名靠前的其它具体合约。" }
];
if (columns.length > 18) columns.pop();

let watchlists = loadWatchlists();
let payload = null;
let dataSource = localStorage.getItem(SOURCE_KEY) || "massive";
if (!["massive", "ibkr"].includes(dataSource)) dataSource = "massive";
let progress = null;
let selectedTicker = "";
let selectedOptionTicker = "";
let expandedOptionKey = "";
let filterMode = "all";
let expiryFilter = "all";
let tableQuery = "";
let suggestions = [];
let highlightedSuggestionIndex = -1;
let sortConfig = { key: "monthly_score", direction: "desc" };

function loadWatchlists() {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Number(parsed.version || 0) >= WATCHLIST_VERSION) return parsed;
      return {
        ...parsed,
        active: "AI Core",
        version: WATCHLIST_VERSION,
        lists: { ...DEFAULT_WATCHLISTS, ...(parsed.lists || {}), "AI Core": DEFAULT_WATCHLISTS["AI Core"] }
      };
    }
  } catch {
    // ignore malformed local state
  }
  return { active: "AI Core", version: WATCHLIST_VERSION, lists: { ...DEFAULT_WATCHLISTS } };
}

function saveWatchlists() {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify({ ...watchlists, version: WATCHLIST_VERSION }));
}

function activeTickers() {
  return watchlists.lists[watchlists.active] || [];
}

function scanTickers() {
  return Array.from(
    new Set(
      activeTickers().map((ticker) => String(ticker).trim().toUpperCase()).filter(Boolean)
    )
  );
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function number(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
}

function money(value) {
  if (value === null || value === undefined || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  const digits = Math.abs(numeric) >= 1000 ? 0 : 2;
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
}

function quoteMoney(value) {
  if (value === null || value === undefined || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "--";
  return money(numeric);
}

function pct(value, digits = 1) {
  if (value === null || value === undefined || value === "") return "--";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  return `${(numeric * 100).toFixed(digits)}%`;
}

function time(value) {
  if (!value) return "--";
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
}

function compactEdge(label) {
  const labels = {
    Extreme: "极高",
    Good: "良好",
    Watch: "观察",
    Normal: "普通",
    Stale: "旧",
    Liquidity: "低流动性",
    "Data Gap": "缺IV/Delta",
    Event: "事件",
    "极高性价比": "极高",
    "好性价比": "良好",
    "可观察": "观察",
    "旧报价": "旧",
    "数据不足": "缺IV/Delta",
    "流动性陷阱": "低流动性",
    "事件风险": "事件"
  };
  return labels[label] || label || "--";
}

function compactQuote(label) {
  const labels = {
    Live: "实时",
    "Close Ref": "收盘",
    "盘中实时": "实时",
    "收盘参考": "收盘"
  };
  return labels[label] || label || "--";
}

function edgeTitle(row) {
  if (row.edge_flag === "Data Gap") return "缺少 IV/Delta/模型价，PER 与 BS 不可靠；Bid/Ask 和 OI 仍可能是实时有效数据。";
  if (row.edge_flag === "Liquidity") return "价差过宽或 OI 偏低，成交质量需要谨慎。";
  if (row.edge_flag === "Stale") return "报价时间偏旧。";
  return row.edge_flag || "--";
}

function compactContract(row) {
  const expiry = row.expiry || row.expiration || "";
  const strike = money(row.strike).replace(/\.00$/, "");
  if (expiry && Number.isFinite(Number(row.strike))) return `${expiry.slice(5)} P${strike}`;
  return String(row.topContract || "--").replace(/^\d{4}-/, "");
}

function tickerName(ticker) {
  return TICKER_NAMES[String(ticker || "").toUpperCase()] || String(ticker || "").toUpperCase();
}

function optionKey(row) {
  return row?.option_ticker || `${row?.ticker || ""}-${row?.expiry || ""}-${row?.strike || ""}`;
}

function expiryYield(row) {
  const explicit = Number(row?.expiry_yield);
  if (row?.expiry_yield !== null && row?.expiry_yield !== undefined && row?.expiry_yield !== "" && Number.isFinite(explicit)) {
    return explicit;
  }
  const credit = Number(row?.target_credit);
  const strike = Number(row?.strike);
  if (!Number.isFinite(credit) || !Number.isFinite(strike) || strike <= 0) return null;
  return credit / strike;
}

function optionExpiry(row) {
  return String(row?.expiry || row?.expiration || "").slice(0, 10);
}

function optionDte(row) {
  const dte = Number(row?.dte);
  return Number.isFinite(dte) ? dte : null;
}

function withinOneYear(row) {
  const dte = optionDte(row);
  return dte !== null && dte >= 0 && dte <= MAX_EXPIRY_DTE;
}

function expiryMatches(row, selectedExpiry) {
  if (!withinOneYear(row)) return false;
  if (selectedExpiry === "all") return true;
  return optionExpiry(row) === selectedExpiry;
}

function formatExpiryLabel(expiry, dte) {
  const parts = String(expiry || "").split("-");
  const datePart = parts.length === 3 && parts[0] === String(new Date().getFullYear()) ? `${parts[1]}-${parts[2]}` : expiry;
  const dteText = Number.isFinite(Number(dte)) ? Math.round(Number(dte)) : "--";
  return `${datePart} ${dteText}天`;
}

function expiryOptions() {
  const activeSet = new Set(scanTickers());
  const byExpiry = new Map();
  for (const item of payload?.expiries || []) {
    const expiry = String(item.expiry || "").slice(0, 10);
    const dte = Number(item.dte);
    if (expiry && Number.isFinite(dte) && dte >= 0 && dte <= MAX_EXPIRY_DTE) {
      byExpiry.set(expiry, Math.min(dte, byExpiry.get(expiry) ?? dte));
    }
  }
  for (const row of payload?.underlyings || []) {
    if (!activeSet.has(String(row.ticker || "").toUpperCase())) continue;
    for (const option of [...(row.topOptions || []), row]) {
      const expiry = optionExpiry(option);
      const dte = optionDte(option);
      if (expiry && dte !== null && dte >= 0 && dte <= MAX_EXPIRY_DTE) {
        byExpiry.set(expiry, Math.min(dte, byExpiry.get(expiry) ?? dte));
      }
    }
  }
  return [...byExpiry.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([expiry, dte]) => ({ value: expiry, label: formatExpiryLabel(expiry, dte) }));
}

function renderExpiryFilter() {
  if (!els.dteFilter) return;
  const options = expiryOptions();
  if (expiryFilter !== "all" && !options.some((item) => item.value === expiryFilter)) {
    expiryFilter = "all";
  }
  els.dteFilter.innerHTML = [
    `<option value="all">全部</option>`,
    ...options.map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
  ].join("");
  els.dteFilter.value = expiryFilter;
}

function detailLine(label, value, tone = "") {
  return `
    <div class="options-expand-line">
      <span>${escapeHtml(label)}</span>
      <strong class="mono ${tone}">${escapeHtml(value)}</strong>
    </div>`;
}

function badge(label, tone = "zinc", title = label) {
  return `<span class="option-badge ${tone}" title="${escapeHtml(title || label || "")}">${escapeHtml(label || "--")}</span>`;
}

function edgeTone(edge) {
  if (edge === "Extreme" || edge === "Good") return "green";
  if (edge === "Stale") return "red";
  if (edge === "Liquidity" || edge === "Data Gap") return "amber";
  return "zinc";
}

function payloadRowForTicker(ticker) {
  const normalized = String(ticker || "").toUpperCase();
  return (payload?.underlyings || []).find((row) => String(row.ticker || "").toUpperCase() === normalized) || null;
}

function sparklinePoints(ticker, row) {
  const seed = String(ticker || "")
    .split("")
    .reduce((total, char) => total + char.charCodeAt(0), 0);
  const score = Number(row?.monthly_score ?? row?.score ?? 50);
  const drift = Number.isFinite(score) ? (score - 55) / 130 : 0;
  const width = 58;
  const height = 24;
  const count = 15;
  const points = [];
  for (let index = 0; index < count; index += 1) {
    const x = (index / (count - 1)) * width;
    const wave = Math.sin((seed + index * 5) * 0.72) * 4;
    const noise = (((seed * (index + 3)) % 11) - 5) * 0.65;
    const y = Math.max(3, Math.min(height - 3, height * 0.58 - drift * index * 5 + wave + noise));
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  return points.join(" ");
}

function watchlistRow(ticker) {
  const row = payloadRowForTicker(ticker);
  const monthly = Number(row?.monthly_score);
  const cycle = Number(row?.cycle_put_edge_ratio ?? row?.put_edge_ratio);
  const tone = Number.isFinite(monthly) && monthly >= 65 ? "up" : Number.isFinite(monthly) && monthly < 45 ? "down" : "flat";
  return `
    <button class="watch-market-row ${selectedTicker === ticker ? "selected" : ""}" type="button" data-watch-ticker="${escapeHtml(ticker)}">
      <span class="watch-name">
        <strong title="${escapeHtml(tickerName(ticker))}">${escapeHtml(tickerName(ticker))}</strong>
        <small>${escapeHtml(ticker)}</small>
      </span>
      <span class="watch-spark ${tone}" aria-hidden="true">
        <svg viewBox="0 0 58 24" focusable="false">
          <polyline points="${sparklinePoints(ticker, row)}"></polyline>
        </svg>
      </span>
      <span class="watch-price mono">${money(row?.spot)}</span>
      <span class="watch-change mono ${tone === "up" ? "value-up" : tone === "down" ? "value-down" : ""}">${Number.isFinite(monthly) ? number(monthly, 1) : "--"}</span>
      <span class="watch-change mono ${tone === "up" ? "value-up" : tone === "down" ? "value-down" : ""}">${Number.isFinite(cycle) ? number(cycle, 2) : "--"}</span>
      <span class="watch-row-remove" data-remove-ticker="${escapeHtml(ticker)}" title="移除">x</span>
    </button>`;
}

function setLoading(mode, loading) {
  const button = mode === "full" ? els.fullScanBtn : els.quickRefreshBtn;
  button.disabled = loading;
  button.textContent =
    mode === "full"
      ? loading ? "完整扫描中" : "完整扫描"
      : loading ? "刷新中" : "快速刷新";
  if (mode === "full") els.quickRefreshBtn.disabled = loading;
  if (mode === "quick") els.fullScanBtn.disabled = loading;
  if (els.dataSourceSelect) els.dataSourceSelect.disabled = loading;
}

async function api(path) {
  const response = await fetch(path);
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || "Request failed");
  return data;
}

async function syncAccountStatus() {
  if (!els.optionsAccountLink) return;
  try {
    const user = await api("/api/me");
    els.optionsAccountLink.textContent = user.email || "账户";
    els.optionsAccountLink.href = "/login?next=/options";
    els.optionsAccountLink.title = "已登录";
  } catch {
    els.optionsAccountLink.textContent = "登录";
    els.optionsAccountLink.href = "/login?next=/options";
    els.optionsAccountLink.title = "登录后 Options 与主站共用同一账户";
  }
}

async function fetchProgress() {
  const tickers = scanTickers();
  if (!tickers.length) return;
  try {
    progress = await api(
      `/api/options/progress?tickers=${encodeURIComponent(tickers.join(","))}&source=${encodeURIComponent(dataSource)}`
    );
    renderProgress();
  } catch {
    // Progress is observational; keep the scan itself authoritative.
  }
}

async function refresh(mode = "quick") {
  const tickers = scanTickers();
  if (!tickers.length) {
    payload = { summary: {}, underlyings: [] };
    render();
    return;
  }
  setLoading(mode, true);
  els.tableStatus.textContent = mode === "full" ? "完整扫描中..." : "快速刷新中...";
  let progressTimer = null;
  progress = {
    active: true,
    source: dataSource,
    mode,
    total: tickers.length,
    completed: 0,
    stage: mode === "full" ? "queued" : "quick_refresh",
    currentTicker: "",
    message: mode === "full" ? `Queued ${tickers.length} tickers` : `Refreshing ${tickers.length} cached option quotes`,
    contracts: 0,
    quoteRequests: 0,
    quotesWithBidAsk: 0,
    quotesWithGreeks: 0,
    events: [],
    errors: []
  };
  renderProgress();
  progressTimer = window.setInterval(fetchProgress, mode === "quick" ? 450 : 900);
  window.setTimeout(fetchProgress, 250);
  try {
    payload = await api(
      `/api/options/scan?tickers=${encodeURIComponent(tickers.join(","))}&mode=${encodeURIComponent(mode)}&source=${encodeURIComponent(dataSource)}&allowInitialFull=false`
    );
    if (!payload.underlyings.some((row) => row.ticker === selectedTicker)) {
      selectedTicker = payload.underlyings[0]?.ticker || "";
      selectedOptionTicker = "";
      expandedOptionKey = "";
    }
    if (mode === "full") {
      selectedOptionTicker = "";
      expandedOptionKey = "";
    }
    render();
  } catch (error) {
    els.tableStatus.textContent = `扫描失败: ${error.message}`;
  } finally {
    if (progressTimer) window.clearInterval(progressTimer);
    await fetchProgress();
    setLoading(mode, false);
  }
}

function renderWatchlists() {
  const names = Object.keys(watchlists.lists);
  els.watchlistSelect.innerHTML = names
    .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
    .join("");
  els.watchlistSelect.value = watchlists.active;
  if (els.watchlistTabs) {
    els.watchlistTabs.innerHTML = names
      .map(
        (name) => `
          <button class="${name === watchlists.active ? "active" : ""}" type="button" data-watchlist-tab="${escapeHtml(name)}" title="${escapeHtml(name)}">
            ${escapeHtml(name)}
          </button>`
      )
      .join("");
  }

  els.tickerChips.innerHTML = activeTickers()
    .map((ticker) => watchlistRow(ticker))
    .join("");
  els.kpiScope.textContent = scanTickers().join(", ") || "--";
  if (els.dataSourceSelect) els.dataSourceSelect.value = dataSource;
}

function renderSuggestions() {
  if (!suggestions.length) {
    els.tickerSuggestions.classList.add("hidden");
    els.tickerSuggestions.innerHTML = "";
    return;
  }
  els.tickerSuggestions.classList.remove("hidden");
  els.tickerSuggestions.innerHTML = suggestions
    .map(
      (item, index) => `
        <button class="${index === highlightedSuggestionIndex ? "active" : ""}"
          data-suggestion-index="${index}"
          type="button">
          <strong>${escapeHtml(item.ticker)}</strong>
          <span>${escapeHtml(item.exchange || "")} / ${escapeHtml(item.type || "")}</span>
          <small>${escapeHtml(item.name || "")}</small>
        </button>`
    )
    .join("");
}

function addTicker(item) {
  const ticker = String(item.ticker || "").toUpperCase();
  if (!ticker) return;
  const current = activeTickers();
  watchlists.lists[watchlists.active] = Array.from(new Set([...current, ticker]));
  saveWatchlists();
  els.tickerSearch.value = "";
  suggestions = [];
  highlightedSuggestionIndex = -1;
  renderWatchlists();
  renderSuggestions();
}

function removeTicker(ticker) {
  watchlists.lists[watchlists.active] = activeTickers().filter((item) => item !== ticker);
  saveWatchlists();
  renderWatchlists();
}

function sortValue(row, key) {
  if (key === "bid") return Number(row.bid);
  if (key === "expiry_yield") return expiryYield(row);
  if (key === "dte_bucket") {
    return { "07-14D": 1, "15-30D": 2, "31-45D": 3, "46-75D": 4, "76-120D": 5, "121-365D": 6 }[row.dte_bucket] || 99;
  }
  if (key === "ticker") return row.ticker || "";
  const value = row[key];
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function activeOptionSort() {
  if (!sortConfig.key || sortConfig.key === "ticker") return { key: "monthly_score", direction: "desc" };
  return sortConfig;
}

function compareBySort(a, b, config = activeOptionSort()) {
  const key = config.key || "monthly_score";
  const direction = config.direction === "asc" ? 1 : -1;
  const av = sortValue(a, key);
  const bv = sortValue(b, key);
  if (key === "ticker") return direction * String(av || "").localeCompare(String(bv || ""));
  if (av === null && bv === null) return String(optionKey(a)).localeCompare(String(optionKey(b)));
  if (av === null) return 1;
  if (bv === null) return -1;
  if (av === bv) return String(optionKey(a)).localeCompare(String(optionKey(b)));
  return av > bv ? direction : -direction;
}

function optionRowsForUnderlying(row, limit = 10) {
  if (!row) return [];
  const seen = new Set();
  const source = [...(row.topOptions || []), row].filter((option) => {
    const key = optionKey(option);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  let options = source.filter((option) => expiryMatches(option, expiryFilter));
  if (filterMode === "valid") options = options.filter((option) => option.platform_valid !== false);
  options = [...options].sort((a, b) => compareBySort(a, b));
  return Number.isFinite(limit) ? options.slice(0, limit) : options;
}

function rowForExpiryFilter(row) {
  const match = optionRowsForUnderlying(row, 1)[0];
  if (!match) return null;
  return { ...row, ...match, topOptions: row.topOptions || [] };
}

function visibleRows() {
  const activeSet = new Set(scanTickers());
  let rows = (payload?.underlyings || [])
    .filter((row) => activeSet.has(String(row.ticker || "").toUpperCase()))
    .map(rowForExpiryFilter)
    .filter(Boolean);
  if (filterMode === "valid") rows = rows.filter((row) => row.platform_valid !== false);
  const query = tableQuery.trim().toUpperCase();
  if (query) {
    rows = rows.filter((row) =>
      `${row.ticker} ${row.option_ticker} ${row.risk_flags || ""}`.toUpperCase().includes(query)
    );
  }
  if (!sortConfig.key) return rows;
  return [...rows].sort((a, b) => {
    const result = compareBySort(a, b, sortConfig);
    return result || String(a.ticker).localeCompare(String(b.ticker));
  });
}

function toggleSort(key) {
  if (sortConfig.key === key) {
    sortConfig = { key, direction: sortConfig.direction === "desc" ? "asc" : "desc" };
  } else {
    sortConfig = { key, direction: key === "ticker" ? "asc" : "desc" };
  }
  renderTable();
}

function renderHead() {
  els.tableHead.innerHTML = columns
    .map((column) => {
      const title = column.title ? ` title="${escapeHtml(column.title)}"` : "";
      if (!column.key) return `<th${title}>${escapeHtml(column.label)}</th>`;
      const arrow =
        sortConfig.key === column.key ? (sortConfig.direction === "desc" ? "↓" : "↑") : "↕";
      const active = sortConfig.key === column.key ? "active" : "";
      return `
        <th${title}>
          <button class="option-sort ${active}" data-sort-key="${escapeHtml(column.key)}" type="button" title="${escapeHtml(column.title || column.label)}">
            ${escapeHtml(column.label)} <span>${arrow}</span>
          </button>
        </th>`;
    })
    .join("");
}

function renderOptionSubtable(row, optionRows) {
  const headers = ["#", "Contract", "Bucket", "Tag", "Monthly", "PER", "Cycle", "Rank", "Quality", "Bid / Ask", "Credit", "BS", "Prem/BS", "Expiry Yld", "DTE", "Ann", "Delta", "IV", "OI", "Spread", "Buffer", "Quote"];
  if (!optionRows.length) {
    return `<div class="option-child-panel"><div class="option-child-head"><strong>${escapeHtml(row.ticker)} Top 10</strong><span>No matching contracts in the current filters.</span></div></div>`;
  }
  return `
    <div class="option-child-panel">
      <div class="option-child-head">
        <strong>${escapeHtml(row.ticker)} Top 10 puts</strong>
        <span>Sorted with the same active table rule.</span>
      </div>
      <div class="option-child-scroll">
        <table class="option-child-table">
          <thead>
            <tr>${headers.map((label) => `<th>${escapeHtml(label)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${optionRows.map((option, index) => `
              <tr class="${selectedOptionTicker === option.option_ticker ? "selected" : ""}" data-child-ticker="${escapeHtml(row.ticker)}" data-child-option="${escapeHtml(option.option_ticker || optionKey(option))}">
                <td class="mono muted">${index + 1}</td>
                <td>${badge(compactContract(option), "sky", option.option_ticker || compactContract(option))}</td>
                <td class="mono value-info">${escapeHtml(option.dte_bucket || "--")}</td>
                <td>${badge(compactEdge(option.edge_flag), edgeTone(option.edge_flag), edgeTitle(option))}</td>
                <td class="mono edge">${number(option.monthly_score)}</td>
                <td class="mono edge">${number(option.put_edge_ratio)}</td>
                <td class="mono edge">${number(option.cycle_put_edge_ratio)}</td>
                <td class="mono">${pct(option.bucket_rank ?? option.put_edge_rank)}</td>
                <td class="mono">${number(option.score)}</td>
                <td class="mono">${quoteMoney(option.bid)} / ${quoteMoney(option.ask)}</td>
                <td class="mono">${quoteMoney(option.target_credit)}</td>
                <td class="mono">${money(option.bs_put_price)}</td>
                <td class="mono ${Number(option.premium_vs_bs_pct) > 0 ? "value-up" : ""}">${pct(option.premium_vs_bs_pct)}</td>
                <td class="mono edge">${pct(expiryYield(option))}</td>
                <td class="mono">${number(option.dte, 0)}</td>
                <td class="mono">${pct(option.ann_yield_bid)}</td>
                <td class="mono">${pct(option.delta)}</td>
                <td class="mono">${pct(option.iv)}</td>
                <td class="mono">${number(option.open_interest, 0)}</td>
                <td class="mono">${pct(option.spread_pct)}</td>
                <td class="mono">${pct(option.breakeven_buffer)}</td>
                <td>${badge(compactQuote(option.quote_mode), option.quote_mode === "Live" ? "green" : "amber", option.quote_mode)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
}

function renderTable() {
  renderHead();
  const rows = visibleRows();
  const errors = payload?.errors || [];
  els.tableStatus.textContent = payload
    ? `显示 ${rows.length}/${payload.underlyings.length} 个标的${errors.length ? ` · ${errors.length} 个错误` : ""}`
    : "等待扫描";
  if (!rows.length) {
    const message = errors.length
      ? errors.slice(0, 3).join("；")
      : payload?.summary?.fullScanRequired
        ? "当前列表还没有完整扫描缓存。点击“完整扫描”后，后续快速刷新会很快。"
        : "暂无数据。点完整扫描开始。";
    els.tableBody.innerHTML = `<tr><td colspan="${columns.length}" class="empty-table">${escapeHtml(message)}</td></tr>`;
    return;
  }
  els.tableBody.innerHTML = rows
    .map(
      (row) => {
        const key = optionKey(row);
        const expanded = expandedOptionKey === key;
        const optionRows = optionRowsForUnderlying(row, 10);
        return `
        <tr class="${row.ticker === selectedTicker ? "selected" : ""}" data-row-ticker="${escapeHtml(row.ticker)}">
          <td class="mono strong">
            <button class="option-row-toggle" type="button" data-expand-option="${escapeHtml(key)}" title="${expanded ? "Hide" : "Show"}">${expanded ? "-" : "+"}</button>
            <span>${escapeHtml(row.ticker)}</span>
          </td>
          <td>${badge(compactContract(row), "sky", row.topContract)}</td>
          <td class="mono value-info">${escapeHtml(row.dte_bucket || "--")}</td>
          <td>${badge(compactEdge(row.edge_flag), edgeTone(row.edge_flag), edgeTitle(row))}</td>
          <td class="mono edge" title="Cycle PER = 到期收益 / |Delta| × min(Buffer / Expected Move, 2)。">${number(row.cycle_put_edge_ratio)}</td>
          <td class="mono" title="同一期限桶内的 Cycle PER 百分位排名。">${pct(row.bucket_rank ?? row.put_edge_rank)}</td>
          <td class="mono edge" title="月度偏好的综合分，默认按它排序。">${number(row.monthly_score)}</td>
          <td class="mono edge">${number(row.put_edge_ratio)}</td>
          <td class="mono" title="0-100 综合质量分：加权看收益、下行缓冲、流动性和风险数据，不是收益率。">${number(row.score)}</td>
          <td class="mono">${money(row.spot)}</td>
          <td class="mono">${quoteMoney(row.bid)} / ${quoteMoney(row.ask)}</td>
          <td class="mono">${quoteMoney(row.target_credit)}</td>
          <td class="mono">${money(row.bs_put_price)}</td>
          <td class="mono ${Number(row.premium_vs_bs_pct) > 0 ? "value-up" : ""}">${pct(row.premium_vs_bs_pct)}</td>
          <td class="mono edge" title="到期收益 = 目标权利金 / 行权价；表示这一单持有到到期且期权归零时，本周期相对行权价的收益。">${pct(expiryYield(row))}</td>
          <td class="mono">${number(row.dte, 0)}</td>
          <td class="mono">${pct(row.ann_yield_bid)}</td>
          <td>${badge(compactQuote(row.quote_mode), row.quote_mode === "Live" ? "green" : "amber", row.quote_mode)}</td>
          <td>
            <button class="option-expand-btn" type="button" data-expand-option="${escapeHtml(key)}">
              <span>${expanded ? "收起" : "展开"}</span>
              <span class="${expanded ? "rotated" : ""}">⌄</span>
            </button>
          </td>
        </tr>
        ${expanded ? `
          <tr class="options-expanded-row">
            <td colspan="${columns.length}">
              ${renderOptionSubtable(row, optionRows)}
              <div class="options-expand-grid">
                <section>
                  <h4>Greeks</h4>
                  ${detailLine("Delta", pct(row.delta))}
                  ${detailLine("Gamma", number(row.gamma, 4))}
                  ${detailLine("Vega", number(row.vega, 4))}
                  ${detailLine("Theta", number(row.theta, 4))}
                  ${detailLine("Rho", number(row.rho, 4))}
                  ${detailLine("IV", pct(row.iv))}
                  ${detailLine("RV", pct(row.realized_vol))}
                </section>
                <section>
                  <h4>流动性</h4>
                  ${detailLine("OI", number(row.open_interest, 0))}
                  ${detailLine("Bid Size", number(row.bid_size, 0))}
                  ${detailLine("Ask Size", number(row.ask_size, 0))}
                  ${detailLine("Spread", pct(row.spread_pct))}
                  ${detailLine("Buffer", pct(row.breakeven_buffer))}
                  ${detailLine("Buffer / EM", `${number(row.buffer_em_ratio)}x`)}
                </section>
                <section>
                  <h4>估值</h4>
                  ${detailLine("权利金", quoteMoney(row.target_credit))}
                  ${detailLine("BS", money(row.bs_put_price))}
                  ${detailLine("权/BS", pct(row.premium_vs_bs_pct), Number(row.premium_vs_bs_pct) > 0 ? "value-up" : "")}
                  ${detailLine("Expected Move", money(row.expected_move))}
                  ${detailLine("Break-even", money(row.breakeven))}
                  ${detailLine("Quote Time", time(row.quote_time))}
                </section>
              </div>
            </td>
          </tr>` : ""}`;
      }
    )
    .join("");
}

function renderKpis() {
  const summary = payload?.summary || {};
  const rate = summary.analyzableContractRate ?? summary.validQuoteRate ?? 0;
  els.kpiUnderlyings.textContent = number(summary.underlyings, 0);
  els.kpiScope.textContent = `${dataSource.toUpperCase()} / ${scanTickers().join(", ") || "--"}`;
  els.kpiContracts.textContent = number(summary.contracts, 0);
  els.kpiValid.textContent = `${number(summary.validContracts, 0)} 可分析`;
  els.kpiRate.textContent = pct(rate);
  els.kpiRateBar.style.width = `${Math.max(0, Math.min(100, Number(rate || 0) * 100))}%`;
  els.kpiBestPer.textContent = number(summary.bestMonthlyScore);
  els.kpiIv.textContent = pct(summary.medianIv);
  els.kpiSpread.textContent = `Spread ${pct(summary.medianSpread)}`;
  els.kpiRefresh.textContent = time(summary.lastRefresh);
  els.kpiMode.textContent = `${summary.refreshMode || "--"} / ${summary.elapsedSeconds ?? "--"}s`;
}

function renderProgress() {
  if (!progress || (!progress.active && progress.stage === "idle")) {
    els.scanProgress?.classList.add("hidden");
    return;
  }
  els.scanProgress?.classList.remove("hidden");
  const total = Number(progress.total || scanTickers().length || 0);
  const completed = Number(progress.completed || 0);
  const pctValue = total > 0 ? Math.max(0, Math.min(1, completed / total)) : 0;
  els.progressMessage.textContent = `${progress.currentTicker || "--"} / ${progress.stage || "queued"} · ${progress.message || "等待扫描"}`;
  els.progressMeta.textContent =
    `${number(completed, 0)} / ${number(total, 0)} · 合约 ${number(progress.contracts || 0, 0)} · 报价 ${number(progress.quotesWithBidAsk || 0, 0)} / ${number(progress.quoteRequests || 0, 0)} · Greeks ${number(progress.quotesWithGreeks || 0, 0)} / ${number(progress.quoteRequests || 0, 0)}`;
  els.progressBar.style.width = `${pctValue * 100}%`;
  const events = progress.events || [];
  const errors = (progress.errors || []).map((message) => ({ message }));
  const items = [...events.slice(-6), ...errors.slice(-3)];
  els.progressEvents.innerHTML = items
    .map((item) => `<span>${escapeHtml(item.time ? `${time(item.time)} · ` : "")}${escapeHtml(item.message || item.stage || "")}</span>`)
    .join("");
}

function selectedRow() {
  const rows = visibleRows();
  return rows.find((row) => row.ticker === selectedTicker) || rows[0];
}

function selectedOption(row) {
  const options = optionRowsForUnderlying(row, 10);
  return options.find((option) => option.option_ticker === selectedOptionTicker) || options[0] || row;
}

function renderDetail() {
  const row = selectedRow();
  if (!row) {
    els.optionDetail.classList.add("hidden");
    els.optionDetail.innerHTML = "";
    return;
  }
  const option = selectedOption(row);
  els.optionDetail.classList.remove("hidden");
  els.optionDetail.innerHTML = `
    <div class="detail-heading">
      <div>
        <strong>${escapeHtml(row.ticker)}</strong>
        <span>${number(row.contractsScanned, 0)} contracts / ${number(row.validContracts, 0)} valid</span>
      </div>
      <select id="optionSelect" class="terminal-select">
        ${optionRowsForUnderlying(row, 10)
          .map(
            (item) => `
              <option value="${escapeHtml(item.option_ticker)}" ${item.option_ticker === option.option_ticker ? "selected" : ""}>
                ${escapeHtml(item.expiry)} P${money(item.strike)} / ${escapeHtml(item.dte_bucket || "--")} / Cycle ${number(item.cycle_put_edge_ratio)} / Monthly ${number(item.monthly_score)} / PER ${number(item.put_edge_ratio)}
              </option>`
          )
          .join("")}
      </select>
    </div>
    <div class="detail-metrics">
      <article title="Cycle PER = 到期收益 / |Delta| × min(Buffer / Expected Move, 2)。"><span>Cycle PER</span><strong class="edge">${number(option.cycle_put_edge_ratio)}</strong></article>
      <article title="月度偏好的综合分，默认按它排序。"><span>月度分</span><strong class="edge">${number(option.monthly_score)}</strong></article>
      <article title="同一期限桶内的 Cycle PER 百分位排名。"><span>桶排名</span><strong>${pct(option.bucket_rank ?? option.put_edge_rank)}</strong></article>
      <article><span>PER</span><strong>${number(option.put_edge_ratio)}</strong></article>
      <article title="到期收益 = 目标权利金 / 行权价；表示这一单持有到到期且期权归零时，本周期相对行权价的收益。"><span>到期收益</span><strong class="edge">${pct(expiryYield(option))}</strong></article>
      <article><span>天数</span><strong>${number(option.dte, 0)}</strong></article>
    </div>
    <div class="detail-grid">
      <section>
        <span>Contract</span>
        <p class="mono">${escapeHtml(option.option_ticker)}</p>
        <p>Break-even ${money(option.breakeven)} / Buffer ${pct(option.breakeven_buffer)}</p>
        <p>Expected Move ${money(option.expected_move)} / 到期收益 ${pct(expiryYield(option))} / 天数 ${number(option.dte, 0)}</p>
      </section>
      <section>
        <span>Risk Flags</span>
        <div class="badge-row">${String(option.risk_flags || "--").split(",").map((flag) => badge(flag.trim())).join("")}</div>
      </section>
      <section>
        <span>Stress</span>
        <p class="mono">10% ${money(option.stress_down_10pct)} / 20% ${money(option.stress_down_20pct)}</p>
        <p class="mono">30% ${money(option.stress_down_30pct)} / 1σ ${money(option.stress_1sigma)} / 2σ ${money(option.stress_2sigma)}</p>
      </section>
    </div>`;
}

function render() {
  renderWatchlists();
  renderKpis();
  renderProgress();
  renderExpiryFilter();
  renderTable();
  renderDetail();
}

function createList() {
  const name = prompt("新自选列表名称");
  if (!name) return;
  watchlists = { active: name, lists: { ...watchlists.lists, [name]: [] } };
  payload = { summary: {}, underlyings: [] };
  selectedTicker = "";
  selectedOptionTicker = "";
  expandedOptionKey = "";
  saveWatchlists();
  render();
}

function deleteList() {
  const names = Object.keys(watchlists.lists);
  if (names.length <= 1) return;
  const next = { ...watchlists.lists };
  delete next[watchlists.active];
  watchlists = { active: Object.keys(next)[0], lists: next };
  payload = null;
  selectedTicker = "";
  selectedOptionTicker = "";
  expandedOptionKey = "";
  saveWatchlists();
  render();
  refresh("quick");
}

async function searchTickers(query) {
  if (!query.trim()) {
    suggestions = [];
    highlightedSuggestionIndex = -1;
    renderSuggestions();
    return;
  }
  const data = await api(`/api/options/tickers?q=${encodeURIComponent(query.trim())}`);
  suggestions = data.results || [];
  highlightedSuggestionIndex = suggestions.length ? 0 : -1;
  renderSuggestions();
}

let searchTimer = null;
els.tickerSearch.addEventListener("input", (event) => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    searchTickers(event.target.value).catch(() => {
      suggestions = [];
      renderSuggestions();
    });
  }, 240);
});

els.tickerSearch.addEventListener("keydown", (event) => {
  if (!suggestions.length) return;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    highlightedSuggestionIndex = (highlightedSuggestionIndex + 1) % suggestions.length;
    renderSuggestions();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    highlightedSuggestionIndex =
      highlightedSuggestionIndex <= 0 ? suggestions.length - 1 : highlightedSuggestionIndex - 1;
    renderSuggestions();
  } else if (event.key === "Enter") {
    event.preventDefault();
    addTicker(suggestions[highlightedSuggestionIndex >= 0 ? highlightedSuggestionIndex : 0]);
  } else if (event.key === "Escape") {
    suggestions = [];
    highlightedSuggestionIndex = -1;
    renderSuggestions();
  }
});

els.tickerSuggestions.addEventListener("mouseover", (event) => {
  const button = event.target.closest("button[data-suggestion-index]");
  if (!button) return;
  highlightedSuggestionIndex = Number(button.dataset.suggestionIndex);
  renderSuggestions();
});

els.tickerSuggestions.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-suggestion-index]");
  if (!button) return;
  addTicker(suggestions[Number(button.dataset.suggestionIndex)]);
});

els.tickerChips.addEventListener("click", (event) => {
  const remove = event.target.closest("[data-remove-ticker]");
  if (remove) {
    event.stopPropagation();
    removeTicker(remove.dataset.removeTicker);
    render();
    return;
  }
  const row = event.target.closest("[data-watch-ticker]");
  if (!row) return;
  selectedTicker = row.dataset.watchTicker;
  selectedOptionTicker = "";
  renderWatchlists();
  renderTable();
  renderDetail();
});

els.watchlistSelect.addEventListener("change", (event) => {
  watchlists.active = event.target.value;
  payload = null;
  selectedTicker = "";
  selectedOptionTicker = "";
  expandedOptionKey = "";
  progress = null;
  saveWatchlists();
  render();
  refresh("quick");
});
els.watchlistTabs?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-watchlist-tab]");
  if (!button || button.dataset.watchlistTab === watchlists.active) return;
  watchlists.active = button.dataset.watchlistTab;
  payload = null;
  selectedTicker = "";
  selectedOptionTicker = "";
  expandedOptionKey = "";
  progress = null;
  saveWatchlists();
  render();
  refresh("quick");
});
if (els.dataSourceSelect) {
  els.dataSourceSelect.addEventListener("change", (event) => {
    const nextSource = event.target.value === "ibkr" ? "ibkr" : "massive";
    if (nextSource === dataSource) return;
    dataSource = nextSource;
    localStorage.setItem(SOURCE_KEY, dataSource);
    payload = null;
    selectedTicker = "";
    selectedOptionTicker = "";
    expandedOptionKey = "";
    progress = null;
    render();
    refresh("quick");
  });
}
els.newListBtn.addEventListener("click", createList);
els.deleteListBtn.addEventListener("click", deleteList);
els.quickRefreshBtn.addEventListener("click", () => refresh("quick"));
els.fullScanBtn.addEventListener("click", () => refresh("full"));
els.validFilter.addEventListener("change", (event) => {
  filterMode = event.target.value;
  renderTable();
});
els.dteFilter?.addEventListener("change", (event) => {
  expiryFilter = event.target.value;
  selectedOptionTicker = "";
  expandedOptionKey = "";
  renderTable();
  renderDetail();
});
els.tableSearch.addEventListener("input", (event) => {
  tableQuery = event.target.value;
  renderTable();
});
els.tableHead.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-sort-key]");
  if (!button) return;
  toggleSort(button.dataset.sortKey);
});
els.tableBody.addEventListener("click", (event) => {
  const childOption = event.target.closest("tr[data-child-option]");
  if (childOption) {
    selectedTicker = childOption.dataset.childTicker || selectedTicker;
    selectedOptionTicker = childOption.dataset.childOption || "";
    renderTable();
    renderDetail();
    return;
  }
  const expandButton = event.target.closest("button[data-expand-option]");
  if (expandButton) {
    expandedOptionKey = expandedOptionKey === expandButton.dataset.expandOption ? "" : expandButton.dataset.expandOption;
    renderTable();
    return;
  }
  const row = event.target.closest("tr[data-row-ticker]");
  if (!row) return;
  selectedTicker = row.dataset.rowTicker;
  selectedOptionTicker = "";
  renderTable();
  renderDetail();
});
els.optionDetail.addEventListener("change", (event) => {
  if (event.target.id !== "optionSelect") return;
  selectedOptionTicker = event.target.value;
  renderDetail();
});

render();
syncAccountStatus();
refresh("quick");
