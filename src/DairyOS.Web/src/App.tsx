/*
 * DairyOS Web App
 * Operator-facing dairy workflow.
 *
 * The normal operator model deliberately avoids exposing:
 *   - milking-frequency history
 *   - effective-date frequency changes
 *   - veterinary directive mechanics
 *
 * Those remain backend-governed capabilities for exceptional/admin use.
 */

import { useEffect, useMemo, useState } from "react";

import MainDashboard from "./components/MainDashboard";
import AnimalRegistry from "./components/AnimalRegistry";
import OperationalModule from "./components/OperationalModule";
import Settings from "./components/Settings";
import type { OperationalEntryConfig } from "./components/OperationalEntryPanel";
import "./App.css";
import { apiUrl } from "./config/api";

type ViewId =
    | "command"
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
    | "alerts"
    | "settings";

type NavigationItem = {
    id: ViewId;
    label: string;
    description: string;
    endpoint?: string;
    selector?: string;
    mode?: "cards" | "entries" | "decisions" | "state";
    entry?: OperationalEntryConfig;
};

const animalField = {
    name: "animal_id",
    label: "Animal",
    type: "animal" as const,
    required: true,
};

const operatorField = {
    name: "operator",
    label: "Operator",
    type: "text" as const,
    required: true,
    placeholder: "Person entering this record",
};

