"use strict";

const API_BASE = "/api/v1/admin";

const state = {
  credentials: null,
  view: "dashboard",
  permissions: [],
};

const content = document.querySelector("#content");
const title = document.querySelector("#page-title");
const eyebrow = document.querySelector("#page-eyebrow");
const pageActions = document.querySelector("#page-actions");
const loginDialog = document.querySelector("#login-dialog");
const loginForm = document.querySelector("#login-form");
const loginError = document.querySelector("#login-error");
const detailDialog = document.querySelector("#detail-dialog");
const detailContent = document.querySelector("#detail-content");
const detailTitle = document.querySelector("#detail-title");
const connection = document.querySelector("#connection");
const toast = document.querySelector("#toast");

const viewMeta = {
  dashboard: ["Обзор", "Операционный центр"],
  users: ["Пользователи", "Управление доступом"],
  plans: ["Тарифы", "Коммерческие параметры"],
  payments: ["Платежи", "Robokassa"],
  jobs: ["Публикации", "Очередь и ошибки"],
  settings: ["Настройки", "Системная конфигурация"],
  audit: ["Аудит", "Действия администраторов"],
};

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
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Europe/Moscow",
  }).format(new Date(value));
}

function formatMoney(value) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function statusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (["paid", "published", "active", "ok"].includes(normalized)) return "ok";
  if (["failed", "cancelled", "refunded", "blocked"].includes(normalized)) return "bad";
  if (["created", "pending", "queued", "processing", "uploading", "new"].includes(normalized)) return "wait";
  return "";
}

function status(value) {
  return `<span class="status ${statusClass(value)}">${escapeHtml(value || "-")}</span>`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 2600);
}

function setConnection(online) {
  connection.classList.toggle("online", online);
  connection.innerHTML = `<i></i>${online ? "Подключено" : "Не подключено"}`;
}

function applyPermissions() {
  const required = {
    dashboard: "VIEW_STATS",
    users: "VIEW_USERS",
    plans: "MANAGE_PLANS",
    payments: "VIEW_PAYMENTS",
    jobs: "VIEW_UPLOAD_JOBS",
    settings: "MANAGE_SETTINGS",
    audit: "VIEW_ERROR_LOGS",
  };
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.hidden = !state.permissions.includes(required[button.dataset.view]);
  });
}

async function api(path, options = {}) {
  if (!state.credentials) throw new Error("Требуется авторизация");
  const headers = {
    Authorization: `Bearer ${state.credentials.apiToken}`,
    "X-Admin-Telegram-Id": state.credentials.telegramId,
    ...(options.headers || {}),
  };
  if (options.method && options.method !== "GET") {
    headers["X-CSRF-Token"] = state.credentials.csrfToken;
  }
  if (options.body) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE}${path}`, {...options, headers});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body.error?.message || body.detail || `HTTP ${response.status}`;
    if (response.status === 401 || response.status === 403) {
      setConnection(false);
    }
    throw new Error(message);
  }
  setConnection(true);
  return body;
}

function loading() {
  content.innerHTML = '<div class="loading">Загрузка данных...</div>';
}

function renderError(error) {
  content.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
}

function metric(label, value, tone = "") {
  return `<article class="metric ${tone}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

async function renderDashboard() {
  const [dashboard, analytics] = await Promise.all([api("/dashboard"), api("/analytics")]);
  const plans = analytics.active_by_plan || {};
  const maxPlan = Math.max(1, ...Object.values(plans));
  content.innerHTML = `
    <div class="metrics">
      ${metric("Пользователи", dashboard.users_total)}
      ${metric("Доход", formatMoney(dashboard.revenue_rub))}
      ${metric("Активная очередь", dashboard.queue_active, dashboard.queue_active ? "warn" : "")}
      ${metric("Ошибки публикации", dashboard.publication_errors, dashboard.publication_errors ? "error" : "")}
    </div>
    <div class="split-grid">
      <section class="panel">
        <h3>Активные тарифы</h3>
        <div class="bar-list">
          ${["free", "pro", "business"].map((plan) => `
            <div class="bar-row">
              <strong>${plan.toUpperCase()}</strong>
              <progress class="bar-track" max="${maxPlan}" value="${plans[plan] || 0}"></progress>
              <span>${plans[plan] || 0}</span>
            </div>`).join("")}
        </div>
      </section>
      <section class="panel">
        <h3>За последние 24 часа</h3>
        <div class="detail-grid">
          <div class="detail-field"><span>Регистрации</span><strong>${analytics.new_registrations_24h}</strong></div>
          <div class="detail-field"><span>Публикации</span><strong>${analytics.uploads_today}</strong></div>
          <div class="detail-field"><span>TikTok ошибки</span><strong>${analytics.tiktok_api_errors}</strong></div>
        </div>
      </section>
    </div>`;
}

