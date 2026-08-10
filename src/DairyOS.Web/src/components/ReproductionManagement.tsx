import React, { useEffect, useMemo, useState } from "react";
import "./ReproductionManagement.css";

type RecordData = Record<string, unknown>;

type Props = {
    onOpenAnimal: (animalId: string) => void;
};

const API = "http://localhost:8000";

function text(
    record: RecordData,
    ...keys: string[]
): string {
    for (const key of keys) {
        const value = record[key];

        if (
            value !== undefined &&
            value !== null &&
            value !== ""
        ) {
            return String(value);
        }
    }

    return "—";
}

function dateValue(record: RecordData): Date | null {
    const raw = text(
        record,
        "timestamp",
        "event_date",
        "date",
    );

    if (raw === "—") {
        return null;
    }

    const date = new Date(raw);

    return Number.isNaN(date.getTime())
        ? null
        : date;
}

function daysSince(record: RecordData): number | null {
    const date = dateValue(record);

    if (!date) {
        return null;
    }

    return Math.floor(
        (Date.now() - date.getTime())
        / 86400000,
    );
}

async function loadBreeding(): Promise<RecordData[]> {
    const response = await fetch(
        `${API}/farm/breeding`,
        {
            cache: "no-store",
        },
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load reproduction records (${response.status})`,
        );
    }

    const payload = await response.json();

    return Array.isArray(payload)
        ? payload
        : [];
}

async function loadAnimals(): Promise<RecordData[]> {
    const response = await fetch(
        `${API}/farm/animals`,
        {
            cache: "no-store",
        },
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load animals (${response.status})`,
        );
    }

    const payload = await response.json();

    return Array.isArray(payload)
        ? payload
        : [];
}

