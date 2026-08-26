import { API_BASE_URL } from "../config/api";

export interface PerformerItem {
  id: string;
  yield: number;
}

export interface HerdCategory {
  name: string;
  value: number;
  color: string;
}

export interface CommandDashboardData {
  todayLiters: number;
  yesterdayLiters: number;
  todayDate: string;
  yesterdayDate: string;
  milkingAnimals: number;
  adultAnimals: number;
  milkingPercentage: number;
  topPerformers: PerformerItem[];
  bottomPerformers: PerformerItem[];
  yieldTrend: Array<{ day: string; yield: number }>;
  herdComposition: HerdCategory[];
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

const EMPTY_DASHBOARD = (): CommandDashboardData => ({
  todayLiters: 0,
  yesterdayLiters: 0,
  todayDate: new Date().toISOString().split("T")[0],
  yesterdayDate: "",
  milkingAnimals: 0,
  adultAnimals: 0,
  milkingPercentage: 0,
  topPerformers: [],
  bottomPerformers: [],
  yieldTrend: [],
  herdComposition: [],
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

export async function fetchCommandDashboardData(): Promise<CommandDashboardData> {
  const base = API_BASE_URL || "http://127.0.0.1:8000";

  const res = await fetch(`${base}/dashboard`, {
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new Error(`Dashboard request failed with HTTP ${res.status}`);
  }

  try {
    const raw = await res.json();

    if (
      raw.todayLiters !== undefined &&
      raw.milkingAnimals !== undefined
    ) {
      return {
        ...EMPTY_DASHBOARD(),
        ...raw,
        topPerformers: Array.isArray(raw.topPerformers)
          ? raw.topPerformers
          : [],
        bottomPerformers: Array.isArray(raw.bottomPerformers)
          ? raw.bottomPerformers
          : [],
        yieldTrend: Array.isArray(raw.yieldTrend)
          ? raw.yieldTrend
          : [],
        herdComposition: Array.isArray(raw.herdComposition)
          ? raw.herdComposition
          : [],
      };
    }

    const dash = raw.dashboard || {};
    const animalsMap = raw.operational_state?.animals || {};
    const animalList = Object.values(animalsMap) as any[];

    const totalAdults = Number(dash.animals?.total ?? animalList.length ?? 0);
    const milkingCount = Number(
      dash.animals?.milking ??
        animalList.filter(
          (a: any) =>
            a.lifecycle_status === "LACTATING" ||
            a.is_currently_milking,
        ).length ??
        0,
    );

    const dryCount = Number(
      dash.animals?.dry ?? Math.max(0, totalAdults - milkingCount),
    );

    const todayLiters = Number(
      dash.milk?.today_litres ?? dash.milk?.litres ?? 0,
    );

    const yesterdayLiters = Number(
      dash.milk?.previous_litres ?? 0,
    );

    return {
      todayLiters,
      yesterdayLiters,
      todayDate:
        dash.milk?.production_date ||
        new Date().toISOString().split("T")[0],
      yesterdayDate: dash.milk?.previous_production_date || "",
      milkingAnimals: milkingCount,
      adultAnimals: totalAdults,
      milkingPercentage:
        totalAdults > 0
          ? Number(((milkingCount / totalAdults) * 100).toFixed(1))
          : 0,
      topPerformers: Array.isArray(dash.milk?.top_performers)
        ? dash.milk.top_performers
        : [],
      bottomPerformers: Array.isArray(dash.milk?.bottom_performers)
        ? dash.milk.bottom_performers
        : [],
      yieldTrend: Array.isArray(dash.milk?.yield_trend)
        ? dash.milk.yield_trend
        : [],
      herdComposition:
        Array.isArray(dash.animals?.composition)
          ? dash.animals.composition
          : [
              ...(milkingCount > 0
                ? [{ name: "Milking", value: milkingCount }]
                : []),
              ...(dryCount > 0
                ? [{ name: "Dry", value: dryCount }]
                : []),
            ],
      health: {
        sick: Number(dash.health?.active_exceptions ?? 0),
        mastitis: Number(dash.health?.critical_cases ?? 0),
        highTemp: Number(dash.health?.high_temperature ?? 0),
        completedVax: Number(dash.health?.completed_vaccinations ?? 0),
        dueVax: Number(dash.health?.due_vaccinations ?? 0),
      },
      reproduction: {
        onHeat: Number(dash.reproduction?.on_heat ?? 0),
        inseminated: Number(dash.reproduction?.inseminated ?? 0),
        pregnant: Number(dash.reproduction?.pregnant ?? 0),
      },
    };
  } catch (err) {
    console.warn("Backend API response could not be parsed.", err);
    throw err;
  }
}
