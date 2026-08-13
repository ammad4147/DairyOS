import { API_BASE_URL as API } from "../config/api";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`DairyOS API ${response.status}: ${path}`);
  return response.json() as Promise<T>;
}

async function post<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`DairyOS API ${response.status}: ${path}`);
  return response.json() as Promise<T>;
}

export type DairyKpis = {
  period_days: number;
  data_status: string;
  values: Record<string, number | null>;
  quality: Record<string, string>;
};

export type AnimalPassport = {
  animal: Record<string, unknown>;
  lifecycle: Record<string, unknown>;
  milk: Record<string, unknown>[];
  feed: Record<string, unknown>[];
  health: Record<string, unknown>[];
  breeding: Record<string, unknown>[];
  treatments: Record<string, unknown>[];
  finance: Record<string, unknown>[];
  passport_status: string;
};

export const farmIntelligenceClient = {
  kpis: (days = 30) => get<DairyKpis>(`/farm/kpis?days=${days}`),
  passport: (animalId: string) => get<AnimalPassport>(`/farm/animals/${encodeURIComponent(animalId)}/passport`),
  youngstock: () => get<Record<string, unknown>>("/farm/youngstock"),
  welfareKpis: (days = 30) => get<Record<string, unknown>>(`/farm/welfare/kpis?days=${days}`),
  heatStress: (farmId = "DEFAULT") => get<Record<string, unknown>>(`/farm/heat-stress?farm_id=${encodeURIComponent(farmId)}`),
  referenceData: () => get<Record<string, unknown>>("/farm/reference-data"),
  sops: (farmId = "DEFAULT") => get<Record<string, unknown>>(`/farm/sops?farm_id=${encodeURIComponent(farmId)}`),
  recordHeatStress: (payload: unknown) => post<Record<string, unknown>>("/farm/heat-stress/observations", payload),
  saveSop: (payload: unknown) => post<Record<string, unknown>>("/farm/sops", payload),
};
