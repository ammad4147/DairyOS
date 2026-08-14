/*
 * DairyOS Settings section (AA-013 §17, minimal build 2026-08-14).
 *
 * The full roles/preferences Settings section (AA-013 §17) is still
 * pending -- this ships the two pieces that were needed immediately:
 * farm identity (farm name + the short Animal ID prefix, e.g. "TD" for
 * Trident Dairies -> animal IDs "TD-001", "TD-002", ...) and the
 * test-data reset action with its optional password gate. Both back
 * onto GET/PUT /settings, POST /settings/reset-protection and
 * POST /settings/reset-test-data.
 */

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "../config/api";
import "./Settings.css";

type SettingsPayload = {
    farm_name: string;
    animal_id_prefix: string;
    reset_protected: boolean;
};

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

    useEffect(() => {
        load();
    }, [load]);

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
