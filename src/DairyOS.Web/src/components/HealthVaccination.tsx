import React, { useEffect, useMemo, useState } from "react";
import "./HealthVaccination.css";

type Animal = {
    animal_id?: string;
    ear_tag?: string;
    breed?: string;
    sex?: string;
    lifecycle_status?: string;
};

type HealthRecord = Record<string, unknown>;
type Vaccination = Record<string, unknown>;

type Props = {
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

async function postJson<T>(
    path: string,
    body: Record<string, unknown>,
): Promise<T> {
    const response = await fetch(`${API}${path}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const message = await response.text();
        throw new Error(
            message || `Request failed: ${response.status}`,
        );
    }

    return response.json() as Promise<T>;
}

function value(
    record: Record<string, unknown>,
    ...keys: string[]
): string {
    for (const key of keys) {
        const current = record[key];

        if (
            current !== undefined
            && current !== null
            && current !== ""
        ) {
            return String(current);
        }
    }

    return "—";
}

function dueState(nextDue: string | undefined): string {
    if (!nextDue) {
        return "NO DATE";
    }

    const due = new Date(nextDue);
    const today = new Date();

    today.setHours(0, 0, 0, 0);
    due.setHours(0, 0, 0, 0);

    if (due < today) {
        return "OVERDUE";
    }

    if (due.getTime() === today.getTime()) {
        return "DUE TODAY";
    }

    const days = Math.ceil(
        (due.getTime() - today.getTime())
        / 86400000,
    );

    if (days <= 30) {
        return "DUE SOON";
    }

    return "SCHEDULED";
}

function HealthVaccination({
    onOpenAnimal,
}: Props) {
    const [animals, setAnimals] = useState<Animal[]>([]);
    const [health, setHealth] = useState<HealthRecord[]>([]);
    const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
    const [selectedAnimal, setSelectedAnimal] =
        useState("");
    const [vaccine, setVaccine] = useState("");
    const [dose, setDose] = useState("");
    const [nextDueDate, setNextDueDate] = useState("");
    const [veterinarian, setVeterinarian] = useState("");
    const [operator, setOperator] = useState("");
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    async function load() {
        setError("");

        try {
            const [
                animalRows,
                healthRows,
            ] = await Promise.all([
                getJson<Animal[]>("/farm/animals"),
                getJson<HealthRecord[]>(
                    "/farm/health-observations",
                ),
            ]);

            setAnimals(
                Array.isArray(animalRows)
                    ? animalRows
                    : [],
            );

            setHealth(
                Array.isArray(healthRows)
                    ? healthRows
                    : [],
            );

            const vaccinationRows: Vaccination[] = [];

            for (const animal of animalRows ?? []) {
                if (!animal.animal_id) {
                    continue;
                }

                try {
                    const rows = await getJson<Vaccination[]>(
                        `/farm/animals/${encodeURIComponent(
                            animal.animal_id,
                        )}/vaccinations`,
                    );

                    if (Array.isArray(rows)) {
                        vaccinationRows.push(...rows);
                    }
                } catch {
                    // One unavailable animal history must not
                    // prevent the rest of the health workspace.
                }
            }

            setVaccinations(vaccinationRows);
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load health information.",
            );
        }
    }

    useEffect(() => {
        void load();
    }, []);

    const reminders = useMemo(
        () =>
            vaccinations
                .filter(
                    record =>
                        value(
                            record,
                            "next_due_date",
                        ) !== "—",
                )
                .map(record => ({
                    ...record,
                    state: dueState(
                        value(
                            record,
                            "next_due_date",
                        ),
                    ),
                }))
                .filter(
                    record =>
                        record.state === "OVERDUE"
                        || record.state === "DUE TODAY"
                        || record.state === "DUE SOON",
                )
                .sort(
                    (a, b) =>
                        value(
                            a,
                            "next_due_date",
                        ).localeCompare(
                            value(
                                b,
                                "next_due_date",
                            ),
                        ),
                ),
        [vaccinations],
    );

    const recentHealth = useMemo(
        () =>
            [...health]
                .filter(
                    record =>
                        value(
                            record,
                            "animal_id",
                        ) !== "—",
                )
                .slice(-12)
                .reverse(),
        [health],
    );

    async function recordVaccination(
        event: React.FormEvent,
    ) {
        event.preventDefault();

        if (!selectedAnimal || !vaccine) {
            setError(
                "Select an animal and enter the vaccine.",
            );
            return;
        }

        setSaving(true);
        setError("");
        setMessage("");

        try {
            await postJson(
                `/farm/animals/${encodeURIComponent(
                    selectedAnimal,
                )}/vaccinations`,
                {
                    vaccine,
                    dose: dose || null,
                    next_due_date:
                        nextDueDate || null,
                    veterinarian:
                        veterinarian || null,
                    operator:
                        operator || "Health Team",
                },
            );

            setMessage(
                `Vaccination recorded for ${selectedAnimal}.`,
            );

            setVaccine("");
            setDose("");
            setNextDueDate("");
            setVeterinarian("");

            await load();
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to record vaccination.",
            );
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="health-vaccination">
            <div className="health-summary">
                <div className="health-summary-card">
                    <span>Animals</span>
                    <strong>{animals.length}</strong>
                </div>

                <div className="health-summary-card">
                    <span>Health Records</span>
                    <strong>{health.length}</strong>
                </div>

                <div className="health-summary-card">
                    <span>Vaccinations</span>
                    <strong>{vaccinations.length}</strong>
                </div>

                <div className="health-summary-card alert">
                    <span>Vaccination Attention</span>
                    <strong>{reminders.length}</strong>
                </div>
            </div>

            {error && (
                <div className="health-message error">
                    {error}
                </div>
            )}

            {message && (
                <div className="health-message success">
                    {message}
                </div>
            )}

            <section className="health-panel">
                <div className="health-panel-header">
                    <div>
                        <h2>Vaccination Reminders</h2>
                        <p>
                            Animal-linked vaccinations requiring
                            attention.
                        </p>
                    </div>
                </div>

                {reminders.length === 0 ? (
                    <div className="health-empty">
                        No vaccination reminders currently due.
                    </div>
                ) : (
                    <div className="health-table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Animal</th>
                                    <th>Vaccine</th>
                                    <th>Next Due</th>
                                    <th>Status</th>
                                    <th />
                                </tr>
                            </thead>
                            <tbody>
                                {reminders.map(
                                    (record, index) => {
                                        const animalId =
                                            value(
                                                record,
                                                "animal_id",
                                            );

                                        return (
                                            <tr
                                                key={`${animalId}-${index}`}
                                            >
                                                <td>
                                                    <button
                                                        className="link-button"
                                                        type="button"
                                                        onClick={() =>
                                                            onOpenAnimal(
                                                                animalId,
                                                            )
                                                        }
                                                    >
                                                        {animalId}
                                                    </button>
                                                </td>
                                                <td>
                                                    {value(
                                                        record,
                                                        "vaccine",
                                                        "vaccination",
                                                    )}
                                                </td>
                                                <td>
                                                    {value(
                                                        record,
                                                        "next_due_date",
                                                    )}
                                                </td>
                                                <td>
                                                    <span
                                                        className={`health-status ${String(
                                                            record.state,
                                                        ).toLowerCase().replace(
                                                            / /g,
                                                            "-",
                                                        )}`}
                                                    >
                                                        {
                                                            record.state
                                                        }
                                                    </span>
                                                </td>
                                                <td>
                                                    <button
                                                        className="small-button"
                                                        type="button"
                                                        onClick={() =>
                                                            onOpenAnimal(
                                                                animalId,
                                                            )
                                                        }
                                                    >
                                                        Passport
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    },
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            <div className="health-grid">
                <section className="health-panel">
                    <div className="health-panel-header">
                        <div>
                            <h2>Record Vaccination</h2>
                            <p>
                                Every vaccination remains linked
                                to the animal passport.
                            </p>
                        </div>
                    </div>

                    <form
                        className="vaccination-form"
                        onSubmit={recordVaccination}
                    >
                        <label>
                            Animal
                            <select
                                value={selectedAnimal}
                                onChange={event =>
                                    setSelectedAnimal(
                                        event.target.value,
                                    )
                                }
                                required
                            >
                                <option value="">
                                    Select animal
                                </option>

                                {animals.map(animal => (
                                    <option
                                        key={animal.animal_id}
                                        value={animal.animal_id}
                                    >
                                        {animal.animal_id}
                                        {animal.ear_tag
                                            ? ` — ${animal.ear_tag}`
                                            : ""}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label>
                            Vaccine
                            <input
                                value={vaccine}
                                onChange={event =>
                                    setVaccine(
                                        event.target.value,
                                    )
                                }
                                placeholder="e.g. FMD"
                                required
                            />
                        </label>

                        <label>
                            Dose
                            <input
                                value={dose}
                                onChange={event =>
                                    setDose(
                                        event.target.value,
                                    )
                                }
                                placeholder="Dose / volume"
                            />
                        </label>

                        <label>
                            Next Due Date
                            <input
                                type="date"
                                value={nextDueDate}
                                onChange={event =>
                                    setNextDueDate(
                                        event.target.value,
                                    )
                                }
                            />
                        </label>

                        <label>
                            Veterinarian
                            <input
                                value={veterinarian}
                                onChange={event =>
                                    setVeterinarian(
                                        event.target.value,
                                    )
                                }
                            />
                        </label>

                        <label>
                            Operator
                            <input
                                value={operator}
                                onChange={event =>
                                    setOperator(
                                        event.target.value,
                                    )
                                }
                                placeholder="Person recording"
                                required
                            />
                        </label>

                        <button
                            className="primary-button"
                            type="submit"
                            disabled={saving}
                        >
                            {saving
                                ? "Saving..."
                                : "Record Vaccination"}
                        </button>
                    </form>
                </section>

                <section className="health-panel">
                    <div className="health-panel-header">
                        <div>
                            <h2>Recent Health Observations</h2>
                            <p>
                                Health records remain directly
                                attributable to animal ID.
                            </p>
                        </div>
                    </div>

                    {recentHealth.length === 0 ? (
                        <div className="health-empty">
                            No health observations recorded.
                        </div>
                    ) : (
                        <div className="health-observation-list">
                            {recentHealth.map(
                                (record, index) => {
                                    const animalId =
                                        value(
                                            record,
                                            "animal_id",
                                        );

                                    return (
                                        <button
                                            key={`${animalId}-${index}`}
                                            type="button"
                                            className="health-observation"
                                            onClick={() =>
                                                onOpenAnimal(
                                                    animalId,
                                                )
                                            }
                                        >
                                            <strong>
                                                {animalId}
                                            </strong>

                                            <span>
                                                {value(
                                                    record,
                                                    "observation",
                                                    "symptom",
                                                )}
                                            </span>

                                            <small>
                                                {value(
                                                    record,
                                                    "severity",
                                                )}
                                            </small>
                                        </button>
                                    );
                                },
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default HealthVaccination;
