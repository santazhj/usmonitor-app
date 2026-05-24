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
const dashboardMetrics = document.querySelector("#dashboardMetrics");
const categoryTabs = document.querySelector("#categoryTabs");
const dashboardRows = document.querySelector("#dashboardRows");
const sourceStatus = document.querySelector("#sourceStatus");
const dataStatus = document.querySelector("#dataStatus");
const lastUpdated = document.querySelector("#lastUpdated");
const refreshLabel = document.querySelector("#refreshLabel");

let appConfig = {};
let dashboardSnapshot = null;
let selectedCategory = "all";

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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showSignedOut() {
  authView.classList.remove("hidden");
  memberView.classList.add("hidden");
  logoutBtn.classList.add("hidden");
  adminLink.classList.add("hidden");
}

function showSignedIn(me) {
  authView.classList.add("hidden");
  memberView.classList.remove("hidden");
  logoutBtn.classList.remove("hidden");
  adminLink.classList.toggle("hidden", !me.is_admin);
}

function moneyAddress(value) {
  return value
    ? `<code>${escapeHtml(value)}</code>`
    : `<span class="muted">未配置</span>`;
}

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleString("zh-Hans", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
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

function renderDashboard() {
  const snapshot = dashboardSnapshot;
  if (!snapshot) return;

  refreshLabel.textContent = `${snapshot.refresh_interval_seconds}s refresh target`;
  dataStatus.textContent = snapshot.data_status_label;
  lastUpdated.textContent = `Updated ${formatDate(snapshot.generated_at)}`;

  dashboardMetrics.innerHTML = [
    ["Tracked", snapshot.metrics.tracked_tickers],
    ["Categories", snapshot.metrics.categories],
    ["Live Prices", snapshot.metrics.live_prices],
    ["Alert Sources", snapshot.metrics.alert_sources]
  ]
    .map(
      ([label, value]) => `
        <article>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>`
    )
    .join("");

  const tabs = [
    { slug: "all", label: "All", count: snapshot.rows.length },
    ...snapshot.categories
  ];
  categoryTabs.innerHTML = tabs
    .map(
      (tab) => `
        <button class="${tab.slug === selectedCategory ? "active" : ""}"
          data-category="${escapeHtml(tab.slug)}" type="button">
          <span>${escapeHtml(tab.label)}</span>
          <small>${escapeHtml(tab.count)}</small>
        </button>`
    )
    .join("");

  const rows =
    selectedCategory === "all"
      ? snapshot.rows
      : snapshot.rows.filter((row) => row.category === selectedCategory);

  dashboardRows.innerHTML = rows
    .map(
      (row) => `
        <article class="market-row">
          <div class="ticker-cell">
            <strong>${escapeHtml(row.ticker)}</strong>
            <span>${escapeHtml(row.company)}</span>
          </div>
          <span class="pending-cell">待接入</span>
          <span class="pending-cell">--</span>
          <span class="pending-cell">--</span>
          <span class="pending-cell">--</span>
          <span class="pending-cell">--</span>
          <span class="pending-cell">--</span>
          <span>${escapeHtml(row.role)}</span>
          <span>${escapeHtml(row.latest_signal)}</span>
        </article>`
    )
    .join("");

  sourceStatus.innerHTML = snapshot.source_status
    .map(
      (source) => `
        <article class="source-item ${escapeHtml(source.status)}">
          <div>
            <strong>${escapeHtml(source.name)}</strong>
            <span>${escapeHtml(source.detail)}</span>
          </div>
          <mark>${escapeHtml(source.status)}</mark>
        </article>`
    )
    .join("");
}

async function loadApp(existingMe) {
  appConfig = await api("/api/config");
  const me = existingMe || (await api("/api/me"));
  showSignedIn(me);
  accountEmail.textContent = me.email;

  const expires = me.subscription.expires_at
    ? new Date(me.subscription.expires_at).toLocaleString("zh-Hans")
    : "等待开通";
  subscriptionState.innerHTML = me.subscription.active
    ? `<strong>已开通</strong><span>${escapeHtml(expires)}</span>`
    : `<strong>待付款</strong><span>${escapeHtml(expires)}</span>`;

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
            <span>${escapeHtml(item.description)}</span>
          </div>
          <mark>${item.subscription_active ? "Active" : "Locked"}</mark>
        </article>`
    )
    .join("");
}

async function loadPayment() {
  const payment = await api("/api/payments/current");
  if (payment.admin_bypass) {
    paymentBox.innerHTML = `
      <p class="status-line">管理员访问已开通，无需付款。</p>
      <dl>
        <div><dt>TRC20</dt><dd>${moneyAddress(payment.trc20_address)}</dd></div>
        <div><dt>ERC20</dt><dd>${moneyAddress(payment.erc20_address)}</dd></div>
      </dl>`;
    return;
  }
  paymentBox.innerHTML = `
    <dl>
      <div><dt>金额</dt><dd>${escapeHtml(payment.amount_usdt)} USDT / 月</dd></div>
      <div><dt>备注码</dt><dd><code>${escapeHtml(payment.payment_code)}</code></dd></div>
      <div><dt>TRC20</dt><dd>${moneyAddress(payment.trc20_address)}</dd></div>
      <div><dt>ERC20</dt><dd>${moneyAddress(payment.erc20_address)}</dd></div>
    </dl>`;
}

async function loadFeed() {
  const feed = await api("/api/feed");
  if (!feed.length) {
    feedBox.innerHTML = `<p class="empty">暂无提醒。</p>`;
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
            查看原帖
          </a>
          <small>${escapeHtml(item.disclaimer)}</small>
        </article>`
    )
    .join("");
}

function updatePushStatus() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    pushStatus.textContent = "当前浏览器不支持 Web Push。";
    return;
  }
  const installed =
    window.navigator.standalone === true ||
    window.matchMedia("(display-mode: standalone)").matches;
  pushStatus.textContent = installed
    ? "已在主屏幕模式运行，可以授权通知。"
    : "iPhone 需要先添加到主屏幕，再授权通知。";
}

async function enablePush() {
  if (!appConfig.vapid_public_key) {
    pushStatus.textContent = "VAPID 公钥未配置。";
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    pushStatus.textContent = "通知权限未开启。";
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
  pushStatus.textContent = "推送已开启。";
}

categoryTabs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-category]");
  if (!button) return;
  selectedCategory = button.dataset.category;
  renderDashboard();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  loginMessage.textContent = "发送中...";
  try {
    const result = await api("/api/auth/request", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(form.entries()))
    });
    loginMessage.innerHTML = result.dev_magic_link
      ? `开发模式链接：<a href="${escapeHtml(result.dev_magic_link)}">打开登录</a>`
      : "登录链接已发送。";
  } catch {
    loginMessage.textContent = "登录失败，请检查邮箱或邀请码。";
  }
});

enablePushBtn.addEventListener("click", enablePush);
testPushBtn.addEventListener("click", async () => {
  pushStatus.textContent = "发送测试中...";
  const result = await api("/api/push/test", { method: "POST" });
  pushStatus.textContent = `测试完成，${result.sent} 成功，${result.failed} 失败。`;
});
logoutBtn.addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  location.reload();
});

loadDashboard().catch(() => {
  dataStatus.textContent = "Dashboard unavailable";
});

api("/api/me")
  .then(loadApp)
  .catch(() => showSignedOut());
