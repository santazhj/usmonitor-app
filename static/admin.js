const accessGate = document.querySelector("#accessGate");
const accessMessage = document.querySelector("#accessMessage");
const accessAction = document.querySelector("#accessAction");
const adminContent = document.querySelector("#adminContent");
const adminSession = document.querySelector("#adminSession");
const adminMessage = document.querySelector("#adminMessage");
const countsBox = document.querySelector("#countsBox");
const paymentsBox = document.querySelector("#paymentsBox");
const sourcesBox = document.querySelector("#sourcesBox");
const jobsBox = document.querySelector("#jobsBox");
const pollBtn = document.querySelector("#pollBtn");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "include",
    ...options
  });
  if (!response.ok) {
    const error = new Error(await response.text());
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

function setGate(title, message, actionText = "", actionHref = "/") {
  accessGate.querySelector("h2").textContent = title;
  accessMessage.textContent = message;
  accessAction.textContent = actionText;
  accessAction.href = actionHref;
  accessAction.classList.toggle("hidden", !actionText);
  accessGate.classList.remove("hidden");
  adminContent.classList.add("hidden");
  adminSession.classList.add("hidden");
}

function showAdmin(email) {
  accessGate.classList.add("hidden");
  adminContent.classList.remove("hidden");
  adminSession.textContent = email;
  adminSession.classList.remove("hidden");
}

function row(label, value) {
  return `<article><span>${label}</span><strong>${value}</strong></article>`;
}

async function loadOverview() {
  const data = await api("/api/admin/overview");
  countsBox.innerHTML = Object.entries(data.counts)
    .map(([key, value]) => row(key, value))
    .join("");

  paymentsBox.innerHTML = data.pending_payments.length
    ? data.pending_payments
        .map(
          (item) => `
          <article class="table-row">
            <span>${item.email}</span>
            <span>${item.amount_usdt} USDT</span>
            <code>${item.payment_code}</code>
            <button data-payment="${item.id}" class="secondary">确认</button>
          </article>`
        )
        .join("")
    : `<p class="empty">暂无待确认付款。</p>`;

  sourcesBox.innerHTML = data.sources
    .map(
      (item) => `
        <article class="table-row">
          <span>@${item.handle}</span>
          <span>${item.external_id || "no id"}</span>
          <code>${item.last_seen_post_id || "new"}</code>
          <mark>${item.is_active ? "Active" : "Paused"}</mark>
        </article>`
    )
    .join("");

  jobsBox.innerHTML = data.jobs
    .map(
      (item) => `
        <article class="table-row">
          <span>${item.job_name}</span>
          <mark>${item.status}</mark>
          <span>${item.message || "-"}</span>
          <time>${new Date(item.started_at).toLocaleString()}</time>
        </article>`
    )
    .join("");

  paymentsBox.querySelectorAll("[data-payment]").forEach((button) => {
    button.addEventListener("click", async () => {
      const txHash = prompt("TX hash / note") || "";
      await api(`/api/admin/payments/${button.dataset.payment}/confirm`, {
        method: "POST",
        body: JSON.stringify({ tx_hash: txHash, months: 1 })
      });
      adminMessage.textContent = "付款已确认。";
      await loadOverview();
    });
  });
}

pollBtn.addEventListener("click", async () => {
  adminMessage.textContent = "轮询中...";
  const result = await api("/api/admin/poll", { method: "POST" });
  adminMessage.textContent = `完成：${JSON.stringify(result)}`;
  await loadOverview();
});

async function initAdmin() {
  try {
    const me = await api("/api/me");
    if (!me.is_admin) {
      setGate(
        "没有管理员权限",
        `当前登录账号 ${me.email} 不是管理员。请退出后使用管理员邮箱登录。`,
        "回到 App",
        "/"
      );
      return;
    }
    showAdmin(me.email);
    await loadOverview();
  } catch (error) {
    const isAuthError = error.status === 401 || error.status === 403;
    setGate(
      "需要管理员登录",
      isAuthError
        ? "请先用管理员邮箱登录，再打开管理后台。"
        : "管理员权限校验失败，请稍后刷新重试。",
      isAuthError ? "回到 App 登录" : "",
      "/"
    );
  }
}

initAdmin();