async function renderUsers(query = "") {
  const params = new URLSearchParams({limit: "100"});
  if (query) {
    if (/^\d+$/.test(query)) params.set("telegram_id", query);
    else params.set("username", query);
  }
  const data = await api(`/users?${params}`);
  pageActions.innerHTML = `
    <form class="filters" id="user-search">
      <input name="query" value="${escapeHtml(query)}" placeholder="Telegram ID или username" aria-label="Поиск пользователя">
      <button class="text-button" type="submit">Найти</button>
    </form>`;
  content.innerHTML = data.items.length ? `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Пользователь</th><th>Telegram ID</th><th>Роль</th><th>Статус</th><th>Регистрация</th></tr></thead>
        <tbody>${data.items.map((user) => `
          <tr>
            <td><button class="row-button" data-user-id="${user.id}" type="button">${escapeHtml(user.username ? `@${user.username}` : "Без username")}</button></td>
            <td>${user.telegram_id}</td>
            <td>${status(user.role)}</td>
            <td>${status(user.is_blocked ? "blocked" : "active")}</td>
            <td>${formatDate(user.created_at)}</td>
          </tr>`).join("")}</tbody>
      </table>
    </div>` : '<div class="empty">Пользователи не найдены</div>';

  document.querySelector("#user-search").addEventListener("submit", (event) => {
    event.preventDefault();
    renderUsers(new FormData(event.currentTarget).get("query").trim()).catch(renderError);
  });
  document.querySelectorAll("[data-user-id]").forEach((button) => {
    button.addEventListener("click", () => openUser(button.dataset.userId));
  });
}

async function openUser(userId) {
  const user = await api(`/users/${userId}`);
  const canManageUsers = state.permissions.includes("MANAGE_USERS");
  const canManageRoles = state.permissions.includes("MANAGE_ROLES");
  detailTitle.textContent = user.username ? `@${user.username}` : String(user.telegram_id);
  const plan = user.subscription?.plan_id?.toUpperCase() || "FREE";
  detailContent.innerHTML = `
    <div class="detail-grid">
      <div class="detail-field"><span>Telegram ID</span><strong>${user.telegram_id}</strong></div>
      <div class="detail-field"><span>Тариф</span><strong>${escapeHtml(plan)}</strong></div>
      <div class="detail-field"><span>Роль</span><strong>${escapeHtml(user.role)}</strong></div>
      <div class="detail-field"><span>Доступ</span><strong>${user.is_blocked ? "Заблокирован" : "Активен"}</strong></div>
      <div class="detail-field"><span>TikTok</span><strong>${user.tiktok_accounts.length ? escapeHtml(user.tiktok_accounts[0].display_name || "Подключен") : "Не подключен"}</strong></div>
      <div class="detail-field"><span>Регистрация</span><strong>${formatDate(user.created_at)}</strong></div>
    </div>
    ${(canManageUsers || canManageRoles) ? `<div class="inline-actions">
      ${canManageUsers ? `<button class="${user.is_blocked ? "text-button" : "danger-button"}" data-user-action="${user.is_blocked ? "unblock" : "block"}" type="button">${user.is_blocked ? "Разблокировать" : "Заблокировать"}</button><button class="text-button" data-user-action="force-free" type="button">Перевести на FREE</button>` : ""}
      ${canManageRoles ? `<select id="role-select" aria-label="Роль пользователя">${["USER", "SUPPORT", "ADMIN", "SUPER_ADMIN"].map((role) => `<option value="${role}" ${role === user.role ? "selected" : ""}>${role}</option>`).join("")}</select><button class="text-button" data-user-action="role" type="button">Изменить роль</button>` : ""}
    </div>` : ""}
    <h3 class="section-heading">Последние публикации</h3>
    ${smallJobsTable(user.upload_jobs)}
    <h3 class="section-heading">Последние платежи</h3>
    ${smallPaymentsTable(user.payments)}`;
  detailDialog.showModal();

  document.querySelectorAll("[data-user-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.userAction;
      if (action === "role") {
        const role = document.querySelector("#role-select").value;
        await mutate(`/users/${userId}/role`, "PATCH", {role}, "Роль обновлена");
      } else {
        const confirmed = window.confirm("Подтвердить административное действие?");
        if (!confirmed) return;
        await mutate(`/users/${userId}/${action}`, "POST", null, "Действие выполнено");
      }
      detailDialog.close();
      await renderUsers();
    });
  });
}

function smallJobsTable(items) {
  if (!items.length) return '<div class="empty">Нет публикаций</div>';
  return `<div class="table-wrap"><table><thead><tr><th>ID</th><th>Статус</th><th>Ошибка</th><th>Дата</th></tr></thead><tbody>${items.map((job) => `<tr><td>${escapeHtml(job.id.slice(0, 8))}</td><td>${status(job.status)}</td><td>${escapeHtml(job.error_message || "-")}</td><td>${formatDate(job.created_at)}</td></tr>`).join("")}</tbody></table></div>`;
}

