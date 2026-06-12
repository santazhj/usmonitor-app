const loginForm = document.querySelector("#passwordLoginForm");
const registerForm = document.querySelector("#registerForm");
const resetForm = document.querySelector("#resetForm");
const loginEmail = document.querySelector("#loginEmail");
const registerEmail = document.querySelector("#registerEmail");
const resetEmail = document.querySelector("#resetEmail");
const registerCode = document.querySelector("#registerCode");
const resetCode = document.querySelector("#resetCode");
const registerPassword = document.querySelector("#registerPassword");
const resetPassword = document.querySelector("#resetPassword");
const registerStrength = document.querySelector("#registerStrength");
const loginButton = document.querySelector("#passwordLoginBtn");
const registerButton = document.querySelector("#registerBtn");
const resetButton = document.querySelector("#resetBtn");
const registerCodeBtn = document.querySelector("#registerCodeBtn");
const resetCodeBtn = document.querySelector("#resetCodeBtn");
const message = document.querySelector("#loginMessage");
const accountSummary = document.querySelector("#accountSummary");
const planBadge = document.querySelector("#loginPlanBadge");
const languageToggle = document.querySelector("#languageToggle");
const authTabs = Array.from(document.querySelectorAll("[data-auth-mode]"));
const authPanels = Array.from(document.querySelectorAll("[data-auth-panel]"));

const LANGUAGE_KEY = "usmonitor.language";
const LAST_EMAIL_KEY = "usmonitor.lastEmail";

let currentLanguage = localStorage.getItem(LANGUAGE_KEY) || "zh";
let currentMode = "login";
let currentUser = null;
let registerChallengeToken = "";
let resetChallengeToken = "";
let countdownTimer = null;

const nextPath = safeNextPath(new URLSearchParams(window.location.search).get("next"));

const COPY = {
  zh: {
    pageTitle: "账户登录 - US Monitor",
    badgeSignedOut: "账户",
    badgeFree: "普通版",
    badgeVip: "VIP",
    eyebrow: "账户访问",
    title: "账号密码登录",
    lede: "注册时用邮箱验证码确认身份并设置密码。之后登录只需要邮箱和密码。",
    tabLogin: "登录",
    tabRegister: "注册",
    tabReset: "找回密码",
    emailLabel: "邮箱",
    passwordLabel: "密码",
    setPasswordLabel: "设置密码",
    newPasswordLabel: "新密码",
    codeLabel: "验证码",
    sendCode: "发送验证码",
    loginSubmit: "登录",
    registerSubmit: "注册并登录",
    resetSubmit: "重设并登录",
    sending: "正在发送验证码...",
    sent: "验证码已发送，请检查邮箱。",
    devCode: "开发验证码：{code}",
    working: "处理中...",
    failedSend: "验证码发送失败，请检查邮箱后重试。",
    failedLogin: "邮箱或密码错误。",
    failedRegister: "注册失败。请确认验证码、邮箱和密码。",
    failedReset: "重设失败。请确认验证码、邮箱和新密码。",
    signedIn: "已登录",
    signedInDetail: "{email} 当前为 {plan}。",
    continueTo: "继续",
    backDashboard: "返回看板",
    logout: "退出登录",
    signedOut: "已退出登录。",
    sideEyebrow: "Private Access",
    sideTitle: "US Monitor 独立账户",
    sideBody: "这个账户只用于 US Monitor 的情报看板、推送和后台权限。Options 工具已保持本地独立，不在本站开放。",
    pointOne: "验证码 15 分钟有效",
    pointTwo: "密码只保存安全哈希",
    pointThree: "找回密码同样使用邮箱验证码",
    weakPassword: "密码至少 8 位，建议包含字母和数字。",
    goodPassword: "密码强度可用。"
  },
  en: {
    pageTitle: "Account Login - US Monitor",
    badgeSignedOut: "Account",
    badgeFree: "Free",
    badgeVip: "VIP",
    eyebrow: "Account Access",
    title: "Password Sign In",
    lede: "Register with an email code and set a password. After that, sign in with email and password.",
    tabLogin: "Sign in",
    tabRegister: "Register",
    tabReset: "Reset password",
    emailLabel: "Email",
    passwordLabel: "Password",
    setPasswordLabel: "Set password",
    newPasswordLabel: "New password",
    codeLabel: "Code",
    sendCode: "Send code",
    loginSubmit: "Sign in",
    registerSubmit: "Register and sign in",
    resetSubmit: "Reset and sign in",
    sending: "Sending code...",
    sent: "Code sent. Check your email.",
    devCode: "Development code: {code}",
    working: "Working...",
    failedSend: "Could not send the code. Check your email and try again.",
    failedLogin: "Email or password is incorrect.",
    failedRegister: "Registration failed. Check your code, email, and password.",
    failedReset: "Reset failed. Check your code, email, and new password.",
    signedIn: "Signed in",
    signedInDetail: "{email} is currently on {plan}.",
    continueTo: "Continue",
    backDashboard: "Back to dashboard",
    logout: "Sign out",
    signedOut: "Signed out.",
    sideEyebrow: "Private Access",
    sideTitle: "US Monitor standalone account",
    sideBody: "This account is only for US Monitor intelligence, push notifications, and admin access. The Options tool stays local and private.",
    pointOne: "Codes expire in 15 minutes",
    pointTwo: "Passwords are stored as secure hashes",
    pointThree: "Password recovery uses an email code",
    weakPassword: "Use at least 8 characters; letters and numbers are recommended.",
    goodPassword: "Password strength is usable."
  }
};

