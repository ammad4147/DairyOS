import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Check,
  Droplets,
  Milk,
  Trash2,
  X,
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { useFarmDateField } from '../utils/farmDate';

const API_BASE =
  API_BASE_URL || 'http://127.0.0.1:8000';

type HerdAnimal = {
  id: string;
  breed: string;
  category: string;
  frequency?: string;
};

type ProductionRow = {
  id: number;
  animal_id: string;
  production_date: string;
  milking_session?: string | null;
  session_ledger: boolean;
  morning_yield?: number | null;
  afternoon_yield?: number | null;
  evening_yield?: number | null;
  total_yield?: number | null;
  status: string;
  notes?: string | null;
};

type DispositionRow = {
  id: number;
  production_date: string;
  disposition_type: string;
  quantity_litres: number;
  sale_id?: string | null;
  counterparty?: string | null;
  selling_price_per_litre?: number | null;
  amount_due: number;
  amount_received: number;
  receivable_outstanding: number;
  notes?: string | null;
  status: string;
};

type Reconciliation = {
  production_date: string;
  production_complete: boolean;
  produced_litres: number | null;
  accounted_litres: number;
  sold_litres: number;
  non_sale_accounted_litres: number;
  unaccounted_litres: number | null;
  over_accounted_litres: number | null;
  sale_value: number;
  cash_received: number;
  receivable_outstanding: number;
  status: string;
};

type MilkCapacity = {
  recorded_production_litres: number;
  ordinary_accounted_litres: number;
  available_saleable_litres: number;
};

type NextSession = {
  animal_id: string;
  milking_frequency?: string;
  expected_sessions: string[];
  settled_sessions: string[];
  next_session: string | null;
  status: string;
};

type QualitySample = {
  id: number;
  quality_date: string;
  fat_pct: number;
  snf_pct: number;
  sample_type: string;
  notes?: string | null;
  recorded_by: string;
  status: string;
  recorded_at: string;
  updated_at: string;
};

type MissedMilkingItem = {
  finding_id: string | null;
  production_date: string;
  animal_id: string;
  milking_frequency?: string | null;
  expected_sessions: string[];
  recorded_sessions: string[];
  farm_not_milked_sessions: string[];
  missing_sessions: string[];
  schedule_source?: string | null;
  severity: string;
  status: string;
};

type FinanceRow = {
  transaction_type: string;
  category?: string;
  amount: number;
  quantity?: number | null;
  date?: string | null;
  status?: string | null;
};

type InlineDispositionType =
  | 'DOMESTIC_USE'
  | 'CALF_FEED'
  | 'WASTAGE';

type SelectedPanel =
  | 'monthProduced'
  | 'monthSold'
  | 'monthRecon'
  | 'dailyProduced'
  | 'dailySold'
  | 'domestic'
  | 'calves'
  | 'wastage'
  | null;

type Props = {
  initialOpenModal?: boolean;
  onModalClose?: () => void;
  herdMasterList?: HerdAnimal[];
  onSaveYield?: (addedLiters: number) => void;
  onOpenAnimalPassport?: (
    animalId: string,
  ) => void;
  onOperationalChanged?: () =>
    void | Promise<void>;
};

const inputStyle: React.CSSProperties = {
  background: '#1e293b',
  color: '#fff',
  border: '1px solid #334155',
  padding: '7px 8px',
  borderRadius: 5,
  fontSize: 11,
  boxSizing: 'border-box',
  width: '100%',
};

const buttonStyle = (
  background: string,
): React.CSSProperties => ({
  background,
  color: '#fff',
  border: 'none',
  padding: '8px 11px',
  borderRadius: 5,
  fontSize: 10,
  fontWeight: 800,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 5,
});

const smallButton: React.CSSProperties = {
  background: '#1e293b',
  border: '1px solid #334155',
  color: '#cbd5e1',
  padding: '4px 7px',
  borderRadius: 4,
  fontSize: 9,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
};

const pakistanDateFormatter = new Intl.DateTimeFormat(
  'en-CA',
  {
    timeZone: 'Asia/Karachi',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  },
);

const today = () =>
  pakistanDateFormatter.format(new Date());

const currentMonth = () =>
  today().slice(0, 7);

const litre = (
  value: number | null | undefined,
) => `${Number(value || 0).toFixed(1)} L`;

