import type { DashboardResponse } from "../models/dashboard";

const API_BASE_URL = "http://localhost:8000";

export async function getDashboard(): Promise<DashboardResponse> {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
        method: "GET",
        headers: {
            Accept: "application/json",
        },
        cache: "no-store",
    });

    if (!response.ok) {
        let detail = `Dashboard request failed: ${response.status}`;

        try {
            const body = await response.json() as { detail?: string };
            if (body.detail) {
                detail = body.detail;
            }
        } catch {
            // Preserve the HTTP status when the response is not JSON.
        }

        throw new Error(detail);
    }

    const payload = await response.json() as DashboardResponse;

    if (!payload || typeof payload !== "object") {
        throw new Error("Dashboard returned an invalid response.");
    }

    if (!payload.dashboard || typeof payload.dashboard !== "object") {
        throw new Error("Dashboard response is missing the runtime dashboard.");
    }

    return payload;
}