function safeNextPath(value) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  if (value === "/login" || value.startsWith("/options")) return "/";
  return value;
}

function t(key, params = {}) {
  let value = COPY[currentLanguage]?.[key] || COPY.zh[key] || key;
  Object.entries(params).forEach(([name, replacement]) => {
    value = value.replaceAll(`{${name}}`, replacement);
  });
  return value;
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

function setMessage(text, tone = "") {
  message.textContent = text;
  message.dataset.tone = tone;
}

function currentPlan(user) {
  return user?.subscription?.active ? t("badgeVip") : t("badgeFree");
}

function updateBadge(user = null) {
  const isVip = Boolean(user?.subscription?.active);
  planBadge.textContent = user ? currentPlan(user) : t("badgeSignedOut");
  planBadge.dataset.planStatus = user ? (isVip ? "vip" : "free") : "loading";
}

function setMode(mode) {
  currentMode = mode;
  authTabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.authMode === mode);
  });
  authPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.authPanel !== mode);
  });
  setMessage("");
  const rememberedEmail = localStorage.getItem(LAST_EMAIL_KEY) || "";
  if (mode === "register" && rememberedEmail && !registerEmail.value) registerEmail.value = rememberedEmail;
  if (mode === "reset" && rememberedEmail && !resetEmail.value) resetEmail.value = rememberedEmail;
}

function renderAccount(user, shouldRedirect = false) {
  currentUser = user;
  updateBadge(user);
  authPanels.forEach((panel) => panel.classList.add("hidden"));
  accountSummary.classList.remove("hidden");
  accountSummary.innerHTML = `
    <strong>${escapeHtml(t("signedIn"))}</strong>
    <span>${escapeHtml(t("signedInDetail", { email: user.email, plan: currentPlan(user) }))}</span>
    <div class="button-row">
      <a class="primary access-action" href="${escapeHtml(nextPath)}">${escapeHtml(t("continueTo"))}</a>
      <a class="secondary access-action" href="/">${escapeHtml(t("backDashboard"))}</a>
      <button id="logoutBtn" class="secondary" type="button">${escapeHtml(t("logout"))}</button>
    </div>`;
  accountSummary.querySelector("#logoutBtn").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    currentUser = null;
    accountSummary.classList.add("hidden");
    updateBadge(null);
    setMode("login");
    setMessage(t("signedOut"), "success");
  });
  if (shouldRedirect && nextPath !== "/") {
    window.setTimeout(() => window.location.assign(nextPath), 450);
  }
}

function applyCopy() {
  document.documentElement.lang = currentLanguage === "zh" ? "zh-Hans" : "en";
  document.title = t("pageTitle");
  languageToggle.textContent = currentLanguage === "zh" ? "EN" : "中文";
  document.querySelectorAll("[data-copy]").forEach((element) => {
    element.textContent = t(element.dataset.copy);
  });
  updateBadge(currentUser);
}