const entryConfigs: Record<string, OperationalEntryConfig> = {
    /*
     * Milk has a dedicated operator-facing entry panel.
     *
     * The panel derives the animal's 2-session/3-session plan from the
     * authoritative backend schedule and presents only the session
     * applicable to the selected animal.
     */
    milk: {
        endpoint: "/farm/milk",
        title: "Record Milk",
        description:
            "Select a milking animal, choose the current session, and enter its yield.",
        fields: [
            animalField,
            operatorField,
        ],
    },

    feed: {
        endpoint: "/farm/feed",
        title: "Record Feed Activity",
        description:
            "Record feed consumption with quantity, location or animal attribution.",
        fields: [
            {
                name: "feed_type",
                label: "Feed Type",
                type: "text",
                required: true,
                placeholder: "Silage, TMR, hay…",
            },
            {
                name: "quantity_kg",
                label: "Quantity (kg)",
                type: "number",
                required: true,
                step: "0.01",
            },
            {
                name: "group_or_pen",
                label: "Group / Pen",
                type: "text",
                placeholder: "Pen A",
            },
            {
                name: "animal_id",
                label: "Animal (optional)",
                type: "animal",
            },
            operatorField,
        ],
    },

    health: {
        endpoint: "/farm/health-observations",
        title: "Record Health Observation",
        description:
            "Capture an attributable observation that can drive health attention and decisions.",
        fields: [
            animalField,
            {
                name: "observation",
                label: "Observation",
                type: "textarea",
                required: true,
                placeholder: "What did you observe?",
            },
            {
                name: "symptom",
                label: "Symptom",
                type: "text",
                placeholder: "Optional symptom",
            },
            {
                name: "temperature_c",
                label: "Temperature (°C)",
                type: "number",
                step: "0.1",
            },
            {
                name: "severity",
                label: "Severity",
                type: "select",
                required: true,
                options: ["NORMAL", "ELEVATED", "HIGH", "CRITICAL"],
            },
            operatorField,
        ],
    },

    breeding: {
        endpoint: "/farm/breeding",
        title: "Record Reproduction Event",
        description:
            "Record heat, insemination, pregnancy, calving and other reproductive events.",
        fields: [
            animalField,
            {
                name: "event_type",
                label: "Event",
                type: "select",
                required: true,
                options: [
                    "heat_detected",
                    "insemination",
                    "pregnancy_diagnosis",
                    "pregnancy_confirmed",
                    "pregnancy_negative",
                    "dry_off",
                    "calving",
                    "abortion",
                    "stillbirth",
                    "postpartum_observation",
                ],
            },
            {
                name: "technician",
                label: "Technician",
                type: "text",
                placeholder: "Dr Vet",
            },
            {
                name: "result",
                label: "Result",
                type: "text",
                placeholder: "Completed / confirmed / negative…",
            },
            {
                name: "semen_or_bull",
                label: "Semen / Bull",
                type: "text",
            },
            {
                name: "notes",
                label: "Notes",
                type: "textarea",
            },
            operatorField,
        ],
    },

    workforce: {
        endpoint: "/farm/workforce",
        title: "Record Workforce Activity",
        description:
            "Record who performed an activity, what was done and its completion status.",
        fields: [
            {
                name: "worker_id",
                label: "Worker ID",
                type: "text",
                required: true,
                placeholder: "WORKER-001",
            },
            {
                name: "activity",
                label: "Activity",
                type: "text",
                required: true,
                placeholder: "Milking, feeding, cleaning…",
            },
            {
                name: "task",
                label: "Task",
                type: "text",
            },
            {
                name: "status",
                label: "Status",
                type: "select",
                options: ["ASSIGNED", "IN_PROGRESS", "COMPLETED", "MISSED"],
            },
            {
                name: "hours",
                label: "Hours",
                type: "number",
                step: "0.25",
            },
            {
                name: "location",
                label: "Location",
                type: "text",
            },
            {
                name: "notes",
                label: "Notes",
                type: "textarea",
            },
            operatorField,
        ],
    },

    inventory: {
        endpoint: "/farm/inventory",
        title: "Record Inventory Movement",
        description:
            "Record stock receipts, consumption, transfers, wastage or adjustments.",
        fields: [
            {
                name: "item",
                label: "Item",
                type: "text",
                required: true,
                placeholder: "Silage, medicine, semen…",
            },
            {
                name: "quantity",
                label: "Quantity",
                type: "number",
                required: true,
                step: "0.01",
                placeholder:
                    "Positive except signed for Transfer/Adjustment",
            },
            {
                name: "movement_type",
                label: "Movement",
                type: "select",
                required: true,
                options: [
                    "PURCHASE",
                    "RECEIPT",
                    "CONSUMPTION",
                    "TRANSFER",
                    "WASTAGE",
                    "ADJUSTMENT",
                ],
            },
            {
                name: "unit",
                label: "Unit",
                type: "text",
                placeholder: "kg, L, doses…",
            },
            {
                name: "location",
                label: "Location",
                type: "text",
            },
            {
                name: "supplier",
                label: "Supplier",
                type: "text",
            },
            {
                name: "notes",
                label: "Notes",
                type: "textarea",
            },
            operatorField,
        ],
    },

    equipment: {
        endpoint: "/farm/equipment",
        title: "Record Equipment Activity",
        description:
            "Record inspection, maintenance, breakdown and operating status.",
        fields: [
            {
                name: "equipment_id",
                label: "Equipment ID",
                type: "text",
                required: true,
                placeholder: "MILKER-001",
            },
            {
                name: "activity",
                label: "Activity",
                type: "text",
                required: true,
                placeholder: "Inspection, maintenance, breakdown…",
            },
            {
                name: "status",
                label: "Status",
                type: "select",
                options: [
                    "OPERATIONAL",
                    "WARNING",
                    "OUT_OF_SERVICE",
                    "MAINTENANCE",
                ],
            },
            {
                name: "running_hours",
                label: "Running Hours",
                type: "number",
                step: "0.1",
            },
            {
                name: "location",
                label: "Location",
                type: "text",
            },
            {
                name: "notes",
                label: "Notes",
                type: "textarea",
            },
            operatorField,
        ],
    },

    finance: {
        endpoint: "/farm/financial",
        title: "Record Financial Transaction",
        description:
            "Capture operational income, expense, payment and cash transactions with provenance.",
        fields: [
            {
                name: "transaction_type",
                label: "Transaction Type",
                type: "select",
                required: true,
                options: [
                    "INCOME",
                    "EXPENSE",
                    "RECEIPT",
                    "PAYMENT",
                    "OWNER_WITHDRAWAL",
                    "LOAN_PAYMENT",
                ],
            },
            {
                name: "amount",
                label: "Amount (PKR)",
                type: "number",
                required: true,
                step: "0.01",
            },
            {
                name: "transaction_date",
                label: "Date of Transaction",
                type: "date",
            },
            {
                name: "category",
                label: "Category",
                type: "select",
                options: [
                    "MILK_SALES",
                    "FEED",
                    "HEALTH",
                    "BREEDING",
                    "LABOUR",
                    "UTILITIES",
                    "EQUIPMENT",
                    "OTHER_OPERATING",
                ],
            },
            {
                name: "payment_method",
                label: "Payment Method",
                type: "select",
                options: ["CASH", "BANK", "MOBILE", "CREDIT"],
            },
            {
                name: "counterparty",
                label: "Counterparty",
                type: "text",
            },
            {
                name: "notes",
                label: "Notes",
                type: "textarea",
            },
            operatorField,
        ],
    },
};

