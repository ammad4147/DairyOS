import React, { useMemo } from "react";

import type { DashboardMilkSummary, DashboardWidget } from "../models/dashboard";

interface Props {
    milk?: DashboardMilkSummary;
    widgets?: DashboardWidget[];
}

function numberValue(value: unknown): number | null {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatLitres(value: unknown): string {
    const numeric = numberValue(value);

    if (numeric === null) {
        return "—";
    }

    return `${numeric.toLocaleString()} L`;
}

function formatNumber(value: unknown): string {
    const numeric = numberValue(value);

    if (numeric === null) {
        return "—";
    }

    return numeric.toLocaleString();
}

function trendText(milk: DashboardMilkSummary): string {
    if (milk.trend !== undefined && milk.trend !== null && milk.trend !== "") {
        return String(milk.trend);
    }

    if (milk.trend_percent !== undefined && milk.trend_percent !== null) {
        const prefix = milk.trend_percent > 0 ? "+" : "";
        return `${prefix}${milk.trend_percent.toFixed(1)}%`;
    }

    const today = numberValue(milk.today_litres);
    const yesterday = numberValue(milk.yesterday_litres ?? milk.previous_day_litres);

    if (today !== null && yesterday !== null && yesterday !== 0) {
        const percent = ((today - yesterday) / yesterday) * 100;
        const prefix = percent > 0 ? "+" : "";
        return `${prefix}${percent.toFixed(1)}%`;
    }

    return "—";
}

function trendClass(milk: DashboardMilkSummary): string {
    const direction = String(milk.trend_direction ?? "").toLowerCase();

    if (direction === "up" || direction === "positive" || direction === "improving") {
        return "production-trend positive";
    }

    if (direction === "down" || direction === "negative" || direction === "declining") {
        return "production-trend negative";
    }

    const today = numberValue(milk.today_litres);
    const yesterday = numberValue(milk.yesterday_litres ?? milk.previous_day_litres);

    if (today !== null && yesterday !== null) {
        if (today > yesterday) return "production-trend positive";
        if (today < yesterday) return "production-trend negative";
    }

    return "production-trend neutral";
}

function getHistory(milk: DashboardMilkSummary) {
    const raw = milk.trend_history ?? milk.history;

    if (!Array.isArray(raw)) {
        return [];
    }

    return raw
        .map((item) => ({
            date: String(item.date ?? ""),
            litres: numberValue(item.litres ?? item.value),
        }))
        .filter((item) => item.litres !== null)
        .slice(-14);
}

function ProductionCard({ milk = {}, widgets = [] }: Props) {
    const history = useMemo(() => getHistory(milk), [milk]);

    const today = numberValue(milk.today_litres);
    const yesterday = numberValue(milk.yesterday_litres ?? milk.previous_day_litres);
    const average = numberValue(
        milk.seven_day_average_litres
        ?? milk.thirty_day_average_litres,
    );

    const maxHistory = Math.max(
        ...history.map((item) => item.litres ?? 0),
        today ?? 0,
        1,
    );

    return (
        <section className="production-card">
            <div className="production-card-heading">
                <div>
                    <span className="card-eyebrow">MILK OPERATIONS</span>
                    <h2>Milk Production</h2>
                </div>

                <span className="production-status">
                    {String(milk.production_status ?? "Live")}
                </span>
            </div>

            <div className="production-primary">
                <div>
                    <span>Today</span>
                    <strong>{formatLitres(milk.today_litres)}</strong>
                </div>

                <div className="production-trend-box">
                    <span>Trend</span>
                    <strong className={trendClass(milk)}>
                        {trendText(milk)}
                    </strong>
                </div>
            </div>

            <div className="production-stat-grid">
                <div>
                    <span>Yesterday</span>
                    <strong>{formatLitres(yesterday)}</strong>
                </div>

                <div>
                    <span>7-day average</span>
                    <strong>{formatLitres(average)}</strong>
                </div>

                <div>
                    <span>Current shift</span>
                    <strong>{formatLitres(milk.current_shift_litres)}</strong>
                </div>

                <div>
                    <span>Events</span>
                    <strong>{formatNumber(milk.events)}</strong>
                </div>
            </div>

            <div className="production-shifts">
                <div>
                    <span>Morning</span>
                    <strong>{formatLitres(milk.morning_litres)}</strong>
                </div>

                <div>
                    <span>Afternoon</span>
                    <strong>{formatLitres(milk.afternoon_litres)}</strong>
                </div>

                <div>
                    <span>Evening</span>
                    <strong>{formatLitres(milk.evening_litres)}</strong>
                </div>

                <div>
                    <span>Shift</span>
                    <strong>{milk.current_shift ?? milk.last_shift ?? "—"}</strong>
                </div>
            </div>

            {history.length > 0 && (
                <div className="production-history">
                    <div className="section-label">
                        Production trend
                    </div>

                    <div className="trend-chart" aria-label="Milk production trend">
                        {history.map((point, index) => {
                            const height = Math.max(
                                8,
                                ((point.litres ?? 0) / maxHistory) * 100,
                            );

                            return (
                                <div className="trend-point" key={`${point.date}-${index}`}>
                                    <div className="trend-bar-wrap">
                                        <div
                                            className="trend-bar"
                                            style={{ height: `${height}%` }}
                                            title={`${point.date}: ${formatLitres(point.litres)}`}
                                        />
                                    </div>

                                    <span>
                                        {point.date
                                            ? point.date.slice(5)
                                            : String(index + 1)}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {history.length === 0 && (
                <div className="production-history-empty">
                    <span className="section-label">Production trend</span>
                    <p>
                        Historical milk readings will appear here as trend data
                        becomes available from the operational API.
                    </p>
                </div>
            )}

            <div className="production-footer">
                <span>
                    Latest operator: <strong>{milk.last_operator ?? "—"}</strong>
                </span>

                {widgets.length > 0 && (
                    <div className="production-widget-summary">
                        {widgets
                            .filter((widget) => widget.widget_id !== "milk.today")
                            .slice(0, 3)
                            .map((widget) => (
                                <span key={widget.widget_id}>
                                    {widget.title}: <strong>{widget.value ?? "—"}</strong>
                                </span>
                            ))}
                    </div>
                )}
            </div>
        </section>
    );
}

export default ProductionCard;
