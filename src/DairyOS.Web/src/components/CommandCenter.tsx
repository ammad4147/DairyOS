import React, { useEffect, useMemo, useState } from "react";

import type {
    DashboardResponse,
    DashboardRuntime,
    OperationalDecision,
    OperationalState,
} from "../models/dashboard";

import { getDashboard } from "../api/dashboardClient";

import "./CommandCenter.css";
import ProductionCard from "./ProductionCard";
import HerdCard from "./HerdCard";
import FeedCard from "./FeedCard";
import AttentionPanel from "./AttentionPanel";

type Props = {
    onOpenAnimal?: (animalId: string) => void;
};

function CommandCenter({
    onOpenAnimal,
}: Props) {
    const [dashboard, setDashboard] =
        useState<DashboardResponse | null>(null);

    const [error, setError] =
        useState<string | null>(null);

    const [loading, setLoading] =
        useState(true);

    const [lastUpdated, setLastUpdated] =
        useState<string | null>(null);

    const loadDashboard = async () => {
        setLoading(true);
        setError(null);

        try {
            const payload = await getDashboard();

            setDashboard(payload);
            setLastUpdated(
                new Date().toLocaleTimeString(),
            );
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load live farm operations.",
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadDashboard();

        const timer = window.setInterval(
            () => void loadDashboard(),
            60_000,
        );

        return () =>
            window.clearInterval(timer);
    }, []);

    const runtimeDashboard: DashboardRuntime =
        useMemo(
            () => dashboard?.dashboard ?? {},
            [dashboard],
        );

    const operationalState: OperationalState =
        useMemo(
            () =>
                dashboard?.operational_state
                ?? runtimeDashboard.operational_state
                ?? {},
            [dashboard, runtimeDashboard],
        );

    const decisions: OperationalDecision[] =
        dashboard?.operational_decisions
        ?? runtimeDashboard.operational_decisions
        ?? [];

    const zones =
        dashboard?.dashboard_view?.layout?.zones
        ?? [];

    const milkZone = zones.find(
        (zone) => zone.zone_id === "milk",
    );

    const herdZone = zones.find(
        (zone) => zone.zone_id === "herd",
    );

    const ownerAttention =
        dashboard?.dashboard_view?.owner_attention
        ?? [];

    const attentionItems =
        ownerAttention.length > 0
            ? ownerAttention
            : decisions.filter(
                (decision) =>
                    decision.owner_action_required
                    || [
                        "critical",
                        "high",
                        "medium",
                    ].includes(
                        String(
                            decision.priority,
                        ).toLowerCase(),
                    ),
            );

    if (loading && !dashboard) {
        return (
            <main className="command-center">
                <div className="farm-loading">
                    Loading farm operations…
                </div>
            </main>
        );
    }

    if (error && !dashboard) {
        return (
            <main className="command-center">
                <div className="farm-error">
                    <div>
                        <strong>
                            Unable to load live farm operations.
                        </strong>
                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        onClick={() =>
                            void loadDashboard()
                        }
                    >
                        Retry
                    </button>
                </div>
            </main>
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
                        Production, herd management,
                        feeding and actionable
                        notifications.
                    </p>
                </div>

                <div className="farm-header-actions">
                    <div className="farm-live-indicator">
                        <span className="live-dot" />
                        {loading
                            ? "Refreshing"
                            : "Live"}

                        {lastUpdated && (
                            <small>
                                {lastUpdated}
                            </small>
                        )}
                    </div>

                    <button
                        type="button"
                        className="farm-refresh"
                        onClick={() =>
                            void loadDashboard()
                        }
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>
            </header>

            {error && (
                <div className="farm-refresh-warning">
                    <strong>
                        Refresh warning
                    </strong>

                    <span>{error}</span>
                </div>
            )}

            <section className="farm-primary-grid">
                <div className="farm-panel farm-panel-large">
                    <ProductionCard
                        milk={runtimeDashboard.milk}
                        widgets={milkZone?.widgets}
                    />
                </div>

                <div className="farm-panel farm-panel-large">
                    <HerdCard
                        animals={
                            operationalState.animals
                        }
                        widgets={
                            herdZone?.widgets
                        }
                        onOpenAnimal={
                            onOpenAnimal
                        }
                    />
                </div>
            </section>

            <section className="farm-secondary-grid">
                <div className="farm-panel">
                    <FeedCard
                        feed={runtimeDashboard.feed}
                    />
                </div>

                <div className="farm-panel attention-panel">
                    <div className="panel-heading">
                        <div>
                            <span className="card-eyebrow">
                                NOTIFICATIONS
                            </span>

                            <h2>
                                Attention Required
                            </h2>
                        </div>
                    </div>

                    <AttentionPanel
                        decisions={
                            attentionItems
                        }
                        onOpenAnimal={
                            onOpenAnimal
                        }
                    />
                </div>
            </section>
        </main>
    );
}

export default CommandCenter;
