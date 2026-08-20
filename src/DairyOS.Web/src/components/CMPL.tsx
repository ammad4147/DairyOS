import { useState, useEffect, useCallback } from "react";
import { apiUrl } from "../config/api";
import "./Settings.css";

export default function CMPLTab() {
  const [cmpScenarios, setCmpScenarios] = useState<any[]>([]);
  const loadCmpScenarios = useCallback(async () => {
    try {
      const response = await fetch(apiUrl("/farm/cmp/scenarios"), { headers: { Accept: "application/json" }});
      const body = await response.json();
      if (response.ok) setCmpScenarios(Array.isArray(body.scenarios) ? body.scenarios : []);
    } catch {}
  }, []);
  useEffect(() => { loadCmpScenarios(); }, [loadCmpScenarios]);

  return (
    <div style={{ padding: '20px' }}>
      <section className="settings-card">
        <h2>CMPL Scenarios (Cost of Milk Production per Liter)</h2>
        <p className="settings-hint">Authoritative calculation based on milk yields and entered expenses.</p>
        <button className="settings-primary-button" style={{ marginBottom: '16px' }}>+ New CMPL Scenario</button>
        <div className="settings-scenario-list">
          {cmpScenarios.length > 0 ? cmpScenarios.map(s => (
            <article key={s.scenario_id} className="settings-scenario">
              <div><strong>{s.name}</strong><div className="settings-hint">{s.period_start} → {s.period_end}</div></div>
              <div className="settings-scenario-metric"><span>Milk volume</span><strong>{Number(s.milk_volume_litres).toFixed(2)} L</strong></div>
              <div className="settings-scenario-metric"><span>CMPL</span><strong>{Number(s.cmp_per_litre).toFixed(2)} {s.currency}/L</strong></div>
            </article>
          )) : <p className="settings-hint">No scenarios created yet.</p>}
        </div>
      </section>
    </div>
  );
}
