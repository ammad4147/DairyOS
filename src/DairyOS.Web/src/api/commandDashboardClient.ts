import { API_BASE_URL } from "../config/api";

export interface CommandDashboardData {
  farmName: string;
  milkingAnimals: number;
  adultAnimals: number;
  milkingPercentage: number;
  todayLiters: number;
  yesterdayLiters: number | null;
  yieldTrend: Array<{ day: string; yield: number }>;
  topPerformers: Array<{ id: string; yield: number }>;
  bottomPerformers: Array<{ id: string; yield: number }>;
  herdComposition: Array<{ name: string; value: number; color: string }>;
  health: {
    status: string;
    activeExceptions: number;
    criticalCases: number;
  };
  reproduction: {
    onHeat: number | null;
    inseminated: number | null;
    pregnant: number | null;
  };
}

const HERD_COLORS: Record<string, string> = {
  MILKING: "#3b82f6",
  DRY: "#f97316",
  HEIFER: "#eab308",
  CALF: "#a855f7",
  BULL: "#ef4444",
  OTHER: "#94a3b8",
};

async function getJson(path: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`DairyOS API ${response.status}: ${path}`);
  }

  return response.json();
}

function normalizeCollection(value: any, keys: string[]): any[] {
  if (Array.isArray(value)) return value;
  for (const key of keys) {
    if (Array.isArray(value?.[key])) return value[key];
  }
  return [];
}

function normalizeDate(value: unknown): string | null {
  if (typeof value !== "string" || !value) return null;
  return value.split("T")[0];
}

export async function fetchCommandDashboardData(
  periodDays = 7,
): Promise<CommandDashboardData> {
  const [dashboard, animalsPayload, milkPayload] = await Promise.all([
    getJson("/dashboard"),
    getJson("/farm/animals"),
    getJson("/farm/milk"),
  ]);

  const animals = normalizeCollection(animalsPayload, ["animals", "records"]);
  const milkRecords = normalizeCollection(milkPayload, ["records", "milk"]);

  const operationalState = dashboard?.operational_state ?? {};
  const dashboardData = dashboard?.dashboard ?? {};
  const authoritativeAnimals = operationalState?.animals ?? {};

  const animalRecords = animals.length
    ? animals
    : Object.values(authoritativeAnimals);

  const herdCounts: Record<string, number> = {};
  const yieldByAnimal: Record<string, number> = {};
  const yieldByDate: Record<string, number> = {};

  for (const animal of animalRecords) {
    const lifecycle = String(
      animal?.lifecycle_status ?? animal?.status ?? "OTHER",
    ).toUpperCase();
    const category = lifecycle.includes("MILK")
      ? "MILKING"
      : lifecycle.includes("DRY")
        ? "DRY"
        : lifecycle.includes("HEIF")
          ? "HEIFER"
          : lifecycle.includes("CALF")
            ? "CALF"
            : lifecycle.includes("BULL")
              ? "BULL"
              : "OTHER";

    herdCounts[category] = (herdCounts[category] ?? 0) + 1;
  }

  for (const record of milkRecords) {
    const date = normalizeDate(record?.production_date ?? record?.date);
    const animalId = record?.animal_id;
    const litres = Number(record?.total_yield ?? record?.litres ?? record?.quantity_litres ?? 0);

    if (!date || !Number.isFinite(litres)) continue;

    yieldByDate[date] = (yieldByDate[date] ?? 0) + litres;

    if (animalId) {
      yieldByAnimal[String(animalId)] =
        (yieldByAnimal[String(animalId)] ?? 0) + litres;
    }
  }

  const operationalDate =
    normalizeDate(dashboardData?.milk?.production_date) ??
    normalizeDate(operationalState?.operational_date);

  const dates = Object.keys(yieldByDate).sort();
  const trendDates = operationalDate
    ? dates.filter((date) => date <= operationalDate).slice(-periodDays)
    : dates.slice(-periodDays);

  const yieldTrend = trendDates.map((date) => ({
    day: date,
    yield: Number(yieldByDate[date].toFixed(2)),
  }));

  const sortedYields = Object.entries(yieldByAnimal)
    .filter(([, value]) => value > 0)
    .sort((a, b) => b[1] - a[1]);

  const topPerformers = sortedYields.slice(0, 5).map(([id, yieldValue]) => ({
    id,
    yield: Number(yieldValue.toFixed(2)),
  }));

  const bottomPerformers = sortedYields
    .slice(-5)
    .reverse()
    .map(([id, yieldValue]) => ({
      id,
      yield: Number(yieldValue.toFixed(2)),
    }));

  const herdComposition = Object.entries(herdCounts)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({
      name: name.charAt(0) + name.slice(1).toLowerCase(),
      value,
      color: HERD_COLORS[name] ?? HERD_COLORS.OTHER,
    }));

  const todayLiters = Number(
    dashboardData?.milk?.today_litres ??
      dashboardData?.milk?.litres ??
      operationalState?.milk_today ??
      0,
  );

  const yesterdayLiters = dashboardData?.milk?.previous_litres == null
    ? null
    : Number(dashboardData.milk.previous_litres);

  const milkingAnimals = Number(
    dashboard?.animals?.milking ??
      operationalState?.animals?.milking ??
      operationalState?.animals?.milking_animals ??
      0,
  );

  const adultAnimals = Number(
    dashboard?.animals?.total ?? operationalState?.animals?.total ?? animalRecords.length,
  );

  const milkingPercentage = Number(
    dashboard?.animals?.milking_percentage ?? 0,
  );

  return {
    farmName: String(dashboard?.farm_status ?? "DairyOS"),
    milkingAnimals,
    adultAnimals,
    milkingPercentage,
    todayLiters,
    yesterdayLiters,
    yieldTrend,
    topPerformers,
    bottomPerformers,
    herdComposition,
    health: {
      status: String(dashboardData?.health?.status ?? "UNKNOWN"),
      activeExceptions: Number(dashboardData?.health?.active_exceptions ?? 0),
      criticalCases: Number(dashboardData?.health?.critical_cases ?? 0),
    },
    reproduction: {
      onHeat: null,
      inseminated: null,
      pregnant: null,
    },
  };
}
