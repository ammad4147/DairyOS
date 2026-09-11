import { API_BASE_URL } from "../config/api";
import { farmToday, shiftFarmDate } from '../utils/farmDate';

export interface PerformerItem {
  id: string;
  yield: number;
}

export interface HerdCategory {
  name: string;
  value: number;
  color?: string;
}

export interface HerdMetrics {
  wetAverageYieldPercentage: number | null;
  dryAverageYieldPercentage: number | null;
}

export interface DashboardSickAnimal {
  animalId: string;
  diagnosis: string;
  severity: string;
  openedAt: string;
  followUpDueAt: string;
}

export interface DashboardVaccinationDue {
  animalId: string;
  vaccine: string;
  administeredDate: string;
  nextDueDate: string;
  dueState: 'OVERDUE' | 'DUE_TODAY' | 'SCHEDULED' | string;
}

export interface CommandDashboardData {
  todayLiters: number;
  yesterdayLiters: number;
  todayDate: string;
  yesterdayDate: string;
  milkingAnimals: number;
  adultAnimals: number;
  milkingPercentage: number;
  averageYieldPerCow: number | null;
  herdComposition: HerdCategory[];
  herdMetrics: HerdMetrics;
  topPerformers: PerformerItem[];
  bottomPerformers: PerformerItem[];
  yieldTrend: Array<{ day: string; yield: number | null }>;
  productionExtremes: {
    highest: PerformerItem[];
    lowest: PerformerItem[];
  };
  yieldDropWatchlist: any[];
  productionDrop: {
    production_date?: string;
    drop_percentage?: number;
    variance_percentage?: number | null;
    severity?: string | null;
    alert_color?: string | null;
    prior_total_litres?: number | null;
    current_total_litres?: number | null;
  } | null;
  health: {
    sick: number;
    mastitis: number;
    highTemp: number;
    completedVax: number;
    dueVax: number;
    sickAnimals: DashboardSickAnimal[];
  };
  vaccination: {
    dueAnimals: DashboardVaccinationDue[];
  };
  reproduction: {
    inseminated: number;
    pregnant: number;
    pregnancyRatio: number;
  };
  finance: {
    receivables: number;
    receivableCount: number;
  };
}

type LedgerProduction = {
  animal_id?: string | null;
  production_date?: string | null;
  recorded_at?: string | null;
  total_yield?: number | null;
  status?: string | null;
};

type LedgerResponse = {
  production?: LedgerProduction[];
  dispositions?: any[];
};

const EMPTY_DASHBOARD = (): CommandDashboardData => ({
  todayLiters: 0,
  yesterdayLiters: 0,
  todayDate: farmToday(),
  yesterdayDate: "",
  milkingAnimals: 0,
  adultAnimals: 0,
  milkingPercentage: 0,
  averageYieldPerCow: 0,
  herdComposition: [],
  herdMetrics: {
    wetAverageYieldPercentage: null,
    dryAverageYieldPercentage: null,
  },
  topPerformers: [],
  bottomPerformers: [],
  yieldTrend: [],
  productionExtremes: {
    highest: [],
    lowest: [],
  },
  yieldDropWatchlist: [],
  productionDrop: null,
  health: {
    sick: 0,
    mastitis: 0,
    highTemp: 0,
    completedVax: 0,
    dueVax: 0,
    sickAnimals: [],
  },
  vaccination: {
    dueAnimals: [],
  },
  reproduction: {
    inseminated: 0,
    pregnant: 0,
    pregnancyRatio: 0,
  },
  finance: {
    receivables: 0,
    receivableCount: 0,
  },
});

const isoDate = (value: unknown): string => {
  if (!value) return "";
  return String(value).slice(0, 10);
};

const sumLedgerForDate = (
  rows: LedgerProduction[],
  targetDate: string,
): number => {
  return rows
    .filter((row) => {
      if (String(row.status || "RECORDED").toUpperCase() === "VOID") {
        return false;
      }

      return isoDate(row.production_date || row.recorded_at) === targetDate;
    })
    .reduce(
      (sum, row) => sum + Number(row.total_yield || 0),
      0,
    );
};

