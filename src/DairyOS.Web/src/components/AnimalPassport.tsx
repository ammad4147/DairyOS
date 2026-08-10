import React, { useEffect, useMemo, useState } from "react";

import "./AnimalPassport.css";

type JsonRecord = Record<string, unknown>;

type Animal = JsonRecord & {
    animal_id?: string;
    ear_tag?: string;
    rfid?: string;
    breed?: string;
    sex?: string;
    animal_type?: string;
    date_of_birth?: string;
    dam_id?: string | null;
    sire_id?: string | null;
    lifecycle_status?: string;
    status?: string;
    is_currently_milking?: boolean;
    milking_frequency?: string | null;
    production_group?: string | null;
    location?: string | null;
};

type Props = {
    animalId: string;
    onBack: () => void;
    onOpenAnimal: (animalId: string) => void;
};

function display(value: unknown): string {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}

function numberValue(value: unknown): number | null {
    return typeof value === "number" && Number.isFinite(value)
        ? value
        : null;
}

function litres(value: unknown): string {
    const number = numberValue(value);

    return number === null
        ? "—"
        : `${number.toLocaleString()} L`;
}

function money(value: unknown): string {
    const number = numberValue(value);

    return number === null
        ? "—"
        : `PKR ${number.toLocaleString(undefined, {
            maximumFractionDigits: 0,
        })}`;
}

function normalise(value: unknown): string {
    return String(value ?? "")
        .trim()
        .toLowerCase()
        .replace(/[_-]+/g, " ");
}

async function getJson<T>(url: string): Promise<T> {
    const response = await fetch(`http://localhost:8000${url}`);

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    return response.json() as Promise<T>;
}