const navigation: NavigationItem[] = [
    {
        id: "command",
        label: "Dashboard",
        description: "Live farm operational picture",
    },
    {
        id: "animals",
        label: "Animals",
        description: "Herd, lifecycle and animal records",
        endpoint: "/farm/animals",
        mode: "cards",
    },
    {
        id: "milk",
        label: "Milk",
        description: "Simple session-based milk recording",
        endpoint: "/farm/milk",
        mode: "entries",
        entry: entryConfigs.milk,
    },
    {
        id: "feed",
        label: "Feeding",
        description: "Feeding activity and quantities",
        endpoint: "/farm/feed",
        mode: "entries",
        entry: entryConfigs.feed,
    },
    {
        id: "health",
        label: "Health",
        description: "Health observations and attention",
        endpoint: "/farm/health-observations",
        mode: "entries",
        entry: entryConfigs.health,
    },
    {
        id: "breeding",
        label: "Breeding",
        description: "Reproduction events and reproductive history",
        endpoint: "/farm/breeding",
        mode: "entries",
        entry: entryConfigs.breeding,
    },
    {
        id: "workforce",
        label: "Workforce",
        description: "Workforce activity and accountability",
        endpoint: "/farm/workforce",
        mode: "entries",
        entry: entryConfigs.workforce,
    },
    {
        id: "inventory",
        label: "Inventory",
        description: "Stock movements and consumption",
        endpoint: "/farm/inventory",
        mode: "entries",
        entry: entryConfigs.inventory,
    },
    {
        id: "equipment",
        label: "Equipment",
        description: "Equipment activity and maintenance",
        endpoint: "/farm/equipment",
        mode: "entries",
        entry: entryConfigs.equipment,
    },
    {
        id: "finance",
        label: "Finance",
        description: "Operational financial transactions",
        endpoint: "/farm/financial",
        mode: "entries",
        entry: entryConfigs.finance,
    },
    {
        id: "analytics",
        label: "Analytics",
        description: "Production and operating indicators",
        endpoint: "/operations/dashboard",
        mode: "state",
    },
    {
        id: "alerts",
        label: "Alerts & Decisions",
        description: "Operational decisions requiring attention",
        endpoint: "/dashboard",
        selector: "operational_decisions",
        mode: "decisions",
    },
    {
        id: "settings",
        label: "Settings",
        description: "Farm identity and test-data reset",
    },
];

