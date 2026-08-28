import { useCallback, useEffect, useMemo, useState } from "react";
import "./OperationalModule.css";
import OperationalEntryPanel, {
    type OperationalEntryConfig,
} from "./OperationalEntryPanel";
import { apiUrl } from "../config/api";
import OperatorDataBlock from "./OperatorDataBlock";

type Mode = "cards" | "entries" | "decisions" | "state";
type TabId =
    | "animals"
    | "milk"
    | "feed"
    | "health"
    | "breeding"
    | "workforce"
    | "inventory"
    | "equipment"
    | "finance"
    | "analytics"
    | "alerts";

type Props = {
    title: string;
    tabId: TabId;
    endpoint?: string;
    selector?: string;
    mode: Mode;
    entry?: OperationalEntryConfig;
};

type Row = Record<string, unknown>;
type TabState = {
    tab_id: string;
    contract_version: string;
    source: string;
    source_detail?: string;
    farm_id: string;
    operational_date: string;
    status: "ACTIVE" | "NO_DATA" | "ATTENTION" | string;
    state: Record<string, unknown>;
};

const DISPLAY_FIELDS: Record<TabId, string[]> = {
    animals: ["animal_id", "animal_type", "breed", "sex", "lifecycle_status", "is_currently_milking", "milking_frequency", "production_group", "location", "non_milking_reason"],
    milk: ["production_date", "animal_id", "milking_session", "total_yield", "status", "operator"],
    feed: ["timestamp", "animal_id", "feed_type", "quantity_kg", "group_or_pen", "operator"],
    health: ["timestamp", "animal_id", "observation", "symptom", "severity", "status", "operator"],
    breeding: ["timestamp", "animal_id", "event_type", "technician", "result", "operator"],
    workforce: ["timestamp", "worker_id", "activity", "task", "status", "hours", "operator"],
    inventory: ["timestamp", "item", "quantity", "movement_type", "unit", "location", "operator"],
    equipment: ["timestamp", "equipment_id", "activity", "status", "running_hours", "location", "operator"],
    finance: ["timestamp", "transaction_type", "category", "amount", "payment_method", "counterparty", "operator"],
    analytics: [],
    alerts: ["priority", "title", "animal_id", "action", "source", "status"],
};

const TAB_HELP: Record<TabId, string> = {
    animals: "Current herd identity and operational state are read from the authoritative Animal Register projection.",
    milk: "Milk records are displayed against the authoritative farm operational date; the tab does not recalculate production locally.",
    feed: "Feeding activity and current feeding state are supplied by the DairyOS API.",
    health: "Health observations and attention state are supplied by the governed health projection.",
    breeding: "Reproductive events and current breeding state are supplied by the DairyOS API.",
    workforce: "Workforce activity is displayed from the live API without local task or workload classification.",
    inventory: "Inventory movements and current stock state are supplied by the canonical inventory services.",
    equipment: "Equipment activity and current equipment state are supplied by the live API.",
    finance: "Financial records and current financial state are displayed without frontend income, expense, or balance calculations.",
    analytics: "Analytics is a read-only presentation of server-produced operational indicators.",
    alerts: "Operational decisions and attention items are displayed as supplied by the command-center projection.",
};

