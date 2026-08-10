import React, { useMemo } from "react";

import type {
    DashboardWidget,
    OperationalAnimalState,
} from "../models/dashboard";

interface Props {
    animals?: Record<string, OperationalAnimalState>;
    widgets?: DashboardWidget[];
}

function normaliseStatus(value: unknown): string {
    return String(value ?? "unknown")
        .trim()
        .toLowerCase()
        .replace(/[_-]+/g, " ");
}

function HerdCard({
    animals = {},
    widgets = [],
}: Props) {
    const animalList = useMemo(
        () => Object.entries(animals),
        [animals],
    );

    const lifecycleCounts = useMemo(() => {
        const counts: Record<string, number> = {};

        for (const [, animal] of animalList) {
            const lifecycle = animal.lifecycle ?? {};

            const status = normaliseStatus(
                lifecycle.status
                ?? lifecycle.lifecycle_status
                ?? animal.status
                ?? "unknown",
            );

            counts[status] =
                (counts[status] ?? 0) + 1;
        }

        return counts;
    }, [animalList]);

    const total = animalList.length;

    const healthAttention = animalList.filter(
        ([, animal]) =>
            Boolean(
                animal.needs_attention
                ?? animal.lifecycle?.needs_attention
                ?? animal.attention_required,
            ),
    ).length;

    const preferredOrder = [
        "calf",
        "calves",
        "heifer",
        "close up",
        "close-up",
        "lactating",
        "milking",
        "dry",
        "sick",
        "pregnant",
        "bull",
        "unknown",
    ];

    const orderedCounts = Object.entries(lifecycleCounts)
        .sort(([left], [right]) => {
            const leftIndex = preferredOrder.indexOf(left);
            const rightIndex = preferredOrder.indexOf(right);

            if (leftIndex === -1 && rightIndex === -1) {
                return left.localeCompare(right);
            }

            if (leftIndex === -1) return 1;
            if (rightIndex === -1) return -1;

            return leftIndex - rightIndex;
        });

    return (
        <section className="herd-card">
            <div className="herd-card-heading">
                <div>
                    <span className="card-eyebrow">
                        HERD MANAGEMENT
                    </span>

                    <h2>Herd Management</h2>
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

                <div
                    className={
                        healthAttention > 0
                            ? "herd-attention active"
                            : "herd-attention"
                    }
                >
                    <span>Needs attention</span>
                    <strong>{healthAttention}</strong>
                </div>
            </div>

            <div className="herd-lifecycle">
                <div className="section-label">
                    Herd by category
                </div>

                {orderedCounts.length > 0 ? (
                    <div className="herd-lifecycle-list">
                        {orderedCounts.map(
                            ([status, count]) => (
                                <div key={status}>
                                    <span>{status}</span>
                                    <strong>{count}</strong>
                                </div>
                            ),
                        )}
                    </div>
                ) : (
                    <div className="herd-empty">
                        No animal records are currently available.
                    </div>
                )}
            </div>

            {widgets.length > 0 && (
                <div className="herd-widgets">
                    {widgets
                        .filter(
                            (widget) =>
                                widget.widget_id
                                !== "herd.summary",
                        )
                        .slice(0, 3)
                        .map((widget) => (
                            <div key={widget.widget_id}>
                                <span>{widget.title}</span>
                                <strong>
                                    {widget.value ?? "—"}
                                </strong>
                            </div>
                        ))}
                </div>
            )}
        </section>
    );
}

export default HerdCard;
