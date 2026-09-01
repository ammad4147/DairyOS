/* DairyOS Live Farm Cockpit v0.4.0 | 2026-08-11
 * Complete replacement/new module.
 * Turns the existing five-prime dashboard into a live operational cockpit
 * using only persisted API records. No synthetic farm values are generated.
 * Requirements: Dashboard Design §3, §4, §5, §6.
 */
(function () {
  "use strict";

  const ENDPOINTS = {
    dashboard: "/dashboard",
    milk: "/farm/milk",
    feed: "/farm/feed",
    health: "/farm/health-observations",
    breeding: "/farm/breeding",
    financial: "/farm/financial",
  };

  const state = {
    dashboard: null,
    milk: [],
    feed: [],
    health: [],
    breeding: [],
    financial: [],
    loadedAt: null,
  };

  const todayKey = () => {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  };

  const dateKey = (value) => {
    if (!value) return "";
    const text = String(value);
    return text.length >= 10 ? text.slice(0, 10) : text;
  };

  const num = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  };

  const fmt = (value, digits = 0) => {
    const n = num(value);
    return n.toLocaleString(undefined, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  };

  const currency = (value) => `PKR ${fmt(value)}`;

  const recordsToday = (records, fields) => records.filter((row) => {
    for (const field of fields) {
      if (dateKey(row && row[field]) === todayKey()) return true;
    }
    return false;
  });

  async function getJson(path) {
    const response = await fetch(path, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }

  async function loadLiveData() {
    const results = await Promise.allSettled(
      Object.values(ENDPOINTS).map((path) => getJson(path))
    );

    const values = Object.keys(ENDPOINTS).reduce((out, key, index) => {
      out[key] = results[index].status === "fulfilled" ? results[index].value : null;
      return out;
    }, {});

    state.dashboard = values.dashboard || {};
    state.milk = Array.isArray(values.milk) ? values.milk : [];
    state.feed = Array.isArray(values.feed) ? values.feed : [];
    state.health = Array.isArray(values.health) ? values.health : [];
    state.breeding = Array.isArray(values.breeding) ? values.breeding : [];
    state.financial = Array.isArray(values.financial) ? values.financial : [];
    state.loadedAt = new Date();
  }

  function dashboardState() {
    return state.dashboard && state.dashboard.dashboard
      ? state.dashboard.dashboard
      : {};
  }

  function herdMetrics() {
    const animals = dashboardState().animals || {};
    const operational = dashboardState().operational_state || {};
    return {
      total: num(animals.total),
      milking: num(animals.milking),
      dry: num(animals.dry),
      attention: num(operational.animals_needing_attention),
    };
  }

  function milkMetrics() {
    const rows = recordsToday(state.milk, ["production_date", "date", "created_at"]);
    const total = rows.reduce((sum, row) => {
      const explicit = num(row.total_yield);
      return sum + (explicit || num(row.morning_yield) + num(row.afternoon_yield) + num(row.evening_yield));
    }, 0);
    const animals = new Set(rows.map((row) => row.animal_id).filter(Boolean));
    return {
      total,
      records: rows.length,
      animals: animals.size,
      average: animals.size ? total / animals.size : 0,
      latest: rows.slice().sort((a, b) => String(b.production_date || "").localeCompare(String(a.production_date || "")))[0],
    };
  }

  function feedMetrics() {
    const rows = recordsToday(state.feed, ["feeding_date", "date", "created_at"]);
    return {
      quantity: rows.reduce((sum, row) => sum + num(row.quantity_kg), 0),
      records: rows.length,
      types: new Set(rows.map((row) => row.feed_type).filter(Boolean)).size,
    };
  }

  function healthMetrics() {
    const open = state.health.filter((row) => {
      const status = String(row.status || "OPEN").toUpperCase();
      return status !== "CLOSED" && status !== "RESOLVED";
    });
    const severe = open.filter((row) => {
      const severity = String(row.severity || "NORMAL").toUpperCase();
      return ["CRITICAL", "SEVERE", "HIGH"].includes(severity);
    });
    const animals = new Set(open.map((row) => row.animal_id).filter(Boolean));
    return { open: open.length, severe: severe.length, animals: animals.size };
  }

  function breedingMetrics() {
    const counts = {};
    state.breeding.forEach((row) => {
      const type = String(row.event_type || "UNKNOWN").toUpperCase();
      counts[type] = (counts[type] || 0) + 1;
    });
    const activeAnimals = new Set(state.breeding.map((row) => row.animal_id).filter(Boolean));
    return {
      total: state.breeding.length,
      animals: activeAnimals.size,
      inseminations: num(counts.INSEMINATION) + num(counts.INSEMINATED) + num(counts.AI),
      pregnancies: num(counts.PREGNANCY_CONFIRMED) + num(counts.PREGNANT),
    };
  }

  function financialMetrics() {
    let income = 0;
    let expense = 0;
    state.financial.forEach((row) => {
      const amount = num(row.amount);
      if (String(row.transaction_type || "").toUpperCase() === "INCOME") income += amount;
      if (String(row.transaction_type || "").toUpperCase() === "EXPENSE") expense += amount;
    });
    return { income, expense, net: income - expense };
  }

  function injectStyles() {
    if (document.getElementById("dairyos-live-styles")) return;
    const style = document.createElement("style");
    style.id = "dairyos-live-styles";
    style.textContent = `
      .live-cockpit{margin:0 0 16px;border:1px solid #d9ddd4;border-radius:14px;background:#fffdf8;box-shadow:0 3px 16px rgba(26,38,31,.035);overflow:hidden}
      .live-cockpit-head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 15px;border-bottom:1px solid #d9ddd4}
      .live-cockpit-title{font-weight:850;letter-spacing:.1px}
      .live-cockpit-meta{font-size:10px;color:#69736d;text-transform:uppercase;letter-spacing:.55px}
      .live-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0}
      .live-domain{padding:13px 14px;border-right:1px solid #e5e8e1;min-width:0}
      .live-domain:last-child{border-right:0}
      .live-domain-link{border:0;background:none;padding:0;text-align:left;width:100%;color:inherit;cursor:pointer}
      .live-domain-link:hover .live-domain-title{text-decoration:underline}
      .live-domain-title{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.55px;color:#69736d}
      .live-primary{font-size:23px;font-weight:900;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .live-secondary{font-size:11px;color:#69736d;margin-top:2px;min-height:17px}
      .live-status{display:inline-flex;margin-top:7px;padding:3px 7px;border-radius:999px;font-size:9px;font-weight:850}
      .live-good{background:#e6f2ec;color:#08704e}.live-watch{background:#fff0d9;color:#9a5608}.live-alert{background:#fee9e6;color:#a31d13}.live-neutral{background:#eef1ed;color:#58645e}
      .live-detail{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:12px;padding:0 14px 14px}
      .live-detail-card{border-top:1px solid #e5e8e1;padding-top:9px}.live-detail-label{font-size:9px;color:#69736d;text-transform:uppercase}.live-detail-value{font-size:13px;font-weight:800;margin-top:2px}
      .live-drill{border:0;background:none;color:#176b52;font-size:10px;font-weight:850;padding:5px 0 0;cursor:pointer}
      @media(max-width:1050px){.live-grid{grid-template-columns:repeat(3,1fr)}.live-domain:nth-child(3){border-right:0}.live-domain:nth-child(n+4){border-top:1px solid #e5e8e1}}
      @media(max-width:720px){.live-grid{grid-template-columns:repeat(2,1fr)}.live-domain{border-right:0}.live-domain:nth-child(n+3){border-top:1px solid #e5e8e1}.live-detail{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function pageFor(id) {
    const pages = {
      herd: "herd",
      milk: "milk",
      health: "health",
      feed: "feed",
      finance: "finance",
      breeding: "breeding",
    };
    return pages[id] || id;
  }

  function domainCard(id, title, primary, secondary, status, detail, target) {
    const safeTarget = pageFor(target || id);
    return `
      <div class="live-domain">
        <button class="live-domain-link" type="button" data-live-target="${safeTarget}">
          <div class="live-domain-title">${title}</div>
          <div class="live-primary">${primary}</div>
          <div class="live-secondary">${secondary}</div>
          <span class="live-status ${status.class}">${status.label}</span>
        </button>
        <div class="live-secondary" style="margin-top:7px">${detail}</div>
        <button class="live-drill" type="button" data-live-target="${safeTarget}">Open ${title} →</button>
      </div>`;
  }

  function renderLiveCockpit() {
    const dashboard = document.getElementById("page-dashboard");
    if (!dashboard) return;
    let root = document.getElementById("live-cockpit");
    if (!root) {
      root = document.createElement("section");
      root.id = "live-cockpit";
      root.className = "live-cockpit";
      const hero = document.getElementById("hero");
      dashboard.insertBefore(root, hero || dashboard.firstChild);
    }

    const herd = herdMetrics();
    const milk = milkMetrics();
    const feed = feedMetrics();
    const health = healthMetrics();
    const finance = financialMetrics();
    const breeding = breedingMetrics();
    const exceptionCount = Array.isArray(state.dashboard?.exceptions)
      ? state.dashboard.exceptions.length
      : num(state.dashboard?.dashboard?.operational_state?.exceptions_count);

    const herdStatus = herd.attention > 0
      ? { class: "live-alert", label: `${fmt(herd.attention)} need action` }
      : { class: "live-good", label: "No attention flags" };
    const milkStatus = milk.total > 0
      ? { class: "live-good", label: `${fmt(milk.animals)} animals recorded` }
      : { class: "live-watch", label: "No milk recorded today" };
    const healthStatus = health.severe > 0
      ? { class: "live-alert", label: `${fmt(health.severe)} severe/open` }
      : health.open > 0
        ? { class: "live-watch", label: `${fmt(health.open)} open` }
        : { class: "live-good", label: "No open cases" };
    const feedStatus = feed.records > 0
      ? { class: "live-good", label: `${fmt(feed.records)} records today` }
      : { class: "live-watch", label: "No feed recorded today" };
    const financeStatus = finance.net < 0
      ? { class: "live-alert", label: "Net recorded flow negative" }
      : finance.income > 0 || finance.expense > 0
        ? { class: "live-good", label: "Recorded flow positive" }
        : { class: "live-neutral", label: "No transactions recorded" };

    root.innerHTML = `
      <div class="live-cockpit-head">
        <div><div class="live-cockpit-title">Live operating picture</div><div class="live-cockpit-meta">Persisted records · No synthetic values · ${state.loadedAt ? state.loadedAt.toLocaleTimeString() : "not refreshed"}</div></div>
        <div class="live-cockpit-meta">${fmt(exceptionCount)} exception signals</div>
      </div>
      <div class="live-grid">
        ${domainCard("herd", "Herd Management", fmt(herd.total), `${fmt(herd.milking)} milking · ${fmt(herd.dry)} dry`, herdStatus, `${fmt(herd.attention)} animals requiring attention`, "herd")}
        ${domainCard("milk", "Milk Records", `${fmt(milk.total, 1)} L`, `${fmt(milk.average, 1)} L / recorded animal`, milkStatus, `${fmt(milk.records)} milk records today`, "milk")}
        ${domainCard("health", "Health & Vaccination", fmt(health.open), `${fmt(health.animals)} animals with open observations`, healthStatus, `${fmt(health.severe)} high-severity open observations`, "health")}
        ${domainCard("feed", "Feed Management", `${fmt(feed.quantity, 1)} kg`, `${fmt(feed.types)} feed types today`, feedStatus, `${fmt(feed.records)} feed records today`, "feed")}
        ${domainCard("finance", "Financials", currency(finance.net), `${currency(finance.income)} income · ${currency(finance.expense)} expense`, financeStatus, `Recorded transactions: ${fmt(state.financial.length)}`, "finance")}
      </div>
      <div class="live-detail">
        <div class="live-detail-card"><div class="live-detail-label">Breeding activity</div><div class="live-detail-value">${fmt(breeding.total)} records · ${fmt(breeding.inseminations)} inseminations · ${fmt(breeding.pregnancies)} pregnancies</div><button class="live-drill" type="button" data-live-target="breeding">Open breeding →</button></div>
        <div class="live-detail-card"><div class="live-detail-label">Milk data coverage</div><div class="live-detail-value">${fmt(milk.animals)} animals represented today</div><button class="live-drill" type="button" data-live-target="milk">Review milk records →</button></div>
        <div class="live-detail-card"><div class="live-detail-label">Evidence boundary</div><div class="live-detail-value">Forecasts are withheld where required source data is absent.</div></div>
      </div>`;

    root.querySelectorAll("[data-live-target]").forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.dataset.liveTarget;
        if (typeof window.openPage === "function") window.openPage(target);
      });
    });
  }

  function augmentDomainPages() {
    const definitions = [
      ["herd", "Herd Management", "Live animal population, lifecycle and attention signals."],
      ["milk", "Milk Records", "Today's recorded production and animal-level milk evidence."],
      ["health", "Health & Vaccination", "Open observations and severity signals from recorded health events."],
      ["feed", "Feed Management", "Today's recorded feed quantities and feed-event coverage."],
      ["finance", "Financials", "Recorded income, expense and net cash movement — not forecasts."],
      ["breeding", "Breeding & Reproduction", "Recorded insemination, pregnancy diagnosis and calving events."],
    ];
    definitions.forEach(([id, title, subtitle]) => {
      const page = document.getElementById(`page-${id}`);
      if (!page || page.querySelector(".live-page-context")) return;
      const context = document.createElement("div");
      context.className = "panel live-page-context";
      context.innerHTML = `<div class="eyebrow">Operational view</div><h2>${title}</h2><p>${subtitle}</p>`;
      page.prepend(context);
    });
  }

  function patchRefresh() {
    if (window.__dairyosLiveRefreshPatched) return;
    window.__dairyosLiveRefreshPatched = true;
    const original = window.refreshAll;
    window.refreshAll = async function () {
      if (typeof original === "function") await original();
      await refreshLive();
    };
  }

  async function refreshLive() {
    try {
      await loadLiveData();
      renderLiveCockpit();
      augmentDomainPages();
    } catch (error) {
      const root = document.getElementById("live-cockpit");
      if (root) {
        root.querySelector(".live-cockpit-meta")?.insertAdjacentText("beforeend", " · live refresh unavailable");
      }
      console.warn("DairyOS live dashboard refresh failed", error);
    }
  }

  async function initialize() {
    injectStyles();
    patchRefresh();
    await refreshLive();
    window.setInterval(refreshLive, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