function text(value: unknown): string {
    if (value === null || value === undefined || value === "") {
        return "";
    }

    if (typeof value === "object") {
        return "Information available.";
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    const raw = String(value).trim();
    if (!raw) return "";

    const normalized = raw.toUpperCase();

    const friendly: Record<string, string> = {
        ACTIVE: "Active",
        INACTIVE: "Inactive",
        ATTENTION: "Needs attention",

        CURRENT: "Current",
        COMPLETE: "Complete",
        COMPLETED: "Completed",
        OPEN: "Open",
        CLOSED: "Closed",
        PENDING: "Pending",
        WARNING: "Warning",
        CRITICAL: "Critical",
        GREEN: "Normal",
        AMBER: "Needs attention",
        RED: "Critical",
        HIGH: "High",
        MEDIUM: "Medium",
        LOW: "Low",
        NONE: "None",
        TRUE: "Yes",
        FALSE: "No",
        HEIFER: "Heifer",
        LACTATING: "Milking",
        DRY: "Dry",
        CALF: "Calf",
        FEMALE: "Female",
        MALE: "Male",
        TWICE_DAILY: "Twice daily",
        THREE_TIMES_DAILY: "Three times daily",
        NOT_PREGNANT: "Not pregnant",
        PREGNANT: "Pregnant",
        NOT_PLANNED: "Not planned",
        NON_MILKING: "Not milking",
        OUT_OF_SERVICE: "Out of service",
        MAINTENANCE: "Maintenance due",
        MISSED: "Missed",
        RECEIVED: "Received",
        RECEIVABLE: "Receivable",
        PAYABLE: "Payable",
        PAID: "Paid",
        VOID: "Voided",
        NO_DATA: "",
    };

    if (friendly[normalized]) {
        return friendly[normalized];
    }

    return raw
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function label(value: string): string {
    return value
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function statusClass(value: unknown): string {
    const normalized = String(value ?? "").toLowerCase();
    if (/critical|failed|error|overdue|out_of_service|missed|negative|red/.test(normalized)) return "danger";
    if (/warning|watch|pending|open|due|elevated|maintenance|amber/.test(normalized)) return "warning";
    return "good";
}

function selectValue(payload: unknown, selector?: string): unknown {
    if (!selector) return payload;
    return selector.split(".").reduce<unknown>((current, key) => {
        if (!current || typeof current !== "object") return undefined;
        return (current as Record<string, unknown>)[key];
    }, payload);
}

function stateRows(tabId: TabId, state: Record<string, unknown>): Row[] {
    if (tabId === "animals") {
        const animals = state.animals;
        if (!animals || typeof animals !== "object" || Array.isArray(animals)) return [];
        return Object.values(animals as Record<string, Row>);
    }
    return [];
}

function stateEntries(state: Record<string, unknown>): Array<[string, unknown]> {
    return Object.entries(state).filter(([, value]) => value !== null && value !== undefined);
}

function recordRows(payload: unknown): Row[] {
    if (Array.isArray(payload)) return payload.filter((value): value is Row => Boolean(value) && typeof value === "object");
    return [];
}

export default function UnifiedOperationalTab({
    title,
    tabId,
    endpoint,
    selector,
    mode,
    entry,
}: Props) {
    const [tabState, setTabState] = useState<TabState | null>(null);
    const [records, setRecords] = useState<Row[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [updated, setUpdated] = useState<string | null>(null);
    const [query, setQuery] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const tabResponse = await fetch(apiUrl(`/operations/tab-state/${tabId}`), {
                headers: { Accept: "application/json" },
            });
            if (!tabResponse.ok) throw new Error(`Tab state request failed: ${tabResponse.status}`);
            const authoritative = (await tabResponse.json()) as TabState;
            setTabState(authoritative);

            if (tabId === "animals") {
                setRecords(stateRows(tabId, authoritative.state));
            } else if (endpoint && mode !== "state") {
                const response = await fetch(apiUrl(endpoint), {
                    headers: { Accept: "application/json" },
                });
                if (!response.ok) throw new Error(`Record request failed: ${response.status}`);
                const payload = await response.json();
                setRecords(recordRows(selectValue(payload, selector)));
            } else {
                setRecords([]);
            }

            setUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Unable to load live DairyOS data");
        } finally {
            setLoading(false);
        }
    }, [endpoint, mode, selector, tabId]);

    useEffect(() => {
        void load();
        const timer = window.setInterval(() => void load(), 60_000);
        return () => window.clearInterval(timer);
    }, [load]);

    const filteredRecords = useMemo(() => {
        const needle = query.trim().toLowerCase();
        if (!needle) return records;
        return records.filter((row) => JSON.stringify(row).toLowerCase().includes(needle));
    }, [query, records]);

    const visibleColumns = useMemo(() => {
        const configured = DISPLAY_FIELDS[tabId];
        return configured.filter((column) => filteredRecords.some((row) => row[column] !== undefined && row[column] !== null && row[column] !== ""));
    }, [filteredRecords, tabId]);

    const summaryEntries = useMemo(() => stateEntries(tabState?.state ?? {}), [tabState]);

    if (loading && !tabState) {
        return (
            <section className="module-view">
                {entry && <OperationalEntryPanel config={entry} onSaved={load} />}
                <div className="module-loading">
                    <span className="loading-mark" />
                    <strong>Loading {title.toLowerCase()}</strong>
                    <span>Reading the authoritative DairyOS tab contract…</span>
                </div>
            </section>
        );
    }

    if (error && !tabState) {
        return (
            <section className="module-view">
                {entry && <OperationalEntryPanel config={entry} onSaved={load} />}
                <div className="module-error">
                    <div><strong>Unable to load live data.</strong><p>{error}</p></div>
                    <button type="button" onClick={() => void load()}>Retry</button>
                </div>
            </section>
        );
    }

    return (
        <section className="module-view">
            {entry && <OperationalEntryPanel config={entry} onSaved={load} />}
            <div className="module-header-row">
                <div>
                    <div className="module-kicker">LIVE OPERATIONS</div>
                    <h2>{title}</h2>
                    <p>{TAB_HELP[tabId]}</p>
                </div>
                <div className="module-actions">
                    <span className="live-chip"><i />LIVE</span>
                    <button type="button" onClick={() => void load()}>Refresh</button>
                </div>
            </div>

            <div className="module-summary">
                <Summary label="Operational date" value={tabState?.operational_date ?? "—"} />
                <Summary label="Farm" value={tabState?.farm_id ?? ""} />

                <Summary label="State" value={tabState?.status ?? "—"} tone={statusClass(tabState?.status)} />
                <Summary label="Records" value={records.length || (tabId === "animals" ? stateRows(tabId, tabState?.state ?? {}).length : "—")} />
            </div>

            {error && (
                <div className="module-error compact">
                    <div><strong>Record view warning</strong><p>{error}</p></div>
                    <button type="button" onClick={() => void load()}>Retry</button>
                </div>
            )}

            {mode === "state" || tabId === "analytics" ? (
                <StateGrid entries={summaryEntries} />
            ) : mode === "decisions" || tabId === "alerts" ? (
                <DecisionView rows={filteredRecords} state={tabState?.state ?? {}} />
            ) : mode === "cards" || tabId === "animals" ? (
                <AnimalTable rows={filteredRecords} />
            ) : (
                <>
                    <div className="module-toolbar">
                        <div>
                            <strong>{filteredRecords.length.toLocaleString()} record{filteredRecords.length === 1 ? "" : "s"}</strong>
                            {updated && <span>Updated {updated}</span>}
                        </div>
                        <label className="search-box">
                            <span>⌕</span>
                            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search records" />
                        </label>
                    </div>
                    <RecordTable rows={filteredRecords} columns={visibleColumns} />
                </>
            )}
        </section>
    );
}

function Summary({ label: heading, value, tone = "neutral" }: { label: string; value: unknown; tone?: string }) {
    return <div className={`summary-box ${tone}`}><span>{heading}</span><strong>{text(value)}</strong></div>;
}

function StateGrid({ entries }: { entries: Array<[string, unknown]> }) {
    if (!entries.length) return <EmptyState title="No operational state yet" />;
    return (
        <div className="state-grid">
            {entries.map(([key, value]) => (
                <div className="state-card" key={key}>
                    <div className="state-card-title">{label(key)}</div>
                    <div className="state-card-value"><OperatorDataBlock value={value} /></div>
                </div>
            ))}
        </div>
    );
}

function AnimalTable({ rows }: { rows: Row[] }) {
    if (!rows.length) return <EmptyState title="No animal records in this view" />;
    return (
        <div className="data-table-wrap">
            <table className="data-table">
                <thead><tr><th>Animal</th><th>Breed</th><th>Lifecycle</th><th>Operational</th><th>Plan</th><th>Location</th></tr></thead>
                <tbody>
                    {rows.slice(0, 250).map((row, index) => (
                        <tr key={String(row.animal_id ?? index)}>
                            <td><strong>{text(row.animal_id)}</strong></td>
                            <td>{text(row.breed)}</td>
                            <td>{text(row.lifecycle_status)}</td>
                            <td><span className={`status-chip ${statusClass(row.is_currently_milking ? "MILKING" : row.non_milking_reason ?? row.status)}`}>{row.is_currently_milking ? "MILKING" : text(row.non_milking_reason ?? row.status)}</span></td>
                            <td>{text(row.milking_frequency)}</td>
                            <td>{text(row.location)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function friendlySource(value: unknown): string {
    if (value === null || value === undefined || value === "") {
        return "";
    }

    const normalized = String(value).trim().toLowerCase();

    const friendly: Record<string, string> = {
        missing_input: "Daily farm records",
        inventory: "Inventory records",
        workforce: "Workforce records",
        equipment: "Equipment records",
        financial: "Financial records",
        milk: "Milk records",
        feeding: "Feeding records",
        health: "Health records",
        breeding: "Breeding records",
        command_center: "Farm operations",
    };

    return friendly[normalized]
        ?? normalized
            .replaceAll("_", " ")
            .replace(/\b\w/g, (character) => character.toUpperCase());
}
function DecisionView({ rows, state }: { rows: Row[]; state: Record<string, unknown> }) {
    const stateRows = [
        ...(Array.isArray(state.exceptions) ? state.exceptions : []),
        ...(Array.isArray(state.heads_up_notifications) ? state.heads_up_notifications : []),
        ...(Array.isArray(state.unhandled_events) ? state.unhandled_events : []),
    ].filter((value): value is Row => Boolean(value) && typeof value === "object");
    const combined = rows.length ? rows : stateRows;
    if (!combined.length) return <EmptyState title="No active attention items" />;
    return (
        <div className="data-table-wrap">
            <table className="data-table">
                <thead><tr><th>Priority</th><th>Title / Event</th><th>Animal</th><th>Action</th><th>Source</th><th>Status</th></tr></thead>
                <tbody>
                    {combined.slice(0, 150).map((row, index) => (
                        <tr key={String(row.id ?? row.decision_id ?? index)} className="decision-row">
                            <td><span className={`status-chip ${statusClass(row.priority)}`}>{text(row.priority)}</span></td>
                            <td>{text(row.title ?? row.event_type ?? row.observation ?? row.message)}</td>
                            <td>{text(row.animal_id)}</td>
                            <td>{text(row.action ?? row.recommended_action)}</td>
                            <td>{friendlySource(row.source)}</td>
                            <td>{text(row.status)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function RecordTable({ rows, columns }: { rows: Row[]; columns: string[] }) {
    if (!rows.length) return <EmptyState title="No records in this view" />;
    const visible = columns.length ? columns : Object.keys(rows[0]);
    return (
        <div className="data-table-wrap">
            <table className="data-table">
                <thead><tr>{visible.map((column) => <th key={column}>{label(column)}</th>)}</tr></thead>
                <tbody>
                    {rows.slice(0, 150).map((row, index) => (
                        <tr key={String(row.id ?? row.timestamp ?? index)}>{visible.map((column) => <td key={column}><Cell value={row[column]} /></td>)}</tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function Cell({ value }: { value: unknown }) {
    const rendered = text(value);
    const shouldBadge = rendered.length < 28 && /critical|warning|open|active|completed|recorded|operational|out_of_service|maintenance|missed/i.test(rendered);
    return shouldBadge ? <span className={`status-chip ${statusClass(rendered)}`}>{rendered}</span> : <span className="cell-text">{rendered}</span>;
}

function EmptyState({ title }: { title: string }) {
    return <div className="empty-state"><strong>{title}</strong></div>;
}
