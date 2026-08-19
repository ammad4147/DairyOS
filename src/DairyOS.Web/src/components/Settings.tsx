/*
 * DairyOS Settings section (AA-013 §17, minimal build 2026-08-14).
 *
 * The full roles/preferences Settings section (AA-013 §17) is still
 * pending -- this ships the farm identity, reset controls, and the
 * backend-authoritative Cost of Milk Production scenario surface.
 */

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "../config/api";
import "./Settings.css";

type SettingsPayload = {
    farm_name: string;
    animal_id_prefix: string;
    reset_protected: boolean;
};

type CMPScenario = {
    id: number;
    scenario_id: string;
    name: string;
    created_at: string | null;
    created_by: string;
    period_start: string;
    period_end: string;
    currency: string;
    basis: string;
    selected_cost_domains: string[];
    assumptions: Record<string, unknown>;
    milk_volume_litres: number;
    eligible_cost: number;
    cmp_per_litre: number;
    status: string;
};

const DEFAULT_COST_DOMAINS = [
    "FEED",
    "LABOUR",
    "HEALTH",
    "BREEDING",
    "UTILITIES",
    "EQUIPMENT",
];

async function putJson(path: string, body: unknown) {
    const response = await fetch(apiUrl(path), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error((data && (data.detail as string)) || `Request failed (${response.status})`);
    }
    return data;
}

