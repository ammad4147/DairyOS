import React, { useEffect, useMemo, useState } from 'react';
import {
  CheckCircle2,
  Plus,
  Printer,
  RefreshCw,
  Save,
  Wheat,
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http' + '://127.0.0.1:8000';

type IngredientDefinition = {
  catalog_name: string;
  display_name?: string;
  dose_unit: 'kg' | 'g';
  fallback_price_per_kg: number;
};

type StageIngredient = IngredientDefinition & {
  quantity: number;
  price_per_kg: number;
  price_source: 'FINANCE' | 'MANUAL_FALLBACK';
  finance_transaction_id?: number | null;
  finance_purchase_date?: string | null;
  cost_per_head_day: number;
};

type StageSummary = {
  key: string;
  label: string;
  ingredients: StageIngredient[];
  ration_kg_per_head_day: number;
  cost_per_head_day: number;
  source: string;
};

type CategorySummary = {
  category: string;
  stage_keys: string[];
  animal_count: number;
  cost_per_head_day: number;
  category_cost_per_day: number;
};

type WeeklyReview = {
  week_start: string;
  week_end: string;
  status: 'DUE' | 'ENDORSED' | string;
  advisory: string;
  endorsement?: {
    reviewer?: string;
    reviewed_on?: string;
    reviewed_at?: string;
    notes?: string | null;
  } | null;
};

type TMRSummary = {
  data_status: string;
  operational_date: string;
  ingredients: IngredientDefinition[];
  stages: Record<string, StageSummary>;
  categories: CategorySummary[];
  herd_counts: Record<string, number>;
  total_herd_feed_cost_per_day: number;
  milk_production_today_liters: number;
  feed_cost_per_litre_today: number | null;
  feed_cost_basis: string;
  weekly_review?: WeeklyReview;
};

type DraftIngredient = StageIngredient;

const categoryOrder = [
  'Milking',
  'Dry',
  'Heifer',
  'Female Calf',
  'Male Calf',
  'Bull',
];

const money = (value: unknown, decimals = 2) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `PKR ${amount.toLocaleString('en-PK', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}`
    : 'N/A';
};

const card: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
  padding: 10,
};

const input: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: '#1e293b',
  color: '#fff',
  border: '1px solid #334155',
  borderRadius: 5,
  padding: '7px 8px',
  fontSize: 10,
};

const smallButton = (
  background: string,
): React.CSSProperties => ({
  background,
  color: '#fff',
  border: 0,
  borderRadius: 5,
  padding: '7px 10px',
  fontSize: 10,
  fontWeight: 800,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
});

const label: React.CSSProperties = {
  color: '#94a3b8',
  fontSize: 9,
  fontWeight: 800,
  textTransform: 'uppercase',
  display: 'block',
};

const th: React.CSSProperties = {
  padding: 8,
  color: '#94a3b8',
  fontSize: 8,
  fontWeight: 900,
  textTransform: 'uppercase',
  textAlign: 'left',
  whiteSpace: 'nowrap',
};

const td: React.CSSProperties = {
  padding: 8,
  borderTop: '1px solid #1f2937',
  verticalAlign: 'middle',
};

const categoryBasis = (category: string) => {
  if (category === 'Milking') {
    return 'Average of Early, Mid and Late Lactation TMR';
  }
  if (category === 'Dry') {
    return 'Average of Far-Off Dry and Close-Up Dry TMR';
  }
  if (category === 'Heifer') {
    return 'Growing Heifer TMR';
  }
  if (
    category === 'Female Calf'
    || category === 'Male Calf'
  ) {
    return 'Calf Starter TMR';
  }
  if (category === 'Bull') {
    return 'Bull TMR';
  }
  return '';
};

