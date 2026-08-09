export interface OperationalEntry {
    [key: string]: unknown;
}

export interface MilkEntryRequest extends OperationalEntry {
    animal_id: string;
    morning_yield: number;
    afternoon_yield: number;
    evening_yield: number;
    milking_session?: string;
    operator: string;
}

export interface FeedEntryRequest extends OperationalEntry {
    feed_type: string;
    quantity_kg: number;
    group_or_pen?: string;
    animal_id?: string;
    operator: string;
}

export interface HealthEntryRequest extends OperationalEntry {
    animal_id: string;
    observation?: string;
    symptom?: string;
    temperature_c?: number;
    severity: string;
    operator: string;
}

export async function postRequest<T>(url: string, payload: unknown): Promise<T> {
    const response = await fetch(`http://localhost:8000${url}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        let detail = `Request failed: ${response.status}`;
        try {
            const body = await response.json() as { detail?: string };
            if (body.detail) detail = body.detail;
        } catch {
            // Keep the HTTP error when the response is not JSON.
        }
        throw new Error(detail);
    }

    return response.json() as Promise<T>;
}

export async function getRequest<T>(url: string): Promise<T> {
    const response = await fetch(`http://localhost:8000${url}`);
    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
}

export function recordMilkEntry(entry: MilkEntryRequest) {
    return postRequest("/farm/milk", entry);
}

export function recordFeedEntry(entry: FeedEntryRequest) {
    return postRequest("/farm/feed", entry);
}

export function recordHealthObservation(entry: HealthEntryRequest) {
    return postRequest("/farm/health-observations", entry);
}

export function recordOperationalEntry(endpoint: string, payload: OperationalEntry) {
    return postRequest(endpoint, payload);
}

export function listOperationalEntries<T = OperationalEntry[]>(endpoint: string) {
    return getRequest<T>(endpoint);
}

export function listAnimals<T = OperationalEntry[]>(currentlyMilking = false) {
    return getRequest<T>(currentlyMilking ? "/farm/animals/current/milking" : "/farm/animals");
}
