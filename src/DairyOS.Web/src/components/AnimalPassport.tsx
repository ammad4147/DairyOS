import React, { useEffect, useMemo, useState } from "react";
import "./AnimalPassport.css";

type RecordData = Record<string, unknown>;

type Animal = RecordData & {
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

const API = "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
    const response = await fetch(`${API}${path}`);

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    return response.json() as Promise<T>;
}

async function sendJson<T>(
    path: string,
    method: string,
    body: Record<string, unknown>,
): Promise<T> {
    const response = await fetch(`${API}${path}`, {
        method,
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Request failed: ${response.status}`);
    }

    return response.json() as Promise<T>;
}

function text(value: unknown): string {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    return String(value);
}

function amount(value: unknown): number {
    return typeof value === "number" && Number.isFinite(value)
        ? value
        : Number(value) || 0;
}

function money(value: number): string {
    return `PKR ${value.toLocaleString(undefined, {
        maximumFractionDigits: 0,
    })}`;
}

function milkValue(record: RecordData): number {
    return amount(
        record.total_yield ?? record.litres,
    );
}

function AnimalPassport({
    animalId,
    onBack,
    onOpenAnimal,
}: Props) {
    const [animal, setAnimal] = useState<Animal | null>(null);
    const [animals, setAnimals] = useState<Animal[]>([]);
    const [milk, setMilk] = useState<RecordData[]>([]);
    const [health, setHealth] = useState<RecordData[]>([]);
    const [breeding, setBreeding] = useState<RecordData[]>([]);
    const [finance, setFinance] = useState<RecordData[]>([]);
    const [vaccinations, setVaccinations] = useState<RecordData[]>([]);
    const [lifecycle, setLifecycle] = useState("");
    const [savingLifecycle, setSavingLifecycle] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    async function load() {
        setLoading(true);
        setError(null);

        try {
            const [
                current,
                allAnimals,
                milkRecords,
                healthRecords,
                breedingRecords,
                financeRecords,
                vaccinationRecords,
            ] = await Promise.all([
                getJson<Animal>(
                    `/farm/animals/${encodeURIComponent(animalId)}`,
                ),
                getJson<Animal[]>("/farm/animals"),
                getJson<RecordData[]>("/farm/milk"),
                getJson<RecordData[]>("/farm/health-observations"),
                getJson<RecordData[]>("/farm/breeding"),
                getJson<RecordData[]>("/farm/financial"),
                getJson<RecordData[]>(
                    `/farm/animals/${encodeURIComponent(animalId)}/vaccinations`,
                ),
            ]);

            setAnimal(current);
            setAnimals(Array.isArray(allAnimals) ? allAnimals : []);
            setLifecycle(
                String(
                    current.lifecycle_status
                    ?? current.status
                    ?? "",
                ),
            );

            setMilk(
                milkRecords.filter(
                    record =>
                        String(record.animal_id ?? "") === animalId,
                ),
            );

            setHealth(
                healthRecords.filter(
                    record =>
                        String(record.animal_id ?? "") === animalId,
                ),
            );

            setBreeding(
                breedingRecords.filter(
                    record =>
                        String(record.animal_id ?? "") === animalId,
                ),
            );

            setFinance(
                financeRecords,
            );

            setVaccinations(
                Array.isArray(vaccinationRecords)
                    ? vaccinationRecords
                    : [],
            );
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load animal passport.",
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        void load();
    }, [animalId]);

    const descendants = useMemo(() => {
        const result: Animal[] = [];
        const queue = [animalId];

        while (queue.length) {
            const parentId = queue.shift()!;

            for (const candidate of animals) {
                if (
                    String(candidate.dam_id ?? "") === parentId
                    && !result.some(
                        item =>
                            item.animal_id === candidate.animal_id,
                    )
                ) {
                    result.push(candidate);

                    if (candidate.animal_id) {
                        queue.push(candidate.animal_id);
                    }
                }
            }
        }

        return result;
    }, [animals, animalId]);

    const relatedIds = useMemo(
        () => new Set([
            animalId,
            ...descendants
                .map(item => item.animal_id)
                .filter(Boolean),
        ]),
        [animalId, descendants],
    );

    const financialRollup = useMemo(() => {
        let income = 0;
        let expense = 0;
        let transactions = 0;

        for (const record of finance) {
            const id = String(
                record.animal_id ?? "",
            );

            if (!relatedIds.has(id)) {
                continue;
            }

            const value = amount(record.amount);
            const type = String(
                record.transaction_type ?? "",
            ).toUpperCase();

            transactions += 1;

            if (
                type === "INCOME"
                || type === "RECEIPT"
                || type === "SALE"
                || type === "REVENUE"
            ) {
                income += value;
            } else {
                expense += value;
            }
        }

        return {
            income,
            expense,
            net: income - expense,
            transactions,
        };
    }, [finance, relatedIds]);

    const milkTotal = milk.reduce(
        (total, record) =>
            total + milkValue(record),
        0,
    );

    const recentMilk = [...milk]
        .sort(
            (a, b) =>
                String(b.timestamp ?? "")
                    .localeCompare(
                        String(a.timestamp ?? ""),
                    ),
        )
        .slice(0, 12);

    const recentHealth = [...health]
        .sort(
            (a, b) =>
                String(b.timestamp ?? "")
                    .localeCompare(
                        String(a.timestamp ?? ""),
                    ),
        )
        .slice(0, 8);

    const recentBreeding = [...breeding]
        .sort(
            (a, b) =>
                String(b.timestamp ?? "")
                    .localeCompare(
                        String(a.timestamp ?? ""),
                    ),
        )
        .slice(0, 8);

    const attentionHealth = health.filter(record =>
        ["HIGH", "CRITICAL", "ELEVATED"].includes(
            String(record.severity ?? "").toUpperCase(),
        ),
    );

    const vaccinationDue = vaccinations.filter(record => {
        const due = String(
            record.next_due_date ?? "",
        );

        return due && due <= new Date()
            .toISOString()
            .slice(0, 10);
    });

    async function saveLifecycle() {
        if (!lifecycle || lifecycle === animal?.lifecycle_status) {
            return;
        }

        setSavingLifecycle(true);

        try {
            const updated = await sendJson<Animal>(
                `/farm/animals/${encodeURIComponent(animalId)}/lifecycle`,
                "PATCH",
                {
                    lifecycle_status: lifecycle,
                    operator: "WEB",
                    reason: "Animal passport lifecycle update",
                },
            );

            setAnimal(updated);
            await load();
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Lifecycle update failed.",
            );
        } finally {
            setSavingLifecycle(false);
        }
    }

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

    if (!animal) {
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
                    {error ?? "Animal not found."}
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

            {error && (
                <div className="passport-alert">
                    {error}
                </div>
            )}

            <header className="passport-header">
                <div>
                    <span className="passport-eyebrow">
                        ANIMAL PASSPORT
                    </span>

                    <h2>{text(animal.animal_id)}</h2>

                    <p>
                        {text(animal.ear_tag)}
                        {animal.breed
                            ? ` · ${text(animal.breed)}`
                            : ""}
                    </p>
                </div>

                <div className="passport-status">
                    {text(animal.lifecycle_status)}
                </div>
            </header>

            <div className="passport-summary">
                <div>
                    <span>Milk recorded</span>
                    <strong>
                        {milkTotal.toLocaleString()} L
                    </strong>
                </div>

                <div>
                    <span>Own + offspring income</span>
                    <strong>
                        {money(financialRollup.income)}
                    </strong>
                </div>

                <div>
                    <span>Own + offspring expense</span>
                    <strong>
                        {money(financialRollup.expense)}
                    </strong>
                </div>

                <div>
                    <span>Net financial position</span>
                    <strong>
                        {money(financialRollup.net)}
                    </strong>
                </div>
            </div>

            <section className="passport-panel passport-wide">
                <div className="passport-section-heading">
                    <span>LIFECYCLE</span>
                    <strong>Operational category</strong>
                </div>

                <div className="passport-fields">
                    <div>
                        <span>Current category</span>
                        <select
                            value={lifecycle}
                            onChange={event =>
                                setLifecycle(
                                    event.target.value,
                                )
                            }
                        >
                            <option value="CALF">Calf</option>
                            <option value="HEIFER">Heifer</option>
                            <option value="CLOSE_UP">
                                Close-up
                            </option>
                            <option value="LACTATING">
                                Lactating
                            </option>
                            <option value="DRY">Dry</option>
                            <option value="SICK">Sick</option>
                            <option value="CULLED">Culled</option>
                        </select>
                    </div>

                    <div>
                        <span>Production group</span>
                        <strong>
                            {text(animal.production_group)}
                        </strong>
                    </div>

                    <div>
                        <span>Milking</span>
                        <strong>
                            {animal.is_currently_milking
                                ? "Yes"
                                : "No"}
                        </strong>
                    </div>

                    <div>
                        <span>Location</span>
                        <strong>
                            {text(animal.location)}
                        </strong>
                    </div>
                </div>

                <button
                    type="button"
                    className="passport-back"
                    disabled={
                        savingLifecycle
                        || lifecycle === animal.lifecycle_status
                    }
                    onClick={() => void saveLifecycle()}
                >
                    {savingLifecycle
                        ? "Saving…"
                        : "Save lifecycle category"}
                </button>
            </section>

            <div className="passport-grid">
                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>IDENTITY</span>
                        <strong>Animal profile</strong>
                    </div>

                    <div className="passport-fields">
                        <div>
                            <span>Animal ID</span>
                            <strong>
                                {text(animal.animal_id)}
                            </strong>
                        </div>

                        <div>
                            <span>Ear tag</span>
                            <strong>
                                {text(animal.ear_tag)}
                            </strong>
                        </div>

                        <div>
                            <span>RFID</span>
                            <strong>
                                {text(animal.rfid)}
                            </strong>
                        </div>

                        <div>
                            <span>Breed</span>
                            <strong>
                                {text(animal.breed)}
                            </strong>
                        </div>

                        <div>
                            <span>Sex</span>
                            <strong>
                                {text(animal.sex)}
                            </strong>
                        </div>

                        <div>
                            <span>Date of birth</span>
                            <strong>
                                {text(animal.date_of_birth)}
                            </strong>
                        </div>
                    </div>
                </section>

                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>LINEAGE</span>
                        <strong>
                            Parents & offspring
                        </strong>
                    </div>

                    <div className="lineage-links">
                        <div>
                            <span>Dam</span>
                            {animal.dam_id ? (
                                <button
                                    type="button"
                                    onClick={() =>
                                        onOpenAnimal(
                                            String(animal.dam_id),
                                        )
                                    }
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
                                    onClick={() =>
                                        onOpenAnimal(
                                            String(animal.sire_id),
                                        )
                                    }
                                >
                                    {animal.sire_id}
                                </button>
                            ) : (
                                <strong>—</strong>
                            )}
                        </div>
                    </div>

                    <div className="calves-heading">
                        <span>Descendants linked</span>
                        <strong>
                            {descendants.length}
                        </strong>
                    </div>

                    <div className="calf-list">
                        {descendants.length === 0 ? (
                            <div className="passport-empty">
                                No linked offspring recorded.
                            </div>
                        ) : (
                            descendants.map(candidate => (
                                <button
                                    type="button"
                                    key={String(
                                        candidate.animal_id,
                                    )}
                                    onClick={() =>
                                        onOpenAnimal(
                                            String(
                                                candidate.animal_id,
                                            ),
                                        )
                                    }
                                >
                                    <strong>
                                        {text(
                                            candidate.animal_id,
                                        )}
                                    </strong>
                                    <span>
                                        {text(
                                            candidate.lifecycle_status,
                                        )}
                                    </span>
                                </button>
                            ))
                        )}
                    </div>
                </section>
            </div>

            <section className="passport-panel passport-wide">
                <div className="passport-section-heading">
                    <span>MILK</span>
                    <strong>
                        Historical animal yield
                    </strong>
                </div>

                {recentMilk.length === 0 ? (
                    <div className="passport-empty">
                        No milk records linked to this animal.
                    </div>
                ) : (
                    <div className="passport-record-table">
                        {recentMilk.map((record, index) => (
                            <div
                                key={`${String(record.timestamp)}-${index}`}
                            >
                                <span>
                                    {text(record.timestamp)}
                                </span>
                                <strong>
                                    {milkValue(record).toLocaleString()} L
                                </strong>
                                <span>
                                    {text(
                                        record.milking_session,
                                    )}
                                </span>
                                <span>
                                    {text(record.operator)}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <div className="passport-grid">
                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>HEALTH</span>
                        <strong>
                            Health assessment
                        </strong>
                    </div>

                    {attentionHealth.length > 0 && (
                        <div className="passport-alert">
                            {attentionHealth.length} health
                            record(s) require attention.
                        </div>
                    )}

                    <div className="passport-record-list">
                        {recentHealth.length === 0 ? (
                            <div className="passport-empty">
                                No health observations.
                            </div>
                        ) : (
                            recentHealth.map(
                                (record, index) => (
                                    <div
                                        key={`${String(record.timestamp)}-${index}`}
                                    >
                                        <strong>
                                            {text(
                                                record.severity,
                                            )}
                                        </strong>
                                        <span>
                                            {text(
                                                record.observation,
                                            )}
                                        </span>
                                        <small>
                                            {text(
                                                record.timestamp,
                                            )}
                                        </small>
                                    </div>
                                ),
                            )
                        )}
                    </div>
                </section>

                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>HEALTH & VACCINATION</span>
                        <strong>
                            Vaccination record & reminders
                        </strong>
                    </div>

                    {vaccinationDue.length > 0 && (
                        <div className="passport-alert">
                            {vaccinationDue.length} vaccination
                            reminder(s) due or overdue.
                        </div>
                    )}

                    <div className="passport-record-list">
                        {vaccinations.length === 0 ? (
                            <div className="passport-empty">
                                No vaccination records.
                            </div>
                        ) : (
                            vaccinations.map(
                                (record, index) => (
                                    <div
                                        key={`${String(record.vaccine)}-${index}`}
                                    >
                                        <strong>
                                            {text(
                                                record.vaccine,
                                            )}
                                        </strong>
                                        <span>
                                            Administered:{" "}
                                            {text(
                                                record.administered_date,
                                            )}
                                        </span>
                                        <small>
                                            Next due:{" "}
                                            {text(
                                                record.next_due_date,
                                            )}
                                        </small>
                                    </div>
                                ),
                            )
                        )}
                    </div>
                </section>
            </div>

            <div className="passport-grid">
                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>REPRODUCTION</span>
                        <strong>
                            Reproductive history
                        </strong>
                    </div>

                    <div className="passport-record-list">
                        {recentBreeding.length === 0 ? (
                            <div className="passport-empty">
                                No reproductive records.
                            </div>
                        ) : (
                            recentBreeding.map(
                                (record, index) => (
                                    <div
                                        key={`${String(record.timestamp)}-${index}`}
                                    >
                                        <strong>
                                            {text(
                                                record.event_type,
                                            )}
                                        </strong>
                                        <span>
                                            {text(
                                                record.result,
                                            )}
                                        </span>
                                        <small>
                                            {text(
                                                record.timestamp,
                                            )}
                                        </small>
                                    </div>
                                ),
                            )
                        )}
                    </div>
                </section>

                <section className="passport-panel">
                    <div className="passport-section-heading">
                        <span>FINANCIAL DYNAMICS</span>
                        <strong>
                            Animal + offspring
                        </strong>
                    </div>

                    <div className="passport-fields">
                        <div>
                            <span>Linked animals</span>
                            <strong>
                                {relatedIds.size}
                            </strong>
                        </div>

                        <div>
                            <span>Income</span>
                            <strong>
                                {money(
                                    financialRollup.income,
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>Expense</span>
                            <strong>
                                {money(
                                    financialRollup.expense,
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>Net</span>
                            <strong>
                                {money(
                                    financialRollup.net,
                                )}
                            </strong>
                        </div>

                        <div>
                            <span>Transactions</span>
                            <strong>
                                {financialRollup.transactions}
                            </strong>
                        </div>

                        <div>
                            <span>Milk records</span>
                            <strong>
                                {milk.length}
                            </strong>
                        </div>
                    </div>

                    <p className="passport-lineage-note">
                        Financial records remain tagged by
                        animal ID; the passport rolls them up
                        through the linked offspring tree.
                    </p>
                </section>
            </div>
        </section>
    );
}

export default AnimalPassport;