function smallPaymentsTable(items) {
  if (!items.length) return '<div class="empty">Нет платежей</div>';
  return `<div class="table-wrap"><table><thead><tr><th>InvId</th><th>Тариф</th><th>Сумма</th><th>Статус</th><th>Дата</th></tr></thead><tbody>${items.map((payment) => `<tr><td>${payment.inv_id}</td><td>${escapeHtml(payment.plan_id.toUpperCase())}</td><td>${formatMoney(payment.amount_rub)}</td><td>${status(payment.status)}</td><td>${formatDate(payment.created_at)}</td></tr>`).join("")}</tbody></table></div>`;
}

async function renderPlans() {
  const plans = await api("/plans");
  content.innerHTML = `
    <div class="table-wrap"><table>
      <thead><tr><th>Тариф</th><th>Цена, RUB</th><th>Лимит</th><th>Срок, дней</th><th>Продажа</th><th></th></tr></thead>
      <tbody>${plans.map((plan) => `
        <tr data-plan-row="${plan.id}">
          <td><strong>${escapeHtml(plan.title)}</strong></td>
          <td><input name="price_rub" type="number" min="0" value="${plan.price_rub}"></td>
          <td><input name="daily_limit" type="number" min="0" value="${plan.daily_limit}"></td>
          <td><input name="duration_days" type="number" min="1" value="${plan.duration_days || ""}" ${plan.id === "free" ? "disabled" : ""}></td>
          <td><select name="is_active"><option value="true" ${plan.is_active ? "selected" : ""}>Включена</option><option value="false" ${!plan.is_active ? "selected" : ""}>Отключена</option></select></td>
          <td><button class="text-button" data-save-plan="${plan.id}" type="button">Сохранить</button></td>
        </tr>`).join("")}</tbody>
    </table></div>`;
  document.querySelectorAll("[data-save-plan]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = document.querySelector(`[data-plan-row="${button.dataset.savePlan}"]`);
      const payload = {
        price_rub: Number(row.querySelector('[name="price_rub"]').value),
        daily_limit: Number(row.querySelector('[name="daily_limit"]').value),
        is_active: row.querySelector('[name="is_active"]').value === "true",
      };
      const duration = row.querySelector('[name="duration_days"]').value;
      if (duration) payload.duration_days = Number(duration);
      await mutate(`/plans/${button.dataset.savePlan}`, "PATCH", payload, "Тариф обновлен");
    });
  });
}

async function renderPayments(statusFilter = "") {
  const params = new URLSearchParams({limit: "100"});
  if (statusFilter) params.set("status", statusFilter);
  const data = await api(`/payments?${params}`);
  pageActions.innerHTML = `<select id="payment-status" aria-label="Статус платежа"><option value="">Все статусы</option>${["created", "pending", "paid", "failed", "cancelled", "refunded"].map((value) => `<option value="${value}" ${statusFilter === value ? "selected" : ""}>${value}</option>`).join("")}</select>`;
  content.innerHTML = data.items.length ? smallPaymentsTable(data.items) : '<div class="empty">Платежей нет</div>';
  document.querySelector("#payment-status").addEventListener("change", (event) => renderPayments(event.target.value).catch(renderError));
}

async function renderJobs(statusFilter = "") {
  const params = new URLSearchParams({limit: "100"});
  if (statusFilter) params.set("status", statusFilter);
  const data = await api(`/upload-jobs?${params}`);
  pageActions.innerHTML = `<select id="job-status" aria-label="Статус публикации"><option value="">Все статусы</option>${["NEW", "VALIDATING", "PREPARING", "QUEUED", "UPLOADING", "PROCESSING", "PUBLISHED", "FAILED", "CANCELLED"].map((value) => `<option value="${value}" ${statusFilter === value ? "selected" : ""}>${value}</option>`).join("")}</select>`;
  content.innerHTML = data.items.length ? `
    <div class="table-wrap"><table>
      <thead><tr><th>ID</th><th>Пользователь</th><th>Статус</th><th>Ошибка</th><th>Дата</th><th></th></tr></thead>
      <tbody>${data.items.map((job) => `<tr><td>${escapeHtml(job.id.slice(0, 8))}</td><td>${escapeHtml(job.user_id.slice(0, 8))}</td><td>${status(job.status)}</td><td>${escapeHtml(job.error_message || "-")}</td><td>${formatDate(job.created_at)}</td><td>${job.retryable ? `<button class="text-button" data-retry-job="${job.id}" type="button">Повторить</button>` : ""}</td></tr>`).join("")}</tbody>
    </table></div>` : '<div class="empty">Заданий нет</div>';
  document.querySelector("#job-status").addEventListener("change", (event) => renderJobs(event.target.value).catch(renderError));
  document.querySelectorAll("[data-retry-job]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!window.confirm("Повторить временно завершившееся задание?")) return;
      await mutate(`/upload-jobs/${button.dataset.retryJob}/retry`, "POST", null, "Задание поставлено в очередь");
      await renderJobs(statusFilter);
    });
  });
}

