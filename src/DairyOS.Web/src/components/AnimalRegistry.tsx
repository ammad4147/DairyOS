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

type PassportRecord = Record<string, any>;
type Passport = {
    animal?: PassportRecord;
    schedule?: { effective?: { milking_frequency?: string | null; expected_sessions?: string[] | null } | null } | null;
    history?: { milk?: PassportRecord[]; feed?: PassportRecord[]; health?: PassportRecord[]; breeding?: PassportRecord[]; treatments?: PassportRecord[]; finance?: PassportRecord[]; operational_events?: PassportRecord[] };
    timeline?: Array<{ domain: string; timestamp: string; record: PassportRecord }>;
    record_counts?: Record<string, number>;
};
type Props = { onNavigate: (view: "milk" | "feed" | "health" | "breeding") => void };
type OperationalMode = "MILKING" | "NON_MILKING";
type NonMilkingCategory = "HEALTH" | "DRY_REPRODUCTIVE" | "MILK_SEPARATELY" | "PERMANENT" | "OTHER";
type CategoryKey = "ALL" | "MILKING" | "DRY" | "HEIFERS" | "CALVES" | "BULLS" | "OTHER";

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

function display(value: unknown, fallback = "—"): string {
    if (value === null || value === undefined || value === "") return fallback;
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "object") return "Recorded";
    return String(value);
}

function humanize(value: unknown): string {
    return String(value ?? "").replaceAll("_", " ").trim().toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) || "—";
}

function formatDate(value: unknown): string {
    if (!value) return "—";
    const parsed = new Date(String(value));
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
}

function frequencyLabel(value: string | null | undefined): string {
    switch (String(value ?? "").toUpperCase()) {
        case "TWICE_DAILY": return "2 sessions";
        case "THRICE_DAILY": return "3 sessions";
        default: return "Not set";
    }
}

function nonMilkingCategoryLabel(category: string | null | undefined): string {
    switch (String(category ?? "").toUpperCase()) {
        case "HEALTH": return "Health restriction";
        case "DRY_REPRODUCTIVE": return "Dry / reproductive break";
        case "MILK_SEPARATELY": return "Milk separately";
        case "PERMANENT": return "Permanent non-milking";
        case "OTHER": return "Other operational";
        default: return "Non-milking";
    }
}

function directiveForCategory(category: NonMilkingCategory): string {
    return category === "MILK_SEPARATELY" ? "MILK_SEPARATELY" : category === "PERMANENT" ? "PERMANENT_NON_MILKING" : "TEMPORARY_NON_MILKING";
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
    const rawStatus = String(animal.status ?? "").toUpperCase();
    if (rawStatus.includes("PREGNANT")) return "Pregnant";
    if (animal.is_currently_milking === true) return `Milking · ${frequencyLabel(animal.milking_frequency)}`;
    if (animalCategory(animal) === "DRY") return "Dry";
    if (animal.non_milking_reason) return `Non-milking · ${nonMilkingCategoryLabel(animal.non_milking_category ?? animal.non_milking_directive)}`;
    return humanize(animal.lifecycle_status ?? animal.status ?? "Active");
}

function operationalMetric(animal: Animal): string {
    const dim = animal.days_in_milk ?? animal.dim ?? animal.current_lactation_days;
    return dim === null || dim === undefined || dim === "" ? "—" : `${String(dim)} d`;
}

function nameOrAlias(animal: Animal): string {
    return display(animal.name ?? animal.alias ?? animal.animal_name);
}

function searchableText(animal: Animal): string {
    return [
        animal.animal_id, animal.ear_tag, animal.rfid, animal.name, animal.alias, animal.animal_name,
        animal.dam_id, animal.sire_id, animal.status, animal.lifecycle_status, animal.non_milking_reason,
        animal.non_milking_directive, animal.non_milking_category, animal.breed, animal.sex,
        animal.production_group, animal.location, animal.animal_type, currentStatus(animal), humanize(animalCategory(animal)),
    ].filter(Boolean).join(" ").toLowerCase();
}

