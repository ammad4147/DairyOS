import type { DashboardResponse } from "../models/dashboard";


export async function getDashboard():

Promise<DashboardResponse> {

    const response = await fetch(
        "http://localhost:8000/dashboard"
    );


    if (!response.ok) {

        throw new Error(
            "Dashboard request failed"
        );

    }


    return response.json();

}