function AnimalPassport({
    animalId,
    onBack,
    onOpenAnimal,
}: Props) {
    const [animal, setAnimal] = useState<Animal | null>(null);
    const [animals, setAnimals] = useState<Animal[]>([]);
    const [milk, setMilk] = useState<JsonRecord[]>([]);
    const [health, setHealth] = useState<JsonRecord[]>([]);
    const [breeding, setBreeding] = useState<JsonRecord[]>([]);
    const [finance, setFinance] = useState<JsonRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);

            try {
                const [
                    animalResult,
                    animalsResult,
                    milkResult,
                    healthResult,
                    breedingResult,
                    financeResult,
                ] = await Promise.all([
                    getJson<Animal>(`/farm/animals/${encodeURIComponent(animalId)}`),
                    getJson<Animal[]>("/farm/animals"),
                    getJson<JsonRecord[]>("/farm/milk"),
                    getJson<JsonRecord[]>("/farm/health-observations"),
                    getJson<JsonRecord[]>("/farm/breeding"),
                    getJson<JsonRecord[]>("/farm/financial"),
                ]);

                if (cancelled) {
                    return;
                }

                setAnimal(animalResult);
                setAnimals(Array.isArray(animalsResult) ? animalsResult : []);

                setMilk(
                    Array.isArray(milkResult)
                        ? milkResult.filter(
                            (record) =>
                                String(record.animal_id ?? "") === animalId,
                        )
                        : [],
                );

                setHealth(
                    Array.isArray(healthResult)
                        ? healthResult.filter(
                            (record) =>
                                String(record.animal_id ?? "") === animalId,
                        )
                        : [],
                );

                setBreeding(
                    Array.isArray(breedingResult)
                        ? breedingResult.filter(
                            (record) =>
                                String(record.animal_id ?? "") === animalId,
                        )
                        : [],
                );

                setFinance(
                    Array.isArray(financeResult)
                        ? financeResult.filter(
                            (record) =>
                                String(record.animal_id ?? "") === animalId,
                        )
                        : [],
                );
            } catch (requestError) {
                if (!cancelled) {
                    setError(
                        requestError instanceof Error
                            ? requestError.message
                            : "Unable to load animal passport.",
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        void load();

        return () => {
            cancelled = true;
        };
    }, [animalId]);

    const calves = useMemo(
        () =>
            animals.filter(
                (candidate) =>
                    String(candidate.dam_id ?? "") === animalId,
            ),
        [animals, animalId],
    );

    const parentIds = useMemo(
        () =>
            [
                animal?.dam_id,
                animal?.sire_id,
            ].filter(
                (value): value is string =>
                    typeof value === "string" && value.length > 0,
            ),
        [animal],
    );

    const totalMilk = useMemo(
        () =>
            milk.reduce(
                (total, record) =>
                    total
                    + (numberValue(record.total_yield) ?? numberValue(record.litres) ?? 0),
                0,
            ),
        [milk],
    );

    const totalFinancial = useMemo(
        () =>
            finance.reduce(
                (total, record) => {
                    const amount = numberValue(record.amount) ?? 0;
                    const type = normalise(record.transaction_type);

                    if (
                        type === "income"
                        || type === "receipt"
                    ) {
                        return total + amount;
                    }

                    return total - amount;
                },
                0,
            ),
        [finance],
    );

    const healthAttention = health.filter((record) => {
        const severity = normalise(record.severity);

        return [
            "elevated",
            "high",
            "critical",
        ].includes(severity);
    });

    const latestMilk = [...milk]
        .sort(
            (left, right) =>
                String(right.timestamp ?? "").localeCompare(
                    String(left.timestamp ?? ""),
                ),
        )
        .slice(0, 8);

    const latestHealth = [...health]
        .sort(
            (left, right) =>
                String(right.timestamp ?? "").localeCompare(
                    String(left.timestamp ?? ""),
                ),
        )
        .slice(0, 8);

    const latestBreeding = [...breeding]
        .sort(
            (left, right) =>
                String(right.timestamp ?? "").localeCompare(
                    String(left.timestamp ?? ""),
                ),
        )
        .slice(0, 8);

    const latestFinance = [...finance]
        .sort(
            (left, right) =>
                String(right.timestamp ?? "").localeCompare(
                    String(left.timestamp ?? ""),
                ),
        )
        .slice(0, 8);

    if (loading) {
        return (
            <section className="animal-passport">
                <button
                    type="button"
                    className="passport-back"
                    onClick={onBack}
                >
                    ← Back to Herd Management
                </button>

                <div className="passport-loading">
                    Loading animal passport…
                </div>
            </section>
        );
    }

    if (error || !animal) {
        return (
            <section className="animal-passport">
                <button
                    type="button"
                    className="passport-back"
                    onClick={onBack}
                >
                    ← Back to Herd Management
                </button>

                <div className="passport-error">
                    <strong>Unable to load animal passport.</strong>
                    <p>{error ?? "Animal not found."}</p>
                </div>
            </section>
        );
    }

    return (
        <section className="animal-passport">
            <div className="passport-topbar">
                <button
                    type="button"
                    className="passport-back"
                    onClick={onBack}
                >
                    ← Back to Herd Management
                </button>

                <span className="passport-live">
                    Animal-linked operational record
                </span>
            </div>

            <header className="passport-header">
                <div>
                    <span className="passport-eyebrow">
                        ANIMAL PASSPORT
                    </span>

                    <h2>{display(animal.animal_id)}</h2>

                    <p>
                        {display(animal.ear_tag)}
                        {animal.breed
                            ? ` · ${display(animal.breed)}`
                            : ""}
                    </p>
                </div>

                <div className="passport-status">
                    {display(
                        animal.lifecycle_status
                        ?? animal.status,
                    )}
                </div>
            </header>

            <div className="passport-summary">
                <div>
                    <span>Lifecycle</span>
                    <strong>
                        {display(animal.lifecycle_status)}
                    </strong>
                </div>

                <div>
                    <span>Current milking</span>
                    <strong>
                        {animal.is_currently_milking ? "Yes" : "No"}
                    </strong>
                </div>

                <div>
                    <span>Total milk recorded</span>
                    <strong>{litres(totalMilk)}</strong>
                </div>

                <div>
                    <span>Financial net recorded</span>
                    <strong>{money(totalFinancial)}</strong>
                </div>
            </div>

            <div className="passport-grid">
                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>IDENTITY</span>
                        <strong>Animal profile</strong>
                    </div>

                    <div className="passport-fields">
                        <div>
                            <span>Animal ID</span>
                            <strong>{display(animal.animal_id)}</strong>
                        </div>

                        <div>
                            <span>Ear tag</span>
                            <strong>{display(animal.ear_tag)}</strong>
                        </div>

                        <div>
                            <span>RFID</span>
                            <strong>{display(animal.rfid)}</strong>
                        </div>

                        <div>
                            <span>Breed</span>
                            <strong>{display(animal.breed)}</strong>
                        </div>

                        <div>
                            <span>Sex</span>
                            <strong>{display(animal.sex)}</strong>
                        </div>

                        <div>
                            <span>Date of birth</span>
                            <strong>{display(animal.date_of_birth)}</strong>
                        </div>

                        <div>
                            <span>Production group</span>
                            <strong>{display(animal.production_group)}</strong>
                        </div>

                        <div>
                            <span>Location</span>
                            <strong>{display(animal.location)}</strong>
                        </div>
                    </div>
                </section>

                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>LINEAGE</span>
                        <strong>Parents & calves</strong>
                    </div>

                    <div className="lineage-links">
                        <div>
                            <span>Dam</span>

                            {animal.dam_id ? (
                                <button
                                    type="button"
                                    onClick={() => onOpenAnimal(String(animal.dam_id))}
                                >
                                    {animal.dam_id}
                                </button>
                            ) : (
                                <strong>—</strong>
                            )}
                        </div>

                        <div>
                            <span>Sire</span>

                            {animal.sire_id ? (
                                <button
                                    type="button"
                                    onClick={() => onOpenAnimal(String(animal.sire_id))}
                                >
                                    {animal.sire_id}
                                </button>
                            ) : (
                                <strong>—</strong>
                            )}
                        </div>
                    </div>

                    <div className="calves-heading">
                        <span>Linked offspring</span>
                        <strong>{calves.length}</strong>
                    </div>

                    {calves.length > 0 ? (
                        <div className="calf-list">
                            {calves.map((calf) => (
                                <button
                                    type="button"
                                    key={String(calf.animal_id)}
                                    onClick={() =>
                                        onOpenAnimal(
                                            String(calf.animal_id),
                                        )
                                    }
                                >
                                    <strong>
                                        {display(calf.animal_id)}
                                    </strong>
                                    <span>
                                        {display(
                                            calf.lifecycle_status,
                                        )}
                                    </span>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="passport-empty">
                            No linked offspring recorded.
                        </div>
                    )}

                    <div className="passport-lineage-note">
                        Parent and offspring relationships remain linked
                        through animal IDs.
                    </div>
                </section>
            </div>

            <section className="passport-panel passport-wide">
                <div className="passport-section-heading">
                    <span>MILK</span>
                    <strong>Animal-linked milk production</strong>
                </div>

                {latestMilk.length > 0 ? (
                    <div className="passport-record-table">
                        {latestMilk.map((record, index) => (
                            <div key={`${String(record.timestamp)}-${index}`}>
                                <span>
                                    {display(record.timestamp)}
                                </span>

                                <strong>
                                    {litres(
                                        record.total_yield
                                        ?? record.litres,
                                    )}
                                </strong>

                                <span>
                                    {display(
                                        record.milking_session,
                                    )}
                                </span>

                                <span>
                                    {display(record.operator)}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="passport-empty">
                        No milk records linked to this animal yet.
                    </div>
                )}
            </section>

            <div className="passport-grid">
                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>HEALTH</span>
                        <strong>Health assessment history</strong>
                    </div>

                    {healthAttention.length > 0 && (
                        <div className="passport-alert">
                            {healthAttention.length} health record(s)
                            require attention.
                        </div>
                    )}

                    {latestHealth.length > 0 ? (
                        <div className="passport-record-list">
                            {latestHealth.map((record, index) => (
                                <div key={`${String(record.timestamp)}-${index}`}>
                                    <strong>
                                        {display(record.severity)}
                                    </strong>

                                    <span>
                                        {display(record.observation)}
                                    </span>

                                    <small>
                                        {display(record.timestamp)}
                                    </small>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="passport-empty">
                            No health observations linked to this animal.
                        </div>
                    )}
                </section>

                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>REPRODUCTION</span>
                        <strong>Reproductive history</strong>
                    </div>

                    {latestBreeding.length > 0 ? (
                        <div className="passport-record-list">
                            {latestBreeding.map((record, index) => (
                                <div key={`${String(record.timestamp)}-${index}`}>
                                    <strong>
                                        {display(record.event_type)}
                                    </strong>

                                    <span>
                                        {display(
                                            record.result
                                            ?? record.notes,
                                        )}
                                    </span>

                                    <small>
                                        {display(record.timestamp)}
                                    </small>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="passport-empty">
                            No reproductive events linked to this animal.
                        </div>
                    )}
                </section>
            </div>

            <section className="passport-panel passport-wide">
                <div className="passport-section-heading">
                    <span>FINANCIAL</span>
                    <strong>Animal financial dynamics</strong>
                </div>

                <div className="financial-summary">
                    <div>
                        <span>Milk / recorded income</span>
                        <strong>
                            {money(
                                finance
                                    .filter(
                                        (record) =>
                                            [
                                                "income",
                                                "receipt",
                                            ].includes(
                                                normalise(
                                                    record.transaction_type,
                                                ),
                                            ),
                                    )
                                    .reduce(
                                        (total, record) =>
                                            total
                                            + (
                                                numberValue(
                                                    record.amount,
                                                )
                                                ?? 0
                                            ),
                                        0,
                                    ),
                            )}
                        </strong>
                    </div>

                    <div>
                        <span>Recorded costs</span>
                        <strong>
                            {money(
                                finance
                                    .filter(
                                        (record) =>
                                            [
                                                "expense",
                                                "payment",
                                                "owner withdrawal",
                                            ].includes(
                                                normalise(
                                                    record.transaction_type,
                                                ),
                                            ),
                                    )
                                    .reduce(
                                        (total, record) =>
                                            total
                                            + (
                                                numberValue(
                                                    record.amount,
                                                )
                                                ?? 0
                                            ),
                                        0,
                                    ),
                            )}
                        </strong>
                    </div>

                    <div>
                        <span>Net recorded</span>
                        <strong>{money(totalFinancial)}</strong>
                    </div>
                </div>

                {latestFinance.length > 0 ? (
                    <div className="passport-record-table">
                        {latestFinance.map((record, index) => (
                            <div key={`${String(record.timestamp)}-${index}`}>
                                <span>
                                    {display(record.transaction_type)}
                                </span>

                                <strong>
                                    {money(record.amount)}
                                </strong>

                                <span>
                                    {display(record.category)}
                                </span>

                                <span>
                                    {display(record.timestamp)}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="passport-empty">
                        No financial records are currently linked to
                        this animal.
                    </div>
                )}

                <div className="passport-lineage-note">
                    This is the animal-level financial ledger. The next
                    financial enhancement will extend this view to
                    automatically consolidate offspring economics.
                </div>
            </section>
        </section>
    );
}

export default AnimalPassport;