async function renderSettings() {
  const settings = await api("/settings");
  content.innerHTML = settings.length ? `
    <div class="table-wrap"><table>
      <thead><tr><th>Ключ</th><th>Значение</th><th>Тип</th><th>Описание</th><th>Изменено</th><th></th></tr></thead>
      <tbody>${settings.map((item) => `<tr data-setting-row="${escapeHtml(item.key)}"><td><strong>${escapeHtml(item.key)}</strong></td><td><input name="value" value="${escapeHtml(item.value)}" ${item.is_editable ? "" : "disabled"}></td><td>${status(item.value_type)}</td><td>${escapeHtml(item.description || "-")}</td><td>${formatDate(item.updated_at)}</td><td>${item.is_editable ? `<button class="text-button" data-save-setting="${escapeHtml(item.key)}" type="button">Сохранить</button>` : ""}</td></tr>`).join("")}</tbody>
    </table></div>` : '<div class="empty">Настройки не созданы</div>';
  document.querySelectorAll("[data-save-setting]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("tr");
      await mutate(`/settings/${encodeURIComponent(button.dataset.saveSetting)}`, "PUT", {value: row.querySelector('[name="value"]').value}, "Настройка обновлена");
    });
  });
}

async function renderAudit(actionFilter = "") {
  const params = new URLSearchParams({limit: "100"});
  if (actionFilter) params.set("action", actionFilter);
  const data = await api(`/audit-actions?${params}`);
  pageActions.innerHTML = `<form class="filters" id="audit-search"><input name="action" value="${escapeHtml(actionFilter)}" placeholder="Тип действия" aria-label="Тип действия"><button class="text-button" type="submit">Фильтр</button></form>`;
  content.innerHTML = data.items.length ? `
    <div class="table-wrap"><table>
      <thead><tr><th>Дата</th><th>Администратор</th><th>Действие</th><th>Объект</th><th>IP</th></tr></thead>
      <tbody>${data.items.map((item) => `<tr><td>${formatDate(item.created_at)}</td><td>${item.admin_telegram_id}</td><td><strong>${escapeHtml(item.action)}</strong></td><td>${escapeHtml(item.target_type || "-")} ${escapeHtml(item.target_id || "")}</td><td>${escapeHtml(item.ip_address || "-")}</td></tr>`).join("")}</tbody>
    </table></div>` : '<div class="empty">Записей аудита нет</div>';
  document.querySelector("#audit-search").addEventListener("submit", (event) => {
    event.preventDefault();
    renderAudit(new FormData(event.currentTarget).get("action").trim()).catch(renderError);
  });
}

async function mutate(path, method, payload, message) {
  await api(path, {method, body: payload ? JSON.stringify(payload) : undefined});
  showToast(message);
}

async function renderView() {
  const [pageTitle, pageEyebrow] = viewMeta[state.view];
  title.textContent = pageTitle;
  eyebrow.textContent = pageEyebrow;
  pageActions.innerHTML = "";
  loading();
  try {
    const renderers = {
      dashboard: renderDashboard,
      users: renderUsers,
      plans: renderPlans,
      payments: renderPayments,
      jobs: renderJobs,
      settings: renderSettings,
      audit: renderAudit,
    };
    await renderers[state.view]();
  } catch (error) {
    renderError(error);
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(loginForm);
  state.credentials = {
    telegramId: String(form.get("telegram_id")).trim(),
    apiToken: String(form.get("api_token")),
    csrfToken: String(form.get("csrf_token")),
  };
  loginError.textContent = "";
  try {
    const session = await api("/session");
    state.permissions = session.permissions;
    applyPermissions();
    loginForm.reset();
    loginDialog.close();
    await renderView();
  } catch (error) {
    state.credentials = null;
    loginError.textContent = error.message;
  }
});

document.querySelector("#navigation").addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (!button || !state.credentials) return;
  state.view = button.dataset.view;
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
  renderView();
});

document.querySelector("#refresh-button").addEventListener("click", () => {
  if (state.credentials) renderView();
});

document.querySelector("#logout-button").addEventListener("click", () => {
  state.credentials = null;
  state.permissions = [];
  setConnection(false);
  content.innerHTML = "";
  loginDialog.showModal();
});

document.querySelector("#detail-close").addEventListener("click", () => detailDialog.close());

loginDialog.showModal();
