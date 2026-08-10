import React, { useMemo } from "react";

import type {
    DashboardWidget,
    OperationalAnimalState,
} from "../models/dashboard";

interface Props {
    animals?: Record<string, OperationalAnimalState>;
    widgets?: DashboardWidget[];
}

function HerdCard({ animals = {}, widgets = [] }: Props) {
    const animalList = useMemo(
        () => Object.entries(animals),
        [animals],
    );

    const lifecycleCounts = useMemo(() => {
        const counts: Record<string, number> = {};

        for (const [, animal] of animalList) {
            const lifecycle = animal.lifecycle ?? {};
            const status = String(
                lifecycle.status
                ?? lifecycle.lifecycle_status
                ?? animal.status
                ?? "unknown",
            ).toLowerCase();

            counts[status] = (counts[status] ?? 0) + 1;
        }

        return counts;
    }, [animalList]);

    const total = animalList.length;

    const milking = animalList.filter(([, animal]) => {
        const value =
            animal.is_currently_milking
            ?? animal.is_milking
            ?? animal.lifecycle?.is_currently_milking;

        return value === true;
    }).length;

    const attention = animalList.filter(([, animal]) => {
        const value =
            animal.needs_attention
            ?? animal.lifecycle?.needs_attention
            ?? animal.attention_required;

        return value === true;
    }).length;

    return (
        <section className="herd-card">
            <div className="herd-card-heading">
                <div>
                    <span className="card-eyebrow">HERD OPERATIONS</span>
                    <h2>Herd</h2>
                </div>

                <span className="herd-count">
                    {total} animals
                </span>
            </div>

            <div className="herd-primary-grid">
                <div>
                    <span>Total</span>
                    <strong>{total}</strong>
                </div>

                <div>
                    <span>Lactating</span>
                    <strong>{milking}</strong>
                </div>

                <div>
                    <span>Dry / other</span>
                    <strong>{Math.max(0, total - milking)}</strong>
                </div>

                <div className={attention > 0 ? "herd-attention active" : "herd-attention"}>
                    <span>Attention</span>
                    <strong>{attention}</strong>
                </div>
            </div>

            {Object.keys(lifecycleCounts).length > 0 && (
                <div className="herd-lifecycle">
                    <div className="section-label">Lifecycle</div>

                    <div className="herd-lifecycle-list">
                        {Object.entries(lifecycleCounts)
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 6)
                            .map(([status, count]) => (
                                <div key={status}>
                                    <span>
                                        {status.replace(/_/g, " ")}
                                    </span>
                                    <strong>{count}</strong>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {widgets.length > 0 && (
                <div className="herd-widgets">
                    {widgets
                        .filter((widget) => widget.widget_id !== "herd.summary")
                        .slice(0, 4)
                        .map((widget) => (
                            <div key={widget.widget_id}>
                                <span>{widget.title}</span>
                                <strong>{widget.value ?? "—"}</strong>
                            </div>
                        ))}
                </div>
            )}

            {total === 0 && (
                <div className="herd-empty">
                    No animal records are currently available.
                </div>
            )}
        </section>
    );
}

export default HerdCard;
