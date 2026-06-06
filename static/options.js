const DEFAULT_TICKERS = [
  "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "AMD", "NFLX",
  "ORCL", "CRM", "ADBE", "QCOM", "INTC", "MU", "ARM", "PLTR", "PANW", "CRWD",
  "TSM", "ASML", "AMAT", "LRCX", "MRVL", "SMCI", "SNOW", "SHOP", "NOW", "APP"
];

const WATCHLIST_KEY = "usmonitor.options.watchlists";

const els = {
  quickRefreshBtn: document.querySelector("#quickRefreshBtn"),
  fullScanBtn: document.querySelector("#fullScanBtn"),
  watchlistSelect: document.querySelector("#watchlistSelect"),
  newListBtn: document.querySelector("#newListBtn"),
  deleteListBtn: document.querySelector("#deleteListBtn"),
  tickerSearch: document.querySelector("#tickerSearch"),
  tickerSuggestions: document.querySelector("#tickerSuggestions"),
  tickerChips: document.querySelector("#tickerChips"),
  tableSearch: document.querySelector("#tableSearch"),
  validFilter: document.querySelector("#validFilter"),
  tableStatus: document.querySelector("#tableStatus"),
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
  { label: "标的", key: "ticker" },
  { label: "合约" },
  { label: "性价" },
  { label: "PER", key: "put_edge_ratio" },
  { label: "质量", key: "score" },
  { label: "现价", key: "spot" },
  { label: "Bid / Ask", key: "bid" },
  { label: "权利金", key: "target_credit" },
  { label: "BS", key: "bs_put_price", title: "Black-Scholes 理论价" },
  { label: "权/BS", key: "premium_vs_bs_pct", title: "目标权利金相对 Black-Scholes 理论价的溢价/折价；正数代表市场权利金高于模型价。" },
  { label: "年化", key: "ann_yield_bid" },
  { label: "Delta", key: "delta" },
  { label: "IV", key: "iv" },
  { label: "OI", key: "open_interest" },
  { label: "Spr", key: "spread_pct" },
  { label: "Buffer", key: "breakeven_buffer" },
  { label: "报价" }
];

let watchlists = loadWatchlists();
let payload = null;
let selectedTicker = "";
let selectedOptionTicker = "";
let filterMode = "all";
let tableQuery = "";
let suggestions = [];
let highlightedSuggestionIndex = -1;
let sortConfig = { key: "put_edge_ratio", direction: "desc" };

function loadWatchlists() {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore malformed local state
  }
  return { active: "AI Core", lists: { "AI Core": DEFAULT_TICKERS } };
}

function saveWatchlists() {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlists));
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
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
}

function money(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  const digits = Math.abs(numeric) >= 1000 ? 0 : 2;
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
}

