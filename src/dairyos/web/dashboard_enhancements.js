/* DairyOS Dashboard Enhancement Layer v0.3.0 | 2026-08-11
 * Purpose: strengthen the five-prime-part cockpit without replacing the existing
 * operator surface or creating a second frontend architecture.
 * Vision coverage: dashboard §3.1 customization/reorder, §3.2 tab prominence,
 * §5 persistent exceptions, §6 responsive operator interaction.
 * Complete replacement/new module.
 */
(function () {
  "use strict";

  const BASE_KEY = "dairyos.dashboard.widgets";
  const ORDER_KEY = "dairyos.dashboard.order";
  const RECOMMENDED = window.DEFAULTS || {
    herd: ["herd-head", "herd-lifecycle", "breeding-due", "calvings"],
    milk: ["milk-today", "milk-trend", "milk-animals", "milk-quality"],
    health: ["health-open", "health-overdue", "health-trend", "health-culls"],
    feed: ["feed-today", "feed-cover", "feed-cost", "feed-gaps"],
    finance: ["finance-flow", "finance-cost", "finance-margin", "finance-recon"],
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

  function read(base, fallback) {
    try {
      const raw = localStorage.getItem(userKey(base));
      return raw ? JSON.parse(raw) : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function write(base, value) {
    localStorage.setItem(userKey(base), JSON.stringify(value));
  }

  function activeWidgets(id) {
    const saved = read(BASE_KEY, {});
    const value = saved[id];
    return Array.isArray(value) ? value : (RECOMMENDED[id] || []).slice();
  }

  function allWidgets(id) {
    const section = (window.PRIME || []).find((item) => item.id === id);
    return section ? section.widgets.map((item) => item[0]) : activeWidgets(id);
  }

  function orderedWidgets(id) {
    const selected = activeWidgets(id);
    const savedOrder = read(ORDER_KEY, {});
    const order = Array.isArray(savedOrder[id]) ? savedOrder[id] : [];
    const merged = [];
    order.forEach((item) => {
      if (selected.includes(item) && !merged.includes(item)) merged.push(item);
    });
    selected.forEach((item) => {
      if (!merged.includes(item)) merged.push(item);
    });
    return merged;
  }

  function saveSelection(id, selected) {
    const saved = read(BASE_KEY, {});
    saved[id] = selected;
    write(BASE_KEY, saved);
  }

  function saveOrder(id, order) {
    const saved = read(ORDER_KEY, {});
    saved[id] = order;
    write(ORDER_KEY, saved);
  }

  function resetSectionEnhanced(id) {
    const selections = read(BASE_KEY, {});
    const orders = read(ORDER_KEY, {});
    delete selections[id];
    delete orders[id];
    write(BASE_KEY, selections);
    write(ORDER_KEY, orders);
    if (typeof window.renderDashboard === "function") window.renderDashboard();
    if (typeof window.toast === "function") window.toast("Section restored to recommended defaults");
  }

  function resetDashboardEnhanced() {
    localStorage.removeItem(userKey(BASE_KEY));
    localStorage.removeItem(userKey(ORDER_KEY));
    if (typeof window.renderDashboard === "function") window.renderDashboard();
    if (typeof window.toast === "function") window.toast("Your dashboard was restored to recommended defaults");
  }

  function customizeEnhanced(id) {
    const section = (window.PRIME || []).find((item) => item.id === id);
    if (!section) return;

    const selected = new Set(activeWidgets(id));
    const order = orderedWidgets(id);
    const available = allWidgets(id);
    const orderedSelected = order.filter((item) => selected.has(item));
    const hidden = available.filter((item) => !selected.has(item));

    const title = document.getElementById("customize-title");
    const body = document.getElementById("customize-body");
    if (!title || !body) return;

    title.textContent = `Customize ${section.title}`;
    body.innerHTML = `
      <p style="margin-bottom:12px">Choose visible widgets and set their order. The section itself can never disappear.</p>
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.7px;color:#69736d;margin:10px 0 6px">Visible · ordered</div>
      <div id="visible-widget-list" class="check-list">
        ${orderedSelected.map((widgetId, index) => `
          <div class="check-row widget-order-row" data-widget="${widgetId}">
            <input type="checkbox" data-widget="${widgetId}" checked>
            <span style="flex:1">${LABELS[widgetId] || widgetId}</span>
            <button type="button" class="icon-btn" data-move="up" ${index === 0 ? "disabled" : ""} aria-label="Move up">↑</button>
            <button type="button" class="icon-btn" data-move="down" ${index === orderedSelected.length - 1 ? "disabled" : ""} aria-label="Move down">↓</button>
          </div>`).join("")}
      </div>
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.7px;color:#69736d;margin:16px 0 6px">Available · hidden</div>
      <div class="check-list">
        ${hidden.map((widgetId) => `
          <label class="check-row">
            <input type="checkbox" data-widget="${widgetId}">
            <span>${LABELS[widgetId] || widgetId}</span>
          </label>`).join("") || '<div class="empty">All recommended widgets are visible.</div>'}
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
      if (typeof window.closeCustomize === "function") window.closeCustomize();
    });

    body.querySelector("#apply-section-enhanced")?.addEventListener("click", () => {
      const visibleRows = [...body.querySelectorAll("#visible-widget-list .widget-order-row")];
      const ordered = visibleRows
        .filter((row) => row.querySelector("input")?.checked)
        .map((row) => row.dataset.widget);
      const newlySelected = [...body.querySelectorAll(".check-list input[data-widget]:checked")]
        .map((input) => input.dataset.widget);
      const selectedFinal = [];
      ordered.forEach((item) => {
        if (!selectedFinal.includes(item)) selectedFinal.push(item);
      });
      newlySelected.forEach((item) => {
        if (!selectedFinal.includes(item)) selectedFinal.push(item);
      });
      saveSelection(id, selectedFinal);
      saveOrder(id, selectedFinal);
      if (typeof window.closeCustomize === "function") window.closeCustomize();
      if (typeof window.renderDashboard === "function") window.renderDashboard();
      if (typeof window.toast === "function") window.toast("Section updated");
    });

    refreshMoveButtons(body.querySelector("#visible-widget-list"));
    document.getElementById("customize-modal")?.classList.add("open");
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

  function patchWidgetStorage() {
    window.widgets = orderedWidgets;
    window.saveWidgets = saveSelection;
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
    if (!group) return;
    const existing = [...group.querySelectorAll(".nav-btn")].map((node) => node.dataset.target);
    if (!existing.includes("breeding")) {
      const button = document.createElement("button");
      button.className = "nav-btn";
      button.dataset.target = "breeding";
      button.innerHTML = '<span class="nav-icon">♧</span><span>Breeding & Reproduction</span>';
      button.onclick = () => window.openPage("breeding");
      group.appendChild(button);
    }
  }

  function addOperationalContext() {
    const dashboard = document.getElementById("page-dashboard");
    if (!dashboard || dashboard.querySelector(".dashboard-contract-note")) return;
    const note = document.createElement("div");
    note.className = "dashboard-contract-note";
    note.style.cssText = "margin-top:12px;color:#69736d;font-size:11px;padding:9px 2px";
    note.textContent = "Dashboard order and widget visibility are remembered for the signed-in operator. Exceptions remain outside customization.";
    dashboard.appendChild(note);
  }

  function initialize() {
    patchWidgetStorage();
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
