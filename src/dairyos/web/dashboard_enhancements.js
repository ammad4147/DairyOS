/* DairyOS Dashboard Enhancement Layer v0.3.1 | 2026-08-11
 * Complete replacement.
 * Strengthens the existing operator cockpit without introducing a second UI.
 * Implements per-user widget persistence, widget ordering, role context and
 * explicit breeding navigation while preserving the existing renderer/API.
 */
(function () {
  "use strict";

  const BASE_KEY = "dairyos.dashboard.widgets";
  const ORDER_KEY = "dairyos.dashboard.order";

  const SECTIONS = {
    herd: {
      title: "Herd Management",
      widgets: ["herd-head", "herd-lifecycle", "breeding-due", "calvings"],
    },
    milk: {
      title: "Milk Records",
      widgets: ["milk-today", "milk-trend", "milk-animals", "milk-quality"],
    },
    health: {
      title: "Health & Vaccination",
      widgets: ["health-open", "health-overdue", "health-trend", "health-culls"],
    },
    feed: {
      title: "Feed Management",
      widgets: ["feed-today", "feed-cover", "feed-cost", "feed-gaps"],
    },
    finance: {
      title: "Financials",
      widgets: ["finance-flow", "finance-cost", "finance-margin", "finance-recon"],
    },
  };

  const LABELS = {
    "herd-head": "Herd headcount",
    "herd-lifecycle": "Lifecycle mix",
    "breeding-due": "Breeding due",
    calvings: "Forecast calvings",
    "milk-today": "Today's milk",
    "milk-trend": "Production trend",
    "milk-animals": "Yield by animal",
    "milk-quality": "Quality signals",
    "health-open": "Open cases",
    "health-overdue": "Protocol gaps",
    "health-trend": "Incident trend",
    "health-culls": "Cull drivers",
    "feed-today": "Feed recorded",
    "feed-cover": "Days of cover",
    "feed-cost": "Feed cost",
    "feed-gaps": "Data gaps",
    "finance-flow": "Cash flow",
    "finance-cost": "Cost per litre",
    "finance-margin": "Margin",
    "finance-recon": "Reconciliation",
  };

  function currentUser() {
    try {
      const raw = sessionStorage.getItem("dairyos.user");
      const user = raw ? JSON.parse(raw) : {};
      return String(user.username || user.user_name || user.name || "operator");
    } catch (_error) {
      return "operator";
    }
  }

  function userKey(base) {
    return `${base}.${currentUser()}`;
  }

  function readUser(base, fallback) {
    try {
      const raw = localStorage.getItem(userKey(base));
      return raw ? JSON.parse(raw) : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function writeUser(base, value) {
    localStorage.setItem(userKey(base), JSON.stringify(value));
  }

  function readBase(base, fallback) {
    try {
      const raw = localStorage.getItem(base);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function writeBase(base, value) {
    localStorage.setItem(base, JSON.stringify(value));
  }

  function selectedWidgets(id) {
    const userSaved = readUser(BASE_KEY, {});
    if (Array.isArray(userSaved[id])) return userSaved[id];

    const legacy = readBase(BASE_KEY, {});
    return Array.isArray(legacy[id]) ? legacy[id] : SECTIONS[id].widgets.slice();
  }

  function orderedWidgets(id) {
    const selected = selectedWidgets(id);
    const userOrder = readUser(ORDER_KEY, {});
    const order = Array.isArray(userOrder[id]) ? userOrder[id] : [];
    const result = [];

    order.forEach((widgetId) => {
      if (selected.includes(widgetId) && !result.includes(widgetId)) result.push(widgetId);
    });
    selected.forEach((widgetId) => {
      if (!result.includes(widgetId)) result.push(widgetId);
    });
    return result;
  }

  function syncBaseRendererState() {
    const selected = {};
    Object.keys(SECTIONS).forEach((id) => {
      selected[id] = orderedWidgets(id);
    });
    writeBase(BASE_KEY, selected);
  }

  function saveSelection(id, selected) {
    const saved = readUser(BASE_KEY, {});
    saved[id] = selected;
    writeUser(BASE_KEY, saved);
    syncBaseRendererState();
  }

  function saveOrder(id, order) {
    const saved = readUser(ORDER_KEY, {});
    saved[id] = order;
    writeUser(ORDER_KEY, saved);
    syncBaseRendererState();
  }

  function resetSectionEnhanced(id) {
    const selections = readUser(BASE_KEY, {});
    const orders = readUser(ORDER_KEY, {});
    delete selections[id];
    delete orders[id];
    writeUser(BASE_KEY, selections);
    writeUser(ORDER_KEY, orders);
    syncBaseRendererState();
    if (typeof window.renderDashboard === "function") window.renderDashboard();
    if (typeof window.toast === "function") window.toast("Section restored to recommended defaults");
  }

  function resetDashboardEnhanced() {
    localStorage.removeItem(userKey(BASE_KEY));
    localStorage.removeItem(userKey(ORDER_KEY));
    const legacy = readBase(BASE_KEY, {});
    Object.keys(SECTIONS).forEach((id) => { legacy[id] = SECTIONS[id].widgets.slice(); });
    writeBase(BASE_KEY, legacy);
    if (typeof window.renderDashboard === "function") window.renderDashboard();
    if (typeof window.toast === "function") window.toast("Dashboard restored to recommended defaults");
  }

  function refreshMoveButtons(list) {
    if (!list) return;
    const rows = [...list.querySelectorAll(".widget-order-row")];
    rows.forEach((row, index) => {
      const up = row.querySelector('[data-move="up"]');
      const down = row.querySelector('[data-move="down"]');
      if (up) up.disabled = index === 0;
      if (down) down.disabled = index === rows.length - 1;
    });
  }

  function customizeEnhanced(id) {
    const section = SECTIONS[id];
    if (!section) return;

    const selected = new Set(selectedWidgets(id));
    const order = orderedWidgets(id);
    const orderedSelected = order.filter((widgetId) => selected.has(widgetId));
    const hidden = section.widgets.filter((widgetId) => !selected.has(widgetId));
    const title = document.getElementById("customize-title");
    const body = document.getElementById("customize-body");
    if (!title || !body) return;

    title.textContent = `Customize ${section.title}`;
    body.innerHTML = `
      <p style="margin-bottom:12px">Choose visible widgets and set their order. The section itself can never disappear.</p>
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.7px;color:#69736d;margin:10px 0 6px">Visible · ordered</div>
      <div id="visible-widget-list" class="check-list">
        ${orderedSelected.map((widgetId) => `
          <div class="check-row widget-order-row" data-widget="${widgetId}">
            <input type="checkbox" data-widget="${widgetId}" checked>
            <span style="flex:1">${LABELS[widgetId] || widgetId}</span>
            <button type="button" class="icon-btn" data-move="up" aria-label="Move up">↑</button>
            <button type="button" class="icon-btn" data-move="down" aria-label="Move down">↓</button>
          </div>`).join("") || '<div class="empty">No widgets selected. Choose one below before applying.</div>'}
      </div>
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.7px;color:#69736d;margin:16px 0 6px">Available · hidden</div>
      <div class="check-list">
        ${hidden.map((widgetId) => `
          <label class="check-row">
            <input type="checkbox" data-widget="${widgetId}">
            <span>${LABELS[widgetId] || widgetId}</span>
          </label>`).join("") || '<div class="empty">All section widgets are visible.</div>'}
      </div>
      <div class="actions" style="margin-top:14px">
        <button class="btn" type="button" id="reset-section-enhanced">Reset section</button>
        <button class="btn btn-primary" type="button" id="apply-section-enhanced">Apply</button>
      </div>`;

    body.querySelectorAll("[data-move]").forEach((button) => {
      button.addEventListener("click", () => {
        const row = button.closest(".widget-order-row");
        const list = document.getElementById("visible-widget-list");
        if (!row || !list) return;
        if (button.dataset.move === "up" && row.previousElementSibling) {
          list.insertBefore(row, row.previousElementSibling);
        }
        if (button.dataset.move === "down" && row.nextElementSibling) {
          list.insertBefore(row.nextElementSibling, row);
        }
        refreshMoveButtons(list);
      });
    });

    body.querySelector("#reset-section-enhanced")?.addEventListener("click", () => {
      resetSectionEnhanced(id);
      window.closeCustomize?.();
    });

    body.querySelector("#apply-section-enhanced")?.addEventListener("click", () => {
      const visibleRows = [...body.querySelectorAll("#visible-widget-list .widget-order-row")];
      const selectedFinal = visibleRows
        .filter((row) => row.querySelector("input")?.checked)
        .map((row) => row.dataset.widget);

      body.querySelectorAll("#customize-body .check-list input[data-widget]:checked").forEach((input) => {
        if (!selectedFinal.includes(input.dataset.widget)) selectedFinal.push(input.dataset.widget);
      });

      saveSelection(id, selectedFinal);
      saveOrder(id, selectedFinal);
      window.closeCustomize?.();
      window.renderDashboard?.();
      window.toast?.("Section updated");
    });

    refreshMoveButtons(body.querySelector("#visible-widget-list"));
    document.getElementById("customize-modal")?.classList.add("open");
  }

  function patchExistingRenderer() {
    // The existing inline renderer uses its own lexical widgets() function.
    // We therefore synchronize the renderer's established storage key rather
    // than replacing the renderer itself. This keeps one dashboard code path.
    syncBaseRendererState();
    window.resetSection = resetSectionEnhanced;
    window.resetDashboard = resetDashboardEnhanced;
    window.customize = customizeEnhanced;
  }

  function addRoleContext() {
    const runtime = document.querySelector(".runtime");
    if (!runtime || runtime.querySelector(".role-context")) return;
    const role = document.createElement("span");
    role.className = "role-context";
    role.style.cssText = "margin-left:10px;padding-left:10px;border-left:1px solid rgba(255,255,255,.22);opacity:.78";
    role.textContent = currentUser();
    runtime.appendChild(role);
  }

  function strengthenNav() {
    const group = document.getElementById("nav-prime");
    if (!group || group.querySelector('[data-target="breeding"]')) return;
    const button = document.createElement("button");
    button.className = "nav-btn";
    button.dataset.target = "breeding";
    button.innerHTML = '<span class="nav-icon">♧</span><span>Breeding & Reproduction</span>';
    button.onclick = () => window.openPage?.("breeding");
    group.appendChild(button);
  }

  function addOperationalContext() {
    const dashboard = document.getElementById("page-dashboard");
    if (!dashboard || dashboard.querySelector(".dashboard-contract-note")) return;
    const note = document.createElement("div");
    note.className = "dashboard-contract-note";
    note.style.cssText = "margin-top:12px;color:#69736d;font-size:11px;padding:9px 2px";
    note.textContent = "Widget visibility and order are remembered for the signed-in operator. The exception rail remains outside customization.";
    dashboard.appendChild(note);
  }

  function initialize() {
    patchExistingRenderer();
    addRoleContext();
    strengthenNav();
    addOperationalContext();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
