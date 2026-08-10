import React, {
    useEffect,
    useMemo,
    useState,
} from "react";

import "./OperationalModule.css";

import OperationalEntryPanel, {
    type OperationalEntryConfig,
} from "./OperationalEntryPanel";

type Mode = "cards" | "entries" | "decisions" | "state";

type Props = {
    title: string;
    endpoint: string;
    selector?: string;
    mode: Mode;
    entry?: OperationalEntryConfig;
};

type Primitive = string | number | boolean | null;
type JsonValue =
    | Primitive
    | JsonValue[]
    | { [key: string]: JsonValue };

function readPath(
    value: JsonValue,
    selector?: string,
): JsonValue {
    if (!selector) {
        return value;
    }

    return selector
        .split(".")
        .reduce<JsonValue>((current, key) => {
            if (
                current &&
                typeof current === "object" &&
                !Array.isArray(current) &&
                key in current
            ) {
                return current[key];
            }

            return null;
        }, value);
}

function displayValue(value: JsonValue): string {
    if (value === null || value === undefined) {
        return "—";
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}

function objectEntries(
    value: JsonValue,
): Array<[string, JsonValue]> {
    if (
        !value ||
        typeof value !== "object" ||
        Array.isArray(value)
    ) {
        return [];
    }

    return Object.entries(value);
}

function OperationalModule({
    title,
    endpoint,
    selector,
    mode,
    entry,
}: Props) {
    const [payload, setPayload] = useState<JsonValue | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);

    const load = async () => {
        const controller = new AbortController();

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `http://localhost:8000${endpoint}`,
                {
                    method: "GET",
                    headers: {
                        Accept: "application/json",
                    },
                    cache: "no-store",
                    signal: controller.signal,
                },
            );

            if (!response.ok) {
                let detail = `Request failed: ${response.status}`;

                try {
                    const body = await response.json() as {
                        detail?: string;
                    };

                    if (body.detail) {
                        detail = body.detail;
                    }
                } catch {
                    // Preserve the HTTP error when response is not JSON.
                }

                throw new Error(detail);
            }

            const data = await response.json() as JsonValue;

            setPayload(readPath(data, selector));
            setLastUpdated(new Date().toLocaleTimeString());
        } catch (requestError) {
            if (
                requestError instanceof DOMException &&
                requestError.name === "AbortError"
            ) {
                return;
            }

            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load operational data.",
            );
        } finally {
            setLoading(false);
        }

        return () => controller.abort();
    };

    useEffect(() => {
        let active = true;

        const initialLoad = async () => {
            if (!active) {
                return;
            }

            await load();
        };

        void initialLoad();

        const timer = window.setInterval(() => {
            if (active) {
                void load();
            }
        }, 60_000);

        return () => {
            active = false;
            window.clearInterval(timer);
        };
    }, [endpoint, selector]);

    const arrayRows = useMemo(() => {
        if (Array.isArray(payload)) {
            return payload.slice(0, 100);
        }

        return [];
    }, [payload]);

    if (loading && payload === null) {
        return (
            <section className="module-view">
                {entry && (
                    <OperationalEntryPanel
                        config={entry}
                        onSaved={() => void load()}
                    />
                )}

                <div className="module-loading">
                    Loading {title.toLowerCase()} data…
                </div>
            </section>
        );
    }

    if (error && payload === null) {
        return (
            <section className="module-view">
                {entry && (
                    <OperationalEntryPanel
                        config={entry}
                        onSaved={() => void load()}
                    />
                )}

                <div className="module-error">
                    <div>
                        <strong>
                            Unable to load live data.
                        </strong>

                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        onClick={() => void load()}
                    >
                        Retry
                    </button>
                </div>
            </section>
        );
    }

    if (mode === "cards") {
        return (
            <section className="module-view">
                {entry && (
                    <OperationalEntryPanel
                        config={entry}
                        onSaved={() => void load()}
                    />
                )}

                <ModuleToolbar
                    count={arrayRows.length}
                    updated={lastUpdated}
                    onRefresh={() => void load()}
                />

                {arrayRows.length > 0 ? (
                    <div className="animal-grid">
                        {arrayRows.map((row, index) => (
                            <AnimalCard
                                key={index}
                                value={row}
                            />
                        ))}
                    </div>
                ) : (
                    <EmptyState title="No animal records yet" />
                )}
            </section>
        );
    }

    if (mode === "entries" || mode === "decisions") {
        return (
            <section className="module-view">
                {entry && (
                    <OperationalEntryPanel
                        config={entry}
                        onSaved={() => void load()}
                    />
                )}

                <ModuleToolbar
                    count={arrayRows.length}
                    updated={lastUpdated}
                    onRefresh={() => void load()}
                />

                {arrayRows.length > 0 ? (
                    <div className="record-list">
                        {arrayRows.map((row, index) => (
                            <RecordCard
                                key={index}
                                value={row}
                                decision={mode === "decisions"}
                            />
                        ))}
                    </div>
                ) : (
                    <EmptyState title="No records yet" />
                )}
            </section>
        );
    }

    if (mode === "state") {
        return (
            <section className="module-view">
                {entry && (
                    <OperationalEntryPanel
                        config={entry}
                        onSaved={() => void load()}
                    />
                )}

                <ModuleToolbar
                    count={null}
                    updated={lastUpdated}
                    onRefresh={() => void load()}
                />

                {objectEntries(payload).length > 0 ? (
                    <div className="state-grid">
                        {objectEntries(payload).map(
                            ([key, value]) => (
                                <div
                                    className="state-card"
                                    key={key}
                                >
                                    <div className="state-card-title">
                                        {formatLabel(key)}
                                    </div>

                                    <div className="state-card-value">
                                        {typeof value === "object"
                                            ? (
                                                <pre>
                                                    {JSON.stringify(
                                                        value,
                                                        null,
                                                        2,
                                                    )}
                                                </pre>
                                            )
                                            : displayValue(value)}
                                    </div>
                                </div>
                            ),
                        )}
                    </div>
                ) : (
                    <EmptyState
                        title="No operational data yet"
                    />
                )}
            </section>
        );
    }

    return (
        <section className="module-view">
            {entry && (
                <OperationalEntryPanel
                    config={entry}
                    onSaved={() => void load()}
                />
            )}

            <ModuleToolbar
                count={
                    Array.isArray(payload)
                        ? payload.length
                        : null
                }
                updated={lastUpdated}
                onRefresh={() => void load()}
            />

            <EmptyState title="No records yet" />
        </section>
    );
}

