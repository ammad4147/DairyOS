import React, {
    useEffect,
    useState
} from "react";

import type {
    DashboardResponse
} from "../models/dashboard";

import {
    getDashboard
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
    const [
        dashboard,
        setDashboard
    ] = useState<DashboardResponse | null>(
        null
    );

    const [
        error,
        setError
    ] = useState<string | null>(
        null
    );

    useEffect(
        () => {
            getDashboard()
                .then(
                    setDashboard
                )
                .catch(
                    error =>
                    setError(
                        error.message
                    )
                );
        },
        []
    );

    if(error){
        return (
            <div className="command-center">
                <h1 className="command-header">
                    DairyOS Command Center
                </h1>
                <p>
                    {error}
                </p>
            </div>
        );
    }

    if(!dashboard){
        return (
            <div className="command-center">
                <h1 className="command-header">
                    DairyOS Command Center
                </h1>
                <p>
                    Loading operational picture...
                </p>
            </div>
        );
    }

    const runtimeDashboard =
        dashboard.dashboard
        ??
        {};

    const operationalState =
        dashboard.operational_state
        ??
        {};

    const milkZone =
        dashboard.dashboard_view.layout.zones.find(
            zone => zone.zone_id === "milk"
        );

    const herdZone =
        dashboard.dashboard_view.layout.zones.find(
            zone => zone.zone_id === "herd"
        );

    return (
        <div className="command-center">
            <h1 className="command-header">
                DairyOS Command Center
            </h1>

            <div className="summary-grid">
                <div className="panel">
                    <StatusCard
                        title="Farm Status"
                        value={
                            dashboard.farm_status
                        }
                    />
                </div>

                <div className="panel">
                    <StatusCard
                        title="System Health"
                        value={
                            dashboard.health
                        }
                    />
                </div>

                <div className="panel">
                    <StatusCard
                        title="Operational Events"
                        value={
                            runtimeDashboard.event_count
                            ??
                            dashboard.event_count
                        }
                    />
                </div>
            </div>

            <div className="operational-grid">
                <div className="panel">
                    <ProductionCard
                        milk={
                            runtimeDashboard.milk
                        }
                        widgets={
                            milkZone?.widgets
                        }
                    />
                </div>

                <div className="panel">
                    <HerdCard
                        animals={
                            operationalState.animals
                        }
                        widgets={
                            herdZone?.widgets
                        }
                    />
                </div>

                <div className="panel">
                    <FeedCard
                        feed={
                            runtimeDashboard.feed
                        }
                    />
                </div>

                <div className="panel">
                    <FreshnessCard
                        freshness={
                            runtimeDashboard.freshness
                        }
                    />
                </div>
            </div>

            <div className="panel attention-panel">
                <AttentionPanel
                    decisions={
                        dashboard.operational_decisions
                    }
                />
            </div>

            <div className="panel">
                <OperationalAreas
                    state={
                        operationalState
                    }
                />
            </div>
        </div>
    );
}

export default CommandCenter;
