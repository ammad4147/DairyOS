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
    layout?: {
        zones?: DashboardZone[];
    };
    owner_attention?: OperationalDecision[];
    farm_timeline?: Array<Record<string, unknown>>;
    quick_actions?: Array<{
        id?: string;
        title?: string;
        [key: string]: unknown;
    }>;
    animal_spotlight?: unknown[];
}

export interface DashboardMilkSummary {
    today_litres?: number;
    events?: number;
    last_operator?: string | null;
    last_shift?: string | null;

    yesterday_litres?: number;
    previous_day_litres?: number;
    seven_day_average_litres?: number;
    seven_day_total_litres?: number;
    thirty_day_average_litres?: number;
    trend?: string | number | null;
    trend_percent?: number | null;
    trend_direction?: string | null;
    morning_litres?: number;
    afternoon_litres?: number;
    evening_litres?: number;
    current_shift_litres?: number;
    current_shift?: string | null;
    production_status?: string | null;

    history?: Array<{
        date?: string;
        litres?: number;
        value?: number;
        [key: string]: unknown;
    }>;

    trend_history?: Array<{
        date?: string;
        litres?: number;
        value?: number;
        [key: string]: unknown;
    }>;

    [key: string]: unknown;
}

export interface DashboardFeedSummary {
    today_kg?: number;
    events?: number;
    last_feed_type?: string | null;
    efficiency?: number | null;
    feed_efficiency?: number | null;
    [key: string]: unknown;
}

export interface DashboardRuntime {
    system?: string;
    module?: string;
    health?: string;
    farm_status?: string | Record<string, unknown> | null;
    operational_state?: OperationalState;
    operational_decisions?: OperationalDecision[];
    operational_decision_summary?: Record<string, unknown>;
    exceptions?: unknown[];
    event_count?: number;
    milk?: DashboardMilkSummary;
    feed?: DashboardFeedSummary;
    freshness?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface OperationalAnimalState {
    lifecycle?: Record<string, unknown>;
    [key: string]: unknown;
}

export interface OperationalState {
    farm_id?: string;
    operational_date?: string;

    animals?: Record<string, OperationalAnimalState>;

    milk_status?: Record<string, unknown>;
    feeding_status?: Record<string, unknown>;
    health_status?: Record<string, unknown>;
    breeding_status?: Record<string, unknown>;
    workforce_status?: Record<string, unknown>;
    inventory_status?: Record<string, unknown>;
    equipment_status?: Record<string, unknown>;
    financial_status?: Record<string, unknown>;

    milk_production_summary?: Record<string, unknown>;
    open_tasks?: unknown[];
    completed_tasks?: unknown[];
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
    owner_action_required?: boolean;
    [key: string]: unknown;
}

export interface DashboardResponse {
    system?: string;
    module?: string;
    health?: string;
    farm_status?: string;

    operational_state?: OperationalState;

    dashboard: DashboardRuntime;

    dashboard_view?: DashboardView;

    operational_decisions?: OperationalDecision[];
    operational_decision_summary?: Record<string, unknown>;
    exceptions?: unknown[];
    event_count?: number;

    [key: string]: unknown;
}