function pct(value, digits = 1) {
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
    Liquidity: "流动性",
    "Data Gap": "缺数",
    Event: "事件",
    "极高性价比": "极高",
    "好性价比": "良好",
    "可观察": "观察",
    "旧报价": "旧",
    "数据不足": "缺数",
    "流动性陷阱": "流动性",
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

function compactContract(row) {
  const expiry = row.expiry || row.expiration || "";
  const strike = money(row.strike).replace(/\.00$/, "");
  if (expiry && Number.isFinite(Number(row.strike))) return `${expiry.slice(5)} P${strike}`;
  return String(row.topContract || "--").replace(/^\d{4}-/, "");
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

function setLoading(mode, loading) {
  const button = mode === "full" ? els.fullScanBtn : els.quickRefreshBtn;
  button.disabled = loading;
  button.textContent =
    mode === "full"
      ? loading ? "完整扫描中" : "完整扫描"
      : loading ? "刷新中" : "快速刷新";
  if (mode === "full") els.quickRefreshBtn.disabled = loading;
  if (mode === "quick") els.fullScanBtn.disabled = loading;
}

async function api(path) {
  const response = await fetch(path);
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || "Request failed");
  return data;
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
  try {
    payload = await api(
      `/api/options/scan?tickers=${encodeURIComponent(tickers.join(","))}&mode=${encodeURIComponent(mode)}&allowInitialFull=false`
    );
    if (!payload.underlyings.some((row) => row.ticker === selectedTicker)) {
      selectedTicker = payload.underlyings[0]?.ticker || "";
      selectedOptionTicker = "";
    }
    if (mode === "full") selectedOptionTicker = "";
    render();
  } catch (error) {
    els.tableStatus.textContent = `扫描失败: ${error.message}`;
  } finally {
    setLoading(mode, false);
  }
}

function renderWatchlists() {
  const names = Object.keys(watchlists.lists);
  els.watchlistSelect.innerHTML = names
    .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
    .join("");
  els.watchlistSelect.value = watchlists.active;

  els.tickerChips.innerHTML = activeTickers()
    .map(
      (ticker) => `
        <span class="ticker-chip">
          ${escapeHtml(ticker)}
          <button type="button" data-remove-ticker="${escapeHtml(ticker)}">x</button>
        </span>`
    )
    .join("");
  els.kpiScope.textContent = scanTickers().join(", ") || "--";
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
  if (key === "ticker") return row.ticker || "";
  const value = row[key];
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function visibleRows() {
  const activeSet = new Set(scanTickers());
  let rows = (payload?.underlyings || []).filter((row) => activeSet.has(String(row.ticker || "").toUpperCase()));
  if (filterMode === "valid") rows = rows.filter((row) => row.platform_valid !== false);
  const query = tableQuery.trim().toUpperCase();
  if (query) {
    rows = rows.filter((row) =>
      `${row.ticker} ${row.option_ticker} ${row.risk_flags || ""}`.toUpperCase().includes(query)
    );
  }
  if (!sortConfig.key) return rows;
  const direction = sortConfig.direction === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const av = sortValue(a, sortConfig.key);
    const bv = sortValue(b, sortConfig.key);
    if (sortConfig.key === "ticker") {
      return direction * String(av).localeCompare(String(bv));
    }
    if (av === null && bv === null) return String(a.ticker).localeCompare(String(b.ticker));
    if (av === null) return 1;
    if (bv === null) return -1;
    if (av === bv) return String(a.ticker).localeCompare(String(b.ticker));
    return av > bv ? direction : -direction;
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
          <button class="option-sort ${active}" data-sort-key="${escapeHtml(column.key)}" type="button">
            ${escapeHtml(column.label)} <span>${arrow}</span>
          </button>
        </th>`;
    })
    .join("");
}

function renderTable() {
  renderHead();
  const rows = visibleRows();
  els.tableStatus.textContent = payload
    ? `显示 ${rows.length}/${payload.underlyings.length} 个标的`
    : "等待扫描";
  if (!rows.length) {
    const message = payload?.summary?.fullScanRequired
      ? "当前列表还没有完整扫描缓存。点击“完整扫描”后，后续快速刷新会很快。"
      : "暂无数据。点完整扫描开始。";
    els.tableBody.innerHTML = `<tr><td colspan="${columns.length}" class="empty-table">${message}</td></tr>`;
    return;
  }
  els.tableBody.innerHTML = rows
    .map(
      (row) => `
        <tr class="${row.ticker === selectedTicker ? "selected" : ""}" data-row-ticker="${escapeHtml(row.ticker)}">
          <td class="mono strong">${escapeHtml(row.ticker)}</td>
          <td>${badge(compactContract(row), "sky", row.topContract)}</td>
          <td>${badge(compactEdge(row.edge_flag), edgeTone(row.edge_flag), row.edge_flag)}</td>
          <td class="mono edge">${number(row.put_edge_ratio)}</td>
          <td class="mono">${number(row.score)}</td>
          <td class="mono">${money(row.spot)}</td>
          <td class="mono">${money(row.bid)} / ${money(row.ask)}</td>
          <td class="mono">${money(row.target_credit)}</td>
          <td class="mono">${money(row.bs_put_price)}</td>
          <td class="mono ${Number(row.premium_vs_bs_pct) > 0 ? "value-up" : ""}">${pct(row.premium_vs_bs_pct)}</td>
          <td class="mono">${pct(row.ann_yield_bid)}</td>
          <td class="mono">${pct(row.delta)}</td>
          <td class="mono">${pct(row.iv)}</td>
          <td class="mono">${number(row.open_interest, 0)}</td>
          <td class="mono">${pct(row.spread_pct)}</td>
          <td class="mono">${pct(row.breakeven_buffer)}</td>
          <td>${badge(compactQuote(row.quote_mode), row.quote_mode === "Live" ? "green" : "amber", row.quote_mode)}</td>
        </tr>`
    )
    .join("");
}

function renderKpis() {
  const summary = payload?.summary || {};
  const rate = summary.analyzableContractRate ?? summary.validQuoteRate ?? 0;
  els.kpiUnderlyings.textContent = number(summary.underlyings, 0);
  els.kpiScope.textContent = scanTickers().join(", ") || "--";
  els.kpiContracts.textContent = number(summary.contracts, 0);
  els.kpiValid.textContent = `${number(summary.validContracts, 0)} 可分析`;
  els.kpiRate.textContent = pct(rate);
  els.kpiRateBar.style.width = `${Math.max(0, Math.min(100, Number(rate || 0) * 100))}%`;
  els.kpiBestPer.textContent = number(summary.bestPer);
  els.kpiIv.textContent = pct(summary.medianIv);
  els.kpiSpread.textContent = `Spread ${pct(summary.medianSpread)}`;
  els.kpiRefresh.textContent = time(summary.lastRefresh);
  els.kpiMode.textContent = `${summary.refreshMode || "--"} / ${summary.elapsedSeconds ?? "--"}s`;
}

function selectedRow() {
  return (payload?.underlyings || []).find((row) => row.ticker === selectedTicker) || payload?.underlyings?.[0];
}

function selectedOption(row) {
  const options = row?.topOptions || [];
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
        ${(row.topOptions || [])
          .map(
            (item) => `
              <option value="${escapeHtml(item.option_ticker)}" ${item.option_ticker === option.option_ticker ? "selected" : ""}>
                ${escapeHtml(item.expiry)} P${money(item.strike)} / PER ${number(item.put_edge_ratio)} / ${money(item.bid)}-${money(item.ask)} / BS ${money(item.bs_put_price)}
              </option>`
          )
          .join("")}
      </select>
    </div>
    <div class="detail-metrics">
      <article><span>PER</span><strong class="edge">${number(option.put_edge_ratio)}</strong></article>
      <article><span>BS Price</span><strong>${money(option.bs_put_price)}</strong></article>
      <article title="目标权利金相对 Black-Scholes 理论价的溢价/折价；正数代表市场权利金高于模型价。"><span>权利金/BS</span><strong>${pct(option.premium_vs_bs_pct)}</strong></article>
      <article><span>Buffer / EM</span><strong>${number(option.buffer_em_ratio)}x</strong></article>
    </div>
    <div class="detail-grid">
      <section>
        <span>Contract</span>
        <p class="mono">${escapeHtml(option.option_ticker)}</p>
        <p>Break-even ${money(option.breakeven)} / Buffer ${pct(option.breakeven_buffer)}</p>
        <p>Expected Move ${money(option.expected_move)} / Delta ${pct(option.delta)} / IV ${pct(option.iv)}</p>
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
  const button = event.target.closest("button[data-remove-ticker]");
  if (!button) return;
  removeTicker(button.dataset.removeTicker);
});

els.watchlistSelect.addEventListener("change", (event) => {
  watchlists.active = event.target.value;
  payload = null;
  selectedTicker = "";
  selectedOptionTicker = "";
  saveWatchlists();
  render();
  refresh("quick");
});
els.newListBtn.addEventListener("click", createList);
els.deleteListBtn.addEventListener("click", deleteList);
els.quickRefreshBtn.addEventListener("click", () => refresh("quick"));
els.fullScanBtn.addEventListener("click", () => refresh("full"));
els.validFilter.addEventListener("change", (event) => {
  filterMode = event.target.value;
  renderTable();
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
refresh("quick");