function App() {
    const [view, setView] = useState<ViewId>("command");
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const [systemHealth, setSystemHealth] = useState("CHECKING");
    const [farmStatus, setFarmStatus] = useState("CHECKING");
    const [farmName, setFarmName] = useState("Trident Dairies");

    useEffect(() => {
        let cancelled = false;

        fetch(apiUrl("/settings"))
            .then((response) => {
                if (!response.ok) throw new Error("Settings fetch failed");
                return response.json() as Promise<{ farm_name?: string }>;
            })
            .then((payload) => {
                if (!cancelled && payload.farm_name) {
                    setFarmName(payload.farm_name);
                }
            })
            .catch(() => {});

        fetch(apiUrl("/health"))
            .then((response) => {
                if (!response.ok) throw new Error("Health check failed");
                return response.json() as Promise<{ status?: string }>;
            })
            .then((payload) => {
                if (!cancelled) {
                    setSystemHealth(payload.status ?? "HEALTHY");
                }
            })
            .catch(() => {
                if (!cancelled) setSystemHealth("OFFLINE");
            });

        fetch(apiUrl("/operations/dashboard"))
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Operations dashboard failed");
                }
                return response.json() as Promise<{ farm_status?: string }>;
            })
            .then((payload) => {
                if (!cancelled) {
                    setFarmStatus(payload.farm_status ?? "UNKNOWN");
                }
            })
            .catch(() => {
                if (!cancelled) setFarmStatus("UNAVAILABLE");
            });

        return () => {
            cancelled = true;
        };
    }, []);

    const activeNavigation = useMemo(
        () =>
            navigation.find((item) => item.id === view) ??
            navigation[0],
        [view],
    );

    const selectView = (nextView: ViewId) => {
        setView(nextView);
        setMobileNavOpen(false);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    return (
        <div className="dairyos-shell">
            <header className="dairyos-topbar">
                <div className="brand-block">
                    <button
                        className="mobile-menu-button"
                        type="button"
                        aria-label="Toggle navigation"
                        onClick={() =>
                            setMobileNavOpen((open) => !open)
                        }
                    >
                        ☰
                    </button>

                    <div className="brand-mark">D</div>

                    <div>
                        <div className="brand-name">DairyOS</div>
                        <div className="brand-subtitle">{farmName}</div>
                    </div>
                </div>

                <div className="topbar-status">
                    <div className="status-pill">
                        <span
                            className={`status-dot ${
                                systemHealth === "OFFLINE"
                                    ? "danger"
                                    : "live"
                            }`}
                        />
                        <span>System {systemHealth}</span>
                    </div>

                    <div className="status-pill">
                        <span>Farm</span>
                        <strong>{farmStatus}</strong>
                    </div>

                    <div className="status-pill">
                        <span>Currency</span>
                        <strong>PKR</strong>
                    </div>
                </div>
            </header>

            <div className="dairyos-body">
                <aside
                    className={`dairyos-sidebar ${
                        mobileNavOpen ? "open" : ""
                    }`}
                >
                    <div className="sidebar-heading">OPERATIONS</div>

                    <nav aria-label="DairyOS navigation">
                        {navigation.map((item) => (
                            <button
                                key={item.id}
                                type="button"
                                className={`nav-item ${
                                    view === item.id ? "active" : ""
                                }`}
                                onClick={() => selectView(item.id)}
                            >
                                <span className="nav-label">
                                    {item.label}
                                </span>

                                {item.id === "alerts" && (
                                    <span className="nav-badge">!</span>
                                )}
                            </button>
                        ))}
                    </nav>

                    <div className="sidebar-footer">
                        <div className="sidebar-footer-title">
                            Operational OS
                        </div>
                        <div className="sidebar-footer-text">
                            Live state is supplied by the DairyOS APIs.
                        </div>
                    </div>
                </aside>

                {mobileNavOpen && (
                    <button
                        className="sidebar-backdrop"
                        type="button"
                        aria-label="Close navigation"
                        onClick={() => setMobileNavOpen(false)}
                    />
                )}

                <main className="dairyos-main">
                    {view === "command" ? (
                        <MainDashboard onNavigate={selectView} />
                    ) : view === "animals" ? (
                        <AnimalRegistry onNavigate={selectView} />
                    ) : view === "settings" ? (
                        <>
                            <div className="page-heading">
                                <div>
                                    <div className="breadcrumb">
                                        DairyOS / {activeNavigation.label}
                                    </div>
                                    <h1>{activeNavigation.label}</h1>
                                    <p>
                                        {activeNavigation.description}
                                    </p>
                                </div>
                            </div>

                            <Settings />
                        </>
                    ) : (
                        <>
                            <div className="page-heading">
                                <div>
                                    <div className="breadcrumb">
                                        DairyOS / {activeNavigation.label}
                                    </div>
                                    <h1>{activeNavigation.label}</h1>
                                    <p>
                                        {activeNavigation.description}
                                    </p>
                                </div>

                                <div className="page-meta">
                                    Live API view
                                </div>
                            </div>

                            <OperationalModule
                                title={activeNavigation.label}
                                endpoint={
                                    activeNavigation.endpoint ??
                                    "/dashboard"
                                }
                                selector={activeNavigation.selector}
                                mode={
                                    activeNavigation.mode ?? "state"
                                }
                                entry={activeNavigation.entry}
                            />
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}

export default App;