function domainLabel(domain: string): string {
    return ({ milk: "Milk Production", feed: "Feeding", health: "Health Observation", breeding: "Breeding", treatments: "Treatment", finance: "Finance", operational_events: "Farm Event" } as Record<string, string>)[domain] ?? humanize(domain);
}

function recordTitle(record: PassportRecord, domain: string): string {
    if (domain === "milk") return display(record.production_date, "Milk record");
    if (domain === "health") return display(record.observation, "Health observation");
    if (domain === "breeding") return humanize(record.event_type ?? "Breeding event");
    if (domain === "feed") return display(record.feed_type, "Feed record");
    return domainLabel(domain);
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
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState<CategoryKey>("ALL");
    const [form, setForm] = useState(initialForm);

    const loadAnimals = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const response = await fetch(`${API}/farm/animals`);
            if (!response.ok) throw new Error(`Animal registry request failed (${response.status})`);
            const payload = await response.json();
            if (!Array.isArray(payload)) throw new Error("Animal registry returned an invalid response");
            setAnimals(payload as Animal[]);
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Unable to load animal registry");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { void loadAnimals(); }, [loadAnimals]);

    useEffect(() => {
        if (!selected) return;
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") { setSelected(null); setPassport(null); }
        };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [selected]);

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

    const updateForm = (name: keyof typeof initialForm, value: string) => setForm((current) => ({ ...current, [name]: value }));

    const submitAnimal = async (event: React.FormEvent) => {
        event.preventDefault();
        setSaving(true); setError(""); setSuccess("");
        const isMilking = form.operational_mode === "MILKING";
        if (!isMilking && !form.non_milking_reason.trim()) {
            setSaving(false); setError("A documented reason is required for a non-milking animal."); return;
        }
        const payload: Record<string, unknown> = { animal_type: form.animal_type, lifecycle_status: isMilking ? "LACTATING" : "DRY", active: true, is_currently_milking: isMilking };
        if (isMilking) payload.milking_frequency = form.milking_frequency;
        const optionalTextFields = ["ear_tag", "rfid", "breed", "sex", "date_of_birth", "dam_id", "sire_id", "production_group", "location"] as const;
        for (const field of optionalTextFields) if (form[field]) payload[field] = form[field];
        try {
            const response = await fetch(`${API}/farm/animals`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            const body = await response.json().catch(() => null);
            if (!response.ok) throw new Error(body && typeof body === "object" && "detail" in body ? String(body.detail) : `Animal creation failed (${response.status})`);
            const created = body as Animal;
            if (!isMilking) {
                const directiveResponse = await fetch(`${API}/farm/animals/${encodeURIComponent(created.animal_id)}/non-milking-directive`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ directive: directiveForCategory(form.non_milking_category), reason: `${nonMilkingCategoryLabel(form.non_milking_category)}: ${form.non_milking_reason.trim()}`, changed_by: "Operator UI" }),
                });
                if (!directiveResponse.ok) {
                    const directiveBody = await directiveResponse.json().catch(() => null);
                    throw new Error(`Animal ${created.animal_id} was registered, but the non-milking governance step failed: ${directiveBody && typeof directiveBody === "object" && "detail" in directiveBody ? String(directiveBody.detail) : `status ${directiveResponse.status}`}`);
                }
            }
            setSuccess(isMilking ? `Animal ${created.animal_id} registered as MILKING · ${frequencyLabel(form.milking_frequency)}.` : `Animal ${created.animal_id} registered as NON-MILKING · ${nonMilkingCategoryLabel(form.non_milking_category)}.`);
            setForm(initialForm); setShowEntry(false); setCategory("ALL");
            await loadAnimals();
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Animal registration failed");
        } finally { setSaving(false); }
    };

    const counts = useMemo(() => {
        const result: Record<CategoryKey, number> = { ALL: animals.length, MILKING: 0, DRY: 0, HEIFERS: 0, CALVES: 0, BULLS: 0, OTHER: 0 };
        animals.forEach((animal) => { result[animalCategory(animal)] += 1; });
        return result;
    }, [animals]);

    const filteredAnimals = useMemo(() => {
        const normalized = search.trim().toLowerCase();
        return animals.filter((animal) => category === "ALL" || animalCategory(animal) === category).filter((animal) => !normalized || searchableText(animal).includes(normalized));
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

    return (
        <section className="animal-registry">
            <div className="animal-registry-toolbar">
                <div><div className="animal-registry-kicker">LIVE OPERATIONS</div><h2>Animals</h2><p>Search the herd, filter by operational category, and open any row for the complete Animal Passport.</p></div>
                <div className="animal-registry-actions">
                    <button type="button" className="animal-button secondary" onClick={() => void loadAnimals()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
                    <button type="button" className="animal-button primary" onClick={() => { setError(""); setSuccess(""); setForm(initialForm); setShowEntry(true); }}>+ Register Animal</button>
                </div>
            </div>

            <div className="animal-herd-banner" aria-label="Herd breakdown">
                {categoryItems.map((item) => <button key={item.key} type="button" className={`animal-summary-card ${category === item.key ? "selected" : ""}`} onClick={() => setCategory(item.key)} aria-pressed={category === item.key}><span>{item.label}</span><strong>{counts[item.key]}</strong><small>{item.description}</small></button>)}
            </div>

            {error && <div className="animal-message error">{error}</div>}
            {success && <div className="animal-message success">{success}</div>}

            <div className="animal-list-toolbar">
                <label className="animal-search" htmlFor="animal-search"><span aria-hidden="true">⌕</span><input id="animal-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tag, name, RFID, dam, sire, status, breed, group…" autoComplete="off" />{search && <button type="button" onClick={() => setSearch("")} aria-label="Clear search">×</button>}</label>
                <div className="animal-list-meta"><strong>{filteredAnimals.length}</strong><span>of {animals.length} animals</span>{(search || category !== "ALL") && <button type="button" className="animal-reset" onClick={() => { setSearch(""); setCategory("ALL"); }}>Clear filters</button>}</div>
            </div>

            <div className="animal-registry-content">
                {loading ? <div className="animal-empty"><strong>Loading live animal register…</strong><span>Reading persisted herd records.</span></div> : filteredAnimals.length === 0 ? <div className="animal-empty"><strong>{animals.length === 0 ? "No animal records in this view" : "No animals match the current filter"}</strong><span>{animals.length === 0 ? "The API is available, but no animal has yet been registered." : "Try a broader search or clear the category filter."}</span>{animals.length === 0 && <button type="button" className="animal-button primary" onClick={() => setShowEntry(true)}>Register the first animal</button>}{(search || category !== "ALL") && <button type="button" className="animal-button secondary" onClick={() => { setSearch(""); setCategory("ALL"); }}>Clear filters</button>}</div> : <div className="animal-table-wrap">
                    <table className="animal-table"><thead><tr><th>Tag / Ear ID</th><th>Name / Alias</th><th>Category / Group</th><th>Current Status</th><th>Age / DOB</th><th>Key Metric</th></tr></thead>
                        <tbody>{filteredAnimals.map((animal) => <tr key={String(animal.animal_id)} tabIndex={0} onClick={() => void openPassport(animal)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); void openPassport(animal); } }}>
                            <td><div className="animal-primary-cell"><strong>{display(animal.ear_tag ?? animal.animal_id)}</strong><span>{animal.ear_tag ? animal.animal_id : display(animal.rfid)}</span></div></td>
                            <td>{nameOrAlias(animal)}</td>
                            <td><div className="animal-category-cell"><span className={`animal-category-chip ${animalCategory(animal).toLowerCase()}`}>{humanize(animalCategory(animal))}</span><small>{display(animal.production_group, "Unassigned")}</small></div></td>
                            <td><span className="animal-status-chip">{currentStatus(animal)}</span></td>
                            <td><div className="animal-age-cell"><strong>{animal.date_of_birth ? formatDate(animal.date_of_birth) : "—"}</strong><small>{display(animal.sex)}</small></div></td>
                            <td><div className="animal-metric-cell"><strong>{operationalMetric(animal)}</strong><small>{animal.is_currently_milking ? "DIM" : "Operational"}</small></div></td>
                        </tr>)}</tbody>
                    </table>
                </div>}
            </div>

            {showEntry && <div className="animal-modal-backdrop" onMouseDown={() => !saving && setShowEntry(false)}><div className="animal-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
                <div className="animal-modal-header"><div><div className="animal-registry-kicker">ANIMAL ENTRY</div><h3>Register Animal</h3><p>First decide whether the animal is currently MILKING or NON-MILKING.</p></div><button type="button" className="animal-close" onClick={() => !saving && setShowEntry(false)} aria-label="Close">×</button></div>
                <form onSubmit={submitAnimal}><div className="animal-form-grid">
                    <label>Animal Type<select value={form.animal_type} onChange={(event) => updateForm("animal_type", event.target.value)}><option value="COW">COW</option><option value="HEIFER">HEIFER</option><option value="CALF">CALF</option><option value="BULL">BULL</option></select></label>
                    <label>Ear Tag<input value={form.ear_tag} onChange={(event) => updateForm("ear_tag", event.target.value)} /></label>
                    <label>RFID<input value={form.rfid} onChange={(event) => updateForm("rfid", event.target.value)} /></label>
                    <label>Breed<input value={form.breed} onChange={(event) => updateForm("breed", event.target.value)} /></label>
                    <label>Sex<select value={form.sex} onChange={(event) => updateForm("sex", event.target.value)}><option value="FEMALE">FEMALE</option><option value="MALE">MALE</option></select></label>
                    <label>Date of Birth<input type="date" value={form.date_of_birth} onChange={(event) => updateForm("date_of_birth", event.target.value)} /></label>
                    <label>Production Group<input value={form.production_group} onChange={(event) => updateForm("production_group", event.target.value)} /></label>
                    <label>Location<input value={form.location} onChange={(event) => updateForm("location", event.target.value)} /></label>
                    <div className="animal-entry-wide"><span className="animal-field-label">Operational Status *</span><div className="animal-mode-buttons"><button type="button" className={form.operational_mode === "MILKING" ? "mode-selected" : ""} onClick={() => updateForm("operational_mode", "MILKING")}>MILKING</button><button type="button" className={form.operational_mode === "NON_MILKING" ? "mode-selected" : ""} onClick={() => updateForm("operational_mode", "NON_MILKING")}>NON-MILKING</button></div></div>
                    {form.operational_mode === "MILKING" ? <label className="animal-entry-wide">Milking Plan *<select value={form.milking_frequency} onChange={(event) => updateForm("milking_frequency", event.target.value)}><option value="TWICE_DAILY">2 sessions / day</option><option value="THRICE_DAILY">3 sessions / day</option></select></label> : <><label>Non-milking Category *<select value={form.non_milking_category} onChange={(event) => updateForm("non_milking_category", event.target.value as NonMilkingCategory)}><option value="HEALTH">Health restriction</option><option value="DRY_REPRODUCTIVE">Dry / reproductive break</option><option value="MILK_SEPARATELY">Milk separately</option><option value="PERMANENT">Permanent non-milking</option><option value="OTHER">Other operational</option></select></label><label>Documented Reason *<textarea value={form.non_milking_reason} onChange={(event) => updateForm("non_milking_reason", event.target.value)} required rows={3} /></label></>}
                    <label>Dam Animal ID<input value={form.dam_id} onChange={(event) => updateForm("dam_id", event.target.value)} /></label><label>Sire Animal ID<input value={form.sire_id} onChange={(event) => updateForm("sire_id", event.target.value)} /></label>
                </div><div className="animal-form-footer"><button type="button" className="animal-button secondary" onClick={() => setShowEntry(false)} disabled={saving}>Cancel</button><button type="submit" className="animal-button primary" disabled={saving}>{saving ? "Persisting…" : "Create Animal"}</button></div></form>
            </div></div>}

            {selected && <div className="animal-drawer-backdrop" onMouseDown={() => { setSelected(null); setPassport(null); }}><aside className="animal-passport-drawer" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
                <div className="animal-drawer-header"><div><div className="animal-registry-kicker">ANIMAL PASSPORT</div><h3>{selected.animal_id}</h3><p>{display(selected.ear_tag, "No ear tag")} · {currentStatus(selected)}</p></div><button type="button" className="animal-close" onClick={() => { setSelected(null); setPassport(null); }} aria-label="Close Animal Passport">×</button></div>
                <div className="animal-passport-actions">{selected.is_currently_milking && <button type="button" className="animal-button primary" onClick={() => { setSelected(null); setPassport(null); onNavigate("milk"); }}>Record Milk</button>}<button type="button" className="animal-button secondary" onClick={() => { setSelected(null); setPassport(null); onNavigate("feed"); }}>Feed</button><button type="button" className="animal-button secondary" onClick={() => { setSelected(null); setPassport(null); onNavigate("health"); }}>Health</button><button type="button" className="animal-button secondary" onClick={() => { setSelected(null); setPassport(null); onNavigate("breeding"); }}>Breeding</button></div>
                {passportLoading ? <div className="animal-empty"><strong>Loading authoritative Animal Passport…</strong><span>Reading integrated animal history.</span></div> : passport ? <div className="animal-passport-body">
                    <div className="animal-passport-identity"><div><span>Permanent Animal ID</span><strong>{selected.animal_id}</strong></div><div><span>Operational Status</span><strong>{currentStatus(selected)}</strong></div><div><span>Lifecycle</span><strong>{humanize(selected.lifecycle_status ?? "")}</strong></div><div><span>Breed / Sex</span><strong>{display(selected.breed)} · {display(selected.sex)}</strong></div><div><span>Birth</span><strong>{formatDate(selected.date_of_birth)}</strong></div><div><span>Parentage</span><strong>{display(selected.dam_id, "Dam —")} · {display(selected.sire_id, "Sire —")}</strong></div><div><span>Milking Plan</span><strong>{passport.schedule?.effective ? frequencyLabel(passport.schedule.effective.milking_frequency) : "—"}</strong></div><div><span>Record Counts</span><strong>{Object.values(passport.record_counts ?? {}).reduce((sum, value) => sum + Number(value || 0), 0)}</strong></div></div>
                    {Object.entries(passport.history ?? {}).map(([domain, records]) => <section key={domain} className="animal-passport-section"><h4>{domainLabel(domain)} <span>{Array.isArray(records) ? records.length : 0}</span></h4>{Array.isArray(records) && records.length > 0 ? records.slice(0, 25).map((record, index) => <div key={`${domain}-${index}`} className="animal-passport-row"><div><strong>{recordTitle(record, domain)}</strong><span>{formatDate(record.production_date ?? record.observed_at ?? record.event_date ?? record.timestamp ?? record.created_at)}</span></div><strong>{display(record.total_yield ?? record.quantity_kg ?? record.amount ?? record.severity ?? record.result, "Recorded")}</strong></div>) : <div className="animal-passport-empty">No persisted records in this domain.</div>}</section>)}
                    <section className="animal-passport-section"><h4>Integrated Timeline <span>{passport.timeline?.length ?? 0}</span></h4>{(passport.timeline ?? []).slice(0, 40).map((item, index) => <div key={`${item.domain}-${item.timestamp}-${index}`} className="animal-passport-row"><div><strong>{domainLabel(item.domain)}</strong><span>{formatDate(item.timestamp)}</span></div><strong>{recordTitle(item.record, item.domain)}</strong></div>)}{(passport.timeline ?? []).length === 0 && <div className="animal-passport-empty">No timeline events recorded.</div>}</section>
                </div> : <div className="animal-empty"><strong>Animal Passport unavailable</strong><span>The registry row is available, but the authoritative passport could not be loaded.</span></div>}
            </aside></div>}
        </section>
    );
}

export default AnimalRegistry;
