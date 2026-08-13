import React, { useEffect, useMemo, useState } from "react";

import {
    listAnimals,
    recordOperationalEntry,
    type OperationalEntry,
} from "../api/farmEntryClient";

import "./OperationalEntryPanel.css";

type FieldType = "text" | "number" | "textarea" | "select" | "animal";

export type EntryField = {
    name: string;
    label: string;
    type: FieldType;
    required?: boolean;
    placeholder?: string;
    options?: string[];
    step?: string;
};

export type OperationalEntryConfig = {
    endpoint: string;
    title: string;
    description: string;
    fields: EntryField[];
};

type Props = {
    config: OperationalEntryConfig;
    onSaved: () => void;
};

function OperationalEntryPanel({ config, onSaved }: Props) {
    const [values, setValues] = useState<Record<string, string>>({});
    const [animals, setAnimals] = useState<OperationalEntry[]>([]);
    const [loadingAnimals, setLoadingAnimals] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const hasAnimalField = useMemo(
        () => config.fields.some((field) => field.type === "animal"),
        [config.fields],
    );

    useEffect(() => {
        if (!hasAnimalField) {
            setAnimals([]);
            return;
        }

        let active = true;
        setLoadingAnimals(true);
        listAnimals<OperationalEntry[]>()
            .then((items) => {
                if (active) setAnimals(Array.isArray(items) ? items : []);
            })
            .catch(() => {
                if (active) setAnimals([]);
            })
            .finally(() => {
                if (active) setLoadingAnimals(false);
            });

        return () => {
            active = false;
        };
    }, [hasAnimalField]);

    useEffect(() => {
        setValues({});
        setMessage(null);
        setError(null);
    }, [config.endpoint]);

    const setValue = (name: string, value: string) => {
        setValues((current) => ({ ...current, [name]: value }));
        setMessage(null);
        setError(null);
    };

    const submit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSaving(true);
        setMessage(null);
        setError(null);

        try {
            const payload: OperationalEntry = {};

            for (const field of config.fields) {
                const value = values[field.name]?.trim() ?? "";

                if (field.required && !value) {
                    throw new Error(`${field.label} is required.`);
                }

                if (!value) continue;

                if (field.type === "number") {
                    const numericValue = Number(value);
                    if (!Number.isFinite(numericValue)) {
                        throw new Error(`${field.label} must be a valid number.`);
                    }
                    payload[field.name] = numericValue;
                } else {
                    payload[field.name] = value;
                }
            }

            await recordOperationalEntry(config.endpoint, payload);
            setValues({});
            setMessage("Entry recorded successfully.");
            onSaved();
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to record the entry.",
            );
        } finally {
            setSaving(false);
        }
    };

    return (
        <section className="entry-panel">
            <div className="entry-panel-header">
                <div>
                    <div className="entry-eyebrow">OPERATIONAL INPUT</div>
                    <h2>{config.title}</h2>
                    <p>{config.description}</p>
                </div>
                <span className="entry-live-badge">Writes to DairyOS</span>
            </div>

            <form className="entry-form" onSubmit={submit}>
                {config.fields.map((field) => (
                    <label
                        className={`entry-field ${field.type === "textarea" ? "wide" : ""}`}
                        key={field.name}
                    >
                        <span>
                            {field.label}
                            {field.required && <b> *</b>}
                        </span>

                        {field.type === "textarea" ? (
                            <textarea
                                value={values[field.name] ?? ""}
                                placeholder={field.placeholder}
                                required={field.required}
                                rows={3}
                                onChange={(event) => setValue(field.name, event.target.value)}
                            />
                        ) : field.type === "animal" ? (
                            <select
                                value={values[field.name] ?? ""}
                                required={field.required}
                                disabled={loadingAnimals}
                                onChange={(event) => setValue(field.name, event.target.value)}
                            >
                                <option value="">
                                    {loadingAnimals ? "Loading animals..." : "Select animal"}
                                </option>
                                {animals.map((animal) => {
                                    const animalId = String(animal.animal_id ?? animal.id ?? "");
                                    const earTag = String(animal.ear_tag ?? "");
                                    if (!animalId) return null;

                                    return (
                                        <option key={animalId} value={animalId}>
                                            {animalId}{earTag ? ` — ${earTag}` : ""}
                                        </option>
                                    );
                                })}
                            </select>
                        ) : field.type === "select" ? (
                            <select
                                value={values[field.name] ?? ""}
                                required={field.required}
                                onChange={(event) => setValue(field.name, event.target.value)}
                            >
                                <option value="">Select...</option>
                                {(field.options ?? []).map((option) => (
                                    <option key={option} value={option}>
                                        {option}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <input
                                type={field.type === "number" ? "number" : "text"}
                                value={values[field.name] ?? ""}
                                placeholder={field.placeholder}
                                required={field.required}
                                step={field.type === "number" ? (field.step ?? "any") : undefined}
                                onChange={(event) => setValue(field.name, event.target.value)}
                            />
                        )}
                    </label>
                ))}

                <div className="entry-actions">
                    <button type="submit" disabled={saving}>
                        {saving ? "Recording..." : "Record Entry"}
                    </button>
                    {message && <span className="entry-success">{message}</span>}
                    {error && <span className="entry-error">{error}</span>}
                </div>
            </form>
        </section>
    );
}

export default OperationalEntryPanel;