export default function Settings() {
    const [settings, setSettings] = useState<SettingsPayload | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);

    const [farmName, setFarmName] = useState("");
    const [prefix, setPrefix] = useState("");
    const [identityStatus, setIdentityStatus] = useState<string | null>(null);
    const [identityError, setIdentityError] = useState<string | null>(null);

    const [protectionPassword, setProtectionPassword] = useState("");
    const [protectionStatus, setProtectionStatus] = useState<string | null>(null);
    const [protectionError, setProtectionError] = useState<string | null>(null);

    const [resetPassword, setResetPassword] = useState("");
    const [resetConfirmText, setResetConfirmText] = useState("");
    const [resetStatus, setResetStatus] = useState<string | null>(null);
    const [resetError, setResetError] = useState<string | null>(null);
    const [resetBusy, setResetBusy] = useState(false);
    const [showResetConfirm, setShowResetConfirm] = useState(false);

    const [cmpScenarios, setCmpScenarios] = useState<CMPScenario[]>([]);
    const [cmpName, setCmpName] = useState("");
    const [cmpCreatedBy, setCmpCreatedBy] = useState("UI Operator");
    const [cmpStart, setCmpStart] = useState("");
    const [cmpEnd, setCmpEnd] = useState("");
    const [cmpDomains, setCmpDomains] = useState<string[]>(DEFAULT_COST_DOMAINS);
    const [cmpBusy, setCmpBusy] = useState(false);
    const [cmpStatus, setCmpStatus] = useState<string | null>(null);
    const [cmpError, setCmpError] = useState<string | null>(null);

    const load = useCallback(() => {
        fetch(apiUrl("/settings"), { headers: { Accept: "application/json" } })
            .then((response) => {
                if (!response.ok) throw new Error(`Failed to load settings (${response.status})`);
                return response.json() as Promise<SettingsPayload>;
            })
            .then((payload) => {
                setSettings(payload);
                setFarmName(payload.farm_name);
                setPrefix(payload.animal_id_prefix);
                setLoadError(null);
            })
            .catch((error: Error) => setLoadError(error.message));
    }, []);

    const loadCmpScenarios = useCallback(async () => {
        try {
            const response = await fetch(apiUrl("/farm/cmp/scenarios"), {
                headers: { Accept: "application/json" },
            });
            const body = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(body.detail || `Failed to load CMP scenarios (${response.status})`);
            setCmpScenarios(Array.isArray(body.scenarios) ? body.scenarios : []);
        } catch (error) {
            setCmpError((error as Error).message);
        }
    }, []);

    useEffect(() => {
        load();
        void loadCmpScenarios();
    }, [load, loadCmpScenarios]);

    const saveIdentity = async () => {
        setIdentityStatus(null);
        setIdentityError(null);
        try {
            const updated = await putJson("/settings", { farm_name: farmName, animal_id_prefix: prefix });
            setSettings(updated as SettingsPayload);
            setIdentityStatus("Saved. New animals will use the updated ID prefix.");
        } catch (error) {
            setIdentityError((error as Error).message);
        }
    };

    const saveProtection = async (enabled: boolean) => {
        setProtectionStatus(null);
        setProtectionError(null);
        try {
            const updated = await fetch(apiUrl("/settings/reset-protection"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled, password: enabled ? protectionPassword : undefined }),
            });
            const body = await updated.json();
            if (!updated.ok) throw new Error(body.detail || "Could not update reset protection");
            setSettings(body as SettingsPayload);
            setProtectionStatus(enabled ? "Reset protection is now ON." : "Reset protection is now OFF.");
            setProtectionPassword("");
        } catch (error) {
            setProtectionError((error as Error).message);
        }
    };

    const runReset = async () => {
        setResetBusy(true);
        setResetStatus(null);
        setResetError(null);
        try {
            const response = await fetch(apiUrl("/settings/reset-test-data"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ confirm: resetConfirmText, password: resetPassword || undefined }),
            });
            const body = await response.json();
            if (!response.ok) throw new Error(body.detail || "Reset failed");
            setResetStatus(`All test data cleared (${(body.tables_cleared as string[]).length} tables). New animals start again at ${prefix || "TD"}-001.`);
            setShowResetConfirm(false);
            setResetConfirmText("");
            setResetPassword("");
        } catch (error) {
            setResetError((error as Error).message);
        } finally {
            setResetBusy(false);
        }
    };

    const toggleCmpDomain = (domain: string) => {
        setCmpDomains((current) =>
            current.includes(domain)
                ? current.filter((item) => item !== domain)
                : [...current, domain],
        );
    };

    const createCmpScenario = async () => {
        setCmpBusy(true);
        setCmpStatus(null);
        setCmpError(null);

        try {
            const response = await fetch(apiUrl("/farm/cmp/scenarios"), {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify({
                    name: cmpName,
                    created_by: cmpCreatedBy,
                    period_start: cmpStart,
                    period_end: cmpEnd,
                    selected_cost_domains: cmpDomains,
                    assumptions: {},
                }),
            });
            const body = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(body.detail || `CMP scenario creation failed (${response.status})`);

            const created = body.scenario as CMPScenario;
            setCmpScenarios((current) => [created, ...current]);
            setCmpName("");
            setCmpStatus(`Scenario ${created.scenario_id} created. Actual milk volume and eligible cost remain backend-authoritative.`);
        } catch (error) {
            setCmpError((error as Error).message);
        } finally {
            setCmpBusy(false);
        }
    };

    if (loadError) {
        return (
            <div className="settings-page">
                <p className="settings-error">Could not load Settings: {loadError}</p>
            </div>
        );
    }

    if (!settings) {
        return <div className="settings-page settings-loading">Loading settings…</div>;
    }

    return (
        <div className="settings-page">
            <section className="settings-card">
                <h2>Farm identity</h2>
                <p className="settings-hint">
                    The Animal ID prefix controls new, system-generated Animal IDs (e.g. "TD" produces "TD-001",
                    "TD-002", ...). Changing it only affects animals registered after the change.
                </p>
                <div className="settings-field-row">
                    <label>
                        Farm name
                        <input value={farmName} onChange={(event) => setFarmName(event.target.value)} />
                    </label>
                    <label>
                        Animal ID prefix
                        <input
                            value={prefix}
                            maxLength={6}
                            onChange={(event) => setPrefix(event.target.value.toUpperCase())}
                        />
                    </label>
                </div>
                <button type="button" className="settings-primary-button" onClick={saveIdentity}>
                    Save
                </button>
                {identityStatus && <p className="settings-success">{identityStatus}</p>}
                {identityError && <p className="settings-error">{identityError}</p>}
            </section>

            <section className="settings-card">
                <h2>Cost of Milk Production scenarios</h2>
                <p className="settings-hint">
                    Scenarios are persisted by the backend. Actual milk volume, eligible cost and cost per litre are
                    calculated by the authoritative CMP service; this UI does not calculate or overwrite those values.
                </p>
                <div className="settings-field-row">
                    <label>
                        Scenario name
                        <input value={cmpName} onChange={(event) => setCmpName(event.target.value)} placeholder="Base cost scenario" />
                    </label>
                    <label>
                        Created by
                        <input value={cmpCreatedBy} onChange={(event) => setCmpCreatedBy(event.target.value)} />
                    </label>
                </div>
                <div className="settings-field-row">
                    <label>
                        Period start
                        <input type="date" value={cmpStart} onChange={(event) => setCmpStart(event.target.value)} />
                    </label>
                    <label>
                        Period end
                        <input type="date" value={cmpEnd} onChange={(event) => setCmpEnd(event.target.value)} />
                    </label>
                </div>
                <div>
                    <p className="settings-hint">Cost domains</p>
                    <div className="settings-domain-list">
                        {DEFAULT_COST_DOMAINS.map((domain) => (
                            <label key={domain} className="settings-domain-option">
                                <input
                                    type="checkbox"
                                    checked={cmpDomains.includes(domain)}
                                    onChange={() => toggleCmpDomain(domain)}
                                />
                                {domain}
                            </label>
                        ))}
                    </div>
                </div>
                <button
                    type="button"
                    className="settings-primary-button"
                    disabled={cmpBusy || !cmpName.trim() || !cmpStart || !cmpEnd || cmpDomains.length === 0}
                    onClick={createCmpScenario}
                >
                    {cmpBusy ? "Creating…" : "Create CMP scenario"}
                </button>
                {cmpStatus && <p className="settings-success">{cmpStatus}</p>}
                {cmpError && <p className="settings-error">{cmpError}</p>}

                {cmpScenarios.length > 0 && (
                    <div className="settings-scenario-list">
                        {cmpScenarios.map((scenario) => (
                            <article key={scenario.scenario_id} className="settings-scenario">
                                <div>
                                    <strong>{scenario.name}</strong>
                                    <div className="settings-hint">
                                        {scenario.period_start} → {scenario.period_end} · {scenario.status}
                                    </div>
                                </div>
                                <div className="settings-scenario-metric">
                                    <span>Milk volume</span>
                                    <strong>{Number(scenario.milk_volume_litres).toFixed(2)} L</strong>
                                </div>
                                <div className="settings-scenario-metric">
                                    <span>Eligible cost</span>
                                    <strong>{Number(scenario.eligible_cost).toFixed(2)} {scenario.currency}</strong>
                                </div>
                                <div className="settings-scenario-metric">
                                    <span>CMP</span>
                                    <strong>{Number(scenario.cmp_per_litre).toFixed(2)} {scenario.currency}/L</strong>
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </section>

            <section className="settings-card">
                <h2>Reset protection</h2>
                <p className="settings-hint">
                    Currently <strong>{settings.reset_protected ? "ON" : "OFF"}</strong>. While this farm is still
                    being built out, resets are unprotected for convenience. Turn this on with a password before
                    going live so the reset action below can't be triggered by accident.
                </p>
                {!settings.reset_protected ? (
                    <div className="settings-field-row">
                        <label>
                            Set a password to enable
                            <input
                                type="password"
                                value={protectionPassword}
                                onChange={(event) => setProtectionPassword(event.target.value)}
                            />
                        </label>
                        <button type="button" className="settings-primary-button" onClick={() => saveProtection(true)}>
                            Enable protection
                        </button>
                    </div>
                ) : (
                    <button type="button" className="settings-secondary-button" onClick={() => saveProtection(false)}>
                        Disable protection
                    </button>
                )}
                {protectionStatus && <p className="settings-success">{protectionStatus}</p>}
                {protectionError && <p className="settings-error">{protectionError}</p>}
            </section>

            <section className="settings-card settings-danger-card">
                <h2>Reset all test data</h2>
                <p className="settings-hint">
                    Permanently clears every animal, milk record, health case, finding, transaction and every other
                    operational record in the database — this farm's own Settings (name and prefix) are kept. This
                    cannot be undone. Use it once, before going live, to clear out test entries.
                </p>
                {!showResetConfirm ? (
                    <button type="button" className="settings-danger-button" onClick={() => setShowResetConfirm(true)}>
                        Reset all test data…
                    </button>
                ) : (
                    <div className="settings-reset-confirm">
                        <label>
                            Type RESET to confirm
                            <input value={resetConfirmText} onChange={(event) => setResetConfirmText(event.target.value)} />
                        </label>
                        {settings.reset_protected && (
                            <label>
                                Reset password
                                <input
                                    type="password"
                                    value={resetPassword}
                                    onChange={(event) => setResetPassword(event.target.value)}
                                />
                            </label>
                        )}
                        <div className="settings-reset-actions">
                            <button
                                type="button"
                                className="settings-danger-button"
                                disabled={resetConfirmText !== "RESET" || resetBusy}
                                onClick={runReset}
                            >
                                {resetBusy ? "Clearing…" : "Confirm reset"}
                            </button>
                            <button
                                type="button"
                                className="settings-secondary-button"
                                onClick={() => {
                                    setShowResetConfirm(false);
                                    setResetConfirmText("");
                                    setResetPassword("");
                                    setResetError(null);
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
                {resetStatus && <p className="settings-success">{resetStatus}</p>}
                {resetError && <p className="settings-error">{resetError}</p>}
            </section>
        </div>
    );
}