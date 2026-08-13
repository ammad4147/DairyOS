import type { DashboardResponse } from "../models/dashboard";

import { API_BASE_URL } from "../config/api";

export async function getDashboard(): Promise<DashboardResponse> {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
        headers: {
            Accept: "application/json",
        },
    });

    if (!response.ok) {
        throw new Error(`Dashboard request failed: ${response.status}`);
    }

    return response.json() as Promise<DashboardResponse>;
}
