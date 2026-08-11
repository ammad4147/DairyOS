/* DairyOS Milk Intelligence Bridge v0.1.0 | 2026-08-11
 * Complete new module.
 * Surfaces persisted milk-production intelligence in the Milk Records domain.
 * No synthetic values; all insights come from /farm/milk/intelligence.
 * Requirements: Dashboard Design §4 Milk Production and §5 yield-drop exceptions.
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

  function render(data) {
    const page = targetPage();
    if (!page) return;

    let panel = document.getElementById("milk-intelligence-panel");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "milk-intelligence-panel";
      panel.className = "panel milk-intelligence-panel";
      page.prepend(panel);
    }

    const alerts = Array.isArray(data.yield_drop_alerts)
      ? data.yield_drop_alerts
      : [];
    const ranking = Array.isArray(data.animal_ranking)
      ? data.animal_ranking
      : [];
    const trend = Array.isArray(data.daily_trend)
      ? data.daily_trend
      : [];

    const alertMarkup = alerts.length
      ? alerts.slice(0, 12).map((alert) => `
          <div class="milk-intel-alert ${alert.severity === "HIGH" ? "high" : "medium"}">
            <div><strong>${esc(alert.animal_id)}</strong> · ${esc(alert.severity)}</div>
            <div>${esc(alert.message)}</div>
            <div class="milk-intel-meta">${esc(alert.previous_date)} → ${esc(alert.latest_date)} · ${fmt(alert.drop_percent)}% drop</div>
          </div>`).join("")
      : '<div class="milk-intel-empty">No persisted animal-level yield-drop alert currently meets the configured threshold.</div>';

    const rankingMarkup = ranking.length
      ? ranking.slice(0, 10).map((row, index) => `
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
      : '<div class="milk-intel-empty">No seven-day milk history is available.</div>';

    panel.innerHTML = `
      <div class="panel-head">
        <div>
          <div class="eyebrow">Evidence-based milk intelligence</div>
          <h2>Milk production signals</h2>
        </div>
        <span class="status-chip ${alerts.length ? "status-alert" : "status-good"}">
          ${alerts.length ? `${alerts.length} yield-drop alert${alerts.length === 1 ? "" : "s"}` : "No yield-drop alerts"}
        </span>
      </div>
      <div class="kpi-strip">
        <div class="kpi"><div class="kpi-label">Yesterday</div><div class="kpi-value">${fmt(data.yesterday_litres)} L</div></div>
        <div class="kpi"><div class="kpi-label">7-day average</div><div class="kpi-value">${fmt(data.seven_day_average_litres)} L</div></div>
        <div class="kpi"><div class="kpi-label">7-day total</div><div class="kpi-value">${fmt(data.seven_day_total_litres)} L</div></div>
        <div class="kpi"><div class="kpi-label">Alert threshold</div><div class="kpi-value">${fmt(data.yield_drop_threshold_percent)}%</div></div>
        <div class="kpi"><div class="kpi-label">Animals ranked</div><div class="kpi-value">${ranking.length}</div></div>
      </div>
      <div class="grid milk-intel-grid">
        <div>
          <h3 style="margin-bottom:8px">Animal yield ranking</h3>
          ${rankingMarkup}
        </div>
        <div>
          <h3 style="margin-bottom:8px">Seven-day production</h3>
          ${trendMarkup}
        </div>
      </div>
      <div style="margin-top:16px">
        <h3 style="margin-bottom:8px">Automatic exceptions</h3>
        <div class="milk-intel-alerts">${alertMarkup}</div>
      </div>
      <div class="milk-intel-foot">Source: persisted milk-production records. Forecasts are withheld where source data is absent.</div>`;
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
      .milk-intel-alert{padding:10px 11px;border-radius:9px;margin-bottom:7px;font-size:12px}
      .milk-intel-alert.high{background:#fee9e6;border-left:4px solid #b42318}
      .milk-intel-alert.medium{background:#fff0d9;border-left:4px solid #b76a12}
      .milk-intel-meta{margin-top:3px;font-size:10px;color:#69736d}
      .milk-intel-empty{padding:12px;background:#fafaf6;border-radius:8px;color:#69736d;font-size:11px}
      .milk-intel-foot{margin-top:13px;padding-top:10px;border-top:1px solid #d9ddd4;color:#69736d;font-size:10px}
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
