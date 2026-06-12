const els = {
  logoutBtn: document.querySelector("#logoutBtn"),
  adminLink: document.querySelector("#adminLink"),
  languageToggle: document.querySelector("#languageToggle"),
  dashboardMetrics: document.querySelector("#dashboardMetrics"),
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
  feed: [],
  user: null
};

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

function formatDateTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString(state.language === "zh" ? "zh-Hans" : "en-US", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function rowStatus(row) {
  if (!Number.isFinite(Number(row.price))) return { key: "missing", label: t("row.missing") };
  const updated = row.market_updated_at ? new Date(row.market_updated_at) : null;
  if (updated && Date.now() - updated.getTime() > 1000 * 60 * 60 * 36) {
    return { key: "stale", label: t("row.stale") };
  }
  return { key: "live", label: t("row.live") };
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
        row.latest_signal
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
          <span>${escapeHtml(item.label)}</span>
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
          <span>${escapeHtml(item.name)}</span>
          <strong>${escapeHtml(item.status || "pending")}</strong>
          <small>${escapeHtml(item.detail || "")}</small>
        </article>`
    )
    .join("");
}

function renderStatus() {
  const snapshot = state.dashboard;
  const status = snapshot?.data_status || "provider_pending";
  els.dataStatus.textContent = t(`status.${status}`) || snapshot?.data_status_label || status;
  els.lastUpdated.textContent = snapshot?.generated_at ? formatDateTime(snapshot.generated_at) : "--";
  els.refreshLabel.textContent = snapshot?.refresh_interval_seconds
    ? t("dashboard.refreshTarget", { seconds: snapshot.refresh_interval_seconds })
    : "--";
}

function renderTable() {
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
              <small>${escapeHtml(row.company || "")}</small>
            </div>
            <div class="number-cell">${escapeHtml(formatNumber(row.price, 2))}</div>
            <div class="number-cell ${tone}">${escapeHtml(formatPercent(row.change_percent))}</div>
            <div class="number-cell">${escapeHtml(formatCompact(row.dollar_volume, "$"))}</div>
            <div class="number-cell">${escapeHtml(formatCompact(row.market_cap, "$"))}</div>
            <div class="number-cell">${escapeHtml(row.pe_note || formatNumber(row.pe_ratio, 1))}</div>
            <div><span class="soft-badge">${escapeHtml(row.category_label || row.ai_layer || "--")}</span></div>
            <div class="role-cell">
              <strong>${escapeHtml(row.role || "--")}</strong>
              <small>${escapeHtml(row.latest_signal || "")}</small>
            </div>
            <div class="source-cell">
              <span class="data-badge ${escapeHtml(status.key)}">${escapeHtml(status.label)}</span>
              <small>${escapeHtml(row.market_provider || row.fundamentals_provider || "--")}</small>
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
  renderCategories();
  renderSources();
  renderTable();
  renderFeed();
}

function openDrawer(row) {
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
        <span class="eyebrow">${escapeHtml(row.category_label || row.ai_layer || "")}</span>
        <h2 id="drawerTitle">${escapeHtml(row.ticker)} <small>${escapeHtml(row.company || "")}</small></h2>
      </div>
      <span class="data-badge ${escapeHtml(status.key)}">${escapeHtml(status.label)}</span>
    </div>
    <div class="drawer-metrics terminal-drawer-grid">
      ${metricBlock(t("table.price"), formatNumber(row.price, 2))}
      ${metricBlock(t("table.change"), formatPercent(row.change_percent))}
      ${metricBlock(t("table.marketCap"), formatCompact(row.market_cap, "$"))}
      ${metricBlock(t("table.pe"), row.pe_note || formatNumber(row.pe_ratio, 1))}
      ${metricBlock(t("table.dollarVolume"), formatCompact(row.dollar_volume, "$"))}
      ${metricBlock(t("table.source"), row.market_provider || row.fundamentals_provider || "--")}
    </div>
    <section class="drawer-section">
      <h3>${escapeHtml(t("drawer.position"))}</h3>
      <p>${escapeHtml(row.role || "--")}</p>
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
    <section class="drawer-section drawer-actions">
      ${row.source_url ? `<a class="terminal-button" href="${escapeHtml(row.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(t("drawer.source"))}</a>` : `<span class="muted">${escapeHtml(t("drawer.noSource"))}</span>`}
      <span class="muted">${escapeHtml(formatDateTime(row.market_updated_at))}</span>
    </section>`;
  els.tickerDrawer.classList.remove("hidden");
  els.tickerDrawer.setAttribute("aria-hidden", "false");
}

function metricBlock(label, value) {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function closeDrawer() {
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
  } catch (error) {
    els.dataStatus.textContent = t("dashboard.loadFailed");
    els.tableStatus.textContent = error.message || t("dashboard.loadFailed");
  }
}

async function loadFeed() {
  try {
    state.feed = await api(`/api/feed?limit=40&lang=${encodeURIComponent(state.language)}`);
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

    const rowEl = event.target.closest(".terminal-data-row[data-ticker]");
    if (rowEl) {
      const row = (state.dashboard?.rows || []).find((item) => item.ticker === rowEl.dataset.ticker);
      if (row) openDrawer(row);
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
  await Promise.all([loadUser(), loadDashboard(), loadFeed()]);
  renderAll();
  const startedAt = Date.now();
  window.addEventListener("beforeunload", () => {
    sendAnalytics("heartbeat", (Date.now() - startedAt) / 1000);
  });
}

init();
