const accessGate = document.querySelector("#accessGate");
const accessMessage = document.querySelector("#accessMessage");
const accessAction = document.querySelector("#accessAction");
const adminContent = document.querySelector("#adminContent");
const adminSession = document.querySelector("#adminSession");
const adminMessage = document.querySelector("#adminMessage");
const countsBox = document.querySelector("#countsBox");
const usersBox = document.querySelector("#usersBox");
const pageStatsBox = document.querySelector("#pageStatsBox");
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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-Hans", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds || 0));
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  }
  if (minutes > 0) return `${minutes}m ${rest}s`;
  return `${rest}s`;
}

function countLabel(key) {
  return (
    {
      users: "用户",
      active_members: "会员",
      page_views: "浏览量",
      avg_stay_seconds: "平均停留",
      push_subscriptions: "推送设备",
      summaries: "提醒摘要",
      deliveries: "推送记录"
    }[key] || key
  );
}

function countValue(key, value) {
  return key === "avg_stay_seconds" ? formatDuration(value) : value;
}

async function loadOverview() {
  const data = await api("/api/admin/overview");
  countsBox.innerHTML = Object.entries(data.counts)
    .map(([key, value]) => row(countLabel(key), countValue(key, value)))
    .join("");

  usersBox.innerHTML = `
    <div class="admin-row user-row admin-table-head">
      <span>用户</span>
      <span>会员</span>
      <span>浏览量</span>
      <span>停留</span>
      <span>最近访问</span>
      <span>开关</span>
    </div>
    ${data.users
      .map((item) => {
        const memberLabel = item.is_admin
          ? "Owner"
          : item.subscription_active
            ? "会员"
            : "免费版";
        const expires = item.subscription_expires_at
          ? `至 ${formatDate(item.subscription_expires_at)}`
          : item.is_admin
            ? "管理员旁路"
            : "未开通";
        return `
          <article class="admin-row user-row">
            <span>
              <strong>${escapeHtml(item.email)}</strong>
              <small>注册 ${formatDate(item.created_at)}</small>
            </span>
            <span>
              <mark class="${item.subscription_active ? "success" : "neutral"}">${memberLabel}</mark>
              <small>${escapeHtml(expires)}</small>
            </span>
            <span>${item.page_views}</span>
            <span>${formatDuration(item.total_seconds)}</span>
            <span>${formatDate(item.last_seen_at || item.last_login_at)}</span>
            <span>
              <label class="switch-control" title="开通或关闭高级会员">
                <input
                  type="checkbox"
                  data-membership="${item.id}"
                  ${item.subscription_active ? "checked" : ""}
                  ${item.is_admin ? "disabled" : ""}
                />
                <i></i>
              </label>
            </span>
          </article>`;
      })
      .join("")}`;

  pageStatsBox.innerHTML = data.page_stats.length
    ? `
      <div class="admin-row page-row admin-table-head">
        <span>页面</span>
        <span>浏览量</span>
        <span>总停留</span>
      </div>
      ${data.page_stats
        .map(
          (item) => `
          <article class="admin-row page-row">
            <span><code>${escapeHtml(item.path)}</code></span>
            <span>${item.page_views}</span>
            <span>${formatDuration(item.total_seconds)}</span>
          </article>`
        )
        .join("")}`
    : `<p class="empty">暂无浏览数据。</p>`;

  paymentsBox.innerHTML = data.pending_payments.length
    ? data.pending_payments
        .map(
          (item) => `
          <article class="table-row">
            <span>${escapeHtml(item.email)}</span>
            <span>${item.amount_usdt} USDT</span>
            <code>${escapeHtml(item.payment_code)}</code>
            <button data-payment="${item.id}" class="secondary">确认</button>
          </article>`
        )
        .join("")
    : `<p class="empty">暂无待确认付款。</p>`;

  sourcesBox.innerHTML = data.sources
    .map(
      (item) => `
        <article class="table-row">
          <span>@${escapeHtml(item.handle)}</span>
          <span>${escapeHtml(item.external_id || "no id")}</span>
          <code>${escapeHtml(item.last_seen_post_id || "new")}</code>
          <mark>${item.is_active ? "Active" : "Paused"}</mark>
        </article>`
    )
    .join("");

  jobsBox.innerHTML = data.jobs
    .map(
      (item) => `
        <article class="table-row">
          <span>${escapeHtml(item.job_name)}</span>
          <mark>${escapeHtml(item.status)}</mark>
          <span>${escapeHtml(item.message || "-")}</span>
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

  usersBox.querySelectorAll("[data-membership]").forEach((input) => {
    input.addEventListener("change", async () => {
      input.disabled = true;
      try {
        const result = await api(`/api/admin/users/${input.dataset.membership}/membership`, {
          method: "POST",
          body: JSON.stringify({ active: input.checked, months: 1 })
        });
        adminMessage.textContent = result.active
          ? "会员已开通或续期 1 个月。"
          : "会员已关闭。";
      } catch (error) {
        input.checked = !input.checked;
        adminMessage.textContent = "会员状态更新失败。";
      } finally {
        await loadOverview();
      }
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