const groupLedgerByDate = (
  rows: LedgerProduction[],
  startDate: string,
  endDate: string,
): Array<{ day: string; yield: number | null }> => {
  const totals = new Map<string, number>();

  for (const row of rows) {
    if (String(row.status || "RECORDED").toUpperCase() === "VOID") {
      continue;
    }

    const day = isoDate(
      row.production_date || row.recorded_at,
    );

    if (!day) continue;

    totals.set(
      day,
      (totals.get(day) || 0) + Number(row.total_yield || 0),
    );
  }

  const series: Array<{ day: string; yield: number | null }> = [];
  const cursor = new Date(`${startDate}T00:00:00Z`);
  const end = new Date(`${endDate}T00:00:00Z`);

  while (cursor <= end) {
    const day = cursor.toISOString().slice(0, 10);
    const total = totals.get(day);

    series.push({
      day,
      yield: total === undefined
        ? null
        : Number(total.toFixed(2)),
    });

    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  return series;
};

export async function fetchCommandDashboardData(): Promise<CommandDashboardData> {
  const base =
    API_BASE_URL ||
    "http://127.0.0.1:8000";

  const today = farmToday();
  const yesterday = shiftFarmDate(today, -1);
  const trendStart = shiftFarmDate(today, -29);

  const [
    dashboardResponse,
    todayLedgerResponse,
    trendLedgerResponse,
  ] = await Promise.all([
    fetch(`${base}/dashboard`, {
      headers: { Accept: "application/json" },
    }),

    fetch(
      `${base}/farm/milk/ledger?start_date=${today}&end_date=${today}`,
      {
        headers: { Accept: "application/json" },
      },
    ),

    fetch(
      `${base}/farm/milk/ledger?start_date=${trendStart}&end_date=${today}`,
      {
        headers: { Accept: "application/json" },
      },
    ),
  ]);

  if (!dashboardResponse.ok) {
    throw new Error(
      `Dashboard request failed with HTTP ${dashboardResponse.status}`,
    );
  }

  if (!todayLedgerResponse.ok) {
    throw new Error(
      `Milk ledger request failed with HTTP ${todayLedgerResponse.status}`,
    );
  }

  if (!trendLedgerResponse.ok) {
    throw new Error(
      `Milk trend ledger request failed with HTTP ${trendLedgerResponse.status}`,
    );
  }

  const raw = await dashboardResponse.json();

  const todayLedger =
    (await todayLedgerResponse.json()) as LedgerResponse;

  const trendLedger =
    (await trendLedgerResponse.json()) as LedgerResponse;

  const data = EMPTY_DASHBOARD();

  const dashboard =
    raw?.dashboard || {};

  const rawMilk =
    raw?.milk || {};

  const rawAnimals =
    raw?.animals || {};

  const rawHealth =
    raw?.health || dashboard.health || {};

  const rawVaccination =
    raw?.vaccination || dashboard.vaccination || {};

  const rawReproduction =
    raw?.reproduction || dashboard.reproduction || {};

  const rawFinance =
    raw?.finance || dashboard.finance || {};

  const todayProduction =
    sumLedgerForDate(
      todayLedger.production || [],
      today,
    );

  const trend =
    groupLedgerByDate(
      trendLedger.production || [],
      trendStart,
      today,
    );

  const yesterdayLiters =
    sumLedgerForDate(
      trendLedger.production || [],
      yesterday,
    );

  const animalMap =
    raw?.operational_state?.animals || {};

  const animalList =
    Object.values(animalMap) as any[];

  const activeAnimalList =
    animalList.filter(
      (animal: any) =>
        animal?.active !== false,
    );

  const milkingAnimals =
    Number(
      rawMilk.current_milking_count ??
      rawMilk.milking_population_count ??
      dashboard.animals?.milking ??
      activeAnimalList.filter(
        (animal: any) =>
          String(
            animal.lifecycle_status || "",
          ).toUpperCase() === "LACTATING" ||
          animal.is_currently_milking === true,
      ).length,
    );

  const milkingPercentage =
    Number(
      rawMilk.milking_percentage ??
      dashboard.animals?.milking_percentage ??
      (
        rawMilk.milking_population_count
          ? (
              milkingAnimals /
              Number(rawMilk.milking_population_count)
            ) *
            100
          : 0
      ),
    );

  const backendAverage =
    rawMilk.average_yield_per_cow;

  const actualAverage =
    backendAverage !== null &&
    backendAverage !== undefined
      ? Number(backendAverage)
      : (
          todayProduction > 0 &&
          milkingAnimals > 0
            ? todayProduction / milkingAnimals
            : null
        );

  const productionDrop =
    rawMilk.production_drop ??
    null;

  const productionExtremes =
    rawMilk.production_extremes ??
    {};

  const yieldDropWatchlist =
    Array.isArray(
      rawMilk.yield_drop_watchlist,
    )
      ? rawMilk.yield_drop_watchlist
      : [];

  const herdComposition =
    Array.isArray(
      dashboard.animals?.composition,
    )
      ? dashboard.animals.composition
      : [];

  const rawHerdMetrics =
    rawAnimals.herd_metrics ??
    dashboard.animals?.herd_metrics ??
    {};

  return {
    ...data,

    // Current-day Milk ledger is authoritative.
    todayLiters:
      Number(
        todayProduction.toFixed(2),
      ),

    yesterdayLiters:
      Number(
        yesterdayLiters.toFixed(2),
      ),

    todayDate:
      today,

    yesterdayDate:
      yesterday,

    milkingAnimals,

    adultAnimals:
      Number(
        rawMilk.milking_population_count ??
        (
          Number(
            rawAnimals.total ||
            dashboard.animals?.total ||
            activeAnimalList.length ||
            0,
          )
        ),
      ),

    milkingPercentage:
      Number(
        milkingPercentage.toFixed(1),
      ),

    averageYieldPerCow:
      actualAverage === null
        ? null
        : Number(
            actualAverage.toFixed(2),
          ),

    topPerformers:
      Array.isArray(
        productionExtremes.highest,
      )
        ? productionExtremes.highest.map(
            (item: any) => ({
              id: String(
                item?.animal_id || "",
              ),
              yield: Number(
                item?.total_litres || 0,
              ),
            }),
          )
        : [],

    bottomPerformers:
      Array.isArray(
        productionExtremes.lowest,
      )
        ? productionExtremes.lowest.map(
            (item: any) => ({
              id: String(
                item?.animal_id || "",
              ),
              yield: Number(
                item?.total_litres || 0,
              ),
            }),
          )
        : [],

    yieldTrend:
      trend,

    herdComposition: herdComposition.map((item: any) => ({
      name: String(item?.name || item?.category || 'Unclassified'),
      value: Number(item?.value ?? item?.count ?? 0),
      color: item?.color ? String(item.color) : undefined,
    })),

    herdMetrics: {
      wetAverageYieldPercentage:
        rawHerdMetrics.wet_average_yield_percentage == null
          ? null
          : Number(rawHerdMetrics.wet_average_yield_percentage),
      dryAverageYieldPercentage:
        rawHerdMetrics.dry_average_yield_percentage == null
          ? null
          : Number(rawHerdMetrics.dry_average_yield_percentage),
    },

    productionExtremes: {
      highest:
        Array.isArray(
          productionExtremes.highest,
        )
          ? productionExtremes.highest.map(
              (item: any) => ({
                id: String(
                  item?.animal_id || "",
                ),
                yield: Number(
                  item?.total_litres || 0,
                ),
              }),
            )
          : [],

      lowest:
        Array.isArray(
          productionExtremes.lowest,
        )
          ? productionExtremes.lowest.map(
              (item: any) => ({
                id: String(
                  item?.animal_id || "",
                ),
                yield: Number(
                  item?.total_litres || 0,
                ),
              }),
            )
          : [],
    },

    yieldDropWatchlist,

    productionDrop,

    health: {
      sick:
        Number(
          rawHealth.active_exceptions ??
          rawHealth.sick ??
          0,
        ),

      mastitis:
        Number(
          rawHealth.critical_cases ??
          rawHealth.mastitis ??
          0,
        ),

      highTemp:
        Number(
          rawHealth.high_temperature ??
          rawHealth.highTemp ??
          0,
        ),

      completedVax:
        Number(
          rawHealth.completed_vaccinations ??
          rawHealth.completedVax ??
          0,
        ),

      dueVax:
        Number(
          rawHealth.due_vaccinations ??
          rawHealth.dueVax ??
          0,
        ),

      sickAnimals:
        Array.isArray(rawHealth.sick_animals)
          ? rawHealth.sick_animals.map((item: any) => ({
              animalId: String(item?.animal_id || ''),
              diagnosis: String(item?.diagnosis || 'Unspecified'),
              severity: String(item?.severity || 'NORMAL'),
              openedAt: String(item?.opened_at || ''),
              followUpDueAt: String(item?.follow_up_due_at || ''),
            }))
          : [],
    },

    vaccination: {
      dueAnimals:
        Array.isArray(rawVaccination.due_animals)
          ? rawVaccination.due_animals.map((item: any) => ({
              animalId: String(item?.animal_id || ''),
              vaccine: String(item?.vaccine || 'Vaccination'),
              administeredDate: String(item?.administered_date || ''),
              nextDueDate: String(item?.next_due_date || ''),
              dueState: String(item?.due_state || 'SCHEDULED'),
            }))
          : [],
    },

    reproduction: {
      inseminated:
        Number(
          rawReproduction.inseminated ??
          0,
        ),

      pregnant:
        Number(
          rawReproduction.pregnant ??
          0,
        ),

      pregnancyRatio:
        Number(
          rawReproduction.pregnancy_ratio_percent ??
          rawReproduction.pregnancyRatio ??
          0,
        ),
    },

    finance: {
      receivables:
        Number(
          rawFinance.receivables ??
          0,
        ),
      receivableCount:
        Number(
          rawFinance.receivable_count ??
          rawFinance.receivableCount ??
          0,
        ),
    },
  };
}
