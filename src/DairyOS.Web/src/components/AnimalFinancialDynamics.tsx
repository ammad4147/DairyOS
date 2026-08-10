import React, { useMemo } from "react";
import "./AnimalFinancialDynamics.css";

type RecordData = Record<string, unknown>;

type Props = {
    animalId: string;
    finance: RecordData[];
    descendants: RecordData[];
    onOpenAnimal: (animalId: string) => void;
};

function numberValue(value: unknown): number {
    if (typeof value === "number" && Number.isFinite(value)) {
        return value;
    }

    return Number(value) || 0;
}

function money(value: number): string {
    return `PKR ${value.toLocaleString(undefined, {
        maximumFractionDigits: 0,
    })}`;
}

function text(record: RecordData, ...keys: string[]): string {
    for (const key of keys) {
        const value = record[key];

        if (
            value !== undefined
            && value !== null
            && value !== ""
        ) {
            return String(value);
        }
    }

    return "—";
}

function isIncome(record: RecordData): boolean {
    const type = String(
        record.transaction_type ?? "",
    ).toUpperCase();

    return [
        "INCOME",
        "RECEIPT",
        "SALE",
        "REVENUE",
    ].includes(type);
}

function AnimalFinancialDynamics({
    animalId,
    finance,
    descendants,
    onOpenAnimal,
}: Props) {
    const descendantIds = useMemo(
        () =>
            new Set(
                descendants
                    .map(item => item.animal_id)
                    .filter(Boolean)
                    .map(String),
            ),
        [descendants],
    );

    const own = useMemo(
        () =>
            finance.filter(
                record =>
                    String(
                        record.animal_id ?? "",
                    ) === animalId,
            ),
        [finance, animalId],
    );

    const offspring = useMemo(
        () =>
            finance.filter(record =>
                descendantIds.has(
                    String(
                        record.animal_id ?? "",
                    ),
                ),
            ),
        [finance, descendantIds],
    );

    const all = useMemo(
        () => [...own, ...offspring],
        [own, offspring],
    );

    const totals = useMemo(() => {
        let income = 0;
        let expense = 0;

        for (const record of all) {
            const amount = numberValue(record.amount);

            if (isIncome(record)) {
                income += amount;
            } else {
                expense += amount;
            }
        }

        return {
            income,
            expense,
            net: income - expense,
        };
    }, [all]);

    return (
        <section className="animal-financial">
            <div className="financial-heading">
                <div>
                    <span>FINANCIAL DYNAMICS</span>
                    <h3>Animal economic performance</h3>
                    <p>
                        Lifetime financial activity linked to{" "}
                        <strong>{animalId}</strong> and her
                        recorded offspring.
                    </p>
                </div>
            </div>

            <div className="financial-cards">
                <div>
                    <span>Own income</span>
                    <strong>
                        {money(
                            own.reduce(
                                (total, record) =>
                                    total
                                    + (
                                        isIncome(record)
                                            ? numberValue(
                                                record.amount,
                                            )
                                            : 0
                                    ),
                                0,
                            ),
                        )}
                    </strong>
                </div>

                <div>
                    <span>Offspring income</span>
                    <strong>
                        {money(
                            offspring.reduce(
                                (total, record) =>
                                    total
                                    + (
                                        isIncome(record)
                                            ? numberValue(
                                                record.amount,
                                            )
                                            : 0
                                    ),
                                0,
                            ),
                        )}
                    </strong>
                </div>

                <div>
                    <span>Total income</span>
                    <strong>
                        {money(totals.income)}
                    </strong>
                </div>

                <div>
                    <span>Total cost</span>
                    <strong>
                        {money(totals.expense)}
                    </strong>
                </div>

                <div className="financial-net">
                    <span>Net contribution</span>
                    <strong>
                        {money(totals.net)}
                    </strong>
                </div>
            </div>

            <div className="financial-meta">
                <span>
                    {own.length} own transactions
                </span>
                <span>
                    {descendantIds.size} linked offspring
                </span>
                <span>
                    {offspring.length} offspring transactions
                </span>
            </div>

            <div className="financial-table-wrap">
                {all.length === 0 ? (
                    <div className="financial-empty">
                        No animal-linked financial transactions
                        have been recorded yet.
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Animal</th>
                                <th>Type</th>
                                <th>Category</th>
                                <th>Amount</th>
                                <th>Date</th>
                                <th>Reference</th>
                            </tr>
                        </thead>

                        <tbody>
                            {[...all]
                                .sort(
                                    (a, b) =>
                                        String(
                                            b.timestamp
                                            ?? b.transaction_date
                                            ?? "",
                                        ).localeCompare(
                                            String(
                                                a.timestamp
                                                ?? a.transaction_date
                                                ?? "",
                                            ),
                                        ),
                                )
                                .map((record, index) => {
                                    const recordAnimal =
                                        String(
                                            record.animal_id
                                            ?? "",
                                        );

                                    return (
                                        <tr
                                            key={`${recordAnimal}-${index}`}
                                        >
                                            <td>
                                                <button
                                                    type="button"
                                                    className="financial-animal-link"
                                                    onClick={() =>
                                                        onOpenAnimal(
                                                            recordAnimal,
                                                        )
                                                    }
                                                >
                                                    {recordAnimal
                                                        || "—"}
                                                </button>
                                            </td>

                                            <td>
                                                {text(
                                                    record,
                                                    "transaction_type",
                                                )}
                                            </td>

                                            <td>
                                                {text(
                                                    record,
                                                    "category",
                                                )}
                                            </td>

                                            <td>
                                                {money(
                                                    numberValue(
                                                        record.amount,
                                                    ),
                                                )}
                                            </td>

                                            <td>
                                                {text(
                                                    record,
                                                    "timestamp",
                                                    "transaction_date",
                                                )}
                                            </td>

                                            <td>
                                                {text(
                                                    record,
                                                    "counterparty",
                                                    "reference",
                                                    "notes",
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                        </tbody>
                    </table>
                )}
            </div>
        </section>
    );
}

export default AnimalFinancialDynamics;
