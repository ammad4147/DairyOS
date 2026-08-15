/* DairyOS Milk Intelligence Bridge v0.2.0 | 2026-08-15
 * Date-based milk intelligence. No relative Today/Yesterday labels.
 * Reads persisted values from /farm/milk/intelligence.
 */
(function () {
  "use strict";

  const ENDPOINT = "/farm/milk/intelligence";

  function esc(value) {
    return String(value ?? "").replace(/[&<>\"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);
  }

  function fmt(value, digits = 1) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";
    return number.toLocaleString(undefined, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  async function load() {
    const response = await fetch(ENDPOINT, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`${ENDPOINT}: ${response.status}`);
    return response.json();
  }

  function targetPage() {
    return document.getElementById("page-milk");
  }

  function updateNotificationBell(badgeData) {
    if (!badgeData) return;
    const badge = document.getElementById("notification-bell-badge");
    if (!badge) return;
    const count = Number(badgeData.total || 0);
    badge.textContent = String(count);
    badge.style.display = count > 0 ? "inline-block" : "none";
    badge.classList.toggle("critical", Boolean(badgeData.has_critical));
  }

  function severityClass(severity) {
    return severity === "RED" || severity === "HIGH" ? "high" : "medium";
  }

  function severityBadge(severity) {
    const value = String(severity || "").toUpperCase();
    if (!value) return "";
    const cls = value === "RED" || value === "HIGH" ? "badge-red" : "badge-amber";
    return `<span class="badge ${cls}">${esc(value)}</span>`;
  }

  function render(data) {
    const page = targetPage();
    if (!page) return;

    updateNotificationBell(data.notification_badge || data.badge);

    let panel = document.getElementById("milk-intelligence-panel");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "milk-intelligence-panel";
      panel.className = "panel milk-intelligence-panel";
      page.prepend(panel);
    }

    const alerts = Array.isArray(data.yield_drop_alerts) ? data.yield_drop_alerts : [];
    const ranking = Array.isArray(data.animal_ranking) ? data.animal_ranking : [];
    const trend = Array.isArray(data.daily_trend) ? data.daily_trend : [];
    const completedDate = data.current_date || data.completed_date || "—";
    const precedingDate = data.preceding_date || data.previous_date || "—";
    const herd = data.herd_comparison || {};

    const alertMarkup = alerts.length
      ? alerts.slice(0, 50).map((alert) => `
          <div class="milk-intel-alert ${severityClass(alert.severity)}">
            <div class="milk-intel-alert-head">
              <strong>${esc(alert.animal_id)}</strong>
              ${severityBadge(alert.severity)}
            </div>
            <div>${esc(alert.message || "Milk yield declined.")}</div>
            <div class="milk-intel-meta">
              ${esc(alert.preceding_date || alert.previous_date || precedingDate)} →
              ${esc(alert.current_date || alert.latest_date || completedDate)} ·
              ${fmt(alert.drop_percent)}% drop · ${fmt(alert.absolute_change)} L
            </div>
            ${alert.passport_url ? `<div class="milk-intel-links"><a class="animal-link" href="${esc(alert.passport_url)}">Open animal passport</a></div>` : ""}
          </div>`).join("")
      : '<div class="milk-intel-empty">No persisted animal-level yield-drop alert meets the configured threshold.</div>';

    const rankingMarkup = ranking.length
      ? ranking.slice(0, 20).map((row, index) => `
          <div class="milk-intel-row">
            <span>#${index + 1} ${esc(row.animal_id)}</span>
            <strong>${fmt(row.litres)} L</strong>
          </div>`).join("")
      : '<div class="milk-intel-empty">No animal-level milk history is available.</div>';

    const trendMarkup = trend.length
      ? trend.map((row) => `
          <div class="milk-intel-row">
            <span>${esc(row.date)}</span>
            <strong>${fmt(row.litres)} L</strong>
          </div>`).join("")
      : '<div class="milk-intel-empty">No completed-date milk history is available.</div>';

    const herdMarkup = herd.severity
      ? `<div class="milk-intel-alert ${severityClass(herd.severity)}">
           <div class="milk-intel-alert-head"><strong>Herd production</strong>${severityBadge(herd.severity)}</div>
           <div>${esc(herd.current_date || completedDate)} vs ${esc(herd.preceding_date || precedingDate)}</div>
           <div class="milk-intel-meta">${fmt(herd.current_total_yield)} L vs ${fmt(herd.preceding_total_yield)} L · ${fmt(herd.drop_percent)}% drop</div>
         </div>`
      : '<div class="milk-intel-empty">No herd-level decline meets the configured threshold.</div>';

    panel.innerHTML = `
      <div class="panel-head">
        <div>
          <div class="eyebrow">Evidence-based milk intelligence</div>
          <h2>Milk production signals</h2>
        </div>
        <span class="status-chip ${alerts.length ? "status-alert" : "status-good"}">
          ${alerts.length ? `${alerts.length} animal decline${alerts.length === 1 ? "" : "s"}` : "No animal yield-drop alerts"}
        </span>
      </div>
      <div class="kpi-strip">
        <div class="kpi"><div class="kpi-label">Completed date</div><div class="kpi-value">${esc(completedDate)}</div></div>
        <div class="kpi"><div class="kpi-label">Preceding completed date</div><div class="kpi-value">${esc(precedingDate)}</div></div>
        <div class="kpi"><div class="kpi-label">Current yield</div><div class="kpi-value">${fmt(data.current_total_litres ?? data.current_date_litres)} L</div></div>
        <div class="kpi"><div class="kpi-label">Preceding yield</div><div class="kpi-value">${fmt(data.preceding_total_litres ?? data.previous_date_litres)} L</div></div>
        <div class="kpi"><div class="kpi-label">Amber / Red</div><div class="kpi-value">15% / 30%</div></div>
      </div>
      <div class="grid milk-intel-grid">
        <div>
          <h3 style="margin-bottom:8px">Animal yield ranking</h3>
          ${rankingMarkup}
        </div>
        <div>
          <h3 style="margin-bottom:8px">Completed-date production trend</h3>
          ${trendMarkup}
        </div>
      </div>
      <div class="milk-intel-section">
        <h3 style="margin-bottom:8px">Herd comparison</h3>
        ${herdMarkup}
      </div>
      <div class="milk-intel-section">
        <h3 style="margin-bottom:8px">Animal decline list (${esc(completedDate)} vs ${esc(precedingDate)})</h3>
        <div class="milk-intel-alerts">${alertMarkup}</div>
      </div>
      <div class="milk-intel-foot">Source: persisted milk-production records. Comparisons use completed dates only; incomplete dates are excluded.</div>`;
  }

  function injectStyles() {
    if (document.getElementById("milk-intelligence-styles")) return;
    const style = document.createElement("style");
    style.id = "milk-intelligence-styles";
    style.textContent = `
      .milk-intelligence-panel{margin-bottom:16px}
      .milk-intel-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
      .milk-intel-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px dashed #e5e8e1;font-size:12px}
      .milk-intel-row:last-child{border-bottom:0}
      .milk-intel-section{margin-top:16px}
      .milk-intel-alert{padding:10px 11px;border-radius:9px;margin-bottom:7px;font-size:12px}
      .milk-intel-alert.high{background:#fee9e6;border-left:4px solid #b42318}
      .milk-intel-alert.medium{background:#fff0d9;border-left:4px solid #b76a12}
      .milk-intel-alert-head{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:4px}
      .badge{font-size:10px;padding:2px 6px;border-radius:4px;font-weight:600}
      .badge-red{background:#b42318;color:#fff}
      .badge-amber{background:#b76a12;color:#fff}
      .milk-intel-meta{margin-top:4px;font-size:11px;color:#4f5752}
      .milk-intel-links{margin-top:6px;font-size:11px}
      .milk-intel-links a,.animal-link{color:#1b4d2e;text-decoration:none;font-weight:600}
      .milk-intel-links a:hover,.animal-link:hover{text-decoration:underline}
      .milk-intel-empty{padding:12px;background:#fafaf6;border-radius:8px;color:#69736d;font-size:11px}
      .milk-intel-foot{margin-top:13px;padding-top:10px;border-top:1px solid #d9ddd4;color:#69736d;font-size:10px}
      #notification-bell-badge.critical{font-weight:700}
      @media(max-width:720px){.milk-intel-grid{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  async function refresh() {
    try {
      const data = await load();
      render(data);
    } catch (error) {
      console.warn("DairyOS milk intelligence unavailable", error);
    }
  }

  function initialize() {
    injectStyles();
    refresh();
    window.setInterval(refresh, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
