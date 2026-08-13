import React, { useCallback, useEffect, useMemo, useState } from "react";
import "./AnimalRegistry.css";

type Animal = {
    id: number | string;
    animal_id: string;
    animal_type?: string | null;
    ear_tag?: string | null;
    rfid?: string | null;
    breed?: string | null;
    sex?: string | null;
    date_of_birth?: string | null;
    dam_id?: string | null;
    sire_id?: string | null;
    lifecycle_status?: string | null;
    status?: string | null;
    is_currently_milking?: boolean;
    milking_frequency?: string | null;
    production_group?: string | null;
    location?: string | null;
    active?: boolean;
    created_at?: string | null;
    updated_at?: string | null;
};

type Passport = {
    [key: string]: unknown;
};

type Props = {
    onNavigate: (
        view: "milk" | "feed" | "health" | "breeding"
    ) => void;
};

const API = "http://localhost:8000";

const initialForm = {
    animal_type: "COW",
    ear_tag: "",
    rfid: "",
    breed: "",
    sex: "FEMALE",
    date_of_birth: "",
    dam_id: "",
    sire_id: "",
    lifecycle_status: "HEIFER",
    is_currently_milking: false,
    milking_frequency: "",
    production_group: "",
    location: "",
};

function display(value: unknown): string {
    if (value === null || value === undefined || value === "") {
        return "Unavailable";
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}

function AnimalRegistry({ onNavigate }: Props) {
    const [animals, setAnimals] = useState<Animal[]>([]);
    const [selected, setSelected] = useState<Animal | null>(null);
    const [passport, setPassport] = useState<Passport | null>(null);
    const [showEntry, setShowEntry] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [passportLoading, setPassportLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [form, setForm] = useState(initialForm);

    const loadAnimals = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch(`${API}/farm/animals`);

            if (!response.ok) {
                throw new Error(`Animal registry request failed (${response.status})`);
            }

            const payload = await response.json();

            if (!Array.isArray(payload)) {
                throw new Error("Animal registry returned an invalid response");
            }

            setAnimals(payload);
        } catch (exc) {
            setError(
                exc instanceof Error
                    ? exc.message
                    : "Unable to load animal registry"
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadAnimals();
    }, [loadAnimals]);

    const openPassport = async (animal: Animal) => {
        setSelected(animal);
        setPassport(null);
        setPassportLoading(true);
        setError("");

        try {
            const response = await fetch(
                `${API}/farm/animals/${encodeURIComponent(animal.animal_id)}/passport`
            );

            if (!response.ok) {
                throw new Error(`Animal Passport request failed (${response.status})`);
            }

            setPassport(await response.json());
        } catch (exc) {
            setError(
                exc instanceof Error
                    ? exc.message
                    : "Unable to load Animal Passport"
            );
        } finally {
            setPassportLoading(false);
        }
    };

    const closePassport = () => {
        setSelected(null);
        setPassport(null);
    };

    const updateForm = (
        name: keyof typeof initialForm,
        value: string | boolean
    ) => {
        setForm((current) => ({
            ...current,
            [name]: value,
        }));
    };

    const submitAnimal = async (event: React.FormEvent) => {
        event.preventDefault();
        setSaving(true);
        setError("");
        setSuccess("");

        const payload: Record<string, unknown> = {
            animal_type: form.animal_type,
            lifecycle_status: form.lifecycle_status,
            active: true,
            is_currently_milking: form.is_currently_milking,
        };

        const optionalTextFields = [
            "ear_tag",
            "rfid",
            "breed",
            "sex",
            "date_of_birth",
            "dam_id",
            "sire_id",
            "milking_frequency",
            "production_group",
            "location",
        ] as const;

        for (const field of optionalTextFields) {
            const value = form[field];

            if (value) {
                payload[field] = value;
            }
        }

        try {
            const response = await fetch(`${API}/farm/animals`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const body = await response.json().catch(() => null);

            if (!response.ok) {
                const detail =
                    body &&
                    typeof body === "object" &&
                    "detail" in body
                        ? String(body.detail)
                        : `Animal creation failed (${response.status})`;

                throw new Error(detail);
            }

            const created = body as Animal;

            setSuccess(
                `Animal registered successfully: ${created.animal_id}`
            );

            setForm(initialForm);
            setShowEntry(false);

            await loadAnimals();
            await openPassport(created);
        } catch (exc) {
            setError(
                exc instanceof Error
                    ? exc.message
                    : "Animal registration failed"
            );
        } finally {
            setSaving(false);
        }
    };

    const counts = useMemo(() => {
        const milking = animals.filter(
            (animal) => animal.is_currently_milking
        ).length;

        const dryOther = animals.length - milking;

        return {
            total: animals.length,
            milking,
            dryOther,
        };
    }, [animals]);

    return (
        <section className="animal-registry">
            <div className="animal-registry-toolbar">
                <div>
                    <div className="animal-registry-kicker">
                        LIVE OPERATIONS
                    </div>
                    <h2>Animals</h2>
                    <p>
                        Actual records only. Every animal receives a permanent
                        DairyOS-generated Animal ID.
                    </p>
                </div>

                <div className="animal-registry-actions">
                    <button
                        type="button"
                        className="animal-button secondary"
                        onClick={() => void loadAnimals()}
                        disabled={loading}
                    >
                        {loading ? "Refreshing…" : "Refresh"}
                    </button>

                    <button
                        type="button"
                        className="animal-button primary"
                        onClick={() => {
                            setError("");
                            setSuccess("");
                            setShowEntry(true);
                        }}
                    >
                        + Register Animal
                    </button>
                </div>
            </div>

            <div className="animal-summary-grid">
                <div className="animal-summary-card">
                    <span>Animals in view</span>
                    <strong>{counts.total}</strong>
                </div>

                <div className="animal-summary-card">
                    <span>Milking</span>
                    <strong>
                        {counts.milking === 0 ? "—" : counts.milking}
                    </strong>
                </div>

                <div className="animal-summary-card">
                    <span>Dry / other</span>
                    <strong>
                        {counts.dryOther === 0 ? "—" : counts.dryOther}
                    </strong>
                </div>

                <div className="animal-summary-card">
                    <span>Source</span>
                    <strong>Live registry</strong>
                </div>
            </div>

            {error && (
                <div className="animal-message error">
                    {error}
                </div>
            )}

            {success && (
                <div className="animal-message success">
                    {success}
                </div>
            )}

            <div className="animal-registry-content">
                {loading ? (
                    <div className="animal-empty">
                        Loading live animal registry…
                    </div>
                ) : animals.length === 0 ? (
                    <div className="animal-empty">
                        <strong>No animal records in this view</strong>
                        <span>
                            The API is available, but no animal has yet been
                            registered.
                        </span>
                        <button
                            type="button"
                            className="animal-button primary"
                            onClick={() => setShowEntry(true)}
                        >
                            Register the first animal
                        </button>
                    </div>
                ) : (
                    <div className="animal-grid">
                        {animals.map((animal) => (
                            <button
                                key={animal.animal_id}
                                type="button"
                                className="animal-card"
                                onClick={() => void openPassport(animal)}
                            >
                                <div className="animal-card-top">
                                    <span className="animal-tag">
                                        {animal.animal_id}
                                    </span>

                                    <span
                                        className={
                                            animal.active
                                                ? "animal-status active"
                                                : "animal-status"
                                        }
                                    >
                                        {animal.active
                                            ? "ACTIVE"
                                            : "INACTIVE"}
                                    </span>
                                </div>

                                <div className="animal-card-title">
                                    {animal.ear_tag || animal.animal_id}
                                </div>

                                <div className="animal-card-subtitle">
                                    {display(animal.breed)} ·{" "}
                                    {display(animal.sex)}
                                </div>

                                <div className="animal-card-data">
                                    <span>
                                        Lifecycle
                                        <strong>
                                            {display(
                                                animal.lifecycle_status
                                            )}
                                        </strong>
                                    </span>

                                    <span>
                                        Location
                                        <strong>
                                            {display(animal.location)}
                                        </strong>
                                    </span>

                                    <span>
                                        Milking
                                        <strong>
                                            {animal.is_currently_milking
                                                ? "Yes"
                                                : "No"}
                                        </strong>
                                    </span>
                                </div>

                                <div className="animal-card-footer">
                                    Open Animal Passport →
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {showEntry && (
                <div className="animal-modal-backdrop">
                    <div className="animal-modal" role="dialog" aria-modal="true">
                        <div className="animal-modal-header">
                            <div>
                                <div className="animal-registry-kicker">
                                    ANIMAL ENTRY
                                </div>
                                <h3>Register Animal</h3>
                                <p>
                                    Animal ID is generated by DairyOS after
                                    successful database persistence.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="animal-close"
                                onClick={() => setShowEntry(false)}
                            >
                                ×
                            </button>
                        </div>

                        <form onSubmit={submitAnimal}>
                            <div className="animal-form-grid">
                                <label>
                                    Animal Type
                                    <select
                                        value={form.animal_type}
                                        onChange={(event) =>
                                            updateForm(
                                                "animal_type",
                                                event.target.value
                                            )
                                        }
                                    >
                                        <option value="COW">COW</option>
                                        <option value="HEIFER">HEIFER</option>
                                        <option value="CALF">CALF</option>
                                        <option value="BULL">BULL</option>
                                    </select>
                                </label>

                                <label>
                                    Ear Tag
                                    <input
                                        value={form.ear_tag}
                                        onChange={(event) =>
                                            updateForm(
                                                "ear_tag",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Physical ear tag"
                                    />
                                </label>

                                <label>
                                    RFID
                                    <input
                                        value={form.rfid}
                                        onChange={(event) =>
                                            updateForm(
                                                "rfid",
                                                event.target.value
                                            )
                                        }
                                        placeholder="RFID / transponder"
                                    />
                                </label>

                                <label>
                                    Breed
                                    <input
                                        value={form.breed}
                                        onChange={(event) =>
                                            updateForm(
                                                "breed",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Holstein Friesian"
                                    />
                                </label>

                                <label>
                                    Sex
                                    <select
                                        value={form.sex}
                                        onChange={(event) =>
                                            updateForm(
                                                "sex",
                                                event.target.value
                                            )
                                        }
                                    >
                                        <option value="FEMALE">FEMALE</option>
                                        <option value="MALE">MALE</option>
                                    </select>
                                </label>

                                <label>
                                    Date of Birth
                                    <input
                                        type="date"
                                        value={form.date_of_birth}
                                        onChange={(event) =>
                                            updateForm(
                                                "date_of_birth",
                                                event.target.value
                                            )
                                        }
                                    />
                                </label>

                                <label>
                                    Lifecycle Status
                                    <select
                                        value={form.lifecycle_status}
                                        onChange={(event) =>
                                            updateForm(
                                                "lifecycle_status",
                                                event.target.value
                                            )
                                        }
                                    >
                                        <option value="CALF">CALF</option>
                                        <option value="HEIFER">HEIFER</option>
                                        <option value="CLOSE_UP">CLOSE_UP</option>
                                        <option value="LACTATING">
                                            LACTATING
                                        </option>
                                        <option value="DRY">DRY</option>
                                        <option value="SICK">SICK</option>
                                    </select>
                                </label>

                                <label>
                                    Production Group
                                    <input
                                        value={form.production_group}
                                        onChange={(event) =>
                                            updateForm(
                                                "production_group",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Milking group"
                                    />
                                </label>

                                <label>
                                    Location
                                    <input
                                        value={form.location}
                                        onChange={(event) =>
                                            updateForm(
                                                "location",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Shed / pen"
                                    />
                                </label>

                                <label>
                                    Dam Animal ID
                                    <input
                                        value={form.dam_id}
                                        onChange={(event) =>
                                            updateForm(
                                                "dam_id",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Optional existing Animal ID"
                                    />
                                </label>

                                <label>
                                    Sire Animal ID
                                    <input
                                        value={form.sire_id}
                                        onChange={(event) =>
                                            updateForm(
                                                "sire_id",
                                                event.target.value
                                            )
                                        }
                                        placeholder="Optional existing Animal ID"
                                    />
                                </label>

                                <label>
                                    Milking Frequency
                                    <select
                                        value={form.milking_frequency}
                                        onChange={(event) =>
                                            updateForm(
                                                "milking_frequency",
                                                event.target.value
                                            )
                                        }
                                    >
                                        <option value="">
                                            Not specified
                                        </option>
                                        <option value="ONCE_DAILY">
                                            ONCE_DAILY
                                        </option>
                                        <option value="TWICE_DAILY">
                                            TWICE_DAILY
                                        </option>
                                        <option value="THRICE_DAILY">
                                            THRICE_DAILY
                                        </option>
                                    </select>
                                </label>

                                <label className="animal-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={form.is_currently_milking}
                                        onChange={(event) =>
                                            updateForm(
                                                "is_currently_milking",
                                                event.target.checked
                                            )
                                        }
                                    />
                                    Currently milking
                                </label>
                            </div>

                            <div className="animal-form-footer">
                                <button
                                    type="button"
                                    className="animal-button secondary"
                                    onClick={() => setShowEntry(false)}
                                >
                                    Cancel
                                </button>

                                <button
                                    type="submit"
                                    className="animal-button primary"
                                    disabled={saving}
                                >
                                    {saving
                                        ? "Persisting…"
                                        : "Create Animal"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {selected && (
                <div className="animal-modal-backdrop">
                    <div className="animal-passport-modal">
                        <div className="animal-modal-header">
                            <div>
                                <div className="animal-registry-kicker">
                                    LIFETIME RECORD
                                </div>
                                <h3>
                                    Animal Passport —{" "}
                                    {selected.animal_id}
                                </h3>
                            </div>

                            <button
                                type="button"
                                className="animal-close"
                                onClick={closePassport}
                            >
                                ×
                            </button>
                        </div>

                        <div className="animal-passport-actions">
                            <button
                                type="button"
                                className="animal-button primary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate("milk");
                                }}
                            >
                                Milk
                            </button>

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate("feed");
                                }}
                            >
                                Feed
                            </button>

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate("health");
                                }}
                            >
                                Health
                            </button>

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate("breeding");
                                }}
                            >
                                Breeding
                            </button>
                        </div>

                        {passportLoading ? (
                            <div className="animal-empty">
                                Loading authoritative Animal Passport…
                            </div>
                        ) : passport ? (
                            <div className="animal-passport">
                                <div className="animal-passport-identity">
                                    <div>
                                        <span>Permanent Animal ID</span>
                                        <strong>
                                            {selected.animal_id}
                                        </strong>
                                    </div>
                                    <div>
                                        <span>Lifecycle</span>
                                        <strong>
                                            {display(
                                                selected.lifecycle_status
                                            )}
                                        </strong>
                                    </div>
                                    <div>
                                        <span>Breed</span>
                                        <strong>
                                            {display(selected.breed)}
                                        </strong>
                                    </div>
                                    <div>
                                        <span>Ear Tag</span>
                                        <strong>
                                            {display(selected.ear_tag)}
                                        </strong>
                                    </div>
                                </div>

                                <div className="animal-passport-json">
                                    {Object.entries(passport).map(
                                        ([key, value]) => (
                                            <div
                                                key={key}
                                                className="animal-passport-row"
                                            >
                                                <span>{key}</span>
                                                <strong>
                                                    {display(value)}
                                                </strong>
                                            </div>
                                        )
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="animal-empty">
                                Animal Passport unavailable.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </section>
    );
}

export default AnimalRegistry;