function startCountdown(button) {
  let seconds = 45;
  clearInterval(countdownTimer);
  button.disabled = true;
  const original = t("sendCode");
  button.textContent = `${seconds}s`;
  countdownTimer = setInterval(() => {
    seconds -= 1;
    button.textContent = seconds > 0 ? `${seconds}s` : original;
    if (seconds <= 0) {
      clearInterval(countdownTimer);
      button.disabled = false;
    }
  }, 1000);
}

async function sendCode(mode) {
  const emailInput = mode === "register" ? registerEmail : resetEmail;
  const codeInput = mode === "register" ? registerCode : resetCode;
  const button = mode === "register" ? registerCodeBtn : resetCodeBtn;
  const email = emailInput.value.trim().toLowerCase();
  if (!email) {
    emailInput.focus();
    return;
  }
  localStorage.setItem(LAST_EMAIL_KEY, email);
  setMessage(t("sending"));
  try {
    const result = await api("/api/auth/code/request", {
      method: "POST",
      body: JSON.stringify({ email, purpose: mode })
    });
    if (mode === "register") registerChallengeToken = result.challenge_token;
    if (mode === "reset") resetChallengeToken = result.challenge_token;
    codeInput.value = result.dev_code || "";
    codeInput.focus();
    startCountdown(button);
    setMessage(
      result.dev_code ? `${t("sent")} ${t("devCode", { code: result.dev_code })}` : t("sent"),
      "success"
    );
  } catch {
    button.disabled = false;
    setMessage(t("failedSend"), "error");
  }
}

function updateStrength(input) {
  const value = input.value || "";
  const good = value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value);
  registerStrength.textContent = value ? (good ? t("goodPassword") : t("weakPassword")) : "";
  registerStrength.dataset.tone = good ? "success" : "warn";
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  const email = String(form.get("email") || "").trim().toLowerCase();
  if (email) localStorage.setItem(LAST_EMAIL_KEY, email);
  loginButton.disabled = true;
  setMessage(t("working"));
  try {
    const result = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password: String(form.get("password") || "") })
    });
    renderAccount(result.user, true);
  } catch {
    setMessage(t("failedLogin"), "error");
  } finally {
    loginButton.disabled = false;
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(registerForm);
  const email = String(form.get("email") || "").trim().toLowerCase();
  if (email) localStorage.setItem(LAST_EMAIL_KEY, email);
  registerButton.disabled = true;
  setMessage(t("working"));
  try {
    const result = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password: String(form.get("password") || ""),
        code: String(form.get("code") || ""),
        challenge_token: registerChallengeToken
      })
    });
    renderAccount(result.user, true);
  } catch {
    setMessage(t("failedRegister"), "error");
  } finally {
    registerButton.disabled = false;
  }
});

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(resetForm);
  const email = String(form.get("email") || "").trim().toLowerCase();
  if (email) localStorage.setItem(LAST_EMAIL_KEY, email);
  resetButton.disabled = true;
  setMessage(t("working"));
  try {
    const result = await api("/api/auth/password/reset", {
      method: "POST",
      body: JSON.stringify({
        email,
        password: String(form.get("password") || ""),
        code: String(form.get("code") || ""),
        challenge_token: resetChallengeToken
      })
    });
    renderAccount(result.user, true);
  } catch {
    setMessage(t("failedReset"), "error");
  } finally {
    resetButton.disabled = false;
  }
});

authTabs.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.authMode));
});

registerCodeBtn.addEventListener("click", () => sendCode("register"));
resetCodeBtn.addEventListener("click", () => sendCode("reset"));
registerPassword.addEventListener("input", () => updateStrength(registerPassword));
resetPassword.addEventListener("input", () => {});

languageToggle.addEventListener("click", () => {
  currentLanguage = currentLanguage === "zh" ? "en" : "zh";
  localStorage.setItem(LANGUAGE_KEY, currentLanguage);
  applyCopy();
  updateStrength(registerPassword);
});

async function init() {
  const rememberedEmail = localStorage.getItem(LAST_EMAIL_KEY) || "";
  if (rememberedEmail) {
    loginEmail.value = rememberedEmail;
    registerEmail.value = rememberedEmail;
    resetEmail.value = rememberedEmail;
  }
  applyCopy();
  try {
    const me = await api("/api/me");
    renderAccount(me, false);
  } catch {
    setMode(currentMode);
  }
}

init();
