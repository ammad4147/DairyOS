import React, {
    useEffect,
    useMemo,
    useState,
} from "react";

import type {
    DashboardResponse,
    DashboardRuntime,
    OperationalDecision,
    OperationalState,
} from "../models/dashboard";

import {
    getDashboard,
} from "../api/dashboardClient";

import "./CommandCenter.css";

import StatusCard from "./StatusCard";
import AttentionPanel from "./AttentionPanel";
import OperationalAreas from "./OperationalAreas";
import ProductionCard from "./ProductionCard";
import HerdCard from "./HerdCard";
import FeedCard from "./FeedCard";
import FreshnessCard from "./FreshnessCard";

function CommandCenter() {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);

    const loadDashboard = async () => {
        setLoading(true);
        setError(null);

        try {
            const payload = await getDashboard();

            setDashboard(payload);
            setLastUpdated(new Date().toLocaleTimeString());
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load the live farm dashboard.",
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadDashboard();

        const timer = window.setInterval(() => {
            void loadDashboard();
        }, 60_000);

        return () => window.clearInterval(timer);
    }, []);

    const runtimeDashboard: DashboardRuntime = useMemo(
        () => dashboard?.dashboard ?? {},
        [dashboard],
    );

    const operationalState: OperationalState = useMemo(
        () =>
            dashboard?.operational_state
            ?? runtimeDashboard.operational_state
            ?? {},
        [dashboard, runtimeDashboard],
    );

    const farmStatus = useMemo(() => {
        const value =
            dashboard?.farm_status
            ?? runtimeDashboard.farm_status
            ?? "UNKNOWN";

        if (typeof value === "string") {
            return value;
        }

        if (value && typeof value === "object") {
            return String(
                value.status
                ?? value.state
                ?? value.farm_status
                ?? "UNKNOWN",
            );
        }

        return "UNKNOWN";
    }, [dashboard, runtimeDashboard]);

    const systemHealth = String(
        dashboard?.health
        ?? runtimeDashboard.health
        ?? "UNKNOWN",
    );

    const decisions: OperationalDecision[] =
        dashboard?.operational_decisions
        ?? runtimeDashboard.operational_decisions
        ?? [];

    const zones =
        dashboard?.dashboard_view?.layout?.zones
        ?? [];

    const milkZone = zones.find((zone) => zone.zone_id === "milk");
    const herdZone = zones.find((zone) => zone.zone_id === "herd");

    const ownerAttention =
        dashboard?.dashboard_view?.owner_attention
        ?? [];

    const eventCount =
        runtimeDashboard.event_count
        ?? dashboard?.event_count
        ?? 0;

    const quickActions =
        dashboard?.dashboard_view?.quick_actions
        ?? [];

    if (loading && !dashboard) {
        return (
            <div className="command-center">
                <div className="farm-loading">
                    Loading live farm operations…
                </div>
            </div>
        );
    }

    if (error && !dashboard) {
        return (
            <div className="command-center">
                <div className="farm-error">
                    <div>
                        <strong>Unable to load the live farm picture.</strong>
                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        onClick={() => void loadDashboard()}
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    if (!dashboard) {
        return null;
    }

    return (
        <main className="command-center">
            <header className="farm-header">
                <div>
                    <span className="farm-eyebrow">
                        TRIDENT DAIRIES
                    </span>

                    <h1>Farm Operations</h1>

                    <p>
                        Live operating picture, decisions and farm performance.
                    </p>
                </div>

                <div className="farm-header-actions">
                    <div className="farm-live-indicator">
                        <span className="live-dot" />
                        {loading ? "Refreshing" : "Live"}

                        {lastUpdated && (
                            <small>
                                {lastUpdated}
                            </small>
                        )}
                    </div>

                    <button
                        type="button"
                        className="farm-refresh"
                        onClick={() => void loadDashboard()}
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>
            </header>

            {error && (
                <div className="farm-refresh-warning">
                    <strong>Refresh warning</strong>
                    <span>{error}</span>
                </div>
            )}

            <section className="farm-status-strip">
                <div className="farm-status-main">
                    <span>Farm status</span>
                    <strong>{farmStatus}</strong>
                </div>

                <div>
                    <span>System</span>
                    <strong>{systemHealth}</strong>
                </div>

                <div>
                    <span>Operational events</span>
                    <strong>{eventCount}</strong>
                </div>

                <div>
                    <span>Owner attention</span>
                    <strong>{ownerAttention.length || decisions.filter(
                        (decision) => decision.owner_action_required,
                    ).length}</strong>
                </div>
            </section>

            <section className="farm-primary-grid">
                <div className="farm-panel farm-panel-large">
                    <ProductionCard
                        milk={runtimeDashboard.milk}
                        widgets={milkZone?.widgets}
                    />
                </div>

                <div className="farm-panel farm-panel-large">
                    <HerdCard
                        animals={operationalState.animals}
                        widgets={herdZone?.widgets}
                    />
                </div>
            </section>

            <section className="farm-secondary-grid">
                <div className="farm-panel">
                    <FeedCard
                        feed={runtimeDashboard.feed}
                    />
                </div>

                <div className="farm-panel">
                    <FreshnessCard
                        freshness={runtimeDashboard.freshness}
                    />
                </div>

                <div className="farm-panel">
                    <StatusCard
                        title="Health decisions"
                        value={decisions.filter(
                            (decision) => String(decision.type).toLowerCase() === "health",
                        ).length}
                    />
                </div>
            </section>

            {quickActions.length > 0 && (
                <section className="farm-panel quick-actions-panel">
                    <div className="panel-heading">
                        <div>
                            <span className="card-eyebrow">ACTION</span>
                            <h2>Quick Actions</h2>
                        </div>
                    </div>

                    <div className="quick-actions">
                        {quickActions.map((action, index) => (
                            <button
                                type="button"
                                key={String(action.id ?? index)}
                                className="quick-action"
                            >
                                {String(action.title ?? action.id ?? "Action")}
                            </button>
                        ))}
                    </div>
                </section>
            )}

            <section className="farm-panel attention-panel">
                <div className="panel-heading">
                    <div>
                        <span className="card-eyebrow">DECISIONS</span>
                        <h2>Attention Required</h2>
                    </div>
                </div>

                <AttentionPanel
                    decisions={
                        ownerAttention.length > 0
                            ? ownerAttention
                            : decisions
                    }
                />
            </section>

            <section className="farm-panel">
                <div className="panel-heading">
                    <div>
                        <span className="card-eyebrow">OPERATIONS</span>
                        <h2>Operational Areas</h2>
                    </div>
                </div>

                <OperationalAreas
                    state={operationalState}
                />
            </section>
        </main>
    );
}

export default CommandCenter;
