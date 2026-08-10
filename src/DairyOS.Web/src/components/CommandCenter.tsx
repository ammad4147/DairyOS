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
                    : "Unable to load the DairyOS dashboard.",
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

    /*
     * The established backend response currently exposes the operational
     * state inside dashboard.operational_state. Older contract consumers may
     * expose it at the response root. Support both without changing the
     * backend contract.
     */
    const operationalState: OperationalState = useMemo(
        () =>
            dashboard?.operational_state
            ?? runtimeDashboard.operational_state
            ?? {},
        [dashboard, runtimeDashboard],
    );

    const farmStatus = useMemo(
        () => {
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
        },
        [dashboard, runtimeDashboard],
    );

    const systemHealth = useMemo(
        () =>
            dashboard?.health
            ?? runtimeDashboard.health
            ?? "UNKNOWN",
        [dashboard, runtimeDashboard],
    );

    const decisions: OperationalDecision[] = useMemo(
        () =>
            dashboard?.operational_decisions
            ?? runtimeDashboard.operational_decisions
            ?? [],
        [dashboard, runtimeDashboard],
    );

    const zones = useMemo(
        () =>
            dashboard?.dashboard_view?.layout?.zones
            ?? [],
        [dashboard],
    );

    const milkZone = useMemo(
        () =>
            zones.find((zone) => zone.zone_id === "milk"),
        [zones],
    );

    const herdZone = useMemo(
        () =>
            zones.find((zone) => zone.zone_id === "herd"),
        [zones],
    );

    const eventCount =
        runtimeDashboard.event_count
        ?? dashboard?.event_count
        ?? 0;

    if (loading && !dashboard) {
        return (
            <div className="command-center">
                <h1 className="command-header">
                    DairyOS Command Center
                </h1>

                <div className="panel">
                    <p>Loading operational picture…</p>
                </div>
            </div>
        );
    }

    if (error && !dashboard) {
        return (
            <div className="command-center">
                <h1 className="command-header">
                    DairyOS Command Center
                </h1>

                <div className="panel">
                    <strong>Unable to load live dashboard.</strong>
                    <p>{error}</p>

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
        <div className="command-center">
            <div className="command-header-row">
                <div>
                    <h1 className="command-header">
                        DairyOS Command Center
                    </h1>

                    <p className="command-subtitle">
                        Live operational picture for Trident Dairies
                    </p>
                </div>

                <div className="command-live-status">
                    <span>
                        {loading ? "Refreshing…" : "Live"}
                    </span>

                    {lastUpdated && (
                        <small>
                            Updated {lastUpdated}
                        </small>
                    )}

                    <button
                        type="button"
                        onClick={() => void loadDashboard()}
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {error && (
                <div className="panel command-refresh-warning">
                    <strong>Dashboard refresh warning</strong>
                    <span>{error}</span>
                </div>
            )}

            <div className="summary-grid">
                <div className="panel">
                    <StatusCard
                        title="Farm Status"
                        value={farmStatus}
                    />
                </div>

                <div className="panel">
                    <StatusCard
                        title="System Health"
                        value={systemHealth}
                    />
                </div>

                <div className="panel">
                    <StatusCard
                        title="Operational Events"
                        value={eventCount}
                    />
                </div>
            </div>

            <div className="operational-grid">
                <div className="panel">
                    <ProductionCard
                        milk={runtimeDashboard.milk}
                        widgets={milkZone?.widgets}
                    />
                </div>

                <div className="panel">
                    <HerdCard
                        animals={operationalState.animals}
                        widgets={herdZone?.widgets}
                    />
                </div>

                <div className="panel">
                    <FeedCard
                        feed={runtimeDashboard.feed}
                    />
                </div>

                <div className="panel">
                    <FreshnessCard
                        freshness={runtimeDashboard.freshness}
                    />
                </div>
            </div>

            <div className="panel attention-panel">
                <AttentionPanel
                    decisions={decisions}
                />
            </div>

            <div className="panel">
                <OperationalAreas
                    state={operationalState}
                />
            </div>
        </div>
    );
}

export default CommandCenter;
