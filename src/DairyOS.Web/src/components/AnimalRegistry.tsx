import React, { useCallback, useEffect, useMemo, useState } from "react";
import "./AnimalRegistry.css";
import { API_BASE_URL as API } from "../config/api";

type Animal = {
    id: number | string;
    animal_id: string;
    animal_type?: string | null;
    ear_tag?: string | null;
    rfid?: string | null;
    name?: string | null;
    alias?: string | null;
    animal_name?: string | null;
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
    non_milking_category?: string | null;
    non_milking_reason?: string | null;
    days_in_milk?: number | null;
    dim?: number | null;
    current_lactation_days?: number | null;
    [key: string]: unknown;
};

type RecordRow = Record<string, unknown>;
type Passport = {
    animal?: RecordRow;
    schedule?: { effective?: { milking_frequency?: string | null; expected_sessions?: string[] | null } | null } | null;
    history?: Record<string, unknown>;
    timeline?: Array<{ domain: string; timestamp: string; record: RecordRow }>;
};
type Props = { onNavigate: (view: "milk" | "feed" | "health" | "breeding") => void };
type CategoryKey = "ALL" | "MILKING" | "DRY" | "HEIFERS" | "CALVES" | "BULLS" | "OTHER";
type OperationalMode = "MILKING" | "NON_MILKING";
type NonMilkingCategory = "HEALTH" | "DRY_REPRODUCTIVE" | "MILK_SEPARATELY" | "PERMANENT" | "OTHER";

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
    operational_mode: "MILKING" as OperationalMode,
    milking_frequency: "TWICE_DAILY",
    non_milking_category: "HEALTH" as NonMilkingCategory,
    non_milking_reason: "",
};

function display(value: unknown, fallback: string | number = "—"): string {
    const safeFallback = typeof fallback === "number" ? "—" : fallback;
    if (value === null || value === undefined || value === "") return safeFallback;
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "object") return "Recorded";
    return String(value);
}

function humanize(value: unknown): string {
    return String(value ?? "")
        .replaceAll("_", " ")
        .trim()
        .toLowerCase()
        .replace(/\b\w/g, (letter) => letter.toUpperCase()) || "—";
}

function formatDate(value: unknown): string {
    if (!value) return "—";
    const parsed = new Date(String(value));
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
}

function frequencyLabel(value: string | null | undefined): string {
    switch (String(value ?? "").toUpperCase()) {
        case "TWICE_DAILY":
            return "2 sessions";
        case "THRICE_DAILY":
            return "3 sessions";
        default:
            return "Not set";
    }
}

