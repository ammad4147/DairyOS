import { API_BASE_URL } from "../config/api";

export interface PerformerItem {
  id: string;
  yield: number;
}

export interface HerdCategory {
  name: string;
  value: number;
  color?: string;
}

export interface CommandDashboardData {
  todayLiters: number;
  yesterdayLiters: number;
  todayDate: string;
  yesterdayDate: string;
  milkingAnimals: number;
  adultAnimals: number;
  milkingPercentage: number;
  averageYieldPerCow: number;
  topPerformers: PerformerItem[];
  bottomPerformers: PerformerItem[];
  yieldTrend: Array<{ day: string; yield: number }>;
  herdComposition: HerdCategory[];
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
  };
  reproduction: {
    onHeat: number;
    inseminated: number;
    pregnant: number;
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
  todayDate: new Date().toISOString().split("T")[0],
  yesterdayDate: "",
  milkingAnimals: 0,
  adultAnimals: 0,
  milkingPercentage: 0,
  averageYieldPerCow: 0,
  topPerformers: [],
  bottomPerformers: [],
  yieldTrend: [],
  herdComposition: [],
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
  },
  reproduction: {
    onHeat: 0,
    inseminated: 0,
    pregnant: 0,
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
): Array<{ day: string; yield: number }> => {
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

  return Array.from(totals.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([day, yieldValue]) => ({
      day,
      yield: Number(yieldValue.toFixed(2)),
    }));
};

export async function fetchCommandDashboardData(): Promise<CommandDashboardData> {
  const base =
    API_BASE_URL ||
    "http://127.0.0.1:8000";

  const today =
    new Date().toISOString().split("T")[0];

  const yesterdayDate = new Date();
  yesterdayDate.setDate(
    yesterdayDate.getDate() - 1,
  );

  const yesterday =
    yesterdayDate.toISOString().split("T")[0];

  const trendStartDate = new Date();
  trendStartDate.setDate(
    trendStartDate.getDate() - 29,
  );

  const trendStart =
    trendStartDate.toISOString().split("T")[0];

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

  const todayProduction =
    sumLedgerForDate(
      todayLedger.production || [],
      today,
    );

  const trend =
    groupLedgerByDate(
      trendLedger.production || [],
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

  const averageYield =
    Number(
      rawMilk.average_yield_per_cow ??
      0,
    );

  const actualAverage =
    averageYield > 0
      ? averageYield
      : (
          milkingAnimals > 0
            ? todayProduction / milkingAnimals
            : 0
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
      Number(
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

    herdComposition,

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
          dashboard.health?.active_exceptions ??
          0,
        ),

      mastitis:
        Number(
          dashboard.health?.critical_cases ??
          0,
        ),

      highTemp:
        Number(
          dashboard.health?.high_temperature ??
          0,
        ),

      completedVax:
        Number(
          dashboard.health?.completed_vaccinations ??
          0,
        ),

      dueVax:
        Number(
          dashboard.health?.due_vaccinations ??
          0,
        ),
    },

    reproduction: {
      onHeat:
        Number(
          dashboard.reproduction?.on_heat ??
          0,
        ),

      inseminated:
        Number(
          dashboard.reproduction?.inseminated ??
          0,
        ),

      pregnant:
        Number(
          dashboard.reproduction?.pregnant ??
          0,
        ),
    },
  };
}