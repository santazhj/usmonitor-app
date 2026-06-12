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
const refreshAdminBtn = document.querySelector("#refreshAdminBtn");

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
  if (minutes >= 60) return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
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
      summaries: "情报摘要",
      deliveries: "推送记录"
    }[key] || key
  );
}

function countValue(key, value) {
  return key === "avg_stay_seconds" ? formatDuration(value) : value;
}

function metricCard(label, value) {
  return `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function renderCounts(counts) {
  countsBox.innerHTML = Object.entries(counts)
    .map(([key, value]) => metricCard(countLabel(key), countValue(key, value)))
    .join("");
}

function renderUsers(users) {
  usersBox.innerHTML = `
    <div class="admin-row user-row admin-table-head">
      <span>用户</span>
      <span>会员</span>
      <span>浏览量</span>
      <span>停留</span>
      <span>最近访问</span>
      <span>开关</span>
    </div>
    ${users
      .map((item) => {
        const memberLabel = item.is_admin ? "Owner" : item.subscription_active ? "会员" : "免费";
        const expires = item.subscription_expires_at
          ? `至 ${formatDate(item.subscription_expires_at)}`
          : item.is_admin
            ? "管理员旁路"
            : "未开通";
        const switchTitle = item.is_admin
          ? "管理员账号自动拥有高级权限，不能通过会员开关关闭。"
          : "开通或关闭高级会员";
        return `
          <article class="admin-row user-row">
            <span>
              <strong>${escapeHtml(item.email)}</strong>
              <small>注册 ${formatDate(item.created_at)}</small>
            </span>
            <span>
              <mark class="${item.subscription_active ? "success" : "neutral"}">${escapeHtml(memberLabel)}</mark>
              <small>${escapeHtml(expires)}</small>
            </span>
            <span>${escapeHtml(item.page_views)}</span>
            <span>${escapeHtml(formatDuration(item.total_seconds))}</span>
            <span>${escapeHtml(formatDate(item.last_seen_at || item.last_login_at))}</span>
            <span>
              <label
                class="switch-control ${item.is_admin ? "admin-bypass-switch" : ""}"
                title="${escapeHtml(switchTitle)}"
                ${item.is_admin ? 'data-admin-bypass="true"' : ""}
              >
                <input
                  type="checkbox"
                  data-membership="${escapeHtml(item.id)}"
                  ${item.subscription_active ? "checked" : ""}
                  ${item.is_admin ? "disabled" : ""}
                />
                <i></i>
              </label>
            </span>
          </article>`;
      })
      .join("")}`;
}

function renderPageStats(rows) {
  pageStatsBox.innerHTML = rows.length
    ? `
      <div class="admin-row page-row admin-table-head">
        <span>页面</span>
        <span>浏览量</span>
        <span>总停留</span>
      </div>
      ${rows
        .map(
          (item) => `
          <article class="admin-row page-row">
            <span><code>${escapeHtml(item.path)}</code></span>
            <span>${escapeHtml(item.page_views)}</span>
            <span>${escapeHtml(formatDuration(item.total_seconds))}</span>
          </article>`
        )
        .join("")}`
    : `<p class="empty">暂无浏览数据。</p>`;
}

function renderPayments(payments) {
  paymentsBox.innerHTML = payments.length
    ? payments
        .map(
          (item) => `
          <article class="table-row admin-payment-row">
            <span>
              <strong>${escapeHtml(item.email)}</strong>
              <small>${escapeHtml(formatDate(item.created_at))}</small>
            </span>
            <span>${escapeHtml(item.amount_usdt)} USDT</span>
            <code>${escapeHtml(item.payment_code)}</code>
            <input data-payment-note="${escapeHtml(item.id)}" placeholder="TX hash / 备注" />
            <button data-payment-confirm="${escapeHtml(item.id)}" class="secondary">确认</button>
            <button data-payment-reject="${escapeHtml(item.id)}" class="danger-button">拒绝</button>
          </article>`
        )
        .join("")
    : `<p class="empty">暂无待确认付款。</p>`;
}

function renderSources(rows) {
  sourcesBox.innerHTML = rows
    .map(
      (item) => `
        <article class="table-row">
          <span>@${escapeHtml(item.handle)}</span>
          <span>${escapeHtml(item.external_id || "no id")}</span>
          <code>${escapeHtml(item.last_seen_post_id || "new")}</code>
          <mark class="${item.is_active ? "success" : "neutral"}">${item.is_active ? "Active" : "Paused"}</mark>
        </article>`
    )
    .join("");
}

function renderJobs(rows) {
  jobsBox.innerHTML = rows
    .map(
      (item) => `
        <article class="table-row job-row">
          <span>${escapeHtml(item.job_name)}</span>
          <mark class="${item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "neutral"}">${escapeHtml(item.status)}</mark>
          <span>${escapeHtml(item.message || "-")}</span>
          <time>${escapeHtml(formatDate(item.started_at))}</time>
        </article>`
    )
    .join("");
}

async function loadOverview() {
  refreshAdminBtn.disabled = true;
  try {
    const data = await api("/api/admin/overview");
    renderCounts(data.counts);
    renderUsers(data.users);
    renderPayments(data.pending_payments);
    renderPageStats(data.page_stats);
    renderSources(data.sources);
    renderJobs(data.jobs);
    adminMessage.textContent = `已刷新：${new Date().toLocaleTimeString("zh-Hans")}`;
  } finally {
    refreshAdminBtn.disabled = false;
  }
}

paymentsBox.addEventListener("click", async (event) => {
  const confirmButton = event.target.closest("[data-payment-confirm]");
  const rejectButton = event.target.closest("[data-payment-reject]");
  const button = confirmButton || rejectButton;
  if (!button) return;
  const id = confirmButton ? confirmButton.dataset.paymentConfirm : rejectButton.dataset.paymentReject;
  const note = paymentsBox.querySelector(`[data-payment-note="${CSS.escape(id)}"]`)?.value || "";
  button.disabled = true;
  try {
    if (confirmButton) {
      await api(`/api/admin/payments/${id}/confirm`, {
        method: "POST",
        body: JSON.stringify({ tx_hash: note, months: 1 })
      });
      adminMessage.textContent = "付款已确认。";
    } else {
      await api(`/api/admin/payments/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: note || "Rejected by admin" })
      });
      adminMessage.textContent = "付款已拒绝。";
    }
    await loadOverview();
  } catch {
    adminMessage.textContent = "付款状态更新失败。";
    button.disabled = false;
  }
});

usersBox.addEventListener("click", (event) => {
  if (event.target.closest("[data-admin-bypass]")) {
    adminMessage.textContent = "管理员账号自动拥有高级权限，不能通过会员开关关闭。";
  }
});

usersBox.addEventListener("change", async (event) => {
  const input = event.target.closest("[data-membership]");
  if (!input) return;
  input.disabled = true;
  try {
    const result = await api(`/api/admin/users/${input.dataset.membership}/membership`, {
      method: "POST",
      body: JSON.stringify({ active: input.checked, months: 1 })
    });
    adminMessage.textContent = result.active ? "会员已开通或续期 1 个月。" : "会员已关闭。";
    await loadOverview();
  } catch {
    input.checked = !input.checked;
    adminMessage.textContent = "会员状态更新失败。";
    input.disabled = false;
  }
});

refreshAdminBtn.addEventListener("click", loadOverview);

async function initAdmin() {
  try {
    const me = await api("/api/me");
    if (!me.is_admin) {
      setGate(
        "没有管理员权限",
        `当前登录账号 ${me.email} 不是管理员。请退出后使用管理员邮箱登录。`,
        "返回看板",
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
      isAuthError ? "返回看板登录" : "",
      "/"
    );
  }
}

initAdmin();