function ReproductionManagement({
    onOpenAnimal,
}: Props) {
    const [records, setRecords] = useState<RecordData[]>([]);
    const [animals, setAnimals] = useState<RecordData[]>([]);
    const [animalId, setAnimalId] = useState("");
    const [eventType, setEventType] = useState(
        "heat_detected",
    );
    const [technician, setTechnician] = useState("");
    const [result, setResult] = useState("");
    const [semen, setSemen] = useState("");
    const [notes, setNotes] = useState("");
    const [operator, setOperator] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    async function refresh() {
        setError("");

        try {
            const [breeding, animalRows] =
                await Promise.all([
                    loadBreeding(),
                    loadAnimals(),
                ]);

            setRecords(breeding);
            setAnimals(animalRows);
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load reproduction data.",
            );
        }
    }

    useEffect(() => {
        void refresh();

        const timer = window.setInterval(
            () => void refresh(),
            60000,
        );

        return () =>
            window.clearInterval(timer);
    }, []);

    const latestByAnimal = useMemo(() => {
        const map = new Map<string, RecordData>();

        for (const record of records) {
            const id = text(record, "animal_id");

            if (id === "—") {
                continue;
            }

            const existing = map.get(id);

            const currentDate = dateValue(record);
            const existingDate = existing
                ? dateValue(existing)
                : null;

            if (
                !existing ||
                (
                    currentDate &&
                    (!existingDate ||
                        currentDate > existingDate)
                )
            ) {
                map.set(id, record);
            }
        }

        return map;
    }, [records]);

    const stats = useMemo(() => {
        let heat = 0;
        let services = 0;
        let confirmed = 0;
        let calvings = 0;

        for (const record of records) {
            const event = text(
                record,
                "event_type",
            ).toLowerCase();

            if (event === "heat_detected") {
                heat++;
            }

            if (event === "insemination") {
                services++;
            }

            if (
                event === "pregnancy_confirmed"
            ) {
                confirmed++;
            }

            if (event === "calving") {
                calvings++;
            }
        }

        return {
            heat,
            services,
            confirmed,
            calvings,
            conceptionRate:
                services > 0
                    ? (
                        confirmed / services * 100
                    ).toFixed(1)
                    : "0.0",
        };
    }, [records]);

    const attention = useMemo(
        () =>
            Array.from(latestByAnimal.entries())
                .filter(([, record]) => {
                    const event = text(
                        record,
                        "event_type",
                    ).toLowerCase();

                    const age = daysSince(record);

                    return (
                        event === "heat_detected"
                        ||
                        event === "pregnancy_diagnosis"
                        ||
                        event === "pregnancy_negative"
                        ||
                        (
                            event === "insemination"
                            && age !== null
                            && age >= 28
                        )
                    );
                })
                .sort((a, b) => {
                    const da = dateValue(a[1]);
                    const db = dateValue(b[1]);

                    return (
                        (db?.getTime() ?? 0)
                        -
                        (da?.getTime() ?? 0)
                    );
                }),
        [latestByAnimal],
    );

    async function recordEvent(
        event: React.FormEvent,
    ) {
        event.preventDefault();

        if (!animalId || !eventType || !operator) {
            setError(
                "Animal, event and operator are required.",
            );
            return;
        }

        setSaving(true);
        setError("");
        setMessage("");

        try {
            const response = await fetch(
                `${API}/farm/breeding`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        animal_id: animalId,
                        event_type: eventType,
                        technician:
                            technician || null,
                        result:
                            result || null,
                        semen_or_bull:
                            semen || null,
                        notes:
                            notes || null,
                        operator,
                    }),
                },
            );

            if (!response.ok) {
                const detail =
                    await response.text();

                throw new Error(
                    detail ||
                    `Unable to record event (${response.status})`,
                );
            }

            setMessage(
                `Reproduction event recorded for ${animalId}.`,
            );

            setResult("");
            setSemen("");
            setNotes("");

            await refresh();
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to record reproduction event.",
            );
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="reproduction-management">
            <div className="reproduction-kpis">
                <div>
                    <span>Heat observations</span>
                    <strong>{stats.heat}</strong>
                </div>

                <div>
                    <span>Inseminations</span>
                    <strong>{stats.services}</strong>
                </div>

                <div>
                    <span>Pregnancies confirmed</span>
                    <strong>{stats.confirmed}</strong>
                </div>

                <div>
                    <span>Calvings</span>
                    <strong>{stats.calvings}</strong>
                </div>

                <div>
                    <span>Conception rate</span>
                    <strong>
                        {stats.conceptionRate}%
                    </strong>
                </div>
            </div>

            {error && (
                <div className="reproduction-message error">
                    {error}
                </div>
            )}

            {message && (
                <div className="reproduction-message success">
                    {message}
                </div>
            )}

            <div className="reproduction-grid">
                <section className="reproduction-panel">
                    <div className="reproduction-panel-heading">
                        <h2>Record Reproduction Event</h2>
                        <p>
                            Every event is permanently linked
                            to the animal ID.
                        </p>
                    </div>

                    <form
                        className="reproduction-form"
                        onSubmit={recordEvent}
                    >
                        <label>
                            Animal
                            <select
                                value={animalId}
                                onChange={event =>
                                    setAnimalId(
                                        event.target.value,
                                    )
                                }
                                required
                            >
                                <option value="">
                                    Select animal
                                </option>

                                {animals.map(
                                    animal => (
                                        <option
                                            key={String(
                                                animal.animal_id,
                                            )}
                                            value={String(
                                                animal.animal_id,
                                            )}
                                        >
                                            {String(
                                                animal.animal_id,
                                            )}
                                        </option>
                                    ),
                                )}
                            </select>
                        </label>

                        <label>
                            Event
                            <select
                                value={eventType}
                                onChange={event =>
                                    setEventType(
                                        event.target.value,
                                    )
                                }
                            >
                                <option value="heat_detected">
                                    Heat detected
                                </option>
                                <option value="insemination">
                                    Insemination
                                </option>
                                <option value="pregnancy_diagnosis">
                                    Pregnancy diagnosis
                                </option>
                                <option value="pregnancy_confirmed">
                                    Pregnancy confirmed
                                </option>
                                <option value="pregnancy_negative">
                                    Pregnancy negative
                                </option>
                                <option value="dry_off">
                                    Dry off
                                </option>
                                <option value="calving">
                                    Calving
                                </option>
                                <option value="abortion">
                                    Abortion
                                </option>
                                <option value="stillbirth">
                                    Stillbirth
                                </option>
                                <option value="postpartum_observation">
                                    Postpartum observation
                                </option>
                            </select>
                        </label>

                        <label>
                            Technician
                            <input
                                value={technician}
                                onChange={event =>
                                    setTechnician(
                                        event.target.value,
                                    )
                            }
                            />
                        </label>

                        <label>
                            Result
                            <input
                                value={result}
                                onChange={event =>
                                    setResult(
                                        event.target.value,
                                    )
                                }
                            />
                        </label>

                        <label>
                            Semen / Bull
                            <input
                                value={semen}
                                onChange={event =>
                                    setSemen(
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

                        <label className="full-width">
                            Notes
                            <textarea
                                value={notes}
                                onChange={event =>
                                    setNotes(
                                        event.target.value,
                                    )
                                }
                            />
                        </label>

                        <button
                            className="reproduction-primary"
                            type="submit"
                            disabled={saving}
                        >
                            {saving
                                ? "Saving..."
                                : "Record Event"}
                        </button>
                    </form>
                </section>

                <section className="reproduction-panel">
                    <div className="reproduction-panel-heading">
                        <h2>Reproduction Attention</h2>
                        <p>
                            Animals requiring follow-up.
                        </p>
                    </div>

                    {attention.length === 0 ? (
                        <div className="reproduction-empty">
                            No reproduction attention currently
                            identified.
                        </div>
                    ) : (
                        <div className="reproduction-attention">
                            {attention.map(
                                ([id, record]) => (
                                    <button
                                        key={id}
                                        type="button"
                                        onClick={() =>
                                            onOpenAnimal(
                                                id,
                                            )
                                        }
                                    >
                                        <strong>{id}</strong>

                                        <span>
                                            {text(
                                                record,
                                                "event_type",
                                            )}
                                        </span>

                                        <small>
                                            {text(
                                                record,
                                                "timestamp",
                                            )}
                                        </small>
                                    </button>
                                ),
                            )}
                        </div>
                    )}
                </section>
            </div>

            <section className="reproduction-panel">
                <div className="reproduction-panel-heading">
                    <h2>Reproductive History</h2>
                    <p>
                        Complete event history with direct
                        Animal Passport linkage.
                    </p>
                </div>

                <div className="reproduction-table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Animal</th>
                                <th>Event</th>
                                <th>Technician</th>
                                <th>Result</th>
                                <th>Date</th>
                                <th />
                            </tr>
                        </thead>

                        <tbody>
                            {[...records]
                                .reverse()
                                .slice(0, 100)
                                .map(
                                    (
                                        record,
                                        index,
                                    ) => {
                                        const id =
                                            text(
                                                record,
                                                "animal_id",
                                            );

                                        return (
                                            <tr
                                                key={`${id}-${index}`}
                                            >
                                                <td>
                                                    <button
                                                        className="reproduction-link"
                                                        type="button"
                                                        onClick={() =>
                                                            onOpenAnimal(
                                                                id,
                                                            )
                                                        }
                                                    >
                                                        {id}
                                                    </button>
                                                </td>

                                                <td>
                                                    {text(
                                                        record,
                                                        "event_type",
                                                    )}
                                                </td>

                                                <td>
                                                    {text(
                                                        record,
                                                        "technician",
                                                    )}
                                                </td>

                                                <td>
                                                    {text(
                                                        record,
                                                        "result",
                                                    )}
                                                </td>

                                                <td>
                                                    {text(
                                                        record,
                                                        "timestamp",
                                                    )}
                                                </td>

                                                <td>
                                                    <button
                                                        className="reproduction-small-button"
                                                        type="button"
                                                        onClick={() =>
                                                            onOpenAnimal(
                                                                id,
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
            </section>
        </div>
    );
}

export default ReproductionManagement;
