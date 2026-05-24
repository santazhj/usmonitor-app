const adminMessage = document.querySelector("#adminMessage");
const countsBox = document.querySelector("#countsBox");
const paymentsBox = document.querySelector("#paymentsBox");
const invitesBox = document.querySelector("#invitesBox");
const sourcesBox = document.querySelector("#sourcesBox");
const jobsBox = document.querySelector("#jobsBox");
const inviteForm = document.querySelector("#inviteForm");
const pollBtn = document.querySelector("#pollBtn");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "include",
    ...options
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
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

  invitesBox.innerHTML = data.invites
    .map(
      (item) => `
        <article class="table-row">
          <code>${item.code}</code>
          <span>${item.label || "-"}</span>
          <span>${item.uses_count}/${item.max_uses}</span>
          <mark>${item.usable ? "Open" : "Closed"}</mark>
        </article>`
    )
    .join("");

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
      const tx_hash = prompt("TX hash / note") || "";
      await api(`/api/admin/payments/${button.dataset.payment}/confirm`, {
        method: "POST",
        body: JSON.stringify({ tx_hash, months: 1 })
      });
      adminMessage.textContent = "付款已确认。";
      await loadOverview();
    });
  });
}

inviteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(inviteForm);
  const result = await api("/api/admin/invites", {
    method: "POST",
    body: JSON.stringify({
      label: form.get("label"),
      max_uses: Number(form.get("max_uses") || 1)
    })
  });
  adminMessage.innerHTML = `邀请码：<code>${result.code}</code>`;
  inviteForm.reset();
  await loadOverview();
});

pollBtn.addEventListener("click", async () => {
  adminMessage.textContent = "轮询中...";
  const result = await api("/api/admin/poll", { method: "POST" });
  adminMessage.textContent = `完成：${JSON.stringify(result)}`;
  await loadOverview();
});

loadOverview().catch(() => {
  adminMessage.textContent = "需要管理员登录。";
});
