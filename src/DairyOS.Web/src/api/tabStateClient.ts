const API_BASE_URL = import.meta.env.VITE_DAIRYOS_API_URL ?? "http://127.0.0.1:8000";

export type OperationalTabId =
    | "animals"
    | "milk"
    | "feed"
    | "health"
    | "breeding"
    | "workforce"
    | "inventory"
    | "equipment"
    | "finance"
    | "analytics"
    | "alerts";

export type OperationalTabState = {
    tab_id: OperationalTabId;
    contract_version: "S-09D.55";
    source: "FarmOperationalState";
    farm_id: string;
    operational_date: string;
    status: "ACTIVE" | "NO_DATA" | "ATTENTION";
    state: Record<string, unknown>;
};

export type OperationalTabStateResponse = {
    system: "DairyOS";
    contract_version: "S-09D.55";
    source: "FarmOperationalState";
    farm_id: string;
    operational_date: string;
    tabs: Record<OperationalTabId, OperationalTabState>;
};

export async function getOperationalTabState(): Promise<OperationalTabStateResponse> {
    const response = await fetch(`${API_BASE_URL}/operations/tab-state`, {
        headers: { Accept: "application/json" },
    });

    if (!response.ok) {
        throw new Error(`Operational tab-state request failed: ${response.status}`);
    }

    return response.json() as Promise<OperationalTabStateResponse>;
}

export async function getOperationalTab(tabId: OperationalTabId): Promise<OperationalTabState> {
    const response = await fetch(`${API_BASE_URL}/operations/tab-state/${tabId}`, {
        headers: { Accept: "application/json" },
    });

    if (!response.ok) {
        throw new Error(`Operational tab request failed: ${response.status}`);
    }

    return response.json() as Promise<OperationalTabState>;
}