async function request<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE}${url}`,
    {
      headers: {
        'Content-Type':
          'application/json',
      },
      ...init,
    },
  );

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;

    try {
      const body =
        (await response.json()) as {
          detail?: unknown;
        };

      if (body.detail) {
        detail =
          typeof body.detail ===
          'string'
            ? body.detail
            : JSON.stringify(
                body.detail,
              );
      }
    } catch {
      // Keep HTTP status.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

const monthBounds = (
  value: string,
) => {
  const date = new Date(
    `${value}T12:00:00`,
  );

  const start = new Date(
    date.getFullYear(),
    date.getMonth(),
    1,
  );

  const end = new Date(
    date.getFullYear(),
    date.getMonth() + 1,
    0,
  );

  return {
    start: pakistanDateFormatter.format(start),
    end: pakistanDateFormatter.format(end),
    label: start.toLocaleDateString(
      'en-PK',
      {
        month: 'long',
        year: 'numeric',
      },
    ),
  };
};

const datesBetween = (
  start: string,
  end: string,
) => {
  const output: string[] = [];
  const cursor = new Date(
    `${start}T12:00:00`,
  );

  const last = new Date(
    `${end}T12:00:00`,
  );

  while (cursor <= last) {
    output.push(
      pakistanDateFormatter.format(cursor),
    );
    cursor.setDate(
      cursor.getDate() + 1,
    );
  }

  return output;
};

const previousDate = (
  value: string,
) => {
  const day = new Date(
    `${value}T12:00:00Z`,
  );
  day.setUTCDate(
    day.getUTCDate() - 1,
  );
  return day
    .toISOString()
    .slice(0, 10);
};

const monthOptions = () => {
  const current = new Date(
    `${today()}T12:00:00`,
  );

  return Array.from(
    { length: 24 },
    (_, index) => {
      const value = new Date(
        current.getFullYear(),
        current.getMonth() -
          index,
        1,
      );

      return {
        value:
          `${value.getFullYear()}-${String(
            value.getMonth() + 1,
          ).padStart(2, '0')}`,
        label:
          value.toLocaleDateString(
            'en-PK',
            {
              month: 'long',
              year: 'numeric',
            },
          ),
      };
    },
  );
};

export default function MilkTab({
  initialOpenModal = false,
  onModalClose,
  herdMasterList = [],
  onSaveYield,
  onOpenAnimalPassport,
  onOperationalChanged,
}: Props) {
  const [date, setDate] =
    useFarmDateField();

  const [
    selectedMonth,
    setSelectedMonth,
  ] = useState(currentMonth());

  const [
    qualityDate,
    setQualityDate,
  ] = useFarmDateField();

  const automaticMonthRef =
    useRef(currentMonth());

  const [
    monthData,
    setMonthData,
  ] = useState<{
    production: ProductionRow[];
    dispositions: DispositionRow[];
  }>({
    production: [],
    dispositions: [],
  });

  const [
    productions,
    setProductions,
  ] = useState<ProductionRow[]>(
    [],
  );

  const [
    dispositions,
    setDispositions,
  ] = useState<DispositionRow[]>(
    [],
  );

  const [
    reconciliation,
    setReconciliation,
  ] =
    useState<Reconciliation | null>(
      null,
    );

  const [
    dailyRecon,
    setDailyRecon,
  ] = useState<Reconciliation[]>(
    [],
  );

  const [capacity, setCapacity] =
    useState<MilkCapacity | null>(null);

  const [
    openingCapacity,
    setOpeningCapacity,
  ] = useState<MilkCapacity | null>(
    null,
  );

  const [
    dailyCapacity,
    setDailyCapacity,
  ] = useState<MilkCapacity | null>(
    null,
  );

  const [finance, setFinance] =
    useState<FinanceRow[]>([]);

  const [
    qualitySample,
    setQualitySample,
  ] =
    useState<QualitySample | null>(
      null,
    );

  const [
    qualitySamples,
    setQualitySamples,
  ] = useState<QualitySample[]>([]);

  const [qualityFat, setQualityFat] =
    useState('');

  const [qualitySnf, setQualitySnf] =
    useState('');

  const [
    qualitySampleType,
    setQualitySampleType,
  ] =
    useState('BULK_TANK');

  const [
    qualityNotes,
    setQualityNotes,
  ] = useState('');

  const [
    productionAnimal,
    setProductionAnimal,
  ] = useState('');

  const [
    productionLitres,
    setProductionLitres,
  ] = useState('');

  const [
    productionNextSession,
    setProductionNextSession,
  ] =
    useState<NextSession | null>(
      null,
    );

  const [
    todayProductions,
    setTodayProductions,
  ] = useState<ProductionRow[]>([]);

  const [
    productionPickerOpen,
    setProductionPickerOpen,
  ] =
    useState(initialOpenModal);

  const [
    inlineDisposition,
    setInlineDisposition,
  ] =
    useState<InlineDispositionType | null>(
      null,
    );

  const [
    dispositionLitres,
    setDispositionLitres,
  ] = useState('');

  const [
    missedSessions,
    setMissedSessions,
  ] = useState<MissedMilkingItem[]>(
    [],
  );

  const missedInspectionStartedRef =
    useRef(false);

  const [
    lateEntryTarget,
    setLateEntryTarget,
  ] = useState<MissedMilkingItem | null>(
    null,
  );

  const [
    lateEntryLitres,
    setLateEntryLitres,
  ] = useState('');

  const [
    lateEntryNext,
    setLateEntryNext,
  ] = useState<NextSession | null>(
    null,
  );

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [
    qualitySaving,
    setQualitySaving,
  ] = useState(false);

  const [error, setError] =
    useState('');

  const [productionAlert, setProductionAlert] =
    useState('');

  const [message, setMessage] =
    useState('');

  const [
    selectedPanel,
    setSelectedPanel,
  ] =
    useState<SelectedPanel>(null);

  const bounds = useMemo(
    () =>
      monthBounds(
        `${selectedMonth}-01`,
      ),
    [selectedMonth],
  );

  const milkingAnimals = useMemo(
    () =>
      herdMasterList.filter(
        (animal) =>
          animal.category
            .toLowerCase()
            .includes('milking'),
      ),
    [herdMasterList],
  );

  /*
   * Automatically advance the selected
   * Production Month when the calendar
   * enters a new month.
   *
   * A manually selected historical month
   * is not forcibly changed.
   */
  useEffect(() => {
    const syncCurrentMonth =
      () => {
        const liveMonth =
          currentMonth();

        if (
          selectedMonth ===
          automaticMonthRef.current &&
          liveMonth !==
            automaticMonthRef.current
        ) {
          automaticMonthRef.current =
            liveMonth;

          setSelectedMonth(
            liveMonth,
          );
        }
      };

    syncCurrentMonth();

    const timer = window.setInterval(
      syncCurrentMonth,
      60 * 1000,
    );

    return () =>
      window.clearInterval(
        timer,
      );
  }, [selectedMonth]);

  const closeProductionPicker =
    () => {
      setProductionPickerOpen(
        false,
      );

      setProductionAnimal('');
      setProductionLitres('');
      setProductionNextSession(
        null,
      );

      onModalClose?.();
    };

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const [
        day,
        month,
        rec,
        quality,
        financeLedger,
        carriedCapacity,
      ] = await Promise.all([
        request<{
          production: ProductionRow[];
          dispositions: DispositionRow[];
        }>(
          `/farm/milk/ledger?start_date=${date}&end_date=${date}`,
        ),

        request<{
          production: ProductionRow[];
          dispositions: DispositionRow[];
        }>(
          `/farm/milk/ledger?start_date=${bounds.start}&end_date=${bounds.end}`,
        ),

        request<Reconciliation>(
          `/farm/milk/reconciliation?production_date=${date}`,
        ),

        request<{
          sample: QualitySample | null;
        }>(
          `/farm/milk/quality?quality_date=${qualityDate}`,
        ),

        request<{
          transactions: FinanceRow[];
        }>(
          '/farm/finance-ledger',
        ),

        request<MilkCapacity>(
          `/farm/milk/capacity?through_date=${bounds.end > today() ? today() : bounds.end}`,
        ),
      ]);

      setProductions(
        day.production || [],
      );

      setDispositions(
        day.dispositions || [],
      );

      setMonthData({
        production:
          month.production || [],
        dispositions:
          month.dispositions || [],
      });

      setReconciliation(rec);
      setCapacity(carriedCapacity);
      setFinance(
        financeLedger.transactions ||
          [],
      );

      setQualitySample(
        quality.sample || null,
      );

      if (quality.sample) {
        setQualityFat(
          String(
            quality.sample.fat_pct,
          ),
        );

        setQualitySnf(
          String(
            quality.sample.snf_pct,
          ),
        );

        setQualitySampleType(
          quality.sample
            .sample_type,
        );

        setQualityNotes(
          quality.sample.notes ||
            '',
        );
      } else {
        setQualityFat('');
        setQualitySnf('');
        setQualitySampleType(
          'BULK_TANK',
        );
        setQualityNotes('');
      }

      const days = datesBetween(
        bounds.start,
        bounds.end,
      );

      /*
       * Reconciliation is supporting
       * information only. It does not create
       * rows in the monthly display.
       */
      const recs =
        await Promise.all(
          days.map(
            (dayDate) =>
              request<Reconciliation>(
                `/farm/milk/reconciliation?production_date=${dayDate}`,
              ).catch(() =>
                null,
              ),
          ),
        );

      setDailyRecon(
        recs.filter(
          (
            value,
          ): value is Reconciliation =>
            Boolean(value),
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load Milk data.',
      );
    } finally {
      setLoading(false);
    }
  };


  const loadOperationalSupplemental =
    async () => {
      try {
        const openingThrough =
          previousDate(
            bounds.start,
          );

        const [
          qualityHistory,
          openingCarry,
          dailyCarry,
        ] = await Promise.all([
          request<{
            samples: QualitySample[];
          }>(
            '/farm/milk/quality',
          ),
          request<MilkCapacity>(
            `/farm/milk/capacity?through_date=${openingThrough}`,
          ),
          request<MilkCapacity>(
            `/farm/milk/capacity?through_date=${date}`,
          ),
        ]);

        setQualitySamples(
          [
            ...(
              qualityHistory.samples ||
              []
            ),
          ].sort(
            (left, right) =>
              right.quality_date.localeCompare(
                left.quality_date,
              ) ||
              right.id - left.id,
          ),
        );
        setOpeningCapacity(
          openingCarry,
        );
        setDailyCapacity(
          dailyCarry,
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to refresh Milk operational controls.',
        );
      }
    };


  const refreshMissedSessions =
    async () => {
      try {
        const missedControl =
          await request<{
            active: MissedMilkingItem[];
          }>(
            '/farm/milk/missed-sessions?lookback_days=31',
          );

        setMissedSessions(
          missedControl.active || [],
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to refresh missed-milking controls.',
        );
      }
    };

  const refreshAll =
    async () => {
      await load();
      await loadOperationalSupplemental();
    };

  useEffect(() => {
    void refreshAll();
  }, [
    date,
    selectedMonth,
    qualityDate,
  ]);


  useEffect(() => {
    if (missedInspectionStartedRef.current) {
      return;
    }

    missedInspectionStartedRef.current = true;
    void refreshMissedSessions();
  }, []);

  const loadTodayProduction =
    async () => {
      try {
        const operationalDate =
          today();

        const live =
          await request<{
            production: ProductionRow[];
            dispositions: DispositionRow[];
          }>(
            `/farm/milk/ledger?start_date=${operationalDate}&end_date=${operationalDate}`,
          );

        setTodayProductions(
          live.production || [],
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to load today\'s milk-session progress.',
        );
      }
    };

  useEffect(() => {
    if (productionPickerOpen) {
      void loadTodayProduction();
    }
  }, [productionPickerOpen]);

  useEffect(() => {
    if (initialOpenModal) {
      setProductionPickerOpen(
        true,
      );
    }
  }, [initialOpenModal]);

  const monthProductionRows =
    monthData.production.filter(
      (row) =>
        row.status !== 'VOID',
    );

  const monthDispositionRows =
    monthData.dispositions.filter(
      (row) =>
        row.status !== 'VOID',
    );

  const monthProduced =
    monthProductionRows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.total_yield || 0,
        ),
      0,
    );

  const monthSold =
    monthDispositionRows
      .filter(
        (row) =>
          row.disposition_type ===
          'SOLD',
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const dispositionTotal = (
    type: string,
  ) =>
    dispositions
      .filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            type,
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const soldToday =
    dispositionTotal('SOLD');

  const domestic =
    dispositionTotal(
      'DOMESTIC_USE',
    );

  const calves =
    dispositionTotal(
      'CALF_FEED',
    );

  const wastage =
    dispositionTotal(
      'WASTAGE',
    );

  const dailyClosingBalance =
    Number(
      dailyCapacity
        ?.available_saleable_litres ||
        0,
    );

  const monthDomestic =
    monthDispositionRows
      .filter(
        (row) =>
          row.disposition_type ===
          'DOMESTIC_USE',
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const monthCalves =
    monthDispositionRows
      .filter(
        (row) =>
          row.disposition_type ===
          'CALF_FEED',
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const monthWastage =
    monthDispositionRows
      .filter(
        (row) =>
          row.disposition_type ===
          'WASTAGE',
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const monthRecon =
    capacity?.available_saleable_litres ??
    (
      monthProduced -
      monthSold -
      monthDomestic -
      monthCalves -
      monthWastage
    );

  const click = (
    panel: Exclude<
      SelectedPanel,
      null
    >,
  ) => {
    setSelectedPanel(
      selectedPanel === panel
        ? null
        : panel,
    );
  };

  const sessionProgressFor = (
    animal: HerdAnimal,
  ) => {
    const row = todayProductions
      .filter(
        (item) =>
          item.animal_id ===
            animal.id &&
          item.status !== 'VOID',
      )
      .sort(
        (left, right) =>
          right.id - left.id,
      )[0];

    const governedExpected =
      productionAnimal ===
        animal.id &&
      productionNextSession
        ?.expected_sessions
        ?.length
        ? productionNextSession
            .expected_sessions
        : null;

    const frequency =
      String(
        animal.frequency || '',
      ).toUpperCase();

    const expected =
      governedExpected ||
      (
        frequency.includes(
          'TWICE',
        )
          ? [
              'MORNING',
              'EVENING',
            ]
          : [
              'MORNING',
              'AFTERNOON',
              'EVENING',
            ]
      );

    const sessionValue = (
      session: string,
    ): number | null => {
      if (!row) {
        return null;
      }

      if (session === 'MORNING') {
        return row.morning_yield ?? null;
      }

      if (session === 'AFTERNOON') {
        return row.afternoon_yield ?? null;
      }

      if (session === 'EVENING') {
        return row.evening_yield ?? null;
      }

      return null;
    };

    const values =
      expected.map(sessionValue);

    const remaining =
      values.filter(
        (value) => value == null,
      ).length;

    const total =
      values.reduce<number>(
        (sum, value) =>
          sum + Number(value || 0),
        0,
      );

    return {
      expected,
      values,
      total,
      remaining,
      complete:
        expected.length > 0 &&
        remaining === 0,
    };
  };

  const selectProductionAnimal =
    async (
      animalId: string,
    ) => {
      setProductionAnimal(
        animalId,
      );

      setProductionLitres('');
      setProductionNextSession(
        null,
      );
      setError('');

      try {
        const next =
          await request<NextSession>(
            `/farm/milk/next-session?animal_id=${encodeURIComponent(
              animalId,
            )}&operational_date=${today()}`,
          );

        setProductionNextSession(
          next,
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to resolve the next milking session.',
        );
      }
    };

  const saveProduction =
    async (
      event: React.FormEvent,
    ) => {
      event.preventDefault();
      setSaving(true);
      setError('');

      try {
        const litres =
          Number(
            productionLitres,
          );

        const operationalDate =
          today();

        let session =
          productionNextSession?.next_session ||
          productionNextSession?.expected_sessions?.[0] ||
          '';

        if (
          !session &&
          productionAnimal
        ) {
          const next =
            await request<NextSession>(
              `/farm/milk/next-session?animal_id=${encodeURIComponent(
                productionAnimal,
              )}&operational_date=${operationalDate}`,
            );

          setProductionNextSession(
            next,
          );

          session =
            next.next_session ||
            next.expected_sessions?.[0] ||
            '';
        }

        if (
          !(litres > 0) ||
          !productionAnimal ||
          !session
        ) {
          throw new Error(
            'Select a milking animal and enter litres; the next session must be available.',
          );
        }

        const saved = await request<{
          withdrawal_warning?: boolean;
          withdrawal_wastage_litres?: number;
          safety_message?: string;
        }>('/farm/milk', {
          method: 'POST',
          body: JSON.stringify({
            animal_id:
              productionAnimal,
            milking_session:
              session,
            morning_yield:
              session ===
              'MORNING'
                ? litres
                : null,
            afternoon_yield:
              session ===
              'AFTERNOON'
                ? litres
                : null,
            evening_yield:
              session ===
              'EVENING'
                ? litres
                : null,
            production_date:
              operationalDate,
            notes: null,
            operator: 'WEB',
          }),
        });

        onSaveYield?.(litres);

        setMessage(
          saved.withdrawal_warning
            ? (
                saved.safety_message ||
                `Withdrawal active — milk recorded in production and automatically posted to WASTAGE; it is not available for sale.`
              )
            : `Milk production recorded for ${productionAnimal}.`,
        );

        setProductionAnimal('');
        setProductionLitres('');
        setProductionNextSession(
          null,
        );

        await refreshAll();
        await loadTodayProduction();
      } catch (err) {
        const detail = err instanceof Error ? err.message : '';
        if (
          detail.includes('MILKING_SESSION_ALREADY_RECORDED') ||
          detail.toLowerCase().includes('already been recorded') ||
          detail.toLowerCase().includes('next session must be available')
        ) {
          setProductionAlert("TODAY'S MILKING SESSIONS ALREADY RECORDED");
        } else {
          setError(detail || 'Milk production save failed.');
        }
      } finally {
        setSaving(false);
      }
    };

  const openInlineDisposition =
    (
      type: InlineDispositionType,
    ) => {
      setInlineDisposition(
        type,
      );
      setDispositionLitres('');
      setError('');
    };

  const closeInlineDisposition =
    () => {
      setInlineDisposition(null);
      setDispositionLitres('');
    };

  const saveDisposition =
    async (
      event: React.FormEvent,
    ) => {
      event.preventDefault();

      if (!inlineDisposition) {
        return;
      }

      setSaving(true);
      setError('');

      try {
        const litres =
          Number(
            dispositionLitres,
          );

        if (!(litres > 0)) {
          throw new Error(
            'Litres must be greater than zero.',
          );
        }

        await request(
          '/farm/milk/dispositions',
          {
            method: 'POST',
            body: JSON.stringify({
              production_date: date,
              disposition_type:
                inlineDisposition,
              quantity_litres:
                litres,
              sale_id: null,
              counterparty: null,
              selling_price_per_litre:
                null,
              notes: null,
            }),
          },
        );

        const label =
          inlineDisposition ===
          'DOMESTIC_USE'
            ? 'Domestic use'
            : inlineDisposition ===
                'CALF_FEED'
              ? 'Calves feed'
              : 'Wastage';

        setMessage(
          `${label} milk recorded.`,
        );

        closeInlineDisposition();
        await refreshAll();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Milk disposition save failed.',
        );
      } finally {
        setSaving(false);
      }
    };


  const saveQualityLog = () => {
    const header = [
      'Date',
      'Fat %',
      'SNF %',
      'Sample Type',
      'Notes',
      'Recorded By',
      'Status',
      'Recorded At',
    ];

    const rows = qualitySamples.map(
      (sample) => [
        sample.quality_date,
        sample.fat_pct,
        sample.snf_pct,
        sample.sample_type,
        sample.notes || '',
        sample.recorded_by,
        sample.status,
        sample.recorded_at,
      ],
    );

    const csv = [header, ...rows]
      .map((row) =>
        row
          .map(
            (value) =>
              `"${String(value ?? '').replace(/"/g, '""')}"`,
          )
          .join(','),
      )
      .join('\r\n');

    const blob = new Blob(
      [csv],
      {
        type: 'text/csv;charset=utf-8;',
      },
    );
    const url =
      URL.createObjectURL(blob);
    const anchor =
      document.createElement('a');
    anchor.href = url;
    anchor.download =
      'DairyOS-Milk-Quality-Log.csv';
    document.body.appendChild(
      anchor,
    );
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const printQualityLog = () => {
    const popup = window.open(
      '',
      '_blank',
      'width=1000,height=760',
    );

    if (!popup) {
      setError(
        'The Milk Quality print window was blocked. Allow pop-ups for DairyOS and try again.',
      );
      return;
    }

    const esc = (
      value: unknown,
    ) =>
      String(value ?? '').replace(
        /[&<>"']/g,
        (character) =>
          (
            {
              '&': '&amp;',
              '<': '&lt;',
              '>': '&gt;',
              '"': '&quot;',
              "'": '&#39;',
            } as Record<
              string,
              string
            >
          )[character] ||
          character,
      );

    const rows = qualitySamples
      .map(
        (sample) => `
          <tr>
            <td>${esc(sample.quality_date)}</td>
            <td>${esc(sample.fat_pct)}</td>
            <td>${esc(sample.snf_pct)}</td>
            <td>${esc(sample.sample_type)}</td>
            <td>${esc(sample.notes || '')}</td>
            <td>${esc(sample.recorded_by)}</td>
            <td>${esc(sample.status)}</td>
          </tr>
        `,
      )
      .join('');

    popup.document.write(`
      <!doctype html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>DairyOS Milk Quality Log</title>
          <style>
            body{font-family:Arial,sans-serif;color:#111827;padding:24px}
            h1{font-size:18px;margin:0 0 12px}
            table{width:100%;border-collapse:collapse;font-size:11px}
            th,td{border-bottom:1px solid #cbd5e1;padding:7px;text-align:left}
            th{background:#f1f5f9;text-transform:uppercase;font-size:9px}
          </style>
        </head>
        <body>
          <h1>DairyOS — Milk Quality Log</h1>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Fat %</th>
                <th>SNF %</th>
                <th>Sample</th>
                <th>Notes</th>
                <th>Recorded By</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="7">No milk-quality samples recorded.</td></tr>'}
            </tbody>
          </table>
        </body>
      </html>
    `);
    popup.document.close();
    popup.focus();
    window.setTimeout(
      () => popup.print(),
      200,
    );
  };

  const startLateEntry =
    async (
      item: MissedMilkingItem,
    ) => {
      setLateEntryTarget(item);
      setLateEntryLitres('');
      setLateEntryNext(null);
      setError('');

      try {
        const next =
          await request<NextSession>(
            `/farm/milk/next-session?animal_id=${encodeURIComponent(
              item.animal_id,
            )}&operational_date=${item.production_date}`,
          );

        if (!next.next_session) {
          throw new Error(
            'This historical animal-day no longer has an outstanding governed milking session.',
          );
        }

        setLateEntryNext(next);
      } catch (err) {
        setLateEntryTarget(null);
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to resolve the historical missed session.',
        );
      }
    };

  const saveLateEntry =
    async (
      event: React.FormEvent,
    ) => {
      event.preventDefault();

      if (
        !lateEntryTarget ||
        !lateEntryNext?.next_session
      ) {
        return;
      }

      const litres =
        Number(lateEntryLitres);

      if (!(litres > 0)) {
        setError(
          'Historical milk litres must be greater than zero.',
        );
        return;
      }

      setSaving(true);
      setError('');

      try {
        const session =
          lateEntryNext.next_session;

        await request(
          '/farm/milk',
          {
            method: 'POST',
            body: JSON.stringify({
              animal_id:
                lateEntryTarget.animal_id,
              milking_session:
                session,
              morning_yield:
                session ===
                'MORNING'
                  ? litres
                  : null,
              afternoon_yield:
                session ===
                'AFTERNOON'
                  ? litres
                  : null,
              evening_yield:
                session ===
                'EVENING'
                  ? litres
                  : null,
              production_date:
                lateEntryTarget.production_date,
              notes:
                `Late correction for ${lateEntryTarget.finding_id || 'missed milking control'}`,
              operator:
                'WEB_LATE_ENTRY',
            }),
          },
        );

        setMessage(
          `Historical ${session} milk recorded for ${lateEntryTarget.animal_id} on ${lateEntryTarget.production_date}.`,
        );
        setLateEntryTarget(null);
        setLateEntryLitres('');
        setLateEntryNext(null);
        await refreshAll();
        await onOperationalChanged?.();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Historical milk entry failed.',
        );
      } finally {
        setSaving(false);
      }
    };

  const rejectMissedEntry =
    async (
      item: MissedMilkingItem,
    ) => {
      if (!item.finding_id) {
        setError(
          'The missed-session finding has not yet been persisted.',
        );
        return;
      }

      const reason = window.prompt(
        'Reason for closing without a milk quantity. Examples: ANIMAL_NOT_MILKED, MEASUREMENT_UNAVAILABLE, OPERATOR_OVERSIGHT_NO_RECOVERY, HEALTH_REASON, OTHER.',
        '',
      );

      if (
        !reason ||
        !reason.trim()
      ) {
        return;
      }

      try {
        await request(
          `/farm/findings/${encodeURIComponent(
            item.finding_id,
          )}/resolve`,
          {
            method: 'POST',
            body: JSON.stringify({
              operator:
                'UI Operator',
              resolution_note:
                `MISSED_MILK_REJECTED: ${reason.trim()}`,
            }),
          },
        );

        setMessage(
          `Missed milk entry ${item.finding_id} closed with an audited reason. No zero-yield production row was created.`,
        );
        await refreshAll();
        await onOperationalChanged?.();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to close the missed milk entry.',
        );
      }
    };

  const saveQuality =
    async (
      event: React.FormEvent,
    ) => {
      event.preventDefault();
      setQualitySaving(true);
      setError('');

      try {
        const fat =
          Number(qualityFat);

        const snf =
          Number(qualitySnf);

        if (
          !(fat > 0) ||
          !(snf > 0)
        ) {
          throw new Error(
            'Fat % and SNF % must be greater than zero.',
          );
        }

        await request(
          '/farm/milk/quality',
          {
            method: 'POST',
            body: JSON.stringify({
              quality_date:
                qualityDate,
              fat_pct: fat,
              snf_pct: snf,
              sample_type:
                qualitySampleType,
              notes:
                qualityNotes ||
                null,
              recorded_by:
                'UI Operator',
            }),
          },
        );

        setMessage(
          `Milk quality sample saved for ${qualityDate}.`,
        );

        await refreshAll();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Milk quality save failed.',
        );
      } finally {
        setQualitySaving(false);
      }
    };

  const voidProduction =
    async (
      row: ProductionRow,
    ) => {
      if (
        !window.confirm(
          `Void milk production record ${row.id}?`,
        )
      ) {
        return;
      }

      try {
        await request(
          `/farm/milk/production/${row.id}/void`,
          {
            method: 'POST',
            body: JSON.stringify({
              reason:
                'Operator void from Milk register',
            }),
          },
        );

        await refreshAll();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to void production.',
        );
      }
    };

  const voidDisposition =
    async (
      row: DispositionRow,
    ) => {
      if (
        !window.confirm(
          `Void milk disposition ${row.id}?`,
        )
      ) {
        return;
      }

      try {
        await request(
          `/farm/milk/dispositions/${row.id}/void`,
          {
            method: 'POST',
            body: JSON.stringify({
              reason:
                'Operator void from Milk register',
            }),
          },
        );

        await refreshAll();
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to void disposition.',
        );
      }
    };

  const detail = useMemo(() => {
    if (
      selectedPanel ===
      'monthSold'
    ) {
      return monthDispositionRows
        .filter(
          (row) =>
            row.disposition_type ===
            'SOLD',
        )
        .sort((a, b) =>
          a.production_date.localeCompare(
            b.production_date,
          ),
        );
    }

    if (
      selectedPanel ===
      'dailySold'
    ) {
      return dispositions.filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            'SOLD',
      );
    }

    if (
      selectedPanel ===
      'domestic'
    ) {
      return dispositions.filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            'DOMESTIC_USE',
      );
    }

    if (
      selectedPanel ===
      'calves'
    ) {
      return dispositions.filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            'CALF_FEED',
      );
    }

    if (
      selectedPanel ===
      'wastage'
    ) {
      return dispositions.filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            'WASTAGE',
      );
    }

    return [];
  }, [
    selectedPanel,
    monthDispositionRows,
    dispositions,
  ]);

  const titleMap: Record<
    Exclude<
      SelectedPanel,
      null
    >,
    string
  > = {
    monthProduced:
      `Total Milk Production — ${bounds.label}`,
    monthSold:
      `Milk Sold — ${bounds.label}`,
    monthRecon:
      `Overall Reconciliation — ${bounds.label}`,
    dailyProduced:
      `Milk Produced — ${date}`,
    dailySold:
      `Milk Sold — ${date}`,
    domestic:
      `Domestic Use — ${date}`,
    calves:
      `Calves Feed — ${date}`,
    wastage:
      `Wastage / Unusable — ${date}`,
  };

  return (
    <div
      style={{
        padding: 14,
        color: '#fff',
        height: '100%',
        overflowY: 'auto',
        overflowX: 'hidden',
        boxSizing: 'border-box',
        minWidth: 0,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent:
            'space-between',
          alignItems: 'center',
          gap: 10,
          marginBottom: 10,
          flexWrap: 'wrap',
        }}
      >
        <div
          style={{
            flex: '1 1 auto',
            minWidth: 0,
          }}
        >
          <div
            style={{
              fontSize: 18,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 7,
            }}
          >
            <Milk
              size={18}
              color="#38bdf8"
            />
            Milk
          </div>

          <div
            style={{
              fontSize: 10,
              color: '#94a3b8',
            }}
          >
            Farm milk production,
            disposition and
            reconciliation.
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            setError('');
            setMessage('');
            setProductionPickerOpen(true);
          }}
          style={{
            ...buttonStyle('#0284c7'),
            flex: '0 0 auto',
            minHeight: 31,
            whiteSpace: 'nowrap',
            border: '1px solid #38bdf8',
          }}
        >
          <Milk size={12} />
          Enter Milk Production
        </button>

        <label
          style={{
            fontSize: 9,
            color: '#94a3b8',
            minWidth: 155,
          }}
        >
          Production Month

          <select
            value={selectedMonth}
            onChange={(event) => {
              const value =
                event.target.value;

              setSelectedMonth(
                value,
              );
              setSelectedPanel(
                'monthProduced',
              );

              /*
               * The current month is the
               * automatic anchor. Once the
               * operator chooses another month,
               * that choice remains explicit.
               */
              automaticMonthRef.current =
                value === currentMonth()
                  ? value
                  : automaticMonthRef.current;
            }}
            style={{
              ...inputStyle,
              marginTop: 4,
              fontSize: 10,
            }}
          >
            {monthOptions().map(
              (option) => (
                <option
                  key={
                    option.value
                  }
                  value={
                    option.value
                  }
                >
                  {option.label}
                </option>
              ),
            )}
          </select>
        </label>
      </div>

      {error && (
        <div
          style={{
            background:
              'rgba(239,68,68,.12)',
            border:
              '1px solid #ef4444',
            color: '#fecaca',
            padding: 8,
            borderRadius: 6,
            marginBottom: 10,
            fontSize: 10,
          }}
        >
          {error}
        </div>
      )}

      {message && (
        <div
          style={{
            background:
              'rgba(52,211,153,.1)',
            border:
              '1px solid #34d399',
            color: '#bbf7d0',
            padding: 8,
            borderRadius: 6,
            marginBottom: 10,
            fontSize: 10,
            display: 'flex',
            alignItems:
              'center',
            gap: 5,
          }}
        >
          <Check size={12} />
          {message}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(3,minmax(0,1fr))',
          gap: 8,
          marginBottom: 8,
        }}
      >
        <MetricButton
          label={`Total Milk Produced (${bounds.label})`}
          value={litre(
            monthProduced,
          )}
          color="#38bdf8"
          active={
            selectedPanel ===
            'monthProduced'
          }
          onClick={() =>
            click('monthProduced')
          }
        />

        <MetricButton
          label={`Milk Sold (${bounds.label})`}
          value={litre(monthSold)}
          color="#34d399"
          active={
            selectedPanel ===
            'monthSold'
          }
          onClick={() =>
            click('monthSold')
          }
        />

        <MetricButton
          label="Overall Reconciliation / Closing Balance"
          value={litre(
            monthRecon,
          )}
          color="#38bdf8"
          active={
            selectedPanel ===
            'monthRecon'
          }
          onClick={() =>
            click('monthRecon')
          }
        />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(6,minmax(0,1fr))',
          gap: 7,
          marginBottom: 10,
        }}
      >
        <MetricButton
          label="Milk Produced"
          value={litre(
            reconciliation?.produced_litres,
          )}
          color="#38bdf8"
          active={
            selectedPanel ===
            'dailyProduced'
          }
          onClick={() =>
            click(
              'dailyProduced',
            )
          }
          suffix={
            <input
              type="date"
              value={date}
              onChange={(event) => {
                event.stopPropagation();
                setDate(
                  event.target
                    .value,
                );
              }}
              onClick={(event) =>
                event.stopPropagation()
              }
              style={{
                ...inputStyle,
                width: '100%',
                marginTop: 5,
                fontSize: 9,
              }}
            />
          }
        />

        <MetricButton
          label="Milk Sold"
          value={litre(
            soldToday,
          )}
          color="#34d399"
          active={
            selectedPanel ===
            'dailySold'
          }
          onClick={() =>
            click('dailySold')
          }
        />

        <MetricButton
          label="Domestic Use"
          value={litre(domestic)}
          color="#f59e0b"
          active={
            selectedPanel ===
            'domestic'
          }
          onClick={() =>
            click('domestic')
          }
          suffix={
            inlineDisposition ===
            'DOMESTIC_USE' ? (
              <InlineDispositionEditor
                litres={
                  dispositionLitres
                }
                setLitres={
                  setDispositionLitres
                }
                saving={saving}
                onSave={
                  saveDisposition
                }
                onCancel={
                  closeInlineDisposition
                }
                color="#b45309"
              />
            ) : (
              <button
                type="button"
                onClick={(
                  event,
                ) => {
                  event.stopPropagation();
                  openInlineDisposition(
                    'DOMESTIC_USE',
                  );
                }}
                style={{
                  ...buttonStyle(
                    '#b45309',
                  ),
                  width: '100%',
                  marginTop: 5,
                }}
              >
                Enter Milk for Domestic Use
              </button>
            )
          }
        />

        <MetricButton
          label="Calves Feed"
          value={litre(calves)}
          color="#a78bfa"
          active={
            selectedPanel ===
            'calves'
          }
          onClick={() =>
            click('calves')
          }
          suffix={
            inlineDisposition ===
            'CALF_FEED' ? (
              <InlineDispositionEditor
                litres={
                  dispositionLitres
                }
                setLitres={
                  setDispositionLitres
                }
                saving={saving}
                onSave={
                  saveDisposition
                }
                onCancel={
                  closeInlineDisposition
                }
                color="#7c3aed"
              />
            ) : (
              <button
                type="button"
                onClick={(
                  event,
                ) => {
                  event.stopPropagation();
                  openInlineDisposition(
                    'CALF_FEED',
                  );
                }}
                style={{
                  ...buttonStyle(
                    '#7c3aed',
                  ),
                  width: '100%',
                  marginTop: 5,
                }}
              >
                Enter Milk for Calves
              </button>
            )
          }
        />

        <MetricButton
          label="Wastage / Not Usable"
          value={litre(wastage)}
          color="#f87171"
          active={
            selectedPanel ===
            'wastage'
          }
          onClick={() =>
            click('wastage')
          }
          suffix={
            inlineDisposition ===
            'WASTAGE' ? (
              <InlineDispositionEditor
                litres={
                  dispositionLitres
                }
                setLitres={
                  setDispositionLitres
                }
                saving={saving}
                onSave={
                  saveDisposition
                }
                onCancel={
                  closeInlineDisposition
                }
                color="#dc2626"
              />
            ) : (
              <button
                type="button"
                onClick={(
                  event,
                ) => {
                  event.stopPropagation();
                  openInlineDisposition(
                    'WASTAGE',
                  );
                }}
                style={{
                  ...buttonStyle(
                    '#dc2626',
                  ),
                  width: '100%',
                  marginTop: 5,
                }}
              >
                Enter Wastage / Unusable
              </button>
            )
          }
        />

        <MetricButton
          label="Closing Milk Balance"
          value={litre(
            dailyClosingBalance,
          )}
          color="#38bdf8"
          active={false}
        />
      </div>

      {selectedPanel && (
        <section
          style={{
            background: '#111827',
            border:
              '1px solid #1f2937',
            borderRadius: 8,
            padding: 10,
            marginBottom: 10,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent:
                'space-between',
              alignItems: 'center',
              marginBottom: 8,
            }}
          >
            <strong
              style={{
                fontSize: 12,
              }}
            >
              {
                titleMap[
                  selectedPanel
                ]
              }
            </strong>

            <button
              style={smallButton}
              onClick={() =>
                setSelectedPanel(
                  null,
                )
              }
            >
              <X size={11} />
              Close
            </button>
          </div>

          {selectedPanel ===
            'monthProduced' && (
            <FarmMonthlyProductionTable
              production={
                monthData.production
              }
              dispositions={
                monthData.dispositions
              }
            />
          )}

          {selectedPanel ===
            'dailyProduced' && (
            <DailyProductionDetail
              date={date}
              production={
                productions
              }
              dispositions={
                dispositions
              }
              onOpenAnimalPassport={
                onOpenAnimalPassport
              }
            />
          )}

          {selectedPanel ===
            'monthRecon' && (
            <MonthlyOverallReconciliation
              monthData={monthData}
              dailyRecon={
                dailyRecon
              }
              openingBalance={
                Number(
                  openingCapacity
                    ?.available_saleable_litres ||
                    0,
                )
              }
              closingBalance={
                Number(
                  capacity
                    ?.available_saleable_litres ||
                    0,
                )
              }
            />
          )}

          {selectedPanel !==
            'monthProduced' &&
            selectedPanel !==
              'dailyProduced' &&
            selectedPanel !==
              'monthRecon' && (
            <SimpleDispositionTable
              rows={detail}
            />
          )}
        </section>
      )}

      {!selectedPanel && (
        <>
          <section
            style={{
              display: 'block',
            }}
          >
            <div
              style={{
                background:
                  '#111827',
                border:
                  '1px solid #1f2937',
                borderRadius: 8,
                overflow:
                  'hidden',
              }}
            >
              <div
                style={{
                  padding:
                    '9px 11px',
                  borderBottom:
                    '1px solid #1f2937',
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  alignItems:
                    'center',
                }}
              >
                <strong
                  style={{
                    fontSize: 12,
                  }}
                >
                  Daily Milk Register —{' '}
                  {date}
                </strong>

                <span
                  style={{
                    fontSize: 9,
                    color:
                      '#64748b',
                  }}
                >
                  {loading
                    ? 'Loading...'
                    : `${productions.length} production records`}
                </span>
              </div>

              <div
                style={{
                  overflowX:
                    'auto',
                }}
              >
                <table
                  style={{
                    ...tableStyle,
                    minWidth: 0,
                  }}
                >
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Animal ID</th>
                      <th>Sessions Production</th>
                      <th>Total Production</th>
                      <th>
                        Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {[
                      ...productions.map(
                        (row) => ({
                          kind: 'PRODUCTION' as const,
                          id: row.id,
                          date:
                            row.production_date.slice(
                              0,
                              10,
                            ),
                          label:
                            row.animal_id,
                          detail: [row.morning_yield,row.afternoon_yield,row.evening_yield].filter(value=>value!=null).map(value=>litre(value)).join(' + '),
                          qty:
                            row.total_yield,
                          row,
                        }),
                      ),

                      ...dispositions.map(
                        (row) => ({
                          kind: 'DISPOSITION' as const,
                          id: row.id,
                          date:
                            row.production_date.slice(
                              0,
                              10,
                            ),
                          label:
                            row.disposition_type,
                          detail:
                            '',
                          qty:
                            row.quantity_litres,
                          row,
                        }),
                      ),
                    ]
                      .filter((entry) => entry.kind === 'PRODUCTION')
                      .map(
                      (entry) => {
                        const status =
                          entry.row
                            .status;

                        const isVoid =
                          status ===
                          'VOID';

                        return (
                          <tr
                            key={`${entry.kind}-${entry.id}`}
                            style={{
                              textAlign:
                                'center',
                              color:
                                isVoid
                                  ? '#f87171'
                                  : undefined,
                              textDecoration:
                                isVoid
                                  ? 'line-through'
                                  : 'none',
                            }}
                          >
                            <td>
                              {
                                entry.date
                              }
                            </td>

                            <td>
                              {entry.kind === 'PRODUCTION' && onOpenAnimalPassport ? (
                                <button type="button" onClick={() => onOpenAnimalPassport((entry.row as ProductionRow).animal_id)} style={{background:'none',border:0,padding:0,color:'#38bdf8',cursor:'pointer',textDecoration:'underline',fontSize:10,fontWeight:800}}>
                                  {entry.label}
                                </button>
                              ) : (entry.label)}
                            </td>

                            <td>
                              {entry.kind === 'PRODUCTION' ? (entry.detail || 'No individual session figures') : `${entry.label} ${litre(entry.qty)}`}
                            </td>

                            <td>
                              <strong style={{color:entry.kind==='PRODUCTION'?'#38bdf8':'#cbd5e1'}}>{litre(entry.qty)}</strong>
                            </td>

                            <td>
                              {!isVoid && (
                                <button
                                  style={{
                                    ...smallButton,
                                    borderColor:
                                      '#7f1d1d',
                                    color:
                                      '#fecaca',
                                    margin:
                                      '0 auto',
                                  }}
                                  onClick={() =>
                                    entry.kind ===
                                    'PRODUCTION'
                                      ? voidProduction(
                                          entry.row as ProductionRow,
                                        )
                                      : voidDisposition(
                                          entry.row as unknown as DispositionRow,
                                        )
                                  }
                                >
                                  <Trash2
                                    size={
                                      10
                                    }
                                  />
                                  Void
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      },
                    )}

                    {productions.length ===
                      0 && (
                      <tr>
                        <td
                          colSpan={
                            5
                          }
                          style={{
                            padding:
                              14,
                            textAlign:
                              'center',
                            color:
                              '#64748b',
                          }}
                        >
                          No milk records
                          for the
                          selected date.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </section>

          <section
            style={{
              background:
                '#111827',
              border:
                `1px solid ${
                  missedSessions.length
                    ? '#f59e0b'
                    : '#1f2937'
                }`,
              borderRadius: 8,
              padding: 10,
              marginTop: 10,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent:
                  'space-between',
                alignItems:
                  'center',
                gap: 8,
                flexWrap:
                  'wrap',
                marginBottom:
                  missedSessions.length
                    ? 8
                    : 0,
              }}
            >
              <div>
                <strong
                  style={{
                    fontSize: 11,
                    color:
                      missedSessions.length
                        ? '#fbbf24'
                        : '#86efac',
                  }}
                >
                  Missed Milking — Action Required
                </strong>
                <div
                  style={{
                    fontSize: 9,
                    color:
                      '#64748b',
                    marginTop: 2,
                  }}
                >
                  Completed dates only.
                  Enter recovered milk
                  against the original
                  production date, or
                  close the omission with
                  an audited reason.
                </div>
              </div>

              <span
                style={{
                  fontSize: 9,
                  fontWeight: 800,
                  color:
                    missedSessions.length
                      ? '#fbbf24'
                      : '#86efac',
                }}
              >
                {missedSessions.length
                  ? `${missedSessions.length} ACTIVE`
                  : 'NO UNRESOLVED MISSED SESSIONS'}
              </span>
            </div>

            {missedSessions.length >
              0 && (
              <div
                style={{
                  display: 'grid',
                  gap: 6,
                }}
              >
                {missedSessions.map(
                  (item) => {
                    const editing =
                      lateEntryTarget
                        ?.finding_id ===
                        item.finding_id &&
                      lateEntryTarget
                        ?.production_date ===
                        item.production_date &&
                      lateEntryTarget
                        ?.animal_id ===
                        item.animal_id;

                    return (
                      <div
                        key={
                          item.finding_id ||
                          `${item.production_date}-${item.animal_id}`
                        }
                        style={{
                          border:
                            '1px solid #92400e',
                          borderRadius: 6,
                          padding: 8,
                          background:
                            'rgba(146,64,14,.10)',
                        }}
                      >
                        <div
                          style={{
                            display:
                              'grid',
                            gridTemplateColumns:
                              '110px 110px 1fr auto',
                            gap: 8,
                            alignItems:
                              'center',
                          }}
                        >
                          <span
                            style={{
                              color:
                                '#cbd5e1',
                              fontSize:
                                10,
                            }}
                          >
                            {
                              item.production_date
                            }
                          </span>
                          <strong
                            style={{
                              color:
                                '#38bdf8',
                              fontSize:
                                10,
                            }}
                          >
                            {
                              item.animal_id
                            }
                          </strong>
                          <span
                            style={{
                              color:
                                '#fde68a',
                              fontSize:
                                9,
                            }}
                          >
                            Recorded:{' '}
                            {item.recorded_sessions.join(
                              ', ',
                            ) ||
                              'none'}
                            {'  •  '}
                            Missing:{' '}
                            <strong>
                              {item.missing_sessions.join(
                                ', ',
                              )}
                            </strong>
                          </span>
                          <div
                            style={{
                              display:
                                'flex',
                              gap: 5,
                              flexWrap:
                                'wrap',
                            }}
                          >
                            <button
                              type="button"
                              onClick={() =>
                                void startLateEntry(
                                  item,
                                )
                              }
                              style={{
                                ...smallButton,
                                borderColor:
                                  '#0284c7',
                                color:
                                  '#bae6fd',
                              }}
                            >
                              Enter Missing Milk
                            </button>
                            <button
                              type="button"
                              onClick={() =>
                                void rejectMissedEntry(
                                  item,
                                )
                              }
                              style={{
                                ...smallButton,
                                borderColor:
                                  '#7f1d1d',
                                color:
                                  '#fecaca',
                              }}
                            >
                              Reject / Close with Reason
                            </button>
                          </div>
                        </div>

                        {editing && (
                          <form
                            onSubmit={
                              saveLateEntry
                            }
                            style={{
                              display:
                                'flex',
                              alignItems:
                                'center',
                              gap: 6,
                              flexWrap:
                                'wrap',
                              borderTop:
                                '1px solid #78350f',
                              marginTop:
                                7,
                              paddingTop:
                                7,
                            }}
                          >
                            <span
                              style={{
                                fontSize:
                                  9,
                                color:
                                  '#fde68a',
                              }}
                            >
                              Historical entry:{' '}
                              {
                                item.production_date
                              }
                              {'  •  '}
                              {
                                lateEntryNext?.next_session ||
                                item.missing_sessions[0]
                              }
                            </span>
                            <input
                              autoFocus
                              type="number"
                              min="0.001"
                              step="0.001"
                              value={
                                lateEntryLitres
                              }
                              onChange={(
                                event,
                              ) =>
                                setLateEntryLitres(
                                  event
                                    .target
                                    .value,
                                )
                              }
                              style={{
                                ...inputStyle,
                                width:
                                  150,
                              }}
                              placeholder="Quantity (L)"
                              required
                            />
                            <button
                              type="submit"
                              disabled={
                                saving ||
                                !lateEntryNext?.next_session
                              }
                              style={{
                                ...buttonStyle(
                                  '#0284c7',
                                ),
                              }}
                            >
                              {saving
                                ? 'Saving...'
                                : 'Save Historical Entry'}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setLateEntryTarget(
                                  null,
                                );
                                setLateEntryLitres(
                                  '',
                                );
                                setLateEntryNext(
                                  null,
                                );
                              }}
                              style={
                                smallButton
                              }
                            >
                              Cancel
                            </button>
                          </form>
                        )}
                      </div>
                    );
                  },
                )}
              </div>
            )}
          </section>

          <section
            style={{
              background:
                '#111827',
              border:
                '1px solid #1f2937',
              borderRadius: 8,
              padding: 10,
              marginTop: 10,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent:
                  'space-between',
                alignItems:
                  'center',
                marginBottom: 7,
                gap: 8,
                flexWrap:
                  'wrap',
              }}
            >
              <div>
                <div
                  style={{
                    display:
                      'flex',
                    alignItems:
                      'center',
                    gap: 8,
                    flexWrap:
                      'wrap',
                  }}
                >
                  <strong
                    style={{
                      fontSize: 11,
                      color:
                        '#a78bfa',
                    }}
                  >
                    Milk Quality
                  </strong>

                  <label
                    style={{
                      fontSize: 9,
                      color:
                        '#94a3b8',
                    }}
                  >
                    Quality Date

                    <input
                      type="date"
                      value={
                        qualityDate
                      }
                      onChange={(
                        event,
                      ) =>
                        setQualityDate(
                          event
                            .target
                            .value,
                        )
                      }
                      style={{
                        ...inputStyle,
                        width: 150,
                        marginLeft: 5,
                        fontSize: 9,
                      }}
                    />
                  </label>
                </div>

                <div
                  style={{
                    fontSize: 9,
                    color:
                      '#64748b',
                  }}
                >
                  Persisted Fat % and
                  SNF % for the
                  selected date.
                </div>
              </div>

              <span
                style={{
                  fontSize: 9,
                  color:
                    qualitySample
                      ? '#34d399'
                      : '#64748b',
                }}
              >
                {qualitySample
                  ? 'SAVED'
                  : 'NOT RECORDED'}
              </span>
            </div>

            <form
              onSubmit={saveQuality}
            >
              <div
                style={{
                  display:
                    'grid',
                  gridTemplateColumns:
                    'repeat(3,minmax(0,1fr))',
                  gap: 6,
                }}
              >
                <input
                  type="number"
                  min="0.001"
                  max="15"
                  step="0.001"
                  value={
                    qualityFat
                  }
                  onChange={(
                    event,
                  ) =>
                    setQualityFat(
                      event
                        .target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                  placeholder="Fat %"
                  required
                />

                <input
                  type="number"
                  min="0.001"
                  max="15"
                  step="0.001"
                  value={
                    qualitySnf
                  }
                  onChange={(
                    event,
                  ) =>
                    setQualitySnf(
                      event
                        .target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                  placeholder="SNF %"
                  required
                />

                <select
                  value={
                    qualitySampleType
                  }
                  onChange={(
                    event,
                  ) =>
                    setQualitySampleType(
                      event
                        .target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                >
                  <option>
                    BULK_TANK
                  </option>
                  <option>
                    COLLECTION
                  </option>
                  <option>
                    PROCESSOR
                  </option>
                  <option>
                    OTHER
                  </option>
                </select>
              </div>

              <input
                value={
                  qualityNotes
                }
                onChange={(
                  event,
                ) =>
                  setQualityNotes(
                    event
                      .target
                      .value,
                  )
                }
                style={{
                  ...inputStyle,
                  marginTop: 6,
                }}
                placeholder="Quality notes"
              />

              <button
                disabled={
                  qualitySaving
                }
                type="submit"
                style={{
                  ...buttonStyle(
                    '#7c3aed',
                  ),
                  marginTop: 6,
                }}
              >
                {qualitySaving
                  ? 'Saving...'
                  : qualitySample
                    ? 'Update Quality Sample'
                    : 'Save Quality Sample'}
              </button>
            </form>


            <div
              style={{
                marginTop: 12,
                paddingTop: 10,
                borderTop:
                  '1px solid #1f2937',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent:
                    'space-between',
                  alignItems:
                    'center',
                  gap: 8,
                  flexWrap: 'wrap',
                  marginBottom: 7,
                }}
              >
                <div>
                  <strong
                    style={{
                      fontSize: 11,
                      color: '#c4b5fd',
                    }}
                  >
                    Milk Quality Log
                  </strong>
                  <div
                    style={{
                      fontSize: 9,
                      color: '#64748b',
                      marginTop: 2,
                    }}
                  >
                    Persisted quality
                    history. Newest
                    sample first.
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: 6,
                  }}
                >
                  <button
                    type="button"
                    onClick={
                      saveQualityLog
                    }
                    style={
                      smallButton
                    }
                  >
                    Save CSV
                  </button>
                  <button
                    type="button"
                    onClick={
                      printQualityLog
                    }
                    style={
                      smallButton
                    }
                  >
                    Print
                  </button>
                </div>
              </div>

              <div
                style={{
                  overflowX: 'auto',
                }}
              >
                <table
                  style={{
                    ...tableStyle,
                    minWidth: 760,
                  }}
                >
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Fat %</th>
                      <th>SNF %</th>
                      <th>Sample</th>
                      <th>Notes</th>
                      <th>
                        Recorded By
                      </th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {qualitySamples.map(
                      (sample) => (
                        <tr
                          key={
                            sample.id
                          }
                        >
                          <td>
                            {
                              sample.quality_date
                            }
                          </td>
                          <td>
                            {
                              sample.fat_pct
                            }
                          </td>
                          <td>
                            {
                              sample.snf_pct
                            }
                          </td>
                          <td>
                            {
                              sample.sample_type
                            }
                          </td>
                          <td>
                            {sample.notes ||
                              '—'}
                          </td>
                          <td>
                            {
                              sample.recorded_by
                            }
                          </td>
                          <td>
                            {
                              sample.status
                            }
                          </td>
                        </tr>
                      ),
                    )}

                    {qualitySamples.length ===
                      0 && (
                      <tr>
                        <td
                          colSpan={7}
                          style={{
                            padding:
                              14,
                            textAlign:
                              'center',
                            color:
                              '#64748b',
                          }}
                        >
                          No milk
                          quality
                          samples
                          recorded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}

      {productionPickerOpen && (
        <div
          style={{
            position:
              'fixed',
            inset: 0,
            background:
              'rgba(2,6,23,.72)',
            display:
              'flex',
            alignItems:
              'center',
            justifyContent:
              'center',
            padding: 18,
            zIndex: 200,
          }}
        >
          {productionAlert && (
            <div role="alertdialog" aria-modal="true" style={{position:'fixed',inset:0,zIndex:220,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(2,6,23,.78)',padding:18}}>
              <div style={{width:'min(430px,100%)',background:'#111827',border:'1px solid #f59e0b',borderRadius:10,padding:20,textAlign:'center',boxShadow:'0 25px 50px -12px rgba(0,0,0,.8)'}}>
                <div style={{fontSize:14,fontWeight:900,color:'#f8fafc'}}>{productionAlert}</div>
                <button type="button" autoFocus onClick={()=>setProductionAlert('')} style={{...buttonStyle('#0284c7'),marginTop:16,minWidth:90}}>OK</button>
              </div>
            </div>
          )}
          <div
            style={{
              width:
                'min(760px, 100%)',
              maxHeight:
                '80vh',
              overflowY:
                'auto',
              background:
                '#0f172a',
              border:
                '1px solid #334155',
              borderRadius:
                10,
              boxShadow:
                '0 25px 50px -12px rgba(0,0,0,.75)',
            }}
          >
            <div
              style={{
                padding: 12,
                borderBottom:
                  '1px solid #1f2937',
                display:
                  'flex',
                alignItems:
                  'center',
                justifyContent:
                  'space-between',
                gap: 8,
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 900,
                    color:
                      '#fff',
                  }}
                >
                  Enter Milk Production
                </div>

                <div
                  style={{
                    fontSize: 9,
                    color:
                      '#94a3b8',
                  }}
                >
                  Select a milking
                  animal. Session
                  and date/time are
                  resolved automatically.
                </div>
              </div>

              <button
                style={
                  smallButton
                }
                onClick={
                  closeProductionPicker
                }
              >
                <X size={12} />
                Close
              </button>
            </div>

            <div
              style={{
                padding: 10,
                display:
                  'grid',
                gap: 6,
              }}
            >
              {milkingAnimals.length ===
              0 ? (
                <div
                  style={{
                    padding:
                      14,
                    color:
                      '#94a3b8',
                    fontSize:
                      10,
                    textAlign:
                      'center',
                  }}
                >
                  No milking
                  animals are
                  currently
                  available.
                </div>
              ) : (
                [...milkingAnimals]
                  .sort((left, right) => {
                    const leftComplete =
                      sessionProgressFor(left).complete;
                    const rightComplete =
                      sessionProgressFor(right).complete;

                    return Number(leftComplete) -
                      Number(rightComplete);
                  })
                  .map(
                  (animal) => {
                    const selected =
                      productionAnimal ===
                      animal.id;

                    const progress =
                      sessionProgressFor(
                        animal,
                      );

                    return (
                      <div
                        key={
                          animal.id
                        }
                        style={{
                          background:
                            progress.complete
                              ? 'rgba(22,101,52,.30)'
                              : selected
                                ? 'rgba(146,64,14,.24)'
                                : 'rgba(146,64,14,.12)',
                          border:
                            `1px solid ${
                              progress.complete
                                ? '#22c55e'
                                : selected
                                  ? '#f59e0b'
                                  : '#92400e'
                            }`,
                          borderRadius:
                            7,
                        }}
                      >
                        <button
                          type="button"
                          disabled={
                            progress.complete
                          }
                          onClick={() => {
                            if (
                              progress.complete
                            ) {
                              return;
                            }

                            void selectProductionAnimal(
                              animal.id,
                            );
                          }}
                          style={{
                            width:
                              '100%',
                            background:
                              'transparent',
                            border: 0,
                            color:
                              '#fff',
                            padding:
                              '9px 10px',
                            display:
                              'grid',
                            gridTemplateColumns:
                              '1fr 1.35fr .7fr 2.2fr auto',
                            gap: 8,
                            alignItems:
                              'center',
                            textAlign:
                              'left',
                            cursor:
                              progress.complete
                                ? 'not-allowed'
                                : 'pointer',
                            opacity:
                              progress.complete
                                ? 0.92
                                : 1,
                            fontFamily:
                              'inherit',
                          }}
                        >
                          <span
                            style={{
                              color:
                                '#38bdf8',
                              fontWeight:
                                800,
                              fontSize:
                                10,
                            }}
                          >
                            {
                              animal.id
                            }
                          </span>

                          <span
                            style={{
                              fontSize:
                                10,
                            }}
                          >
                            {
                              animal.category
                            }
                            {' / '}
                            {animal.breed ||
                              'Unknown'}
                          </span>

                          <span
                            style={{
                              color:
                                '#cbd5e1',
                              fontSize:
                                10,
                            }}
                          >
                            {animal.frequency ||
                              'AUTO'}
                          </span>

                          <span
                            title={
                              progress.expected
                                .map(
                                  (
                                    session,
                                    index,
                                  ) =>
                                    `${session}: ${
                                      progress.values[index] == null
                                        ? 'not recorded'
                                        : litre(progress.values[index])
                                    }`,
                                )
                                .join(' | ')
                            }
                            style={{
                              color:
                                progress.complete
                                  ? '#bbf7d0'
                                  : '#fde68a',
                              fontSize: 9,
                              fontWeight: 700,
                              minWidth: 0,
                            }}
                          >
                            <span
                              style={{
                                display: 'block',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {progress.values
                                .map(
                                  (value) =>
                                    value == null
                                      ? '□'
                                      : litre(value),
                                )
                                .join(' + ')}
                            </span>
                            <span
                              style={{
                                display: 'block',
                                marginTop: 1,
                                fontSize: 8,
                              }}
                            >
                              {progress.complete
                                ? `✓ Complete   Total: ${litre(progress.total)}`
                                : `● ${progress.remaining} session${
                                    progress.remaining === 1 ? '' : 's'
                                  } remaining   Total: ${litre(progress.total)}`}
                            </span>
                          </span>

                          <span
                            style={{
                              color:
                                progress.complete
                                  ? '#86efac'
                                  : selected
                                    ? '#fbbf24'
                                    : '#fde68a',
                              fontSize: 9,
                              fontWeight: 800,
                            }}
                          >
                            {progress.complete
                              ? 'Locked'
                              : selected
                                ? 'Selected'
                                : 'Enter'}
                          </span>
                        </button>

                        {selected &&
                          !progress.complete && (
                          <form
                            onSubmit={
                              saveProduction
                            }
                            style={{
                              borderTop:
                                '1px solid #1f2937',
                              padding:
                                8,
                              display:
                                'flex',
                              alignItems:
                                'center',
                              gap: 6,
                              flexWrap:
                                'wrap',
                            }}
                          >
                            <div
                              style={{
                                flex: '1 0 100%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                gap: 8,
                                background: 'rgba(245,158,11,.10)',
                                border: '1px solid #92400e',
                                borderRadius: 5,
                                padding: '5px 7px',
                                color: '#fde68a',
                                fontSize: 9,
                              }}
                            >
                              <span>
                                {progress.expected
                                  .map(
                                    (session, index) =>
                                      `${session} ${
                                        progress.values[index] == null
                                          ? '□'
                                          : `✓ ${litre(progress.values[index])}`
                                      }`,
                                  )
                                  .join('  •  ')}
                              </span>
                              <strong>
                                {`● ${progress.remaining} session${
                                  progress.remaining === 1 ? '' : 's'
                                } remaining   Total: ${litre(progress.total)}`}
                              </strong>
                            </div>

                            <input
                              autoFocus
                              type="number"
                              min="0.001"
                              step="0.001"
                              value={
                                productionLitres
                              }
                              onChange={(
                                event,
                              ) =>
                                setProductionLitres(
                                  event
                                    .target
                                    .value,
                                )
                              }
                              style={{
                                ...inputStyle,
                                width: 150,
                              }}
                              placeholder="Quantity (L)"
                              required
                            />

                            <button
                              disabled={
                                saving
                              }
                              type="submit"
                              style={{
                                ...buttonStyle(
                                  '#0284c7',
                                ),
                                minWidth:
                                  74,
                              }}
                            >
                              {saving
                                ? 'Saving...'
                                : 'Save'}
                            </button>

                            <button
                              type="button"
                              onClick={(
                                event,
                              ) => {
                                event.stopPropagation();
                                setProductionAnimal(
                                  '',
                                );
                                setProductionLitres(
                                  '',
                                );
                                setProductionNextSession(
                                  null,
                                );
                              }}
                              style={{
                                ...smallButton,
                                marginLeft:
                                  'auto',
                              }}
                            >
                              <X size={11} />
                              Cancel
                            </button>
                          </form>
                        )}
                      </div>
                    );
                  },
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FarmMonthlyProductionTable({
  production,
  dispositions,
}: {
  production: ProductionRow[];
  dispositions: DispositionRow[];
}) {
  const dates = Array.from(
    new Set([
      ...production
        .filter(
          (row) =>
            row.status !==
            'VOID',
        )
        .map((row) =>
          row.production_date.slice(
            0,
            10,
          ),
        ),
      ...dispositions
        .filter(
          (row) =>
            row.status !==
            'VOID',
        )
        .map((row) =>
          row.production_date.slice(
            0,
            10,
          ),
        ),
    ]),
  ).sort();

  return (
    <div
      style={{
        overflowX: 'auto',
      }}
    >
      <table
        style={tableStyle}
      >
        <thead>
          <tr>
            <th>Date</th>
            <th>
              Milk Produced
            </th>
            <th>
              Calves Feed
            </th>
            <th>
              Domestic Use
            </th>
            <th>
              Wastage/Unusable
            </th>
            <th>
              Sold
            </th>
          </tr>
        </thead>

        <tbody>
          {dates.map(
            (day) => {
              const produced =
                production
                  .filter(
                    (row) =>
                      row.status !==
                        'VOID' &&
                      row.production_date.slice(
                        0,
                        10,
                      ) === day,
                  )
                  .reduce(
                    (sum, row) =>
                      sum +
                      Number(
                        row.total_yield ||
                          0,
                      ),
                    0,
                  );

              const amount =
                (
                  type: string,
                ) =>
                  dispositions
                    .filter(
                      (row) =>
                        row.status !==
                          'VOID' &&
                        row.production_date.slice(
                          0,
                          10,
                        ) === day &&
                        row.disposition_type ===
                          type,
                    )
                    .reduce(
                      (sum, row) =>
                        sum +
                        Number(
                          row.quantity_litres ||
                            0,
                        ),
                      0,
                    );

              return (
                <tr
                  key={day}
                >
                  <td>{day}</td>
                  <td>
                    {litre(
                      produced,
                    )}
                  </td>
                  <td>
                    {litre(
                      amount(
                        'CALF_FEED',
                      ),
                    )}
                  </td>
                  <td>
                    {litre(
                      amount(
                        'DOMESTIC_USE',
                      ),
                    )}
                  </td>
                  <td>
                    {litre(
                      amount(
                        'WASTAGE',
                      ),
                    )}
                  </td>
                  <td>
                    {litre(
                      amount(
                        'SOLD',
                      ),
                    )}
                  </td>
                </tr>
              );
            },
          )}

          {dates.length ===
            0 && (
            <tr>
              <td
                colSpan={6}
                style={{
                  padding: 14,
                }}
              >
                No actual milk
                production or
                disposition entries
                exist for the
                selected month.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function DailyProductionDetail({
  date,
  production,
  dispositions,
  onOpenAnimalPassport,
}: {
  date: string;
  production: ProductionRow[];
  dispositions: DispositionRow[];
  onOpenAnimalPassport?: (
    animalId: string,
  ) => void;
}) {
  const produced =
    production
      .filter(
        (row) =>
          row.status !==
          'VOID',
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.total_yield ||
              0,
          ),
        0,
      );

  const dispositionAmount = (
    type: string,
  ) =>
    dispositions
      .filter(
        (row) =>
          row.status !==
            'VOID' &&
          row.disposition_type ===
            type,
      )
      .reduce(
        (sum, row) =>
          sum +
          Number(
            row.quantity_litres ||
              0,
          ),
        0,
      );

  const animalTotals =
    Array.from(
      production
        .filter(
          (row) =>
            row.status !==
            'VOID',
        )
        .reduce(
          (map, row) => {
            const current = map.get(row.animal_id) || {morning:0,afternoon:0,evening:0,total:0};
            map.set(row.animal_id, {
              morning: current.morning + Number(row.morning_yield || 0),
              afternoon: current.afternoon + Number(row.afternoon_yield || 0),
              evening: current.evening + Number(row.evening_yield || 0),
              total: current.total + Number(row.total_yield || 0),
            });

            return map;
          },
          new Map<
            string,
            {morning:number;afternoon:number;evening:number;total:number}
          >(),
        ),
    ).sort(
      ([a], [b]) =>
        a.localeCompare(b),
    );

  return (
    <div
      style={{
        display: 'grid',
        gap: 12,
      }}
    >
      <div>
        <div
          style={{
            fontSize: 10,
            color: '#94a3b8',
            fontWeight: 800,
            marginBottom: 6,
          }}
        >
          Farm Production &
          Disposition — {date}
        </div>

        <div
          style={{
            overflowX:
              'auto',
          }}
        >
          <table
            style={tableStyle}
          >
            <thead>
              <tr>
                <th>Date</th>
                <th>
                  Milk Produced
                </th>
                <th>
                  Calves Feed
                </th>
                <th>
                  Domestic Use
                </th>
                <th>
                  Wastage/Unusable
                </th>
                <th>
                  Sold
                </th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>{date}</td>
                <td>
                  {litre(
                    produced,
                  )}
                </td>
                <td>
                  {litre(
                    dispositionAmount(
                      'CALF_FEED',
                    ),
                  )}
                </td>
                <td>
                  {litre(
                    dispositionAmount(
                      'DOMESTIC_USE',
                    ),
                  )}
                </td>
                <td>
                  {litre(
                    dispositionAmount(
                      'WASTAGE',
                    ),
                  )}
                </td>
                <td>
                  {litre(
                    dispositionAmount(
                      'SOLD',
                    ),
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div
          style={{
            fontSize: 10,
            color: '#94a3b8',
            fontWeight: 800,
            marginBottom: 6,
          }}
        >
          Daily Milk Register —{' '}
          {date}
        </div>

        <div
          style={{
            overflowX:
              'auto',
          }}
        >
          <table
            style={tableStyle}
          >
            <thead>
              <tr>
                <th>Animal ID</th>
                <th>Sessions Production</th>
                <th>Total Production</th>
              </tr>
            </thead>

            <tbody>
              {animalTotals.map(
                ([
                  animalId,
                  totals,
                ]) => (
                  <tr
                    key={
                      animalId
                    }
                  >
                    <td>
                      {onOpenAnimalPassport ? (
                        <button
                          type="button"
                          onClick={() =>
                            onOpenAnimalPassport(
                              animalId,
                            )
                          }
                          style={{
                            background:
                              'none',
                            border: 0,
                            padding: 0,
                            color:
                              '#38bdf8',
                            cursor:
                              'pointer',
                            textDecoration:
                              'underline',
                            fontSize:
                              10,
                            fontWeight:
                              800,
                          }}
                        >
                          {
                            animalId
                          }
                        </button>
                      ) : (
                        <span
                          style={{
                            color:
                              '#38bdf8',
                            fontWeight:
                              800,
                          }}
                        >
                          {
                            animalId
                          }
                        </span>
                      )}
                    </td>

                    <td>{[totals.morning,totals.afternoon,totals.evening].filter(value=>value>0).map(value=>litre(value)).join(' + ') || 'No individual session figures'}</td>
                    <td><strong style={{color:'#38bdf8'}}>{litre(totals.total)}</strong></td>
                  </tr>
                ),
              )}

              {animalTotals.length ===
                0 && (
                <tr>
                  <td
                    colSpan={
                      3
                    }
                    style={{
                      padding:
                        14,
                    }}
                  >
                    No animal milk
                    production
                    recorded for
                    this date.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MonthlyOverallReconciliation({
  monthData,
  dailyRecon,
  openingBalance,
  closingBalance,
}: {
  monthData: {
    production: ProductionRow[];
    dispositions: DispositionRow[];
  };
  dailyRecon: Reconciliation[];
  openingBalance: number;
  closingBalance: number;
}) {
  const dates = Array.from(
    new Set([
      ...monthData.production
        .filter(
          (row) =>
            row.status !==
            'VOID',
        )
        .map((row) =>
          row.production_date.slice(
            0,
            10,
          ),
        ),
      ...monthData.dispositions
        .filter(
          (row) =>
            row.status !==
            'VOID',
        )
        .map((row) =>
          row.production_date.slice(
            0,
            10,
          ),
        ),
    ]),
  ).sort();

  const reconByDate =
    new Map(
      dailyRecon.map(
        (row) => [
          row.production_date,
          row,
        ],
      ),
    );

  let runningBalance =
    Number(openingBalance || 0);
  let totalProduced = 0;
  let totalSold = 0;
  let totalDomestic = 0;
  let totalCalves = 0;
  let totalWastage = 0;
  let totalOther = 0;

  const rows = dates.map(
    (day) => {
      const produced =
        monthData.production
          .filter(
            (row) =>
              row.status !==
                'VOID' &&
              row.production_date.slice(
                0,
                10,
              ) === day,
          )
          .reduce(
            (sum, row) =>
              sum +
              Number(
                row.total_yield ||
                  0,
              ),
            0,
          );

      const amount =
        (
          type: string,
        ) =>
          monthData.dispositions
            .filter(
              (row) =>
                row.status !==
                  'VOID' &&
                row.production_date.slice(
                  0,
                  10,
                ) === day &&
                row.disposition_type ===
                  type,
            )
            .reduce(
              (sum, row) =>
                sum +
                Number(
                  row.quantity_litres ||
                    0,
                ),
              0,
            );

      const sold =
        amount('SOLD');
      const domestic =
        amount('DOMESTIC_USE');
      const calves =
        amount('CALF_FEED');
      const wastage =
        amount('WASTAGE');

      const other =
        monthData.dispositions
          .filter(
            (row) =>
              row.status !==
                'VOID' &&
              row.production_date.slice(
                0,
                10,
              ) === day &&
              ![
                'SOLD',
                'DOMESTIC_USE',
                'CALF_FEED',
                'WASTAGE',
              ].includes(
                row.disposition_type,
              ),
          )
          .reduce(
            (sum, row) =>
              sum +
              Number(
                row.quantity_litres ||
                  0,
              ),
            0,
          );

      const dayOpening =
        runningBalance;
      const rawClosing =
        dayOpening +
        produced -
        sold -
        domestic -
        calves -
        wastage -
        other;

      runningBalance =
        Math.max(
          rawClosing,
          0,
        );

      totalProduced += produced;
      totalSold += sold;
      totalDomestic += domestic;
      totalCalves += calves;
      totalWastage += wastage;
      totalOther += other;

      const persisted =
        reconByDate.get(day);

      return {
        day,
        opening: dayOpening,
        produced,
        sold,
        domestic,
        calves,
        wastage,
        other,
        closing: runningBalance,
        inventoryStatus:
          rawClosing < -0.01
            ? 'UNBACKED DISPOSITION'
            : 'BALANCED',
        productionStatus:
          persisted?.production_complete
            ? 'COMPLETE'
            : 'INCOMPLETE',
      };
    },
  );

  return (
    <div
      style={{
        display: 'grid',
        gap: 10,
      }}
    >
      <div
        style={{
          fontSize: 9,
          color: '#64748b',
        }}
      >
        Physical milk inventory authority:
        opening balance + production −
        all governed dispositions =
        closing balance. Production
        completeness is shown separately
        and is not treated as milk
        inventory.
      </div>

      <div
        style={{
          overflowX:
            'auto',
        }}
      >
        <table
          style={tableStyle}
        >
          <thead>
            <tr>
              <th>Date</th>
              <th>
                Opening Milk Balance
              </th>
              <th>
                Milk Produced
              </th>
              <th>
                Milk Sold
              </th>
              <th>
                Domestic Use
              </th>
              <th>
                Calves Feed
              </th>
              <th>
                Wastage/Unusable
              </th>
              <th>
                Other
              </th>
              <th>
                Closing Milk Balance
              </th>
              <th>
                Production Control
              </th>
            </tr>
          </thead>

          <tbody>
            {rows.map(
              (row) => (
                <tr
                  key={row.day}
                >
                  <td>{row.day}</td>
                  <td>
                    {litre(
                      row.opening,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.produced,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.sold,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.domestic,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.calves,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.wastage,
                    )}
                  </td>
                  <td>
                    {litre(
                      row.other,
                    )}
                  </td>
                  <td>
                    <strong
                      style={{
                        color:
                          row.inventoryStatus ===
                          'BALANCED'
                            ? '#34d399'
                            : '#f87171',
                      }}
                    >
                      {litre(
                        row.closing,
                      )}
                    </strong>
                  </td>
                  <td>
                    <span
                      style={{
                        color:
                          row.productionStatus ===
                          'COMPLETE'
                            ? '#34d399'
                            : '#f59e0b',
                        fontWeight: 800,
                      }}
                    >
                      {
                        row.productionStatus
                      }
                    </span>
                  </td>
                </tr>
              ),
            )}

            {rows.length ===
              0 && (
              <tr>
                <td
                  colSpan={
                    10
                  }
                  style={{
                    padding:
                      14,
                  }}
                >
                  No actual
                  production or
                  disposition
                  entries exist
                  for the selected
                  month.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div
        style={{
          overflowX:
            'auto',
        }}
      >
        <table
          style={tableStyle}
        >
          <thead>
            <tr>
              <th>
                Overall Monthly
                Totals
              </th>
              <th>
                Opening Milk Balance
              </th>
              <th>
                Milk Produced
              </th>
              <th>
                Milk Sold
              </th>
              <th>
                Domestic Use
              </th>
              <th>
                Calves Feed
              </th>
              <th>
                Wastage/Unusable
              </th>
              <th>
                Other
              </th>
              <th>
                Closing Milk Balance
              </th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td>
                Selected Month
              </td>
              <td>
                {litre(
                  openingBalance,
                )}
              </td>
              <td>
                {litre(
                  totalProduced,
                )}
              </td>
              <td>
                {litre(
                  totalSold,
                )}
              </td>
              <td>
                {litre(
                  totalDomestic,
                )}
              </td>
              <td>
                {litre(
                  totalCalves,
                )}
              </td>
              <td>
                {litre(
                  totalWastage,
                )}
              </td>
              <td>
                {litre(
                  totalOther,
                )}
              </td>
              <td>
                <strong
                  style={{
                    color:
                      '#38bdf8',
                  }}
                >
                  {litre(
                    closingBalance,
                  )}
                </strong>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SimpleDispositionTable({
  rows,
}: {
  rows: DispositionRow[];
}) {
  return (
    <div
      style={{
        overflowX:
          'auto',
      }}
    >
      <table
        style={{
          ...tableStyle,
          minWidth: 320,
        }}
      >
        <thead>
          <tr>
            <th>Date</th>
            <th>Litres</th>
          </tr>
        </thead>

        <tbody>
          {rows.map(
            (row) => (
              <tr
                key={row.id}
              >
                <td>
                  {row.production_date.slice(
                    0,
                    10,
                  )}
                </td>
                <td>
                  {litre(
                    row.quantity_litres,
                  )}
                </td>
              </tr>
            ),
          )}

          {rows.length ===
            0 && (
            <tr>
              <td
                colSpan={2}
                style={{
                  padding:
                    14,
                }}
              >
                No actual records
                for this selection.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function InlineDispositionEditor({
  litres,
  setLitres,
  saving,
  onSave,
  onCancel,
  color,
}: {
  litres: string;
  setLitres: (
    value: string,
  ) => void;
  saving: boolean;
  onSave: (
    event: React.FormEvent,
  ) => void;
  onCancel: () => void;
  color: string;
}) {
  return (
    <form
      onSubmit={onSave}
      onClick={(event) =>
        event.stopPropagation()
      }
      style={{
        display: 'grid',
        gridTemplateColumns:
          '1fr auto auto',
        gap: 4,
        marginTop: 5,
      }}
    >
      <input
        autoFocus
        type="number"
        min="0.001"
        step="0.001"
        value={litres}
        onChange={(event) =>
          setLitres(
            event.target.value,
          )
        }
        style={{
          ...inputStyle,
          fontSize: 10,
          padding:
            '6px 7px',
        }}
        placeholder="Litres"
        required
      />

      <button
        disabled={saving}
        type="submit"
        style={{
          ...buttonStyle(
            color,
          ),
          padding:
            '6px 8px',
          fontSize: 9,
        }}
      >
        {saving
          ? '...'
          : 'Save'}
      </button>

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onCancel();
        }}
        style={{
          ...smallButton,
          padding:
            '5px 6px',
        }}
      >
        <X size={10} />
      </button>
    </form>
  );
}

function MetricButton({
  label,
  value,
  color,
  active = false,
  onClick,
  suffix,
}: {
  label: string;
  value: string;
  color: string;
  active?: boolean;
  onClick?: () => void;
  suffix?: React.ReactNode;
}) {
  const clickable =
    typeof onClick ===
    'function';

  return (
    <div
      onClick={
        clickable
          ? onClick
          : undefined
      }
      role={
        clickable
          ? 'button'
          : undefined
      }
      tabIndex={
        clickable
          ? 0
          : undefined
      }
      onKeyDown={
        clickable
          ? (event) => {
              if (
                event.key ===
                  'Enter' ||
                event.key ===
                  ' '
              ) {
                event.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
      style={{
        textAlign:
          'left',
        background:
          active
            ? '#16253a'
            : '#111827',
        border:
          `1px solid ${
            active
              ? color
              : '#1f2937'
          }`,
        borderLeft:
          `4px solid ${color}`,
        borderRadius: 7,
        padding:
          '9px 10px',
        color: '#fff',
        cursor:
          clickable
            ? 'pointer'
            : 'default',
        minWidth: 0,
        fontFamily:
          'inherit',
      }}
    >
      <div
        style={{
          fontSize: 8,
          color:
            '#94a3b8',
          textTransform:
            'uppercase',
          fontWeight: 800,
          lineHeight:
            1.25,
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: 15,
          fontWeight: 900,
          color,
          marginTop: 3,
        }}
      >
        {value}
      </div>

      {suffix}
    </div>
  );
}

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse:
    'collapse',
  fontSize: 10,
  textAlign:
    'center',
};
