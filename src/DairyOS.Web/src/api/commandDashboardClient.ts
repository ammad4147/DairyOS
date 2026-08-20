export interface FinancialTransaction {
  id: string;
  transaction_type: 'INCOME' | 'EXPENSE';
  category: string;
  amount: number;
  operator: string;
  notes?: string;
  timestamp: string;
}

export interface YieldTrendItem {
  day: string;
  yield: number;
}

export interface Performer {
  id: string;
  yield: number;
}

export interface HerdCategory {
  name: string;
  value: number;
  color: string;
}

export interface CommandDashboardData {
  milkingAnimals: number;
  adultAnimals: number;
  milkingPercentage: number;
  todayLiters: number;
  yesterdayLiters: number;
  todayDate: string;
  yesterdayDate: string;
  yieldTrend: YieldTrendItem[];
  topPerformers: Performer[];
  bottomPerformers: Performer[];
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

export async function fetchCommandDashboardData(): Promise<CommandDashboardData> {
  return {
    milkingAnimals: 142,
    adultAnimals: 210,
    milkingPercentage: 67.6,
    todayLiters: 1236,
    yesterdayLiters: 1310,
    todayDate: "2026-08-19",
    yesterdayDate: "2026-08-18",
    yieldTrend: [
      { day: "1", yield: 1190 }, { day: "2", yield: 1210 }, { day: "3", yield: 1205 }, { day: "4", yield: 1240 },
      { day: "5", yield: 1225 }, { day: "6", yield: 1310 }, { day: "7", yield: 1236 }, { day: "8", yield: 1250 },
      { day: "9", yield: 1280 }, { day: "10", yield: 1265 }, { day: "11", yield: 1290 }, { day: "12", yield: 1300 },
      { day: "13", yield: 1305 }, { day: "14", yield: 1236 }, { day: "15", yield: 1245 }, { day: "16", yield: 1270 },
      { day: "17", yield: 1285 }, { day: "18", yield: 1295 }, { day: "19", yield: 1310 }, { day: "20", yield: 1250 },
      { day: "21", yield: 1240 }, { day: "22", yield: 1260 }, { day: "23", yield: 1275 }, { day: "24", yield: 1290 },
      { day: "25", yield: 1300 }, { day: "26", yield: 1315 }, { day: "27", yield: 1280 }, { day: "28", yield: 1260 },
      { day: "29", yield: 1250 }, { day: "30", yield: 1236 }
    ],
    topPerformers: [
      { id: "COW-102", yield: 38.5 },
      { id: "COW-215", yield: 36.2 },
      { id: "COW-044", yield: 35.0 }
    ],
    bottomPerformers: [
      { id: "COW-310", yield: 8.2 },
      { id: "COW-118", yield: 9.1 },
      { id: "COW-402", yield: 10.0 }
    ],
    herdComposition: [
      { name: "Milking", value: 142, color: "#22c55e" },
      { name: "Dry", value: 68, color: "#f59e0b" },
      { name: "Heifers", value: 45, color: "#38bdf8" },
      { name: "Female Calves", value: 30, color: "#a855f7" },
      { name: "Male Calves", value: 25, color: "#ec4899" },
      { name: "Bulls", value: 8, color: "#64748b" }
    ],
    health: { sick: 4, mastitis: 2, highTemp: 2, completedVax: 185, dueVax: 12 },
    reproduction: { onHeat: 6, inseminated: 14, pregnant: 88 }
  };
}

export async function fetchFinancialLedger(): Promise<FinancialTransaction[]> {
  return [
    { id: "TX-101", transaction_type: "EXPENSE", category: "Feed Purchases (Silage, Hay, Concentrates)", amount: 450000, operator: "Ammad Hassan", notes: "Bulk corn silage procurement", timestamp: "2026-08-18" },
    { id: "TX-102", transaction_type: "EXPENSE", category: "Veterinary, Medicine & AI Services", amount: 65000, operator: "Ammad Hassan", notes: "Vaccination & routine checkup", timestamp: "2026-08-19" },
    { id: "TX-103", transaction_type: "EXPENSE", category: "Utilities (Electricity, Water, Fuel)", amount: 120000, operator: "Ammad Hassan", notes: "Tube well and parlor electricity", timestamp: "2026-08-19" },
    { id: "TX-104", transaction_type: "INCOME", category: "Commercial Milk Sales", amount: 380000, operator: "Ammad Hassan", notes: "Daily wholesale delivery", timestamp: "2026-08-19" },
    { id: "TX-105", transaction_type: "INCOME", category: "Manure & Organic Compost Sale", amount: 25000, operator: "Ammad Hassan", notes: "Local agricultural supply", timestamp: "2026-08-20" }
  ];
}

export async function postFinancialTransaction(tx: Omit<FinancialTransaction, 'id' | 'timestamp'>): Promise<boolean> {
  return true;
}
