import React, {
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  RefreshCw,
  SlidersHorizontal,
  Warehouse,
  Wheat,
  Wrench,
} from 'lucide-react';

import { API_BASE_URL } from '../config/api';
import TMRPreparationTool from './TMRPreparationTool';


const API_BASE =
  API_BASE_URL || 'http' + '://127.0.0.1:8000';


type FeedStorageItem = {
  id: number;
  item: string;
  unit: string;
  purchased_from_finance: number;
  auto_consumed_from_tmr: number;
  manual_override_net: number;
  legacy_manual_usage: number;
  projected_balance: number;
  balance: number;
  shortage: number;
  latest_finance_unit_rate?: number | null;
  latest_finance_transaction_id?: number | null;
  latest_finance_purchase_date?: string | null;
  status: string;
};


type FeedEquipment = {
  finance_transaction_id: number;
  equipment_name: string;
  purchase_date?: string | null;
  supplier?: string | null;
  finance_reference?: string | null;
  quantity?: number | null;
  unit?: string | null;
  unit_rate?: number | null;
  amount: number;
  finance_status?: string | null;
  status: 'OPERATIONAL' | 'NON_OPERATIONAL' | 'NOT_SET';
  status_source: 'MANUAL' | 'UNSET';
  status_operator?: string | null;
  status_recorded_at?: string | null;
};


const panel: React.CSSProperties = {
  background: '#0f172a',
  border: '1px solid #1f2937',
  borderRadius: 9,
  padding: 12,
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


const button = (
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
  justifyContent: 'center',
  gap: 5,
});


const label: React.CSSProperties = {
  color: '#94a3b8',
  fontSize: 8,
  fontWeight: 900,
  textTransform: 'uppercase',
  display: 'block',
};


