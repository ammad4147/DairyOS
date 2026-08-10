import type { DashboardResponse } from "../models/dashboard";

const API_BASE_URL = "http://localhost:8000";

export async function getDashboard(): Promise<DashboardResponse> {
    const response = await fetch(
        `${API_BASE_URL}/dashboard`,
        {
            headers: {
                Accept: "application/json",
            },
        },
    );

    if (!response.ok) {
        throw new Error(
            `Dashboard request failed: ${response.status}`,
        );
    }

    return response.json() as Promise<DashboardResponse>;
}
