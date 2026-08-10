import React from "react";

interface Decision {
    priority?: string;
    title?: string;
    action?: string;
    animal_id?: string;
    details?: Record<string, unknown>;
    owner_action_required?: boolean;
}

interface Props {
    decisions: Decision[];
    onOpenAnimal?: (animalId: string) => void;
}

function AttentionPanel({
    decisions,
    onOpenAnimal,
}: Props) {
    if (decisions.length === 0) {
        return (
            <div className="attention-empty">
                No pending attention items.
            </div>
        );
    }

    return (
        <div className="attention-list">
            {decisions.slice(0, 8).map(
                (decision, index) => {
                    const animalId = decision.animal_id;

                    return (
                        <div
                            className="attention-item"
                            key={`${animalId ?? "farm"}-${index}`}
                        >
                            <div className="attention-item-top">
                                <span
                                    className={`attention-priority ${String(
                                        decision.priority ?? "normal",
                                    ).toLowerCase()}`}
                                >
                                    {decision.priority ?? "normal"}
                                </span>

                                {animalId && (
                                    <button
                                        type="button"
                                        onClick={() =>
                                            onOpenAnimal?.(animalId)
                                        }
                                    >
                                        {animalId}
                                    </button>
                                )}
                            </div>

                            <strong>
                                {decision.title
                                    ?? decision.action
                                    ?? "Operational attention"}
                            </strong>

                            {decision.action
                                && decision.title
                                && (
                                    <p>
                                        {decision.action}
                                    </p>
                                )}
                        </div>
                    );
                },
            )}
        </div>
    );
}

export default AttentionPanel;
