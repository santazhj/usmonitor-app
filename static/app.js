const authView = document.querySelector("#authView");
const appView = document.querySelector("#appView");
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

let appConfig = {};

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

function show(view) {
  authView.classList.toggle("hidden", view !== "auth");
  appView.classList.toggle("hidden", view !== "app");
}

function moneyAddress(value) {
  return value ? `<code>${value}</code>` : `<span class="muted">未配置</span>`;
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

async function loadApp() {
  appConfig = await api("/api/config");
  const me = await api("/api/me");
  show("app");
  accountEmail.textContent = me.email;
  adminLink.classList.toggle("hidden", !me.is_admin);
  logoutBtn.classList.remove("hidden");

  const expires = me.subscription.expires_at
    ? new Date(me.subscription.expires_at).toLocaleString()
    : "等待开通";
  subscriptionState.innerHTML = me.subscription.active
    ? `<strong>已开通</strong><span>${expires}</span>`
    : `<strong>待付款</strong><span>${expires}</span>`;

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
            <strong>${item.name}</strong>
            <span>${item.description}</span>
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
      <div><dt>金额</dt><dd>${payment.amount_usdt} USDT / 月</dd></div>
      <div><dt>备注码</dt><dd><code>${payment.payment_code}</code></dd></div>
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
        <article class="alert-card" id="alert-${item.id}">
          <header>
            <h3>${item.title}</h3>
            <time>${new Date(item.created_at).toLocaleString()}</time>
          </header>
          <p>${item.notification_text}</p>
          <ul>${item.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}</ul>
          <div class="ticker-row">${item.tickers.map((t) => `<span>${t}</span>`).join("")}</div>
          <p class="why">${item.why_it_matters}</p>
          <a href="${item.source_url}" target="_blank" rel="noreferrer">查看原帖</a>
          <small>${item.disclaimer}</small>
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
    ? "已在主屏幕模式运行。"
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
      ? `开发模式链接：<a href="${result.dev_magic_link}">打开登录</a>`
      : "登录链接已发送。";
  } catch (error) {
    loginMessage.textContent = "登录失败，请检查邮箱或邀请码。";
  }
});

enablePushBtn.addEventListener("click", enablePush);
testPushBtn.addEventListener("click", async () => {
  pushStatus.textContent = "发送测试中...";
  const result = await api("/api/push/test", { method: "POST" });
  pushStatus.textContent = `测试完成：${result.sent} 成功，${result.failed} 失败。`;
});
logoutBtn.addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  location.reload();
});

api("/api/me")
  .then(loadApp)
  .catch(() => show("auth"));
