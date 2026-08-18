import React, { useCallback, useEffect, useMemo, useState } from "react";
import "./AnimalRegistry.css";
import { API_BASE_URL as API } from "../config/api";

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
    non_milking_directive?: string | null;
    non_milking_reason?: string | null;
    non_milking_since?: string | null;
    non_milking_until?: string | null;
    non_milking_changed_by?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
};

type PassportRecord = {
    [key: string]: any;
};

type Passport = {
    animal?: PassportRecord;

    schedule?: {
        effective?: {
            milking_frequency?: string | null;
            expected_sessions?: string[] | null;
            source?: string | null;
        } | null;
    } | null;

    history?: {
        milk?: PassportRecord[];
        feed?: PassportRecord[];
        health?: PassportRecord[];
        breeding?: PassportRecord[];
        treatments?: PassportRecord[];
        finance?: PassportRecord[];
        operational_events?: PassportRecord[];
    };

    timeline?: Array<{
        domain: string;
        timestamp: string;
        record: PassportRecord;
    }>;

    record_counts?: Record<string, number>;
};

type Props = {
    onNavigate: (
        view: "milk" | "feed" | "health" | "breeding",
    ) => void;
};

type OperationalMode =
    | "MILKING"
    | "NON_MILKING";

type NonMilkingCategory =
    | "HEALTH"
    | "DRY_REPRODUCTIVE"
    | "MILK_SEPARATELY"
    | "PERMANENT"
    | "OTHER";

const initialForm = {
    animal_type: "COW",
    ear_tag: "",
    rfid: "",
    breed: "",
    sex: "FEMALE",
    date_of_birth: "",
    dam_id: "",
    sire_id: "",
    production_group: "",
    location: "",

    operational_mode:
        "MILKING" as OperationalMode,

    milking_frequency:
        "TWICE_DAILY",

    non_milking_category:
        "HEALTH" as NonMilkingCategory,

    non_milking_reason: "",
};

function display(value: unknown): string {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "Unavailable";
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (typeof value === "object") {
        return "Recorded";
    }

    return String(value);
}

function formatDate(value: unknown): string {
    if (!value) {
        return "Unavailable";
    }

    const parsed = new Date(String(value));

    if (Number.isNaN(parsed.getTime())) {
        return String(value);
    }

    return parsed.toLocaleString();
}

function frequencyLabel(
    value: string | null | undefined,
): string {
    switch (
        String(value ?? "").toUpperCase()
    ) {
        case "TWICE_DAILY":
            return "2 sessions";

        case "THRICE_DAILY":
            return "3 sessions";

        default:
            return "Not set";
    }
}

function nonMilkingCategoryLabel(
    category: NonMilkingCategory | string | null | undefined,
): string {
    switch (
        String(category ?? "").toUpperCase()
    ) {
        case "HEALTH":
            return "Health restriction";

        case "DRY_REPRODUCTIVE":
            return "Dry / reproductive break";

        case "MILK_SEPARATELY":
            return "Milk separately";

        case "PERMANENT":
            return "Permanent non-milking";

        case "OTHER":
            return "Other operational";

        default:
            return "Non-milking";
    }
}

function directiveForCategory(
    category: NonMilkingCategory,
): string {
    switch (category) {
        case "MILK_SEPARATELY":
            return "MILK_SEPARATELY";

        case "PERMANENT":
            return "PERMANENT_NON_MILKING";

        case "HEALTH":
        case "DRY_REPRODUCTIVE":
        case "OTHER":
        default:
            return "TEMPORARY_NON_MILKING";
    }
}

function getOperatorAlerts(
    passport: Passport,
): string[] {
    const alerts: string[] = [];

    const health =
        passport.history?.health ?? [];

    health.forEach((item) => {
        if (
            String(item.severity).toUpperCase() ===
            "CRITICAL"
        ) {
            alerts.push(
                `${item.observation ?? "Health event"} requires attention`,
            );
        }
    });

    return alerts;
}

function domainLabel(
    domain: string,
): string {
    const labels: Record<
        string,
        string
    > = {
        milk: "Milk Production",
        feed: "Feeding",
        health: "Health Observation",
        breeding: "Breeding",
        operational_events: "Farm Event",
    };

    return (
        labels[domain] ?? domain
    );
}

