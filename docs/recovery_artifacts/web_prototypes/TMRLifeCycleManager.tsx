import { useEffect, useMemo, useState } from "react";
import "./TMRLifeCycleManager.css";

type Ingredient = {
    name: string;
    unit: "kg" | "g";
    step: number;
    min: number;
    max: number;
    price: number;
};

type StageKey =
    | "early_milking"
    | "mid_milking"
    | "late_milking"
    | "far_off"
    | "close_up"
    | "heifer_growth"
    | "calf_starter";

type TMRBatchResponse = {
    status?: string;
    timestamp?: string;
    feed_type?: string;
    quantity_kg?: number;
};

const ingredients: Ingredient[] = [
    { name: "Silage", unit: "kg", step: 0.5, min: 0, max: 60, price: 20 },
    { name: "Vanda (Concentrate)", unit: "kg", step: 0.5, min: 0, max: 25, price: 100 },
    { name: "Wheat Straw", unit: "kg", step: 0.5, min: 0, max: 12, price: 20 },
    { name: "Soybean Meal", unit: "kg", step: 0.25, min: 0, max: 5, price: 180 },
    { name: "Molasses", unit: "kg", step: 0.25, min: 0, max: 3, price: 85 },
    { name: "Bypass Fat", unit: "g", step: 25, min: 0, max: 600, price: 480 },
    { name: "Mineral Mixture", unit: "g", step: 25, min: 0, max: 400, price: 460 },
    { name: "Meetha Soda", unit: "g", step: 25, min: 0, max: 400, price: 200 },
    { name: "Anionic Salts (DCAD)", unit: "g", step: 25, min: 0, max: 300, price: 350 },
    { name: "Toxin Binder", unit: "g", step: 10, min: 0, max: 150, price: 260 },
    { name: "Lysine / Methionine", unit: "g", step: 5, min: 0, max: 80, price: 4000 },
];

const presets: Record<StageKey, number[]> = {
    early_milking: [22, 9.5, 2.5, 2.5, 1, 400, 200, 200, 0, 50, 30],
    mid_milking: [20, 7, 3.5, 1.5, 0.5, 200, 150, 150, 0, 40, 15],
    late_milking: [16, 5, 4.5, 1, 0.5, 75, 100, 100, 0, 30, 0],
    far_off: [10, 2, 6.5, 0, 0, 0, 100, 0, 0, 30, 0],
    close_up: [12, 3.5, 3.5, 1, 1, 0, 150, 0, 175, 50, 20],
    heifer_growth: [12, 3, 2.5, 0.5, 0, 0, 100, 50, 0, 30, 0],
    calf_starter: [4, 2, 0.5, 0, 0, 0, 40, 0, 0, 20, 0],
};

const stageInfo: Record<StageKey, string> = {
    early_milking: "30–35 L/day target · High energy density · Peak stress period",
    mid_milking: "20–25 L/day target · Rumen stability focus · Monitor BCS",
    late_milking: "10–15 L/day target · Avoid over-conditioning",
    far_off: "Dry cow · High fibre, low energy · Prevent obesity pre-calving",
    close_up: "Transition diet · Negative DCAD · No Meetha Soda with anionic salts",
    heifer_growth: "700–900 g/day gain target · Moderate protein · Avoid over-feeding",
    calf_starter: "4–8 weeks · Rumen development · Fresh mix only",
};

const advice: Record<StageKey, string> = {
    early_milking:
        "Maximise energy density. Silage quality is paramount. Monitor intake, rumen fill and early-lactation condition closely.",
    mid_milking:
        "Prioritise rumen stability and consistent forage quality. Reduce bypass fat as production declines.",
    late_milking:
        "Reduce concentrate gradually as yield falls. Monitor BCS and avoid excessive condition before dry-off.",
    far_off:
        "Keep energy controlled and fibre adequate. Avoid over-conditioning before calving.",
    close_up:
        "Use the transition ration carefully. Anionic salts support negative DCAD management. Do not combine this preset with Meetha Soda.",
    heifer_growth:
        "Target steady structural growth. Avoid over-conditioning while maintaining mineral and protein adequacy.",
    calf_starter:
        "Freshness is critical. Provide small fresh batches and transition gradually as rumen development progresses.",
};

const stageLabels: Record<StageKey, string> = {
    early_milking: "Early Lactation (0–70 DIM)",
    mid_milking: "Mid Lactation (70–200 DIM)",
    late_milking: "Late Lactation (200–305 DIM)",
    far_off: "Far-Off Dry (>21d pre-calving)",
    close_up: "Close-Up (last 21d pre-calving)",
    heifer_growth: "Growing Heifer",
    calf_starter: "Calf Starter",
};