function nonMilkingCategoryLabel(value: string | null | undefined): string {
    switch (String(value ?? "").toUpperCase()) {
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

function animalCategory(animal: Animal): CategoryKey {
    const type = String(animal.animal_type ?? "").toUpperCase();
    if (animal.is_currently_milking === true) return "MILKING";
    if (type === "CALF") return "CALVES";
    if (type === "HEIFER") return "HEIFERS";
    if (type === "BULL" || String(animal.sex ?? "").toUpperCase() === "MALE") return "BULLS";
    const lifecycle = String(animal.lifecycle_status ?? animal.status ?? "").toUpperCase();
    const directive = String(animal.non_milking_directive ?? "").toUpperCase();
    if (type === "COW" && (lifecycle === "DRY" || directive.includes("NON_MILKING"))) return "DRY";
    return "OTHER";
}

function currentStatus(animal: Animal): string {
    const raw = String(animal.status ?? "").toUpperCase();
    if (raw.includes("PREGNANT")) return "Pregnant";
    if (animal.is_currently_milking === true) return `Milking · ${frequencyLabel(animal.milking_frequency)}`;
    if (animalCategory(animal) === "DRY") return "Dry";
    if (animal.non_milking_reason) {
        return `Non-milking · ${nonMilkingCategoryLabel(animal.non_milking_category ?? animal.non_milking_directive)}`;
    }
    return humanize(animal.lifecycle_status ?? animal.status ?? "Active");
}

function operationalMetric(animal: Animal): string {
    const dim = animal.days_in_milk ?? animal.dim ?? animal.current_lactation_days;
    return dim === null || dim === undefined ? "—" : `${dim} d`;
}

function nameOrAlias(animal: Animal): string {
    return display(animal.name ?? animal.alias ?? animal.animal_name);
}

function searchableText(animal: Animal): string {
    return [
        animal.animal_id,
        animal.ear_tag,
        animal.rfid,
        animal.name,
        animal.alias,
        animal.animal_name,
        animal.dam_id,
        animal.sire_id,
        animal.status,
        animal.lifecycle_status,
        animal.non_milking_reason,
        animal.non_milking_directive,
        animal.non_milking_category,
        animal.breed,
        animal.sex,
        animal.production_group,
        animal.location,
        animal.animal_type,
        currentStatus(animal),
        humanize(animalCategory(animal)),
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
}

function recordTitle(record: RecordRow, domain: string): string {
    if (domain === "milk") return display(record.production_date, "Milk record");
    if (domain === "health") return display(record.observation, "Health observation");
    if (domain === "breeding") return humanize(record.event_type ?? "Breeding event");
    if (domain === "feed") return display(record.feed_type, "Feed record");
    return humanize(domain);
}

function domainLabel(domain: string): string {
    const labels: Record<string, string> = {
        milk: "Milk Production",
        feed: "Feeding",
        health: "Health Observation",
        breeding: "Breeding",
        treatments: "Treatment",
        finance: "Finance",
        operational_events: "Farm Event",
    };
    return labels[domain] ?? humanize(domain);
}

function directiveForCategory(category: NonMilkingCategory): string {
    if (category === "MILK_SEPARATELY") return "MILK_SEPARATELY";
    if (category === "PERMANENT") return "PERMANENT_NON_MILKING";
    return "TEMPORARY_NON_MILKING";
}

function AnimalRegistry({ onNavigate }: Props) {
    void onNavigate;

    const [animals, setAnimals] = useState<Animal[]>([]);
    const [selected, setSelected] = useState<Animal | null>(null);
    const [passport, setPassport] = useState<Passport | null>(null);
    const [loading, setLoading] = useState(true);
    const [passportLoading, setPassportLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [showEntry, setShowEntry] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState<CategoryKey>("ALL");
    const [form, setForm] = useState(initialForm);

    const loadAnimals = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const response = await fetch(`${API}/farm/animals`);
            if (!response.ok) throw new Error(`Animal registry request failed (${response.status})`);
            const payload: unknown = await response.json();
            if (!Array.isArray(payload)) throw new Error("Animal registry returned an invalid response");
            setAnimals(payload as Animal[]);
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Unable to load animal registry");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadAnimals();
    }, [loadAnimals]);

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setSelected(null);
                setPassport(null);
                setShowEntry(false);
            }
        };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, []);

    const openPassport = async (animal: Animal) => {
        setSelected(animal);
        setPassport(null);
        setPassportLoading(true);
        setError("");
        try {
            const response = await fetch(`${API}/farm/animals/${encodeURIComponent(animal.animal_id)}/passport`);
            if (!response.ok) throw new Error(`Animal Passport request failed (${response.status})`);
            setPassport((await response.json()) as Passport);
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Unable to load Animal Passport");
        } finally {
            setPassportLoading(false);
        }
    };

    const closePassport = () => {
        setSelected(null);
        setPassport(null);
    };

    const updateForm = (name: keyof typeof initialForm, value: string) => {
        setForm((current) => ({ ...current, [name]: value }));
    };

    const submitAnimal = async (event: React.FormEvent) => {
        event.preventDefault();
        setSaving(true);
        setError("");
        setSuccess("");

        const isMilking = form.operational_mode === "MILKING";
        if (!isMilking && !form.non_milking_reason.trim()) {
            setSaving(false);
            setError("A documented reason is required for a non-milking animal.");
            return;
        }

        const payload: Record<string, unknown> = {
            animal_type: form.animal_type,
            lifecycle_status: isMilking ? "LACTATING" : "DRY",
            active: true,
            is_currently_milking: isMilking,
        };
        if (isMilking) payload.milking_frequency = form.milking_frequency;

        for (const field of [
            "ear_tag",
            "rfid",
            "breed",
            "sex",
            "date_of_birth",
            "dam_id",
            "sire_id",
            "production_group",
            "location",
        ] as const) {
            if (form[field]) payload[field] = form[field];
        }

        try {
            const response = await fetch(`${API}/farm/animals`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const body: unknown = await response.json().catch(() => null);
            if (!response.ok) {
                const detail = body && typeof body === "object" && "detail" in body ? String(body.detail) : `Animal creation failed (${response.status})`;
                throw new Error(detail);
            }

            const created = body as Animal;
            if (!isMilking) {
                const directiveResponse = await fetch(`${API}/farm/animals/${encodeURIComponent(created.animal_id)}/non-milking-directive`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        directive: directiveForCategory(form.non_milking_category),
                        reason: `${nonMilkingCategoryLabel(form.non_milking_category)}: ${form.non_milking_reason.trim()}`,
                        changed_by: "Operator UI",
                    }),
                });
                if (!directiveResponse.ok) {
                    const directiveBody: unknown = await directiveResponse.json().catch(() => null);
                    const detail = directiveBody && typeof directiveBody === "object" && "detail" in directiveBody ? String(directiveBody.detail) : `status ${directiveResponse.status}`;
                    throw new Error(`Animal ${created.animal_id} was registered, but the non-milking governance step failed: ${detail}`);
                }
            }

            setSuccess(
                isMilking
                    ? `Animal ${created.animal_id} registered as MILKING · ${frequencyLabel(form.milking_frequency)}.`
                    : `Animal ${created.animal_id} registered as NON-MILKING · ${nonMilkingCategoryLabel(form.non_milking_category)}.`,
            );
            setForm(initialForm);
            setShowEntry(false);
            setCategory("ALL");
            await loadAnimals();
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Animal registration failed");
        } finally {
            setSaving(false);
        }
    };

    const counts = useMemo(() => {
        const result: Record<CategoryKey, number> = {
            ALL: animals.length,
            MILKING: 0,
            DRY: 0,
            HEIFERS: 0,
            CALVES: 0,
            BULLS: 0,
            OTHER: 0,
        };
        for (const animal of animals) result[animalCategory(animal)] += 1;
        return result;
    }, [animals]);

    const filteredAnimals = useMemo(() => {
        const query = search.trim().toLowerCase();
        return animals
            .filter((animal) => category === "ALL" || animalCategory(animal) === category)
            .filter((animal) => !query || searchableText(animal).includes(query));
    }, [animals, category, search]);

    const categoryItems: Array<{ key: CategoryKey; label: string; description: string }> = [
        { key: "ALL", label: "Total", description: "All animals" },
        { key: "MILKING", label: "Milking", description: "Currently milking" },
        { key: "DRY", label: "Dry", description: "Dry / non-milking cows" },
        { key: "HEIFERS", label: "Heifers", description: "Young females before calving" },
        { key: "CALVES", label: "Calves", description: "Calves" },
        { key: "BULLS", label: "Bulls", description: "Male animals" },
        { key: "OTHER", label: "Other", description: "Other herd categories" },
    ];

    const historySections = passport?.history ? Object.entries(passport.history) : [];

    return (
        <section className="animal-registry">
            <div className="animal-registry-toolbar">
                <div>
                    <div className="animal-registry-kicker">LIVE OPERATIONS</div>
                    <h2>Animals</h2>
                    <p>Search the herd, filter by operational category, and open any row for the complete Animal Passport.</p>
                </div>
                <div className="animal-registry-actions">
                    <button type="button" className="animal-button secondary" onClick={() => void loadAnimals()} disabled={loading}>
                        {loading ? "Refreshing…" : "Refresh"}
                    </button>
                    <button type="button" className="animal-button primary" onClick={() => { setError(""); setSuccess(""); setForm(initialForm); setShowEntry(true); }}>
                        + Register Animal
                    </button>
                </div>
            </div>

            <div className="animal-herd-banner" aria-label="Herd breakdown">
                {categoryItems.map((item) => (
                    <button key={item.key} type="button" className={`animal-summary-card ${category === item.key ? "selected" : ""}`} onClick={() => setCategory(item.key)} aria-pressed={category === item.key}>
                        <span>{item.label}</span>
                        <strong>{counts[item.key]}</strong>
                        <small>{item.description}</small>
                    </button>
                ))}
            </div>

            {error && <div className="animal-message error">{error}</div>}
            {success && <div className="animal-message success">{success}</div>}

            <div className="animal-registry-filters">
                <label className="animal-search">
                    <span>Search herd</span>
                    <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tag, name, dam, sire, status, breed, group…" aria-label="Search animals" />
                </label>
                <div className="animal-filter-summary">Showing <strong>{filteredAnimals.length}</strong> of {animals.length}</div>
            </div>

            <div className="animal-table-wrap">
                <table className="animal-table">
                    <thead>
                        <tr>
                            <th>Tag / Ear ID</th>
                            <th>Name / Alias</th>
                            <th>Category / Group</th>
                            <th>Current Status</th>
                            <th>Age / DOB</th>
                            <th>DIM</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredAnimals.map((animal) => (
                            <tr
                                key={String(animal.id)}
                                tabIndex={0}
                                onClick={() => void openPassport(animal)}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter" || event.key === " ") {
                                        event.preventDefault();
                                        void openPassport(animal);
                                    }
                                }}
                            >
                                <td><strong>{display(animal.ear_tag ?? animal.animal_id)}</strong><span>{animal.rfid ? `RFID ${animal.rfid}` : animal.animal_id}</span></td>
                                <td>{nameOrAlias(animal)}</td>
                                <td><strong>{humanize(animalCategory(animal))}</strong><span>{display(animal.production_group)}</span></td>
                                <td><span className="animal-status-chip">{currentStatus(animal)}</span></td>
                                <td><strong>{animal.date_of_birth ? formatDate(animal.date_of_birth) : "—"}</strong></td>
                                <td>{operationalMetric(animal)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {!loading && filteredAnimals.length === 0 && <div className="animal-empty"><strong>No animals match this view.</strong><span>Change the category filter or broaden the search terms.</span></div>}
            </div>

            {showEntry && (
                <div className="animal-modal-backdrop" role="presentation" onClick={() => setShowEntry(false)}>
                    <div className="animal-modal" role="dialog" aria-modal="true" aria-labelledby="animal-entry-title" onClick={(event) => event.stopPropagation()}>
                        <header className="animal-modal-header">
                            <div><h3 id="animal-entry-title">Register Animal</h3><p>Register through the existing governed animal workflow.</p></div>
                            <button type="button" className="animal-close" onClick={() => setShowEntry(false)} aria-label="Close">×</button>
                        </header>
                        <form onSubmit={submitAnimal}>
                            <div className="animal-form-grid">
                                {([
                                    ["animal_type", "Animal Type", "text"],
                                    ["ear_tag", "Ear Tag", "text"],
                                    ["rfid", "RFID", "text"],
                                    ["breed", "Breed", "text"],
                                    ["sex", "Sex", "text"],
                                    ["date_of_birth", "Date of Birth", "date"],
                                    ["dam_id", "Dam ID", "text"],
                                    ["sire_id", "Sire ID", "text"],
                                    ["production_group", "Production Group", "text"],
                                    ["location", "Location", "text"],
                                ] as const).map(([name, label, type]) => (
                                    <label key={name}>{label}<input type={type} value={form[name]} onChange={(event) => updateForm(name, event.target.value)} /></label>
                                ))}
                                <label>Operational Mode<select value={form.operational_mode} onChange={(event) => updateForm("operational_mode", event.target.value)}><option value="MILKING">Milking</option><option value="NON_MILKING">Non-milking</option></select></label>
                                {form.operational_mode === "MILKING" ? (
                                    <label>Milking Frequency<select value={form.milking_frequency} onChange={(event) => updateForm("milking_frequency", event.target.value)}><option value="TWICE_DAILY">Twice daily</option><option value="THRICE_DAILY">Three times daily</option></select></label>
                                ) : (
                                    <>
                                        <label>Non-milking Category<select value={form.non_milking_category} onChange={(event) => updateForm("non_milking_category", event.target.value)}><option value="HEALTH">Health restriction</option><option value="DRY_REPRODUCTIVE">Dry / reproductive break</option><option value="MILK_SEPARATELY">Milk separately</option><option value="PERMANENT">Permanent non-milking</option><option value="OTHER">Other operational</option></select></label>
                                        <label>Documented Reason<input required value={form.non_milking_reason} onChange={(event) => updateForm("non_milking_reason", event.target.value)} /></label>
                                    </>
                                )}
                            </div>
                            <div className="animal-form-footer">
                                <button type="button" className="animal-button secondary" onClick={() => setShowEntry(false)}>Cancel</button>
                                <button type="submit" className="animal-button primary" disabled={saving}>{saving ? "Saving…" : "Register Animal"}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {selected && (
                <div className="animal-drawer-backdrop" role="presentation" onClick={closePassport}>
                    <aside className="animal-passport-drawer" role="dialog" aria-modal="true" aria-labelledby="animal-passport-title" onClick={(event) => event.stopPropagation()}>
                        <header className="animal-modal-header">
                            <div>
                                <div className="animal-registry-kicker">ANIMAL PASSPORT</div>
                                <h3 id="animal-passport-title">{selected.ear_tag ?? selected.animal_id}</h3>
                                <p>{nameOrAlias(selected)} · {currentStatus(selected)}</p>
                            </div>
                            <button type="button" className="animal-close" onClick={closePassport} aria-label="Close passport">×</button>
                        </header>

                        {passportLoading ? (
                            <div className="animal-passport-loading">Loading complete passport…</div>
                        ) : passport ? (
                            <div className="animal-passport">
                                <div className="animal-passport-identity">
                                    {Object.entries(passport.animal ?? selected).slice(0, 12).map(([key, value]) => (
                                        <div key={key}><span>{humanize(key)}</span><strong>{display(value)}</strong></div>
                                    ))}
                                </div>

                                <div className="animal-passport-section">
                                    <h4>Schedule</h4>
                                    <div className="animal-passport-row"><span>Frequency</span><strong>{frequencyLabel(passport.schedule?.effective?.milking_frequency ?? selected.milking_frequency)}</strong></div>
                                    <div className="animal-passport-row"><span>Expected Sessions</span><strong>{display(passport.schedule?.effective?.expected_sessions?.join(", "))}</strong></div>
                                </div>

                                {historySections.map(([domain, records]) => {
                                    if (!Array.isArray(records) || records.length === 0) return null;
                                    return (
                                        <div className="animal-passport-section" key={domain}>
                                            <h4>{domainLabel(domain)} · {records.length}</h4>
                                            {records.slice(0, 10).map((record, index) => {
                                                if (!record || typeof record !== "object") return null;
                                                const typedRecord = record as RecordRow;
                                                const values = Object.values(typedRecord).slice(0, 3);
                                                return <div className="animal-passport-row" key={`${domain}-${index}`}><span>{recordTitle(typedRecord, domain)}</span><strong>{values.map((value) => display(value)).join(" · ")}</strong></div>;
                                            })}
                                        </div>
                                    );
                                })}

                                {passport.timeline && passport.timeline.length > 0 && (
                                    <div className="animal-passport-section">
                                        <h4>Timeline · {passport.timeline.length}</h4>
                                        {passport.timeline.slice(0, 20).map((item, index) => (
                                            <div className="animal-passport-row" key={`${item.domain}-${item.timestamp}-${index}`}>
                                                <span>{domainLabel(item.domain)} · {formatDate(item.timestamp)}</span>
                                                <strong>{recordTitle(item.record, item.domain)}</strong>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="animal-passport-loading">Unable to load passport details.</div>
                        )}
                    </aside>
                </div>
            )}
        </section>
    );
}

export default AnimalRegistry;