function ModuleToolbar({
    count,
    updated,
    onRefresh,
}: {
    count: number | null;
    updated: string | null;
    onRefresh: () => void;
}) {
    return (
        <div className="module-toolbar">
            <div>
                <strong>
                    {count === null
                        ? "Operational state"
                        : `${count} record${count === 1 ? "" : "s"}`}
                </strong>

                {updated && (
                    <span>
                        Updated {updated}
                    </span>
                )}
            </div>

            <button
                type="button"
                onClick={onRefresh}
            >
                Refresh
            </button>
        </div>
    );
}

function AnimalCard({
    value,
}: {
    value: JsonValue;
}) {
    const entries = objectEntries(value);

    const get = (key: string) =>
        entries.find(
            ([entryKey]) => entryKey === key,
        )?.[1] ?? null;

    return (
        <article className="animal-card">
            <div className="animal-card-topline">
                <span className="animal-tag">
                    {displayValue(
                        get("ear_tag")
                        || get("animal_id"),
                    )}
                </span>

                <span className="animal-status">
                    {displayValue(
                        get("lifecycle_status")
                        || get("status"),
                    )}
                </span>
            </div>

            <h2>
                {displayValue(get("animal_id"))}
            </h2>

            <div className="animal-meta">
                <div>
                    <span>Breed</span>
                    <strong>
                        {displayValue(get("breed"))}
                    </strong>
                </div>

                <div>
                    <span>Sex</span>
                    <strong>
                        {displayValue(get("sex"))}
                    </strong>
                </div>

                <div>
                    <span>Milking</span>
                    <strong>
                        {get("is_currently_milking")
                            ? "Yes"
                            : "No"}
                    </strong>
                </div>

                <div>
                    <span>Location</span>
                    <strong>
                        {displayValue(get("location"))}
                    </strong>
                </div>
            </div>
        </article>
    );
}

function RecordCard({
    value,
    decision,
}: {
    value: JsonValue;
    decision: boolean;
}) {
    const entries = objectEntries(value);

    const importantKeys = [
        "animal_id",
        "worker_id",
        "equipment_id",
        "item",
        "transaction_type",
        "amount",
        "feed_type",
        "quantity_kg",
        "quantity",
        "litres",
        "total_yield",
        "severity",
        "observation",
        "event_type",
        "title",
        "priority",
        "action",
        "timestamp",
        "operator",
        "source",
        "status",
        "activity",
        "technician",
        "result",
        "category",
        "payment_method",
        "counterparty",
        "movement_type",
        "unit",
        "location",
    ];

    const important = entries.filter(
        ([key]) => importantKeys.includes(key),
    );

    return (
        <article
            className={
                `record-card ${decision ? "decision-card" : ""}`
            }
        >
            <div className="record-card-header">
                <strong>
                    {displayValue(
                        entries.find(
                            ([key]) => key === "title",
                        )?.[1]
                        ?? entries.find(
                            ([key]) => key === "animal_id",
                        )?.[1]
                        ?? entries.find(
                            ([key]) => key === "item",
                        )?.[1]
                        ?? entries.find(
                            ([key]) => key === "transaction_type",
                        )?.[1]
                        ?? "Operational record",
                    )}
                </strong>

                <span>
                    {displayValue(
                        entries.find(
                            ([key]) => key === "priority",
                        )?.[1]
                        ?? entries.find(
                            ([key]) => key === "status",
                        )?.[1]
                        ?? "RECORDED",
                    )}
                </span>
            </div>

            <div className="record-fields">
                {important.map(
                    ([key, fieldValue]) => (
                        <div key={key}>
                            <span>
                                {formatLabel(key)}
                            </span>

                            <strong>
                                {displayValue(fieldValue)}
                            </strong>
                        </div>
                    ),
                )}
            </div>
        </article>
    );
}

function EmptyState({
    title,
}: {
    title: string;
}) {
    return (
        <div className="empty-state">
            <div className="empty-state-icon">
                ✓
            </div>

            <strong>{title}</strong>

            <span>
                The API is available, but there is
                nothing to display here yet.
            </span>
        </div>
    );
}

function formatLabel(value: string): string {
    return value
        .replace(/_/g, " ")
        .replace(
            /\b\w/g,
            (character) => character.toUpperCase(),
        );
}

export default OperationalModule;