const storageKey = "dairyos_tmr_lifecycle_v1";

function formatNumber(value: number) {
    return Math.round(value).toLocaleString("en-PK");
}

function TMRLifeCycleManager() {
    const [stage, setStage] = useState<StageKey>("early_milking");
    const [herdSize, setHerdSize] = useState(10);
    const [quantities, setQuantities] = useState<number[]>(
        presets.early_milking,
    );
    const [prices, setPrices] = useState<number[]>(
        ingredients.map((item) => item.price),
    );
    const [message, setMessage] = useState("");
    const [saving, setSaving] = useState(false);
    const [savedBatch, setSavedBatch] = useState<TMRBatchResponse | null>(
        null,
    );
    const [showAdvice, setShowAdvice] = useState(false);

    useEffect(() => {
        try {
            const saved = localStorage.getItem(storageKey);
            if (!saved) {
                return;
            }

            const parsed = JSON.parse(saved) as {
                stage?: StageKey;
                herdSize?: number;
                quantities?: number[];
                prices?: number[];
            };

            if (parsed.stage && presets[parsed.stage]) {
                setStage(parsed.stage);
            }

            if (typeof parsed.herdSize === "number") {
                setHerdSize(parsed.herdSize);
            }

            if (
                Array.isArray(parsed.quantities) &&
                parsed.quantities.length === ingredients.length
            ) {
                setQuantities(parsed.quantities);
            }

            if (
                Array.isArray(parsed.prices) &&
                parsed.prices.length === ingredients.length
            ) {
                setPrices(parsed.prices);
            }
        } catch {
            // Ignore an invalid browser session and retain standard defaults.
        }
    }, []);

    const rows = useMemo(
        () =>
            ingredients.map((ingredient, index) => {
                const quantity = quantities[index] ?? 0;
                const price = prices[index] ?? ingredient.price;
                const cost =
                    ingredient.unit === "g"
                        ? (quantity / 1000) * price
                        : quantity * price;

                return {
                    ingredient,
                    quantity,
                    price,
                    cost,
                    batch: quantity * Math.max(herdSize, 0),
                };
            }),
        [herdSize, prices, quantities],
    );

    const headCost = rows.reduce((sum, row) => sum + row.cost, 0);
    const batchCost = headCost * Math.max(herdSize, 0);
    const batchWeight = rows.reduce(
        (sum, row) =>
            sum +
            (row.ingredient.unit === "kg" ? row.batch : 0),
        0,
    );

    const modified = quantities.map(
        (quantity, index) => quantity !== presets[stage][index],
    );

    const updateQuantity = (index: number, value: number) => {
        setQuantities((current) => {
            const next = [...current];
            next[index] = Number.isFinite(value) ? value : 0;
            return next;
        });
        setMessage("");
    };

    const updatePrice = (index: number, value: number) => {
        setPrices((current) => {
            const next = [...current];
            next[index] = Number.isFinite(value) ? value : 0;
            return next;
        });
        setMessage("");
    };

    const loadStandard = (nextStage: StageKey = stage) => {
        setQuantities([...presets[nextStage]]);
        setMessage("Industry-standard TMR loaded.");
    };

    const changeStage = (nextStage: StageKey) => {
        setStage(nextStage);
        setQuantities([...presets[nextStage]]);
        setMessage(`${stageLabels[nextStage]} standard loaded.`);
    };

    const saveBrowser = () => {
        localStorage.setItem(
            storageKey,
            JSON.stringify({
                stage,
                herdSize,
                quantities,
                prices,
            }),
        );
        setMessage("TMR plan saved in this browser.");
    };

    const reset = () => {
        setQuantities([...presets[stage]]);
        setPrices(ingredients.map((item) => item.price));
        setMessage("TMR restored to standard.");
    };

    const recordBatch = async () => {
        if (herdSize <= 0) {
            setMessage("Enter a herd/group size greater than zero.");
            return;
        }

        setSaving(true);
        setMessage("");

        try {
            const payload = {
                feed_type: "TMR_BATCH",
                quantity_kg: Number(batchWeight.toFixed(2)),
                group_or_pen: stage,
                operator: "WEB",
                status: "RECORDED",
                tmr_stage: stage,
                herd_size: herdSize,
                cost_per_head_pkr: Number(headCost.toFixed(2)),
                batch_cost_pkr: Number(batchCost.toFixed(2)),
                batch_weight_kg: Number(batchWeight.toFixed(2)),
                ingredients: rows
                    .filter((row) => row.quantity > 0)
                    .map((row) => ({
                        name: row.ingredient.name,
                        quantity_per_head: row.quantity,
                        unit: row.ingredient.unit,
                        price_per_kg: row.price,
                        batch_quantity: row.batch,
                        cost_per_head: Number(row.cost.toFixed(2)),
                    })),
            };

            const response = await fetch(
                "http://localhost:8000/farm/feed",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                },
            );

            if (!response.ok) {
                const detail = await response.text();
                throw new Error(detail || "TMR batch could not be recorded.");
            }

            const result =
                (await response.json()) as TMRBatchResponse;

            setSavedBatch(result);
            setMessage(
                `TMR batch recorded: ${formatNumber(batchWeight)} kg for ${herdSize} animals.`,
            );
        } catch (error) {
            setMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to record TMR batch.",
            );
        } finally {
            setSaving(false);
        }
    };

    const shareWhatsApp = () => {
        const lines = [
            "*DairyOS TMR BATCH SHEET*",
            `Stage: ${stageLabels[stage]}`,
            `Animals: ${herdSize}`,
            `Batch Weight: ${formatNumber(batchWeight)} kg`,
            `Cost / Head: Rs. ${formatNumber(headCost)}`,
            `Batch Cost: Rs. ${formatNumber(batchCost)}`,
            "",
            "*Ingredients:*",
            ...rows
                .filter((row) => row.quantity > 0)
                .map(
                    (row) =>
                        `• ${row.ingredient.name}: ${row.batch} ${row.ingredient.unit}`,
                ),
            "",
            "_DairyOS · Trident Dairies_",
        ];

        window.open(
            `https://wa.me/?text=${encodeURIComponent(lines.join("\n"))}`,
            "_blank",
            "noopener,noreferrer",
        );
    };

    return (
        <section className="tmr-manager">
            <div className="tmr-header">
                <div>
                    <div className="tmr-kicker">FEED & NUTRITION</div>
                    <h2>TMR Life-Cycle Manager</h2>
                    <p>
                        Prepare, cost and record the daily total mixed
                        ration for each animal stage.
                    </p>
                    <span className="tmr-standard-badge">
                        ✓ HF industry-standard starting presets
                    </span>
                </div>

                <div className="tmr-selector">
                    <label htmlFor="tmr-stage">Animal Stage</label>
                    <select
                        id="tmr-stage"
                        value={stage}
                        onChange={(event) =>
                            changeStage(
                                event.target.value as StageKey,
                            )
                        }
                    >
                        <optgroup label="Milking">
                            <option value="early_milking">
                                {stageLabels.early_milking}
                            </option>
                            <option value="mid_milking">
                                {stageLabels.mid_milking}
                            </option>
                            <option value="late_milking">
                                {stageLabels.late_milking}
                            </option>
                        </optgroup>

                        <optgroup label="Dry">
                            <option value="far_off">
                                {stageLabels.far_off}
                            </option>
                            <option value="close_up">
                                {stageLabels.close_up}
                            </option>
                        </optgroup>

                        <optgroup label="Young Stock">
                            <option value="heifer_growth">
                                {stageLabels.heifer_growth}
                            </option>
                            <option value="calf_starter">
                                {stageLabels.calf_starter}
                            </option>
                        </optgroup>
                    </select>

                    <div className="tmr-stage-info">
                        {stageInfo[stage]}
                    </div>
                </div>

                <div className="tmr-herd-input">
                    <label htmlFor="tmr-herd-size">Herd / Group Size</label>
                    <input
                        id="tmr-herd-size"
                        type="number"
                        min="0"
                        value={herdSize}
                        onChange={(event) =>
                            setHerdSize(
                                Math.max(
                                    0,
                                    Number(event.target.value) || 0,
                                ),
                            )
                        }
                    />
                    <span>animals</span>
                </div>
            </div>

            <div className="tmr-actions">
                <button
                    type="button"
                    className="tmr-button secondary"
                    onClick={reset}
                >
                    Reset to Standard
                </button>

                <button
                    type="button"
                    className="tmr-button advisory"
                    onClick={() => setShowAdvice(true)}
                >
                    Advisory
                </button>

                <button
                    type="button"
                    className="tmr-button secondary"
                    onClick={saveBrowser}
                >
                    Save
                </button>

                <button
                    type="button"
                    className="tmr-button dark"
                    onClick={() => window.print()}
                >
                    Print
                </button>

                <button
                    type="button"
                    className="tmr-button whatsapp"
                    onClick={shareWhatsApp}
                >
                    WhatsApp
                </button>

                <button
                    type="button"
                    className="tmr-button primary"
                    disabled={saving}
                    onClick={recordBatch}
                >
                    {saving ? "Recording..." : "Record TMR Batch"}
                </button>
            </div>

            {message && (
                <div className="tmr-message" role="status">
                    {message}
                </div>
            )}

            {savedBatch && (
                <div className="tmr-recorded">
                    Last API record:{" "}
                    {savedBatch.status ?? "RECORDED"}
                    {savedBatch.timestamp
                        ? ` · ${new Date(savedBatch.timestamp).toLocaleString(
                              "en-PK",
                          )}`
                        : ""}
                </div>
            )}

            <div className="tmr-table-wrap">
                <table className="tmr-table">
                    <thead>
                        <tr>
                            <th>Ingredient</th>
                            <th>Qty / Head</th>
                            <th>Price / KG</th>
                            <th>Batch Load</th>
                            <th>Cost / Head</th>
                        </tr>
                    </thead>

                    <tbody>
                        {rows.map((row, index) => (
                            <tr key={row.ingredient.name}>
                                <td>
                                    <strong>{row.ingredient.name}</strong>
                                    {modified[index] && (
                                        <span
                                            className="tmr-mod-dot"
                                            title="Modified from standard"
                                        />
                                    )}
                                </td>

                                <td>
                                    <div className="tmr-qty">
                                        <input
                                            type="number"
                                            min={row.ingredient.min}
                                            max={row.ingredient.max}
                                            step={row.ingredient.step}
                                            value={row.quantity}
                                            onChange={(event) =>
                                                updateQuantity(
                                                    index,
                                                    Number(
                                                        event.target.value,
                                                    ),
                                                )
                                            }
                                        />
                                        <span>
                                            {row.ingredient.unit}
                                        </span>
                                    </div>
                                </td>

                                <td>
                                    <div className="tmr-qty">
                                        <input
                                            type="number"
                                            min="0"
                                            step="1"
                                            value={row.price}
                                            onChange={(event) =>
                                                updatePrice(
                                                    index,
                                                    Number(
                                                        event.target.value,
                                                    ),
                                                )
                                            }
                                        />
                                        <span>/ kg</span>
                                    </div>
                                </td>

                                <td className="tmr-batch">
                                    {herdSize > 0
                                        ? `${row.batch.toLocaleString()} ${row.ingredient.unit}`
                                        : "—"}
                                </td>

                                <td className="tmr-cost">
                                    Rs. {formatNumber(row.cost)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="tmr-stats">
                <div className="tmr-stat head">
                    <span>Cost / Head / Day</span>
                    <strong>Rs. {formatNumber(headCost)}</strong>
                </div>

                <div className="tmr-stat group">
                    <span>Group Cost / Day</span>
                    <strong>Rs. {formatNumber(batchCost)}</strong>
                </div>

                <div className="tmr-stat weight">
                    <span>Batch Weight</span>
                    <strong>{formatNumber(batchWeight)} KG</strong>
                </div>
            </div>

            <div className="tmr-footer-note">
                <strong>Operational rule:</strong> TMR preparation is a
                planning calculation. The{" "}
                <strong>Record TMR Batch</strong> action creates the
                operational feed record through the existing DairyOS
                feed API.
            </div>

            {showAdvice && (
                <div
                    className="tmr-modal-backdrop"
                    role="presentation"
                    onClick={() => setShowAdvice(false)}
                >
                    <div
                        className="tmr-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="tmr-advisory-title"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <button
                            type="button"
                            className="tmr-modal-close"
                            onClick={() => setShowAdvice(false)}
                        >
                            Close
                        </button>

                        <div className="tmr-kicker">ADVISORY</div>
                        <h3 id="tmr-advisory-title">
                            {stageLabels[stage]}
                        </h3>

                        <p>{advice[stage]}</p>

                        <ul>
                            <li>
                                Mixing order: straw → silage →
                                concentrate / SBM → dry additives →
                                molasses last.
                            </li>
                            <li>
                                Mix for approximately 3–5 minutes after
                                the final ingredient.
                            </li>
                            <li>
                                Check sorting and actual intake after
                                feeding.
                            </li>
                            <li>
                                Adjust silage quantity when dry matter
                                changes materially.
                            </li>
                        </ul>

                        <p className="tmr-disclaimer">
                            These are starting-point management values.
                            Final ration decisions should follow actual
                            milk records, BCS, feed analysis and
                            veterinary/nutrition advice.
                        </p>
                    </div>
                </div>
            )}
        </section>
    );
}

export default TMRLifeCycleManager;
