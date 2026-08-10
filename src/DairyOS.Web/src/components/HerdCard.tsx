import React, { useMemo } from "react";

import type {
    DashboardWidget,
    OperationalAnimalState,
} from "../models/dashboard";

interface Props {
    animals?: Record<string, OperationalAnimalState>;
    widgets?: DashboardWidget[];
    onOpenAnimal?: (animalId: string) => void;
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
    onOpenAnimal,
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
                                <button
                                    type="button"
                                    className="herd-category-row"
                                    key={status}
                                    onClick={() => {
                                        const match =
                                            animalList.find(
                                                ([, animal]) =>
                                                    normaliseStatus(
                                                        animal.lifecycle?.status
                                                        ?? animal.lifecycle?.lifecycle_status
                                                        ?? animal.status,
                                                    ) === status,
                                            );

                                        if (match && onOpenAnimal) {
                                            onOpenAnimal(match[0]);
                                        }
                                    }}
                                >
                                    <span>{status}</span>
                                    <strong>{count}</strong>
                                </button>
                            ),
                        )}
                    </div>
                ) : (
                    <div className="herd-empty">
                        No animal records are currently available.
                    </div>
                )}
            </div>

            {animalList.length > 0 && (
                <div className="herd-animal-list">
                    <div className="section-label">
                        Animal register
                    </div>

                    {animalList.slice(0, 8).map(
                        ([animalId, animal]) => (
                            <button
                                type="button"
                                key={animalId}
                                onClick={() =>
                                    onOpenAnimal?.(animalId)
                                }
                            >
                                <strong>{animalId}</strong>
                                <span>
                                    {normaliseStatus(
                                        animal.lifecycle?.status
                                        ?? animal.lifecycle?.lifecycle_status
                                        ?? animal.status,
                                    )}
                                </span>
                            </button>
                        ),
                    )}
                </div>
            )}

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