const money = (value: unknown) => {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return '—';
  }

  return `PKR ${amount.toLocaleString('en-PK', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};


const quantity = (
  value: unknown,
  unit = 'kg',
) => {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return `0 ${unit}`;
  }

  return `${amount.toLocaleString('en-PK', {
    maximumFractionDigits: 3,
  })} ${unit}`;
};


export default function FeedTab() {
  const [feedItems, setFeedItems] =
    useState<FeedStorageItem[]>([]);

  const [equipment, setEquipment] =
    useState<FeedEquipment[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState('');

  const [message, setMessage] =
    useState('');

  const [overrideItem, setOverrideItem] =
    useState('');

  const [overrideQuantity, setOverrideQuantity] =
    useState('');

  const [overrideNotes, setOverrideNotes] =
    useState('');

  const [overrideSaving, setOverrideSaving] =
    useState(false);

  const [
    equipmentStatusSaving,
    setEquipmentStatusSaving,
  ] = useState<number | null>(null);


  const visibleFeedItems = useMemo(
    () =>
      feedItems.filter(
        item =>
          !item.item.startsWith(
            'FEED-SURFACE-',
          ),
      ),
    [feedItems],
  );


  const selectedOverrideItem = useMemo(
    () =>
      visibleFeedItems.find(
        item => String(item.id) === overrideItem,
      ) ?? null,
    [visibleFeedItems, overrideItem],
  );


  const load = async (
    quiet = false,
  ) => {
    if (!quiet) {
      setLoading(true);
    }

    setError('');

    try {
      const [
        storageResponse,
        equipmentResponse,
      ] = await Promise.all([
        fetch(
          `${API_BASE}/farm/feed-inventory/authoritative`,
        ),
        fetch(
          `${API_BASE}/farm/feed-equipment`,
        ),
      ]);

      const storageBody =
        await storageResponse
          .json()
          .catch(() => null);

      const equipmentBody =
        await equipmentResponse
          .json()
          .catch(() => null);

      if (!storageResponse.ok) {
        throw new Error(
          storageBody?.detail
          || 'Feed Storage Status is unavailable.',
        );
      }

      setFeedItems(
        (storageBody?.items ?? []).map(
          (row: any) => ({
            id: Number(row.id),
            item: String(row.item),
            unit: String(row.unit || 'kg'),
            purchased_from_finance:
              Number(
                row.purchased_from_finance || 0,
              ),
            auto_consumed_from_tmr:
              Number(
                row.auto_consumed_from_tmr || 0,
              ),
            manual_override_net:
              Number(
                row.manual_override_net || 0,
              ),
            legacy_manual_usage:
              Number(
                row.legacy_manual_usage || 0,
              ),
            projected_balance:
              Number(
                row.projected_balance || 0,
              ),
            balance:
              Number(row.balance || 0),
            shortage:
              Number(row.shortage || 0),
            latest_finance_unit_rate:
              row.latest_finance_unit_rate == null
                ? null
                : Number(
                    row.latest_finance_unit_rate,
                  ),
            latest_finance_transaction_id:
              row.latest_finance_transaction_id == null
                ? null
                : Number(
                    row.latest_finance_transaction_id,
                  ),
            latest_finance_purchase_date:
              row.latest_finance_purchase_date
              ?? null,
            status:
              String(
                row.status
                || 'NO_THRESHOLD',
              ),
          }),
        ),
      );

      if (!equipmentResponse.ok) {
        throw new Error(
          equipmentBody?.detail
          || 'Feed equipment list is unavailable.',
        );
      }

      setEquipment(
        Array.isArray(
          equipmentBody?.equipment,
        )
          ? equipmentBody.equipment
          : [],
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to load Feed data.',
      );
    } finally {
      if (!quiet) {
        setLoading(false);
      }
    }
  };


  useEffect(() => {
    void load();

    const timer = window.setInterval(
      () => {
        void load(true);
      },
      60_000,
    );

    return () =>
      window.clearInterval(timer);
  }, []);


  const saveOverride = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();

    if (!selectedOverrideItem) {
      setError(
        'Select a Feed Storage item.',
      );
      return;
    }

    const delta =
      Number(overrideQuantity);

    if (
      !Number.isFinite(delta)
      || delta === 0
    ) {
      setError(
        'Manual override must be a non-zero signed quantity.',
      );
      return;
    }

    setOverrideSaving(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_BASE}/farm/feed-inventory/manual-override`,
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify({
            item:
              selectedOverrideItem.item,
            quantity_delta: delta,
            notes:
              overrideNotes.trim()
              || null,
            recorded_by:
              'UI Operator',
          }),
        },
      );

      const body =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof body?.detail === 'string'
            ? body.detail
            : body?.detail?.error
              || 'Manual stock override failed.',
        );
      }

      setOverrideQuantity('');
      setOverrideNotes('');

      setMessage(
        `Manual physical-stock override recorded for ${selectedOverrideItem.item}.`,
      );

      await load(true);
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Manual stock override failed.',
      );
    } finally {
      setOverrideSaving(false);
    }
  };


  const setEquipmentStatus = async (
    item: FeedEquipment,
    status: string,
  ) => {
    if (
      status !== 'OPERATIONAL'
      && status !== 'NON_OPERATIONAL'
    ) {
      return;
    }

    setEquipmentStatusSaving(
      item.finance_transaction_id,
    );

    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_BASE}/farm/feed-equipment/${item.finance_transaction_id}/status`,
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify({
            status,
            operator: 'UI Operator',
          }),
        },
      );

      const body =
        await response
          .json()
          .catch(() => null);

      if (!response.ok) {
        throw new Error(
          body?.detail
          || 'Equipment status could not be saved.',
        );
      }

      setMessage(
        `${item.equipment_name} status set to ${status === 'OPERATIONAL' ? 'Operational' : 'Non-Operational'}.`,
      );

      await load(true);
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Equipment status could not be saved.',
      );
    } finally {
      setEquipmentStatusSaving(
        null,
      );
    }
  };


  return (
    <div
      style={{
        padding: 12,
        color: '#fff',
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* 1. TMR IS THE PRIMARY FEED OPERATION                           */}
      {/* ------------------------------------------------------------- */}

      <section style={panel}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginBottom: 9,
          }}
        >
          <Wheat
            size={15}
            color="#38bdf8"
          />

          <strong
            style={{
              fontSize: 13,
            }}
          >
            Total Mixed Ration Preparation
          </strong>
        </div>

        <TMRPreparationTool />
      </section>


      {/* ------------------------------------------------------------- */}
      {/* 2. FEED STORAGE STATUS                                        */}
      {/* ------------------------------------------------------------- */}

      <section
        style={{
          ...panel,
          marginTop: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent:
              'space-between',
            gap: 10,
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 900,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Warehouse
                size={15}
                color="#34d399"
              />

              Feed Storage Status
            </div>

            <div
              style={{
                marginTop: 3,
                color: '#94a3b8',
                fontSize: 9,
              }}
            >
              Finance purchases establish stock.
              Governed TMR automatically consumes
              storage according to the active herd.
              Manual override is reserved for
              physical stock corrections.
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              void load()
            }
            style={button('#334155')}
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>


        {error && (
          <div
            style={{
              marginTop: 8,
              padding: 7,
              borderRadius: 5,
              background:
                'rgba(127,29,29,.18)',
              border:
                '1px solid #7f1d1d',
              color: '#fecaca',
              fontSize: 9,
            }}
          >
            {error}
          </div>
        )}


        {message && (
          <div
            style={{
              marginTop: 8,
              padding: 7,
              borderRadius: 5,
              background:
                'rgba(22,101,52,.16)',
              border:
                '1px solid #166534',
              color: '#bbf7d0',
              fontSize: 9,
            }}
          >
            {message}
          </div>
        )}


        <div
          style={{
            marginTop: 8,
            color: '#64748b',
            fontSize: 8,
          }}
        >
          Automatic TMR consumption is reconciled
          by the DairyOS runtime independently of
          this page. Feed Storage refresh is
          read-only. Closed historical consumption
          days remain locked.
        </div>


        <div
          style={{
            overflowX: 'auto',
            marginTop: 9,
          }}
        >
          <table
            style={{
              width: '100%',
              minWidth: 850,
              borderCollapse:
                'collapse',
              fontSize: 9,
            }}
          >
            <thead>
              <tr
                style={{
                  color: '#94a3b8',
                  textAlign: 'left',
                  borderBottom:
                    '1px solid #1f2937',
                }}
              >
                <th style={{ padding: 7 }}>
                  Ingredient
                </th>

                <th
                  style={{
                    padding: 7,
                    textAlign: 'right',
                  }}
                >
                  Finance Purchased
                </th>

                <th
                  style={{
                    padding: 7,
                    textAlign: 'right',
                  }}
                >
                  TMR Consumed
                </th>

                <th
                  style={{
                    padding: 7,
                    textAlign: 'right',
                  }}
                >
                  Manual Override
                </th>

                <th
                  style={{
                    padding: 7,
                    textAlign: 'right',
                  }}
                >
                  Storage Balance
                </th>

                <th
                  style={{
                    padding: 7,
                    textAlign: 'right',
                  }}
                >
                  Finance Rate
                </th>

                <th style={{ padding: 7 }}>
                  Status
                </th>
              </tr>
            </thead>

            <tbody>
              {visibleFeedItems.map(
                item => (
                  <tr
                    key={item.id}
                    style={{
                      borderBottom:
                        '1px solid #1a2234',
                    }}
                  >
                    <td
                      style={{
                        padding: 7,
                        fontWeight: 800,
                      }}
                    >
                      {item.item}

                      {item.latest_finance_transaction_id != null && (
                        <div
                          style={{
                            color: '#64748b',
                            fontSize: 7,
                            marginTop: 2,
                          }}
                        >
                          Finance Tx #
                          {
                            item.latest_finance_transaction_id
                          }
                          {
                            item.latest_finance_purchase_date
                              ? ` · ${item.latest_finance_purchase_date}`
                              : ''
                          }
                        </div>
                      )}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        textAlign: 'right',
                      }}
                    >
                      {quantity(
                        item.purchased_from_finance,
                        item.unit,
                      )}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        textAlign: 'right',
                        color: '#38bdf8',
                      }}
                    >
                      {quantity(
                        item.auto_consumed_from_tmr,
                        item.unit,
                      )}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        textAlign: 'right',
                        color:
                          item.manual_override_net === 0
                            ? '#64748b'
                            : '#fbbf24',
                      }}
                    >
                      {item.manual_override_net > 0
                        ? '+'
                        : ''}
                      {quantity(
                        item.manual_override_net,
                        item.unit,
                      )}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        textAlign: 'right',
                        fontWeight: 900,
                        color:
                          item.shortage > 0
                            ? '#f87171'
                            : '#86efac',
                      }}
                    >
                      {item.shortage > 0
                        ? `SHORT ${quantity(
                            item.shortage,
                            item.unit,
                          )}`
                        : quantity(
                            item.balance,
                            item.unit,
                          )}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        textAlign: 'right',
                      }}
                    >
                      {item.latest_finance_unit_rate == null
                        ? '—'
                        : `${money(
                            item.latest_finance_unit_rate,
                          )} / ${item.unit}`}
                    </td>

                    <td
                      style={{
                        padding: 7,
                        fontWeight: 800,
                        color:
                          item.status === 'SHORTAGE'
                            ? '#f87171'
                            : item.status === 'LOW'
                              ? '#fbbf24'
                              : '#cbd5e1',
                      }}
                    >
                      {item.status.replace(
                        /_/g,
                        ' ',
                      )}
                    </td>
                  </tr>
                ),
              )}

              {!loading
                && visibleFeedItems.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      style={{
                        padding: 12,
                        color: '#64748b',
                        textAlign: 'center',
                      }}
                    >
                      No governed Feed Storage
                      items are currently available.
                    </td>
                  </tr>
                )}
            </tbody>
          </table>
        </div>


        <form
          onSubmit={saveOverride}
          style={{
            marginTop: 10,
            borderTop:
              '1px solid #1f2937',
            paddingTop: 10,
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <SlidersHorizontal
              size={13}
              color="#fbbf24"
            />

            Manual Storage Override
          </div>

          <div
            style={{
              color: '#64748b',
              fontSize: 8,
              marginTop: 3,
            }}
          >
            Use only when the physical stock count
            differs from DairyOS. Positive quantity
            adds stock; negative quantity removes
            stock. This does not record feeding.
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns:
                '1.4fr .8fr 1.6fr auto',
              gap: 7,
              alignItems: 'end',
              marginTop: 8,
            }}
          >
            <label style={label}>
              Feed Item

              <select
                required
                value={overrideItem}
                onChange={event =>
                  setOverrideItem(
                    event.target.value,
                  )
                }
                style={input}
              >
                <option value="">
                  Select item…
                </option>

                {visibleFeedItems.map(
                  item => (
                    <option
                      key={item.id}
                      value={String(
                        item.id,
                      )}
                    >
                      {item.item}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label style={label}>
              Signed Quantity

              <input
                required
                type="number"
                step="0.001"
                value={
                  overrideQuantity
                }
                onChange={event =>
                  setOverrideQuantity(
                    event.target.value,
                  )
                }
                placeholder={
                  selectedOverrideItem
                    ? `± ${selectedOverrideItem.unit}`
                    : '+ / -'
                }
                style={input}
              />
            </label>

            <label style={label}>
              Reason / Notes

              <input
                required
                value={overrideNotes}
                onChange={event =>
                  setOverrideNotes(
                    event.target.value,
                  )
                }
                placeholder="Physical stock correction reason"
                style={input}
              />
            </label>

            <button
              type="submit"
              disabled={
                overrideSaving
                || !selectedOverrideItem
              }
              style={{
                ...button('#d97706'),
                opacity:
                  overrideSaving
                  || !selectedOverrideItem
                    ? 0.5
                    : 1,
              }}
            >
              {overrideSaving
                ? 'Saving…'
                : 'Apply Override'}
            </button>
          </div>
        </form>
      </section>


      {/* ------------------------------------------------------------- */}
      {/* 3. SIMPLE FINANCE-LINKED EQUIPMENT LIST                        */}
      {/* ------------------------------------------------------------- */}

      <section
        style={{
          ...panel,
          marginTop: 10,
        }}
      >
        <div
          style={{
            fontSize: 13,
            fontWeight: 900,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Wrench
            size={15}
            color="#f59e0b"
          />

          Feed-Related Equipment
        </div>

        <div
          style={{
            marginTop: 3,
            color: '#94a3b8',
            fontSize: 9,
          }}
        >
          Equipment purchased in Finance appears
          here automatically. Operational status
          is selected manually only; DairyOS does
          not infer equipment status.
        </div>


        {equipment.length === 0 ? (
          <div
            style={{
              marginTop: 10,
              color: '#64748b',
              fontSize: 10,
            }}
          >
            No Finance Equipment Purchase records
            currently exist.
          </div>
        ) : (
          <div
            style={{
              overflowX: 'auto',
              marginTop: 9,
            }}
          >
            <table
              style={{
                width: '100%',
                minWidth: 720,
                borderCollapse:
                  'collapse',
                fontSize: 9,
              }}
            >
              <thead>
                <tr
                  style={{
                    color: '#94a3b8',
                    textAlign: 'left',
                    borderBottom:
                      '1px solid #1f2937',
                  }}
                >
                  <th style={{ padding: 7 }}>
                    Equipment
                  </th>

                  <th style={{ padding: 7 }}>
                    Purchase Date
                  </th>

                  <th style={{ padding: 7 }}>
                    Supplier
                  </th>

                  <th style={{ padding: 7 }}>
                    Finance Ref
                  </th>

                  <th
                    style={{
                      padding: 7,
                      textAlign: 'right',
                    }}
                  >
                    Amount
                  </th>

                  <th style={{ padding: 7 }}>
                    Manual Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {equipment.map(
                  item => (
                    <tr
                      key={
                        item.finance_transaction_id
                      }
                      style={{
                        borderBottom:
                          '1px solid #1a2234',
                      }}
                    >
                      <td
                        style={{
                          padding: 7,
                          fontWeight: 800,
                        }}
                      >
                        {item.equipment_name}

                        <div
                          style={{
                            color: '#64748b',
                            fontSize: 7,
                            marginTop: 2,
                          }}
                        >
                          Finance Tx #
                          {
                            item.finance_transaction_id
                          }
                        </div>
                      </td>

                      <td style={{ padding: 7 }}>
                        {item.purchase_date
                          || '—'}
                      </td>

                      <td style={{ padding: 7 }}>
                        {item.supplier || '—'}
                      </td>

                      <td style={{ padding: 7 }}>
                        {item.finance_reference
                          || '—'}
                      </td>

                      <td
                        style={{
                          padding: 7,
                          textAlign: 'right',
                          fontWeight: 800,
                        }}
                      >
                        {money(
                          item.amount,
                        )}
                      </td>

                      <td style={{ padding: 7 }}>
                        <select
                          value={item.status}
                          disabled={
                            equipmentStatusSaving
                            === item.finance_transaction_id
                          }
                          onChange={event =>
                            void setEquipmentStatus(
                              item,
                              event.target.value,
                            )
                          }
                          style={{
                            ...input,
                            minWidth: 155,
                          }}
                        >
                          <option value="NOT_SET">
                            Select status…
                          </option>

                          <option value="OPERATIONAL">
                            Operational
                          </option>

                          <option value="NON_OPERATIONAL">
                            Non-Operational
                          </option>
                        </select>

                        {item.status_source === 'MANUAL'
                          && (
                            <div
                              style={{
                                color: '#64748b',
                                fontSize: 7,
                                marginTop: 2,
                              }}
                            >
                              Manual
                              {
                                item.status_operator
                                  ? ` · ${item.status_operator}`
                                  : ''
                              }
                            </div>
                          )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