export default function TMRPreparationTool() {
  const [summary, setSummary] = useState<TMRSummary | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('Milking');
  const [selectedStage, setSelectedStage] = useState('early_milking');
  const [draft, setDraft] = useState<DraftIngredient[]>([]);
  const [operator, setOperator] = useState('UI Operator');
  const [reviewer, setReviewer] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [savingStage, setSavingStage] = useState(false);
  const [endorsing, setEndorsing] = useState(false);
  const [showAddIngredient, setShowAddIngredient] = useState(false);
  const [addingIngredient, setAddingIngredient] = useState(false);
  const [newIngredient, setNewIngredient] = useState({
    name: '',
    display_name: '',
    dose_unit: 'kg' as 'kg' | 'g',
    fallback_price_per_kg: 0,
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/farm/tmr`);
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          body?.detail || 'Unable to load governed TMR.',
        );
      }

      setSummary(body);
    } catch (exc) {
      setSummary(null);
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to load governed TMR.',
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const categories = useMemo(() => {
    const rows = summary?.categories ?? [];

    return [...rows].sort(
      (a, b) =>
        categoryOrder.indexOf(a.category)
        - categoryOrder.indexOf(b.category),
    );
  }, [summary]);

  const activeCategory = useMemo(
    () =>
      categories.find(
        row => row.category === selectedCategory,
      ) ?? categories[0] ?? null,
    [categories, selectedCategory],
  );

  useEffect(() => {
    if (!activeCategory) {
      return;
    }

    if (!activeCategory.stage_keys.includes(selectedStage)) {
      setSelectedStage(
        activeCategory.stage_keys[0] || '',
      );
    }
  }, [activeCategory, selectedStage]);

  const activeStage = useMemo(
    () =>
      summary?.stages?.[selectedStage] ?? null,
    [summary, selectedStage],
  );

  useEffect(() => {
    if (!activeStage) {
      setDraft([]);
      return;
    }

    setDraft(
      activeStage.ingredients.map(row => ({ ...row })),
    );
  }, [activeStage]);

  const previewStageCost = useMemo(
    () =>
      draft.reduce((total, row) => {
        const quantityKg =
          row.dose_unit === 'g'
            ? Number(row.quantity || 0) / 1000
            : Number(row.quantity || 0);

        const rate =
          row.price_source === 'FINANCE'
            ? Number(row.price_per_kg || 0)
            : Number(row.fallback_price_per_kg || 0);

        return total + quantityKg * rate;
      }, 0),
    [draft],
  );

  const previewRationKg = useMemo(
    () =>
      draft.reduce(
        (total, row) =>
          total
          + (
            row.dose_unit === 'g'
              ? Number(row.quantity || 0) / 1000
              : Number(row.quantity || 0)
          ),
        0,
      ),
    [draft],
  );

  const updateQuantity = (
    index: number,
    value: number,
  ) => {
    setDraft(current =>
      current.map((row, rowIndex) =>
        rowIndex === index
          ? {
              ...row,
              quantity: Math.max(0, value || 0),
            }
          : row,
      ),
    );
  };

  const updateFallbackPrice = (
    index: number,
    value: number,
  ) => {
    setDraft(current =>
      current.map((row, rowIndex) =>
        rowIndex === index
          ? {
              ...row,
              fallback_price_per_kg:
                Math.max(0, value || 0),
              price_per_kg:
                row.price_source === 'FINANCE'
                  ? row.price_per_kg
                  : Math.max(0, value || 0),
            }
          : row,
      ),
    );
  };

  const saveStage = async () => {
    if (!selectedStage || !draft.length) {
      return;
    }

    setSavingStage(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_BASE}/farm/tmr/stages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            stage: selectedStage,
            operator: operator.trim() || 'UI Operator',
            ingredients: draft.map(row => ({
              catalog_name: row.catalog_name,
              quantity: Number(row.quantity || 0),
              dose_unit: row.dose_unit,
              fallback_price_per_kg:
                Number(
                  row.fallback_price_per_kg || 0,
                ),
            })),
          }),
        },
      );

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          body?.detail
          || 'Unable to save governed TMR stage.',
        );
      }

      setSummary(body.summary);
      setMessage(
        `${activeStage?.label || selectedStage} saved as a new governed TMR version.`,
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to save TMR stage.',
      );
    } finally {
      setSavingStage(false);
    }
  };

  const addIngredient = async () => {
    const name = newIngredient.name.trim();

    if (!name) {
      setError('Ingredient name is required.');
      return;
    }

    setAddingIngredient(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_BASE}/farm/tmr/ingredients`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name,
            display_name:
              newIngredient.display_name.trim() || name,
            dose_unit: newIngredient.dose_unit,
            fallback_price_per_kg:
              Number(
                newIngredient.fallback_price_per_kg || 0,
              ),
          }),
        },
      );

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          body?.detail || 'Unable to add TMR ingredient.',
        );
      }

      const catalogName = String(
        body?.catalog_name || name,
      );

      setDraft(current => {
        if (
          current.some(
            row => row.catalog_name === catalogName,
          )
        ) {
          return current;
        }

        return [
          ...current,
          {
            catalog_name: catalogName,
            display_name:
              String(body?.display_name || catalogName),
            dose_unit:
              body?.dose_unit === 'g' ? 'g' : 'kg',
            quantity: 0,
            fallback_price_per_kg:
              Number(
                body?.fallback_price_per_kg || 0,
              ),
            price_per_kg:
              Number(
                body?.fallback_price_per_kg || 0,
              ),
            price_source: 'MANUAL_FALLBACK',
            finance_transaction_id: null,
            finance_purchase_date: null,
            cost_per_head_day: 0,
          },
        ];
      });

      setSummary(current =>
        current
          ? {
              ...current,
              ingredients: [
                ...current.ingredients.filter(
                  row =>
                    row.catalog_name !== catalogName,
                ),
                {
                  catalog_name: catalogName,
                  display_name:
                    String(
                      body?.display_name || catalogName,
                    ),
                  dose_unit:
                    body?.dose_unit === 'g'
                      ? 'g'
                      : 'kg',
                  fallback_price_per_kg:
                    Number(
                      body?.fallback_price_per_kg || 0,
                    ),
                },
              ],
            }
          : current,
      );

      setNewIngredient({
        name: '',
        display_name: '',
        dose_unit: 'kg',
        fallback_price_per_kg: 0,
      });

      setShowAddIngredient(false);

      setMessage(
        `${catalogName} added to the governed Feed ingredient catalog. It is now available to Finance Feed Expenses; save this TMR stage if it should be part of the ration.`,
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to add TMR ingredient.',
      );
    } finally {
      setAddingIngredient(false);
    }
  };

  const endorse = async () => {
    if (!reviewer.trim()) {
      setError('Vet reviewer name / ID is required.');
      return;
    }

    setEndorsing(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_BASE}/farm/tmr/endorse`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            reviewer: reviewer.trim(),
            notes: reviewNotes.trim() || null,
          }),
        },
      );

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          body?.detail
          || 'Unable to endorse weekly TMR review.',
        );
      }

      setSummary(body.summary);
      setReviewNotes('');
      setMessage(
        'Weekly whole-herd TMR review endorsed and retained in audit history.',
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to endorse TMR review.',
      );
    } finally {
      setEndorsing(false);
    }
  };

  const selectCategory = (
    category: CategorySummary,
  ) => {
    setSelectedCategory(category.category);
    setSelectedStage(
      category.stage_keys[0] || '',
    );
    setMessage('');
    setError('');
  };

  const weekly = summary?.weekly_review;
  const alreadyEndorsed =
    weekly?.status === 'ENDORSED';

  return (
    <div
      style={{
        background: '#0f172a',
        border: '1px solid #1f2937',
        borderRadius: 10,
        overflow: 'hidden',
        color: '#fff',
      }}
    >
      <div
        style={{
          padding: 14,
          borderBottom: '1px solid #1f2937',
          display: 'flex',
          justifyContent: 'space-between',
          gap: 12,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              color: '#38bdf8',
              fontSize: 15,
              display: 'flex',
              alignItems: 'center',
              gap: 7,
            }}
          >
            <Wheat size={18} />
            TMR Preparation Tool
          </h3>

          <div
            style={{
              marginTop: 4,
              color: '#94a3b8',
              fontSize: 10,
            }}
          >
            Governed whole-herd ration authority.
            Finance supplies ingredient purchase prices;
            TMR supplies consumed feed cost for COP.
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            gap: 7,
            flexWrap: 'wrap',
          }}
        >
          <button
            type="button"
            onClick={() => void load()}
            style={smallButton('#334155')}
          >
            <RefreshCw size={12} />
            Refresh
          </button>

          <button
            type="button"
            onClick={() => window.print()}
            style={smallButton('#475569')}
          >
            <Printer size={12} />
            Print
          </button>

          <button
            type="button"
            onClick={() =>
              setShowAddIngredient(value => !value)
            }
            style={smallButton('#2563eb')}
          >
            <Plus size={12} />
            Add Ingredient
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            margin: 12,
            padding: 9,
            borderRadius: 6,
            border: '1px solid #7f1d1d',
            background: 'rgba(127,29,29,.18)',
            color: '#fecaca',
            fontSize: 10,
          }}
        >
          {error}
        </div>
      )}

      {message && (
        <div
          style={{
            margin: 12,
            padding: 9,
            borderRadius: 6,
            border: '1px solid #166534',
            background: 'rgba(22,101,52,.16)',
            color: '#bbf7d0',
            fontSize: 10,
          }}
        >
          {message}
        </div>
      )}

      {loading || !summary ? (
        <div
          style={{
            padding: 20,
            color: '#94a3b8',
            fontSize: 10,
          }}
        >
          {loading
            ? 'Loading governed TMR…'
            : 'TMR data unavailable.'}
        </div>
      ) : (
        <>
          <div
            style={{
              padding: 12,
              display: 'grid',
              gridTemplateColumns:
                'repeat(3,minmax(0,1fr))',
              gap: 8,
              borderBottom: '1px solid #1f2937',
            }}
          >
            <Metric
              label="Whole Herd Feed Cost / Day"
              value={money(
                summary.total_herd_feed_cost_per_day,
              )}
            />

            <Metric
              label="Milk Production Today"
              value={`${Number(
                summary.milk_production_today_liters || 0,
              ).toLocaleString('en-PK', {
                maximumFractionDigits: 2,
              })} L`}
            />

            <Metric
              label="Live Feed Cost / L"
              value={
                summary.feed_cost_per_litre_today == null
                  ? 'N/A'
                  : money(
                      summary.feed_cost_per_litre_today,
                    )
              }
            />
          </div>

          <div
            style={{
              padding: '12px 12px 4px',
              color: '#94a3b8',
              fontSize: 9,
              fontWeight: 800,
              textTransform: 'uppercase',
            }}
          >
            DairyOS Herd Categories — Cost / Head / Day
          </div>

          <div
            style={{
              padding: '4px 12px 12px',
              display: 'grid',
              gridTemplateColumns:
                'repeat(6,minmax(120px,1fr))',
              gap: 7,
              overflowX: 'auto',
            }}
          >
            {categories.map(category => {
              const active =
                category.category ===
                activeCategory?.category;

              return (
                <button
                  key={category.category}
                  type="button"
                  onClick={() =>
                    selectCategory(category)
                  }
                  style={{
                    ...card,
                    textAlign: 'left',
                    cursor: 'pointer',
                    color: '#fff',
                    outline: active
                      ? '1px solid #38bdf8'
                      : 'none',
                    background: active
                      ? 'rgba(14,165,233,.09)'
                      : '#111827',
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 900,
                      color: active
                        ? '#38bdf8'
                        : '#e2e8f0',
                    }}
                  >
                    {category.category}
                  </div>

                  <div
                    style={{
                      marginTop: 6,
                      fontSize: 15,
                      fontWeight: 900,
                    }}
                  >
                    {money(
                      category.cost_per_head_day,
                    )}
                  </div>

                  <div
                    style={{
                      marginTop: 3,
                      color: '#64748b',
                      fontSize: 8,
                    }}
                  >
                    / head / day
                  </div>

                  <div
                    style={{
                      marginTop: 7,
                      color: '#94a3b8',
                      fontSize: 8,
                    }}
                  >
                    {category.animal_count} animal(s)
                  </div>

                  <div
                    style={{
                      marginTop: 2,
                      color: '#34d399',
                      fontSize: 9,
                      fontWeight: 800,
                    }}
                  >
                    {money(
                      category.category_cost_per_day,
                    )}{' '}
                    / day
                  </div>
                </button>
              );
            })}
          </div>

          {activeCategory && (
            <div
              style={{
                margin: '0 12px 12px',
                padding: 10,
                borderRadius: 7,
                background: '#111827',
                border: '1px solid #1f2937',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 10,
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 900,
                    }}
                  >
                    {activeCategory.category}
                  </div>

                  <div
                    style={{
                      color: '#94a3b8',
                      fontSize: 9,
                      marginTop: 3,
                    }}
                  >
                    {categoryBasis(
                      activeCategory.category,
                    )}
                  </div>
                </div>

                <div
                  style={{
                    textAlign: 'right',
                  }}
                >
                  <div
                    style={{
                      color: '#64748b',
                      fontSize: 8,
                      textTransform: 'uppercase',
                      fontWeight: 800,
                    }}
                  >
                    Governed category cost
                  </div>

                  <div
                    style={{
                      color: '#38bdf8',
                      fontSize: 16,
                      fontWeight: 900,
                      marginTop: 2,
                    }}
                  >
                    {money(
                      activeCategory.cost_per_head_day,
                    )}
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: 6,
                  flexWrap: 'wrap',
                  marginTop: 10,
                }}
              >
                {activeCategory.stage_keys.map(key => {
                  const stage = summary.stages[key];
                  if (!stage) {
                    return null;
                  }

                  const active = key === selectedStage;

                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() =>
                        setSelectedStage(key)
                      }
                      style={{
                        ...smallButton(
                          active
                            ? '#0369a1'
                            : '#1e293b',
                        ),
                        border: '1px solid #334155',
                      }}
                    >
                      {stage.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {showAddIngredient && (
            <div
              style={{
                margin: '0 12px 12px',
                ...card,
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 900,
                  marginBottom: 8,
                }}
              >
                Add Governed Feed Ingredient
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns:
                    '1.2fr 1.2fr 100px 140px auto',
                  gap: 7,
                  alignItems: 'end',
                }}
              >
                <label style={label}>
                  Catalog / Finance Name
                  <input
                    value={newIngredient.name}
                    onChange={event =>
                      setNewIngredient(current => ({
                        ...current,
                        name: event.target.value,
                      }))
                    }
                    style={input}
                  />
                </label>

                <label style={label}>
                  Display Name
                  <input
                    value={
                      newIngredient.display_name
                    }
                    onChange={event =>
                      setNewIngredient(current => ({
                        ...current,
                        display_name:
                          event.target.value,
                      }))
                    }
                    style={input}
                  />
                </label>

                <label style={label}>
                  Dose Unit
                  <select
                    value={newIngredient.dose_unit}
                    onChange={event =>
                      setNewIngredient(current => ({
                        ...current,
                        dose_unit:
                          event.target.value === 'g'
                            ? 'g'
                            : 'kg',
                      }))
                    }
                    style={input}
                  >
                    <option value="kg">kg</option>
                    <option value="g">g</option>
                  </select>
                </label>

                <label style={label}>
                  Fallback PKR / kg
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={
                      newIngredient
                        .fallback_price_per_kg
                    }
                    onChange={event =>
                      setNewIngredient(current => ({
                        ...current,
                        fallback_price_per_kg:
                          Math.max(
                            0,
                            Number(
                              event.target.value,
                            ) || 0,
                          ),
                      }))
                    }
                    style={input}
                  />
                </label>

                <button
                  type="button"
                  disabled={addingIngredient}
                  onClick={() =>
                    void addIngredient()
                  }
                  style={{
                    ...smallButton('#2563eb'),
                    opacity:
                      addingIngredient ? 0.5 : 1,
                  }}
                >
                  <Plus size={12} />
                  {addingIngredient
                    ? 'Adding…'
                    : 'Add'}
                </button>
              </div>

              <div
                style={{
                  color: '#64748b',
                  fontSize: 9,
                  marginTop: 7,
                }}
              >
                The ingredient is registered in the
                shared Feed catalog and becomes
                available in Finance → Feed Expenses.
                Save the selected TMR stage after
                assigning its ration quantity.
              </div>
            </div>
          )}

          {activeStage && (
            <>
              <div
                style={{
                  padding: '0 12px 8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 10,
                  alignItems: 'end',
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 900,
                      color: '#e2e8f0',
                    }}
                  >
                    {activeStage.label}
                  </div>

                  <div
                    style={{
                      marginTop: 3,
                      color: '#64748b',
                      fontSize: 9,
                    }}
                  >
                    Governed version currently:
                    {' '}
                    {money(
                      activeStage.cost_per_head_day,
                    )}
                    {' / head / day'}
                  </div>
                </div>

                <label
                  style={{
                    ...label,
                    width: 180,
                  }}
                >
                  Updated By
                  <input
                    value={operator}
                    onChange={event =>
                      setOperator(
                        event.target.value,
                      )
                    }
                    style={input}
                  />
                </label>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    width: '100%',
                    minWidth: 900,
                    borderCollapse: 'collapse',
                    fontSize: 10,
                  }}
                >
                  <thead>
                    <tr
                      style={{
                        background: '#111827',
                      }}
                    >
                      <th style={th}>Ingredient</th>
                      <th style={th}>
                        Qty / Head / Day
                      </th>
                      <th style={th}>
                        Price / kg
                      </th>
                      <th style={th}>
                        Price Authority
                      </th>
                      <th
                        style={{
                          ...th,
                          textAlign: 'right',
                        }}
                      >
                        Cost / Head / Day
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {draft.map((row, index) => {
                      const quantityKg =
                        row.dose_unit === 'g'
                          ? Number(
                              row.quantity || 0,
                            ) / 1000
                          : Number(
                              row.quantity || 0,
                            );

                      const rate =
                        row.price_source
                          === 'FINANCE'
                          ? Number(
                              row.price_per_kg || 0,
                            )
                          : Number(
                              row
                                .fallback_price_per_kg
                              || 0,
                            );

                      const cost =
                        quantityKg * rate;

                      return (
                        <tr
                          key={row.catalog_name}
                        >
                          <td
                            style={{
                              ...td,
                              fontWeight: 800,
                            }}
                          >
                            {row.display_name
                              || row.catalog_name}

                            <div
                              style={{
                                color: '#64748b',
                                fontSize: 8,
                                marginTop: 2,
                              }}
                            >
                              {row.catalog_name}
                            </div>
                          </td>

                          <td style={td}>
                            <div
                              style={{
                                display: 'flex',
                                gap: 5,
                                alignItems: 'center',
                              }}
                            >
                              <input
                                type="number"
                                min={0}
                                step={
                                  row.dose_unit === 'g'
                                    ? 5
                                    : 0.25
                                }
                                value={
                                  row.quantity || ''
                                }
                                onChange={event =>
                                  updateQuantity(
                                    index,
                                    Number(
                                      event
                                        .target
                                        .value,
                                    ),
                                  )
                                }
                                style={{
                                  ...input,
                                  width: 88,
                                }}
                              />

                              <span
                                style={{
                                  color: '#94a3b8',
                                }}
                              >
                                {row.dose_unit}
                              </span>
                            </div>
                          </td>

                          <td style={td}>
                            <input
                              type="number"
                              min={0}
                              step="0.01"
                              value={rate}
                              disabled={
                                row.price_source
                                === 'FINANCE'
                              }
                              onChange={event =>
                                updateFallbackPrice(
                                  index,
                                  Number(
                                    event
                                      .target
                                      .value,
                                  ),
                                )
                              }
                              style={{
                                ...input,
                                width: 100,
                                opacity:
                                  row.price_source
                                  === 'FINANCE'
                                    ? 0.65
                                    : 1,
                              }}
                            />
                          </td>

                          <td style={td}>
                            {row.price_source
                            === 'FINANCE' ? (
                              <div>
                                <span
                                  style={{
                                    color: '#34d399',
                                    fontWeight: 900,
                                  }}
                                >
                                  Finance
                                </span>

                                <div
                                  style={{
                                    color: '#64748b',
                                    fontSize: 8,
                                    marginTop: 2,
                                  }}
                                >
                                  Tx #
                                  {row.finance_transaction_id
                                    ?? '—'}
                                  {row.finance_purchase_date
                                    ? ` · ${row.finance_purchase_date}`
                                    : ''}
                                </div>
                              </div>
                            ) : (
                              <span
                                style={{
                                  color: '#fbbf24',
                                  fontWeight: 800,
                                }}
                              >
                                Manual fallback
                              </span>
                            )}
                          </td>

                          <td
                            style={{
                              ...td,
                              textAlign: 'right',
                              fontWeight: 900,
                              color: '#cbd5e1',
                            }}
                          >
                            {money(cost)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns:
                    'repeat(3,minmax(0,1fr))',
                  gap: 8,
                  padding: 12,
                  borderTop:
                    '1px solid #1f2937',
                }}
              >
                <Metric
                  label="Draft Ration / Head / Day"
                  value={`${previewRationKg.toLocaleString(
                    'en-PK',
                    {
                      maximumFractionDigits: 3,
                    },
                  )} kg`}
                />

                <Metric
                  label="Draft Cost / Head / Day"
                  value={money(previewStageCost)}
                />

                <div
                  style={{
                    ...card,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent:
                      'space-between',
                    gap: 8,
                  }}
                >
                  <div>
                    <div
                      style={{
                        color: '#64748b',
                        fontSize: 8,
                        textTransform:
                          'uppercase',
                        fontWeight: 900,
                      }}
                    >
                      Version Control
                    </div>

                    <div
                      style={{
                        color: '#94a3b8',
                        fontSize: 9,
                        marginTop: 3,
                      }}
                    >
                      Saving creates a new
                      governed TMR version.
                    </div>
                  </div>

                  <button
                    type="button"
                    disabled={savingStage}
                    onClick={() =>
                      void saveStage()
                    }
                    style={{
                      ...smallButton('#059669'),
                      opacity:
                        savingStage ? 0.5 : 1,
                    }}
                  >
                    <Save size={12} />
                    {savingStage
                      ? 'Saving…'
                      : 'Save TMR'}
                  </button>
                </div>
              </div>
            </>
          )}

          <div
            style={{
              margin: '0 12px 12px',
              ...card,
              border:
                alreadyEndorsed
                  ? '1px solid #166534'
                  : '1px solid #92400e',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: 10,
                flexWrap: 'wrap',
              }}
            >
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    fontWeight: 900,
                    fontSize: 11,
                    color:
                      alreadyEndorsed
                        ? '#86efac'
                        : '#fbbf24',
                  }}
                >
                  <CheckCircle2 size={14} />
                  Weekly Vet TMR Review
                </div>

                <div
                  style={{
                    marginTop: 4,
                    color: '#cbd5e1',
                    fontSize: 10,
                  }}
                >
                  {weekly?.advisory
                    || 'Weekly TMR review status unavailable.'}
                </div>

                {weekly && (
                  <div
                    style={{
                      marginTop: 3,
                      color: '#64748b',
                      fontSize: 9,
                    }}
                  >
                    Week {weekly.week_start}
                    {' → '}
                    {weekly.week_end}
                  </div>
                )}

                {alreadyEndorsed
                  && weekly?.endorsement && (
                    <div
                      style={{
                        marginTop: 5,
                        color: '#86efac',
                        fontSize: 9,
                      }}
                    >
                      Endorsed by
                      {' '}
                      {weekly.endorsement.reviewer
                        || 'Vet'}
                      {weekly.endorsement.reviewed_on
                        ? ` on ${weekly.endorsement.reviewed_on}`
                        : ''}
                    </div>
                  )}
              </div>

              <div
                style={{
                  minWidth: 300,
                  display: 'grid',
                  gridTemplateColumns:
                    '1fr 1.4fr auto',
                  gap: 7,
                  alignItems: 'end',
                }}
              >
                <label style={label}>
                  Vet Name / ID
                  <input
                    value={reviewer}
                    disabled={alreadyEndorsed}
                    onChange={event =>
                      setReviewer(
                        event.target.value,
                      )
                    }
                    style={input}
                  />
                </label>

                <label style={label}>
                  Review Notes
                  <input
                    value={reviewNotes}
                    disabled={alreadyEndorsed}
                    onChange={event =>
                      setReviewNotes(
                        event.target.value,
                      )
                    }
                    style={input}
                  />
                </label>

                <button
                  type="button"
                  disabled={
                    alreadyEndorsed
                    || endorsing
                    || !reviewer.trim()
                  }
                  onClick={() => void endorse()}
                  style={{
                    ...smallButton('#059669'),
                    opacity:
                      alreadyEndorsed
                      || endorsing
                      || !reviewer.trim()
                        ? 0.5
                        : 1,
                  }}
                >
                  <CheckCircle2 size={12} />
                  {alreadyEndorsed
                    ? 'Endorsed'
                    : endorsing
                      ? 'Endorsing…'
                      : 'Vet Endorse TMR Review'}
                </button>
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '0 12px 12px',
              color: '#64748b',
              fontSize: 9,
            }}
          >
            {summary.feed_cost_basis}
            {' · '}
            Operational date:
            {' '}
            {summary.operational_date}
            {' · '}
            TMR whole-herd feed cost is the governed
            Feed Cost / L input to Auto COP.
          </div>
        </>
      )}
    </div>
  );
}

function Metric({
  label: metricLabel,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={card}>
      <div
        style={{
          color: '#64748b',
          fontSize: 8,
          textTransform: 'uppercase',
          fontWeight: 900,
        }}
      >
        {metricLabel}
      </div>

      <div
        style={{
          color: '#38bdf8',
          fontSize: 16,
          fontWeight: 900,
          marginTop: 4,
        }}
      >
        {value}
      </div>
    </div>
  );
}
