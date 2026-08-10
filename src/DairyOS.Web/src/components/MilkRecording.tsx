import React, { useEffect, useState } from "react";

import "./MilkRecording.css";

type MilkDashboard = {
    yesterday_litres: number;
    seven_day_average_litres: number;
    seven_day_total_litres: number;
    yield_drop_threshold_percent: number;
    daily_trend: Array<{
        date: string;
        litres: number;
    }>;
    animal_ranking: Array<{
        animal_id: string;
        litres: number;
    }>;
    yield_drop_alerts: Array<{
        animal_id: string;
        previous_litres: number;
        latest_litres: number;
        drop_percent: number;
        severity: string;
        message: string;
    }>;
};

type Props = {
    onOpenAnimal?: (animalId: string) => void;
};

function MilkRecording({
    onOpenAnimal,
}: Props) {
    const [data, setData] =
        useState<MilkDashboard | null>(null);

    const [threshold, setThreshold] =
        useState(20);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState<string | null>(null);

    const load = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `http://localhost:8000/farm/milk/intelligence?threshold_percent=${threshold}`,
                {
                    cache: "no-store",
                },
            );

            if (!response.ok) {
                throw new Error(
                    `Milk intelligence request failed: ${response.status}`,
                );
            }

            const payload =
                await response.json() as MilkDashboard;

            setData(payload);
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load milk intelligence.",
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void load();

        const timer =
            window.setInterval(
                () => void load(),
                60_000,
            );

        return () =>
            window.clearInterval(timer);
    }, [threshold]);

    if (loading && !data) {
        return (
            <section className="milk-recording">
                <div className="milk-loading">
                    Loading milk intelligence…
                </div>
            </section>
        );
    }

    if (error && !data) {
        return (
            <section className="milk-recording">
                <div className="milk-error">
                    <strong>
                        Unable to load milk intelligence
                    </strong>
                    <span>{error}</span>
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

    if (!data) {
        return null;
    }

    const maxTrend = Math.max(
        ...data.daily_trend.map(
            (row) => row.litres,
        ),
        1,
    );

    return (
        <section className="milk-recording">
            <div className="milk-summary-grid">
                <article className="milk-summary-card">
                    <span>Yesterday</span>
                    <strong>
                        {data.yesterday_litres.toFixed(1)} L
                    </strong>
                </article>

                <article className="milk-summary-card">
                    <span>7-day average</span>
                    <strong>
                        {data.seven_day_average_litres.toFixed(1)} L
                    </strong>
                </article>

                <article className="milk-summary-card">
                    <span>7-day total</span>
                    <strong>
                        {data.seven_day_total_litres.toFixed(1)} L
                    </strong>
                </article>

                <article className="milk-summary-card threshold">
                    <span>Yield-drop alert</span>
                    <label>
                        <input
                            type="number"
                            min="1"
                            max="100"
                            step="1"
                            value={threshold}
                            onChange={(event) =>
                                setThreshold(
                                    Number(
                                        event.target.value,
                                    ),
                                )
                            }
                        />
                        %
                    </label>
                </article>
            </div>

            {data.yield_drop_alerts.length > 0 && (
                <section className="milk-alert-panel">
                    <div className="milk-section-heading">
                        <div>
                            <span className="eyebrow">
                                ATTENTION
                            </span>
                            <h2>
                                Milk yield notifications
                            </h2>
                        </div>
                        <span className="alert-count">
                            {data.yield_drop_alerts.length}
                        </span>
                    </div>

                    <div className="milk-alert-list">
                        {data.yield_drop_alerts.map(
                            (alert) => (
                                <button
                                    className="milk-alert"
                                    key={alert.animal_id}
                                    type="button"
                                    onClick={() =>
                                        onOpenAnimal?.(
                                            alert.animal_id,
                                        )
                                    }
                                >
                                    <span>
                                        <strong>
                                            {alert.animal_id}
                                        </strong>
                                        <small>
                                            {alert.message}
                                        </small>
                                    </span>

                                    <b>
                                        -{alert.drop_percent}%
                                    </b>
                                </button>
                            ),
                        )}
                    </div>
                </section>
            )}

            <div className="milk-intelligence-grid">
                <section className="milk-panel">
                    <div className="milk-section-heading">
                        <div>
                            <span className="eyebrow">
                                PRODUCTION
                            </span>
                            <h2>Daily milk trend</h2>
                        </div>
                    </div>

                    <div className="milk-trend">
                        {data.daily_trend.map(
                            (row) => (
                                <div
                                    className="trend-column"
                                    key={row.date}
                                    title={`${row.date}: ${row.litres.toFixed(1)} L`}
                                >
                                    <div className="trend-value">
                                        {row.litres.toFixed(0)}
                                    </div>

                                    <div className="trend-track">
                                        <div
                                            className="trend-bar"
                                            style={{
                                                height: `${Math.max(3, (row.litres / maxTrend) * 100)}%`,
                                            }}
                                        />
                                    </div>

                                    <small>
                                        {row.date.slice(5)}
                                    </small>
                                </div>
                            ),
                        )}
                    </div>
                </section>

                <section className="milk-panel">
                    <div className="milk-section-heading">
                        <div>
                            <span className="eyebrow">
                                ANIMAL PERFORMANCE
                            </span>
                            <h2>Top animals · 7 days</h2>
                        </div>
                    </div>

                    <div className="milk-ranking">
                        {data.animal_ranking
                            .slice(0, 10)
                            .map((row, index) => (
                                <button
                                    type="button"
                                    className="milk-ranking-row"
                                    key={row.animal_id}
                                    onClick={() =>
                                        onOpenAnimal?.(
                                            row.animal_id,
                                        )
                                    }
                                >
                                    <span className="rank">
                                        {index + 1}
                                    </span>

                                    <span className="animal-link">
                                        {row.animal_id}
                                    </span>

                                    <strong>
                                        {row.litres.toFixed(1)} L
                                    </strong>
                                </button>
                            ))}

                        {data.animal_ranking.length === 0 && (
                            <div className="milk-empty">
                                No animal-linked milk records yet.
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </section>
    );
}

export default MilkRecording;
