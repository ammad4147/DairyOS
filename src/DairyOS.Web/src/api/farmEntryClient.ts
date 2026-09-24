import { apiUrl } from "../config/api";

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

const RETRY_PREFIX = "dairyos:uncertain-write:";
const uncertainRequestIds = new Map<string, string>();

async function retryKey(url: string, payload: unknown): Promise<string | null> {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) return null;
    const stablePayload = { ...(payload as Record<string, unknown>) };
    delete stablePayload.request_id;
    const bytes = new TextEncoder().encode(`${url}\n${JSON.stringify(stablePayload)}`);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    const fingerprint = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${RETRY_PREFIX}${fingerprint}`;
}

export async function postRequest<T>(url: string, payload: unknown): Promise<T> {
    const key = await retryKey(url, payload);
    let requestId = payload && typeof payload === "object" && !Array.isArray(payload)
        ? (payload as Record<string, unknown>).request_id as string | undefined
        : undefined;
    if (!requestId && key) {
        try {
            requestId = uncertainRequestIds.get(key) || sessionStorage.getItem(key) || undefined;
        } catch {
            requestId = uncertainRequestIds.get(key);
        }
    }
    requestId ||= crypto.randomUUID();
    const requestPayload = payload && typeof payload === "object" && !Array.isArray(payload)
        ? { ...(payload as Record<string, unknown>), request_id: requestId }
        : payload;
    let response: Response;
    try {
        response = await fetch(apiUrl(url), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestPayload),
        });
    } catch (error) {
        // The server may have committed before the connection was lost. Retain
        // this ID only for an explicit retry of this identical request.
        if (key) {
            uncertainRequestIds.set(key, requestId);
            try { sessionStorage.setItem(key, requestId); } catch { /* in-memory retry remains available in this tab */ }
        }
        throw new Error("DairyOS lost the server response. The outcome is unconfirmed—check the register before retrying.", { cause: error });
    }

    // A success or a definitive client rejection ends the uncertain attempt.
    // A server failure can happen after commit, so retain its ID for retry.
    if (key && response.status < 500) {
        uncertainRequestIds.delete(key);
        try { sessionStorage.removeItem(key); } catch { /* no durable retry marker to clear */ }
    }

    if (!response.ok) {
        let detail = `Request failed: ${response.status}`;
        try {
            const body = await response.json() as { detail?: string };
            if (body.detail) detail = body.detail;
        } catch {
            // Keep the HTTP error when the response is not JSON.
        }
        if (response.status >= 500) {
            detail = `${detail}. The write outcome is unconfirmed—check the register before retrying.`;
        }
        throw new Error(detail);
    }

    return response.json() as Promise<T>;
}

export async function getRequest<T>(url: string): Promise<T> {
    const response = await fetch(apiUrl(url));
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