function AnimalRegistry({
    onNavigate,
}: Props) {
    const [animals, setAnimals] =
        useState<Animal[]>([]);

    const [selected, setSelected] =
        useState<Animal | null>(null);

    const [passport, setPassport] =
        useState<Passport | null>(null);

    const [showEntry, setShowEntry] =
        useState(false);

    const [loading, setLoading] =
        useState(true);

    const [saving, setSaving] =
        useState(false);

    const [passportLoading, setPassportLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    const [success, setSuccess] =
        useState("");

    const [form, setForm] =
        useState(initialForm);

    const loadAnimals = useCallback(
        async () => {
            setLoading(true);
            setError("");

            try {
                const response =
                    await fetch(
                        `${API}/farm/animals`,
                    );

                if (!response.ok) {
                    throw new Error(
                        `Animal registry request failed (${response.status})`,
                    );
                }

                const payload =
                    await response.json();

                if (
                    !Array.isArray(
                        payload,
                    )
                ) {
                    throw new Error(
                        "Animal registry returned an invalid response",
                    );
                }

                setAnimals(payload);
            } catch (exc) {
                setError(
                    exc instanceof Error
                        ? exc.message
                        : "Unable to load animal registry",
                );
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    useEffect(() => {
        void loadAnimals();
    }, [loadAnimals]);

    const openPassport = async (
        animal: Animal,
    ) => {
        setSelected(animal);
        setPassport(null);
        setPassportLoading(true);
        setError("");

        try {
            const response =
                await fetch(
                    `${API}/farm/animals/${encodeURIComponent(animal.animal_id)}/passport`,
                );

            if (!response.ok) {
                throw new Error(
                    `Animal Passport request failed (${response.status})`,
                );
            }

            setPassport(
                await response.json(),
            );
        } catch (exc) {
            setError(
                exc instanceof Error
                    ? exc.message
                    : "Unable to load Animal Passport",
            );
        } finally {
            setPassportLoading(
                false,
            );
        }
    };

    const closePassport = () => {
        setSelected(null);
        setPassport(null);
    };

    const updateForm = (
        name: keyof typeof initialForm,
        value: string,
    ) => {
        setForm((current) => ({
            ...current,
            [name]: value,
        }));
    };

    const submitAnimal = async (
        event: React.FormEvent,
    ) => {
        event.preventDefault();

        setSaving(true);
        setError("");
        setSuccess("");

        const isMilking =
            form.operational_mode ===
            "MILKING";

        if (
            !isMilking &&
            !form.non_milking_reason.trim()
        ) {
            setSaving(false);
            setError(
                "A documented reason is required for a non-milking animal.",
            );
            return;
        }

        const payload: Record<
            string,
            unknown
        > = {
            animal_type:
                form.animal_type,

            lifecycle_status:
                isMilking
                    ? "LACTATING"
                    : "DRY",

            active: true,

            is_currently_milking:
                isMilking,
        };

        if (isMilking) {
            payload.milking_frequency =
                form.milking_frequency;
        }

        const optionalTextFields = [
            "ear_tag",
            "rfid",
            "breed",
            "sex",
            "date_of_birth",
            "dam_id",
            "sire_id",
            "production_group",
            "location",
        ] as const;

        for (const field of optionalTextFields) {
            const value =
                form[field];

            if (value) {
                payload[field] = value;
            }
        }

        try {
            const response =
                await fetch(
                    `${API}/farm/animals`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",
                        },
                        body: JSON.stringify(
                            payload,
                        ),
                    },
                );

            const body =
                await response
                    .json()
                    .catch(
                        () => null,
                    );

            if (!response.ok) {
                const detail =
                    body &&
                    typeof body ===
                        "object" &&
                    "detail" in body
                        ? String(
                              body.detail,
                          )
                        : `Animal creation failed (${response.status})`;

                throw new Error(
                    detail,
                );
            }

            const created =
                body as Animal;

            /*
             * Non-milking governance is deliberately applied through the
             * existing veterinary endpoint rather than by inventing a second
             * persistence model in the UI.
             */
            if (!isMilking) {
                const directive =
                    directiveForCategory(
                        form.non_milking_category,
                    );

                const documentedReason =
                    `${nonMilkingCategoryLabel(form.non_milking_category)}: ${form.non_milking_reason.trim()}`;

                const directiveResponse =
                    await fetch(
                        `${API}/farm/animals/${encodeURIComponent(created.animal_id)}/non-milking-directive`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    directive,
                                    reason:
                                        documentedReason,
                                    changed_by:
                                        "Operator UI",
                                },
                            ),
                        },
                    );

                if (
                    !directiveResponse.ok
                ) {
                    const directiveBody =
                        await directiveResponse
                            .json()
                            .catch(
                                () =>
                                    null,
                            );

                    const detail =
                        directiveBody &&
                        typeof directiveBody ===
                            "object" &&
                        "detail" in
                            directiveBody
                            ? String(
                                  directiveBody.detail,
                              )
                            : `Non-milking governance failed (${directiveResponse.status})`;

                    throw new Error(
                        `Animal ${created.animal_id} was registered, but the non-milking governance step failed: ${detail}`,
                    );
                }
            }

            setSuccess(
                isMilking
                    ? `Animal ${created.animal_id} registered as MILKING · ${frequencyLabel(form.milking_frequency)}.`
                    : `Animal ${created.animal_id} registered as NON-MILKING · ${nonMilkingCategoryLabel(form.non_milking_category)}.`,
            );

            setForm(initialForm);
            setShowEntry(false);

            await loadAnimals();
        } catch (exc) {
            setError(
                exc instanceof Error
                    ? exc.message
                    : "Animal registration failed",
            );
        } finally {
            setSaving(false);
        }
    };

    const counts = useMemo(() => {
        const milking =
            animals.filter(
                (animal) =>
                    animal.is_currently_milking,
            ).length;

        const nonMilking =
            animals.length -
            milking;

        return {
            total:
                animals.length,
            milking,
            nonMilking,
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
                        Each animal has one operational
                        state: MILKING with a 2- or
                        3-session plan, or NON-MILKING
                        with a governed reason.
                    </p>
                </div>

                <div className="animal-registry-actions">
                    <button
                        type="button"
                        className="animal-button secondary"
                        onClick={() =>
                            void loadAnimals()
                        }
                        disabled={loading}
                    >
                        {loading
                            ? "Refreshing…"
                            : "Refresh"}
                    </button>

                    <button
                        type="button"
                        className="animal-button primary"
                        onClick={() => {
                            setError("");
                            setSuccess("");
                            setForm(
                                initialForm,
                            );
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
                    <strong>
                        {counts.total}
                    </strong>
                </div>

                <div className="animal-summary-card">
                    <span>Milking</span>
                    <strong>
                        {counts.milking ===
                        0
                            ? "—"
                            : counts.milking}
                    </strong>
                </div>

                <div className="animal-summary-card">
                    <span>Non-milking</span>
                    <strong>
                        {counts.nonMilking ===
                        0
                            ? "—"
                            : counts.nonMilking}
                    </strong>
                </div>

                <div className="animal-summary-card">
                    <span>Source</span>
                    <strong>
                        Live registry
                    </strong>
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
                ) : animals.length ===
                  0 ? (
                    <div className="animal-empty">
                        <strong>
                            No animal records in this
                            view
                        </strong>

                        <span>
                            The API is available, but no
                            animal has yet been registered.
                        </span>

                        <button
                            type="button"
                            className="animal-button primary"
                            onClick={() =>
                                setShowEntry(
                                    true,
                                )
                            }
                        >
                            Register the first animal
                        </button>
                    </div>
                ) : (
                    <div className="animal-grid">
                        {animals.map(
                            (animal) => {
                                const milking =
                                    animal.is_currently_milking ===
                                    true;

                                return (
                                    <button
                                        key={
                                            animal.animal_id
                                        }
                                        type="button"
                                        className="animal-card"
                                        onClick={() =>
                                            void openPassport(
                                                animal,
                                            )
                                        }
                                    >
                                        <div className="animal-card-top">
                                            <span className="animal-tag">
                                                {
                                                    animal.animal_id
                                                }
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
                                            {animal.ear_tag ||
                                                animal.animal_id}
                                        </div>

                                        <div className="animal-card-subtitle">
                                            {display(
                                                animal.breed,
                                            )}{" "}
                                            ·{" "}
                                            {display(
                                                animal.sex,
                                            )}
                                        </div>

                                        <div className="animal-card-data">
                                            <span>
                                                Operational
                                                status

                                                <strong>
                                                    {milking
                                                        ? `MILKING · ${frequencyLabel(animal.milking_frequency)}`
                                                        : `NON-MILKING · ${animal.non_milking_reason || display(animal.lifecycle_status)}`}
                                                </strong>
                                            </span>

                                            <span>
                                                Lifecycle

                                                <strong>
                                                    {display(
                                                        animal.lifecycle_status,
                                                    )}
                                                </strong>
                                            </span>

                                            <span>
                                                Location

                                                <strong>
                                                    {display(
                                                        animal.location,
                                                    )}
                                                </strong>
                                            </span>
                                        </div>

                                        <div className="animal-card-footer">
                                            Open Animal Passport →
                                        </div>
                                    </button>
                                );
                            },
                        )}
                    </div>
                )}
            </div>

            {showEntry && (
                <div className="animal-modal-backdrop">
                    <div
                        className="animal-modal"
                        role="dialog"
                        aria-modal="true"
                    >
                        <div className="animal-modal-header">
                            <div>
                                <div className="animal-registry-kicker">
                                    ANIMAL ENTRY
                                </div>

                                <h3>
                                    Register Animal
                                </h3>

                                <p>
                                    First decide whether
                                    the animal is currently
                                    MILKING or NON-MILKING.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="animal-close"
                                onClick={() =>
                                    setShowEntry(
                                        false,
                                    )
                                }
                            >
                                ×
                            </button>
                        </div>

                        <form
                            onSubmit={
                                submitAnimal
                            }
                        >
                            <div className="animal-form-grid">
                                <label>
                                    Animal Type

                                    <select
                                        value={
                                            form.animal_type
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "animal_type",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                    >
                                        <option value="COW">
                                            COW
                                        </option>
                                        <option value="HEIFER">
                                            HEIFER
                                        </option>
                                        <option value="CALF">
                                            CALF
                                        </option>
                                        <option value="BULL">
                                            BULL
                                        </option>
                                    </select>
                                </label>

                                <label>
                                    Ear Tag

                                    <input
                                        value={
                                            form.ear_tag
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "ear_tag",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Physical ear tag"
                                    />
                                </label>

                                <label>
                                    RFID

                                    <input
                                        value={
                                            form.rfid
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "rfid",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="RFID / transponder"
                                    />
                                </label>

                                <label>
                                    Breed

                                    <input
                                        value={
                                            form.breed
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "breed",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Holstein Friesian"
                                    />
                                </label>

                                <label>
                                    Sex

                                    <select
                                        value={
                                            form.sex
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "sex",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                    >
                                        <option value="FEMALE">
                                            FEMALE
                                        </option>
                                        <option value="MALE">
                                            MALE
                                        </option>
                                    </select>
                                </label>

                                <label>
                                    Date of Birth

                                    <input
                                        type="date"
                                        value={
                                            form.date_of_birth
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "date_of_birth",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                    />
                                </label>

                                <label>
                                    Production Group

                                    <input
                                        value={
                                            form.production_group
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "production_group",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Milking group"
                                    />
                                </label>

                                <label>
                                    Location

                                    <input
                                        value={
                                            form.location
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "location",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Shed / pen"
                                    />
                                </label>

                                <div
                                    className="entry-field wide"
                                    style={{
                                        gridColumn:
                                            "1 / -1",
                                    }}
                                >
                                    <span>
                                        Operational
                                        Status *
                                    </span>

                                    <div
                                        style={{
                                            display:
                                                "flex",
                                            gap: "10px",
                                            flexWrap:
                                                "wrap",
                                        }}
                                    >
                                        {(
                                            [
                                                [
                                                    "MILKING",
                                                    "MILKING",
                                                ],
                                                [
                                                    "NON_MILKING",
                                                    "NON-MILKING",
                                                ],
                                            ] as const
                                        ).map(
                                            ([
                                                value,
                                                label,
                                            ]) => (
                                                <button
                                                    key={
                                                        value
                                                    }
                                                    type="button"
                                                    onClick={() =>
                                                        updateForm(
                                                            "operational_mode",
                                                            value,
                                                        )
                                                    }
                                                    style={{
                                                        padding:
                                                            "11px 18px",
                                                        borderRadius:
                                                            "8px",
                                                        border:
                                                            form.operational_mode ===
                                                            value
                                                                ? "2px solid #246a48"
                                                                : "1px solid #d8e3dc",
                                                        background:
                                                            form.operational_mode ===
                                                            value
                                                                ? "#e8f4ec"
                                                                : "#fff",
                                                        fontWeight:
                                                            800,
                                                        cursor:
                                                            "pointer",
                                                    }}
                                                >
                                                    {
                                                        label
                                                    }
                                                </button>
                                            ),
                                        )}
                                    </div>
                                </div>

                                {form.operational_mode ===
                                "MILKING" ? (
                                    <label
                                        style={{
                                            gridColumn:
                                                "1 / -1",
                                        }}
                                    >
                                        Milking Plan *

                                        <select
                                            value={
                                                form.milking_frequency
                                            }
                                            onChange={(
                                                event,
                                            ) =>
                                                updateForm(
                                                    "milking_frequency",
                                                    event
                                                        .target
                                                        .value,
                                                )
                                            }
                                        >
                                            <option value="TWICE_DAILY">
                                                2 sessions /
                                                day
                                            </option>

                                            <option value="THRICE_DAILY">
                                                3 sessions /
                                                day
                                            </option>
                                        </select>
                                    </label>
                                ) : (
                                    <>
                                        <label>
                                            Non-milking
                                            Category *

                                            <select
                                                value={
                                                    form.non_milking_category
                                                }
                                                onChange={(
                                                    event,
                                                ) =>
                                                    updateForm(
                                                        "non_milking_category",
                                                        event
                                                            .target
                                                            .value,
                                                    )
                                                }
                                            >
                                                <option value="HEALTH">
                                                    Health
                                                    restriction
                                                </option>

                                                <option value="DRY_REPRODUCTIVE">
                                                    Dry /
                                                    reproductive
                                                    break
                                                </option>

                                                <option value="MILK_SEPARATELY">
                                                    Milk
                                                    separately
                                                </option>

                                                <option value="PERMANENT">
                                                    Permanent
                                                    non-milking
                                                </option>

                                                <option value="OTHER">
                                                    Other
                                                    operational
                                                </option>
                                            </select>
                                        </label>

                                        <label>
                                            Documented
                                            Reason *

                                            <textarea
                                                value={
                                                    form.non_milking_reason
                                                }
                                                onChange={(
                                                    event,
                                                ) =>
                                                    updateForm(
                                                        "non_milking_reason",
                                                        event
                                                            .target
                                                            .value,
                                                    )
                                                }
                                                required
                                                rows={3}
                                                placeholder="State why this animal is not currently in the normal milking herd."
                                            />
                                        </label>
                                    </>
                                )}

                                <label>
                                    Dam Animal ID

                                    <input
                                        value={
                                            form.dam_id
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "dam_id",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Optional existing Animal ID"
                                    />
                                </label>

                                <label>
                                    Sire Animal ID

                                    <input
                                        value={
                                            form.sire_id
                                        }
                                        onChange={(
                                            event,
                                        ) =>
                                            updateForm(
                                                "sire_id",
                                                event
                                                    .target
                                                    .value,
                                            )
                                        }
                                        placeholder="Optional existing Animal ID"
                                    />
                                </label>
                            </div>

                            <div className="animal-form-footer">
                                <button
                                    type="button"
                                    className="animal-button secondary"
                                    onClick={() =>
                                        setShowEntry(
                                            false,
                                        )
                                    }
                                >
                                    Cancel
                                </button>

                                <button
                                    type="submit"
                                    className="animal-button primary"
                                    disabled={
                                        saving
                                    }
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
                                    {
                                        selected.animal_id
                                    }
                                </h3>
                            </div>

                            <button
                                type="button"
                                className="animal-close"
                                onClick={
                                    closePassport
                                }
                            >
                                ×
                            </button>
                        </div>

                        <div className="animal-passport-actions">
                            {selected.is_currently_milking ? (
                                <button
                                    type="button"
                                    className="animal-button primary"
                                    onClick={() => {
                                        closePassport();
                                        onNavigate(
                                            "milk",
                                        );
                                    }}
                                >
                                    Record Milk
                                </button>
                            ) : (
                                <div
                                    className="animal-message"
                                    style={{
                                        margin: 0,
                                    }}
                                >
                                    NON-MILKING —{" "}
                                    {selected.non_milking_reason ||
                                        display(
                                            selected.lifecycle_status,
                                        )}
                                </div>
                            )}

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate(
                                        "feed",
                                    );
                                }}
                            >
                                Feed
                            </button>

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate(
                                        "health",
                                    );
                                }}
                            >
                                Health
                            </button>

                            <button
                                type="button"
                                className="animal-button secondary"
                                onClick={() => {
                                    closePassport();
                                    onNavigate(
                                        "breeding",
                                    );
                                }}
                            >
                                Breeding
                            </button>
                        </div>

                        {passportLoading ? (
                            <div className="animal-empty">
                                Loading authoritative
                                Animal Passport…
                            </div>
                        ) : passport ? (
                            <div className="animal-passport">
                                <div className="animal-passport-identity">
                                    <div>
                                        <span>
                                            Permanent
                                            Animal ID
                                        </span>
                                        <strong>
                                            {
                                                selected.animal_id
                                            }
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Operational
                                            Status
                                        </span>

                                        <strong>
                                            {selected.is_currently_milking
                                                ? `MILKING · ${frequencyLabel(selected.milking_frequency)}`
                                                : `NON-MILKING · ${selected.non_milking_reason || "Reason recorded"}`}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Lifecycle
                                        </span>

                                        <strong>
                                            {display(
                                                selected.lifecycle_status,
                                            )}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Breed
                                        </span>

                                        <strong>
                                            {display(
                                                selected.breed,
                                            )}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>
                                            Ear Tag
                                        </span>

                                        <strong>
                                            {display(
                                                selected.ear_tag,
                                            )}
                                        </strong>
                                    </div>
                                </div>

                                {selected.non_milking_reason && (
                                    <div className="animal-message">
                                        <strong>
                                            Governed
                                            non-milking
                                            reason
                                        </strong>
                                        <br />
                                        {
                                            selected.non_milking_reason
                                        }
                                    </div>
                                )}

                                <div className="animal-passport-alerts">
                                    {getOperatorAlerts(
                                        passport,
                                    ).map(
                                        (alert) => (
                                            <div
                                                key={alert}
                                                className="animal-alert critical"
                                            >
                                                ⚠{" "}
                                                {alert}
                                            </div>
                                        ),
                                    )}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>Milk</h4>

                                    {(passport.history
                                        ?.milk ??
                                        []
                                    ).map(
                                        (
                                            record,
                                        ) => (
                                            <div
                                                key={String(
                                                    record.id,
                                                )}
                                                className="animal-passport-row"
                                            >
                                                <span>
                                                    {formatDate(
                                                        record.production_date,
                                                    )}
                                                </span>

                                                <strong>
                                                    {record.total_yield ??
                                                        0}{" "}
                                                    L
                                                </strong>
                                            </div>
                                        ),
                                    )}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>Feed</h4>

                                    {(passport.history
                                        ?.feed ??
                                        []
                                    ).map(
                                        (
                                            record,
                                        ) => (
                                            <div
                                                key={String(
                                                    record.id,
                                                )}
                                                className="animal-passport-row"
                                            >
                                                <span>
                                                    {
                                                        record.feed_type
                                                    }
                                                </span>

                                                <strong>
                                                    {record.quantity_kg ??
                                                        0}{" "}
                                                    kg
                                                </strong>
                                            </div>
                                        ),
                                    )}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>Health</h4>

                                    {(passport.history
                                        ?.health ??
                                        []
                                    ).map(
                                        (
                                            record,
                                        ) => (
                                            <div
                                                key={String(
                                                    record.id,
                                                )}
                                                className="animal-passport-row"
                                            >
                                                <span>
                                                    {
                                                        record.observation
                                                    }
                                                </span>

                                                <strong>
                                                    {
                                                        record.severity
                                                    }
                                                </strong>
                                            </div>
                                        ),
                                    )}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>Breeding</h4>

                                    {(passport.history
                                        ?.breeding ??
                                        []).length ===
                                    0 ? (
                                        <div className="animal-passport-row">
                                            <span>
                                                Status
                                            </span>

                                            <strong>
                                                No breeding
                                                records
                                            </strong>
                                        </div>
                                    ) : (
                                        (
                                            passport
                                                .history
                                                ?.breeding ??
                                            []
                                        ).map(
                                            (
                                                record,
                                            ) => (
                                                <div
                                                    key={String(
                                                        record.id,
                                                    )}
                                                    className="animal-passport-row"
                                                >
                                                    <span>
                                                        Breeding
                                                        Event
                                                    </span>

                                                    <strong>
                                                        {display(
                                                            record,
                                                        )}
                                                    </strong>
                                                </div>
                                            ),
                                        )
                                    )}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>
                                        Timeline
                                    </h4>

                                    {(
                                        passport.timeline ??
                                        []
                                    ).map(
                                        (
                                            event,
                                            index,
                                        ) => (
                                            <div
                                                key={`${event.domain}-${index}`}
                                                className="animal-passport-row"
                                            >
                                                <span>
                                                    {formatDate(
                                                        event.timestamp,
                                                    )}
                                                </span>

                                                <strong>
                                                    {domainLabel(
                                                        event.domain,
                                                    )}
                                                </strong>
                                            </div>
                                        ),
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="animal-empty">
                                Animal Passport
                                unavailable.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </section>
    );
}

export default AnimalRegistry;
