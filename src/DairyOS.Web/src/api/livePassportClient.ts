import { API_BASE_URL } from "../config/api";

export interface AnimalPassportData {
  animal_id: string;
  tag_id?: string;
  lifecycle_state?: string;
  lactation_stage?: string;
  health_history?: Array<{ date: string; title: string; notes?: string; severity?: string }>;
  reproductive_logs?: Array<{ date: string; event: string; technician?: string; result?: string }>;
  feed_cost_summary?: { daily_cost_pkr: number; ration_name?: string };
}

export async function fetchAnimalPassport(animalId: string): Promise<AnimalPassportData | null> {
  try {
    const cleanId = animalId.replace("#", "");
    const res = await fetch(`${API_BASE_URL}/farm/animals/${cleanId}/passport`, {
      headers: { Accept: "application/json" }
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
