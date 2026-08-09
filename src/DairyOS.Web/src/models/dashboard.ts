export interface DashboardWidget {
    widget_id: string;
    title: string;
    subtitle?: string;
    value: string | number | null;
    status?: string;
    trend?: string;
    zone?: string;
    position?: number;
    size?: string;
    visible?: boolean;
    user_configurable?: boolean;
    refresh_interval_seconds?: number;
    importance?: string;
    actionability?: string;
    last_updated?: string | null;
    data_freshness?: string;
    has_alert?: boolean;
    has_action?: boolean;
    click_target?: string | null;
}

export interface DashboardZone {
    zone_id: string;
    title: string;
    widgets: DashboardWidget[];
    visible?: boolean;
}

export interface DashboardView {
    layout: {
        zones: DashboardZone[];
    };
}

export interface DashboardMilkSummary {
    today_litres?: number;
    events?: number;
    last_operator?: string | null;
    last_shift?: string | null;
}

export interface DashboardFeedSummary {
    today_kg?: number;
    events?: number;
    last_feed_type?: string | null;
}

export interface DashboardRuntime {
    event_count?: number;
    milk?: DashboardMilkSummary;
    feed?: DashboardFeedSummary;
    freshness?: Record<string, unknown>;
    farm_status?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface OperationalAnimalState {
    lifecycle?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface OperationalState {
    animals?: Record<string, OperationalAnimalState>;
    milk_status?: Record<string, unknown>;
    feeding_status?: Record<string, unknown>;
    health_status?: Record<string, unknown>;
    breeding_status?: Record<string, unknown>;
    workforce_status?: Record<string, unknown>;
    inventory_status?: Record<string, unknown>;
    equipment_status?: Record<string, unknown>;
    financial_status?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface OperationalDecision {
    type?: string;
    priority?: string;
    animal_id?: string;
    action?: string;
    title?: string;
    details?: Record<string, unknown>;
    source?: string;
    escalation_level?: string;
    [key: string]: unknown;
}

export interface DashboardResponse {
    system: string;
    module: string;
    health: string;
    farm_status: string;
    operational_state: OperationalState;
    dashboard: DashboardRuntime;
    dashboard_view: DashboardView;
    operational_decisions: OperationalDecision[];
    operational_decision_summary: Record<string, unknown>;
    exceptions: unknown[];
    event_count: number;
}
