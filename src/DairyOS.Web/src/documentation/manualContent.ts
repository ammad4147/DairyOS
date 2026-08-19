export type ManualAudience = "operator" | "technical";

export type ManualSection = {
    id: string;
    title: string;
    summary: string;
    content: string;
    keywords: string[];
};

export type ManualDocument = {
    id: ManualAudience;
    title: string;
    audience: string;
    purpose: string;
    sections: ManualSection[];
};

export const MANUALS: ManualDocument[] = [
    {
        id: "operator",
        title: "DairyOS Operator Manual",
        audience: "Farm operators, supervisors and authorised users",
        purpose: "A practical operating guide for entering farm facts, monitoring execution, responding to findings, and keeping operational records complete and attributable.",
        sections: [
            {
                id: "operator-start",
                title: "1. Getting started",
                summary: "Use the live navigation to work from authoritative operational views.",
                keywords: ["login", "dashboard", "navigation", "settings", "operator"],
                content: `## Daily start

1. Open DairyOS and confirm **System** is healthy and **Farm** shows the expected operational state.
2. Check **Dashboard** for the current operational picture and decision/alert indicators.
3. Open **Animals** and confirm the herd population and milking population are plausible.
4. Open **Alerts & Decisions** before starting repetitive work; unresolved findings may change priorities.
5. Use **Settings → Help & Documentation** whenever a workflow or field definition is unclear.

### Data-entry rule

Record what actually occurred. Do not use zero to mean a session was missed, and do not invent historical values to fill gaps. DairyOS treats persisted domain records as authoritative and derives higher-level views from them.`
            },
            {
                id: "operator-animals",
                title: "2. Herd and animal management",
                summary: "Maintain one operational identity per animal and use the passport for detailed history.",
                keywords: ["animals", "herd", "milking", "dry", "heifer", "calf", "passport", "ear tag", "RFID"],
                content: `## Register an animal

1. Open **Animals**.
2. Select **Register Animal**.
3. Enter the permanent system-generated Animal ID information available to the farm, including ear tag/RFID, breed, sex, date of birth and group/location.
4. Choose the current operational state: **MILKING** or **NON-MILKING**.
5. For a milking animal, select the governed **2-session** or **3-session** plan.
6. For a non-milking animal, select a reason category and enter a documented reason.
7. Save and confirm the success message.

### Find an animal

Use the Animals search field for partial or exact matches across Animal ID, ear tag/RFID, name or alias, dam/sire, status, lifecycle, breed, sex, group and location.

### Animal passport

Click any animal row to open the complete passport. The passport is the detailed read surface for identity, operational status, effective milking plan, record counts, milk/feed/health/breeding history and timeline. Use the passport before making a decision that depends on animal chronology.`
            },
            {
                id: "operator-milk",
                title: "3. Milk logging",
                summary: "Record actual milk outcomes against the animal's effective session plan and production date.",
                keywords: ["milk", "milking", "session", "yield", "production date", "morning", "afternoon", "evening", "missed"],
                content: `## Record milk

1. Open **Milk** or select **Record Milk** from an animal passport.
2. Select an existing animal from the governed animal list.
3. Use the session presented by DairyOS for that animal's effective frequency.
4. Enter the measured litres and operator attribution.
5. Confirm the production date and save.

### Completeness

Expected sessions are resolved from the effective milking schedule. A missing session remains missing; it is not converted to zero. Analytics and reconciliation should therefore distinguish **recorded**, **skipped/not entered**, and **missing** outcomes.

### Reconciliation

Use **Milk Reconciliation** for a specific production date. Production must be complete before produced litres can be fully reconciled to sales and non-sale dispositions. Unaccounted or over-accounted litres are operational exceptions, not values to be silently balanced by the UI.`
            },
            {
                id: "operator-feed",
                title: "4. Feed management",
                summary: "Record feed activity with quantity and operational attribution.",
                keywords: ["feed", "feeding", "silage", "TMR", "hay", "quantity", "kg", "ration"],
                content: `## Record feed activity

1. Open **Feeding**.
2. Select the feed type.
3. Enter the observed quantity in kilograms.
4. Add group/pen or animal attribution where relevant.
5. Record the operator and save.

### Operating practice

Keep feed records dated to the actual feeding activity. Use persisted records for consumption and cost analysis. Where data is incomplete, leave the deficiency explicit rather than manufacturing an estimate.`
            },
            {
                id: "operator-health",
                title: "5. Health and treatment monitoring",
                summary: "Capture observations and treatments as attributable dated events.",
                keywords: ["health", "treatment", "observation", "symptom", "severity", "temperature", "critical"],
                content: `## Record a health observation

1. Open **Health**.
2. Select the animal.
3. Describe the observation and relevant symptom.
4. Enter temperature when measured.
5. Assign the observed severity.
6. Record the operator and save.

### Findings and follow-up

Critical and high-severity observations can feed operational attention. A finding should be resolved only after the responsible farm process has actually been completed. Avoid changing a finding merely to improve dashboard appearance.`
            },
            {
                id: "operator-breeding",
                title: "6. Reproduction workflows",
                summary: "Record breeding events chronologically and use the reproductive current-state authority for current status.",
                keywords: ["breeding", "reproduction", "heat", "insemination", "pregnancy", "calving", "dry off", "abortion"],
                content: `## Record reproduction

1. Open **Breeding**.
2. Select the animal.
3. Choose the event type.
4. Enter technician/result/semen or bull details and notes as applicable.
5. Record the operator and save.

### Chronology and current state

Historical reproductive facts remain persisted breeding records. Current reproductive state is resolved by the reproductive state authority from the recorded chronology. Same-day calving is represented as **CALVED** in the API vocabulary. Do not infer a different current state in the frontend.`
            },
            {
                id: "operator-alerts",
                title: "7. Alerts, findings and decisions",
                summary: "Treat findings as operational work, not display-only messages.",
                keywords: ["alerts", "findings", "decisions", "acknowledge", "resolve", "critical", "warning"],
                content: `## Work a finding

1. Open **Alerts & Decisions**.
2. Review the source, animal/date context and recommended operational action.
3. Acknowledge when the responsible person has accepted the work.
4. Perform the farm action in the appropriate operational section.
5. Resolve only when the underlying condition is actually addressed.

Severity indicates operational priority; it is not a substitute for the underlying domain evidence.`
            },
            {
                id: "operator-finance",
                title: "8. Finance and sales records",
                summary: "Keep financial facts attributable and distinguish revenue, receipts and receivables.",
                keywords: ["finance", "sales", "revenue", "receipt", "receivable", "cash", "bank", "owner withdrawal", "CMP"],
                content: `## Financial transaction entry

Record transaction type, amount, transaction date, category, payment method, counterparty and operator. Use the actual transaction date.

### Milk sales

Milk sales originate from persisted milk dispositions. Recognised revenue, amount received and receivable outstanding are separate concepts. Do not treat an unpaid invoice as cash received.

### Cost of milk production

CMP scenarios distinguish actual persisted values from scenario assumptions. The backend CMP service remains authoritative for actual milk volume, eligible cost and cost per litre.`
            },
            {
                id: "operator-settings",
                title: "9. Settings and permissions",
                summary: "Manage farm identity, reset protection and access documentation without bypassing server authority.",
                keywords: ["settings", "permissions", "roles", "password", "reset protection", "documentation", "help"],
                content: `## Settings

Use **Settings** to manage farm identity, Animal ID prefix, reset protection and CMP scenarios. Reset-test-data is destructive; use it only during controlled testing and enable protection before production use.

### Permissions

User permissions are governed by the server-side authentication and authorisation layer. Frontend visibility is not a security boundary. A user who must not perform an action must also be denied by the API.`
            },
            {
                id: "operator-troubleshooting",
                title: "10. Basic troubleshooting",
                summary: "Use evidence-first checks before escalating a problem.",
                keywords: ["troubleshooting", "offline", "error", "failed", "retry", "diagnostic", "health"],
                content: `## API unavailable

1. Confirm the API process is running.
2. Open the health endpoint and readiness endpoint.
3. Confirm the configured PostgreSQL target is reachable.
4. Refresh the affected section.

## A record will not save

Check required fields, animal identity and the operational date/session. Read the returned API detail rather than retrying blindly.

## Data looks missing

Check the selected date/period and the data-status/completeness indication. DairyOS deliberately avoids converting absent observations into zero values.

## Escalation package

Record the time, page, operation, Animal ID if applicable, exact error message, production date and the last successful action. Do not send credentials or secrets in an incident report.`
            },
        ],
    },
    {
        id: "technical",
        title: "DairyOS Technical Manual",
        audience: "Technical administrators, developers, deployment and support staff",
        purpose: "A production-oriented reference for the DairyOS architecture, persistence model, API surfaces, configuration, deployment and diagnostics.",
        sections: [
            {
                id: "technical-architecture",
                title: "1. Architecture and authority",
                summary: "Layered modular architecture with persisted domain facts and backend-derived read models.",
                keywords: ["architecture", "Clean Architecture", "DDD", "SOLID", "domain", "service", "repository", "authority"],
                content: `## Runtime model

DairyOS is a Python/FastAPI backend with SQLAlchemy persistence and a React/Vite operator application. The backend is organised around domain models, repositories, application/domain services and API routers. The web shell consumes backend-authoritative read contracts.

### Authority principle

Authoritative domain data is persisted once. Higher layers consume lower-layer truth and must not redefine it. Current operational state, effective milking schedule, milk completeness, reconciliation, dispositions and analytics each have explicit backend authorities.

### Main runtime surfaces

- **FastAPI:** API/runtime boundary.
- **SQLAlchemy:** PostgreSQL persistence boundary.
- **Repository layer:** persistence adapters and domain access.
- **Service layer:** business rules and derived intelligence.
- **React/Vite:** operator presentation and navigation.
- **Settings / documentation:** local static help; no runtime dependency on the API.`
            },
            {
                id: "technical-api",
                title: "2. API contract map",
                summary: "The API exposes explicit routes for operational domains and date-scoped analytics.",
                keywords: ["API", "FastAPI", "OpenAPI", "routes", "analytics", "reconciliation", "settings", "passport"],
                content: `## Key operational routes

| Capability | Route |
| --- | --- |
| Main dashboard | GET /dashboard |
| Settings | GET/PUT /settings |
| Animals | GET/POST /farm/animals |
| Animal passport | GET /farm/animals/{animal_id}/passport |
| Effective milking schedule | GET /farm/animals/{animal_id}/milking-frequency/history |
| Milk entry | POST /farm/milk |
| Milk analytics | GET /farm/milk/analytics |
| Milk production summary | GET /farm/milk/production-summary |
| Milk reconciliation | GET /farm/milk/reconciliation?production_date=YYYY-MM-DD |
| Milk dispositions | GET /farm/milk/dispositions |
| Analytics catalog | GET /farm/analytics/catalog |
| Analytics implementation contract | GET /farm/analytics/implementation-contract |
| CMP scenarios | GET/POST /farm/cmp/scenarios |
| Heat-stress intelligence | GET /farm/heat-stress/intelligence |
| Operational findings | GET /farm/findings |
| Health observations | GET /farm/health-observations |
| Breeding | GET/POST /farm/breeding |
| Feed | GET/POST /farm/feed |
| Finance | GET/POST /farm/financial |

The generated OpenAPI document at `/openapi.json` is the application-level route contract. Date-scoped analytics should reject an omitted required date rather than silently guessing one.`
            },
            {
                id: "technical-database",
                title: "3. PostgreSQL and persistence",
                summary: "PostgreSQL is the authoritative production datastore with environment-driven SQLAlchemy configuration.",
                keywords: ["PostgreSQL", "SQLAlchemy", "psycopg", "DATABASE_URL", "migration", "backup", "restore", "schema"],
                content: `## Connection configuration

The single database session module resolves the connection from **DAIRYOS_DATABASE_URL** first, then DAIRYOS_DB_HOST/PORT/NAME/USER/PASSWORD. SQLAlchemy uses the **postgresql+psycopg** dialect.

Production startup refuses to fall back to the well-known development password when an explicit production password is absent.

## Schema and migrations

ORM models are registered at the database initialization boundary. Schema evolution belongs to the migration layer; runtime create_all is an initialization boundary, not a substitute for controlled production migrations.

## Backup

Use `scripts/database_backup.py` for PostgreSQL dumps and verification. The backup utility normalizes SQLAlchemy PostgreSQL URLs to a libpq-compatible target and does not place the database password in the command-line target. Prefer a disposable restore target for acceptance testing.`
            },
            {
                id: "technical-configuration",
                title: "4. Deployment configuration",
                summary: "Use explicit environment configuration for development and production deployments.",
                keywords: ["deployment", "Docker", "Compose", "environment", "production", "frontend", "port", "CORS"],
                content: `## Local development

Typical local configuration uses PostgreSQL on localhost:5432 and a development environment. The web application defaults to the backend at http://127.0.0.1:8000 unless an explicit frontend API URL is supplied.

## Docker Compose

The production compose configuration supplies explicit PostgreSQL credentials and a production authentication secret through environment variables. The API waits for a healthy database service before starting.

## Frontend build

The React/Vite application is built with `npm ci` followed by `npm run build`. The build must pass TypeScript checking before Vite emits production assets.

## CORS

Allowed browser origins are intentionally constrained to the local operator-development port range. Production deployments should set an explicit, reviewed frontend origin policy rather than broadly enabling cross-origin access.`
            },
            {
                id: "technical-device",
                title: "5. Sensors and device integration",
                summary: "Device protocols must feed persisted dated observations; they do not become a second source of truth.",
                keywords: ["sensor", "telemetry", "device", "IoT", "THI", "environment", "protocol", "observation"],
                content: `## Integration pattern

Device or telemetry adapters should submit observed facts with an explicit observation date/time, source identifier and attributable payload. The integration boundary should validate the payload before persistence.

### Environmental telemetry

Heat-stress intelligence consumes persisted environmental observations and governed milk production dates. Correlations should only be reported when both source populations have sufficient coverage.

### Recommended device contract

Minimum message envelope: ` + "`source_id`, `observed_at`, `measurement_type`, `value`, `unit`, `quality/status`." + `

Avoid embedding dashboard-only calculations in devices. Store measurements; derive farm intelligence in the backend.`
            },
            {
                id: "technical-diagnostics",
                title: "6. Diagnostics, errors and logs",
                summary: "Diagnose from the runtime boundary inward and preserve exact error evidence.",
                keywords: ["diagnostics", "logs", "logging", "error", "traceback", "health", "readiness", "CI"],
                content: `## Runtime checks

- **GET /health**: service health.
- **GET /readiness**: readiness including database/runtime state.
- **GET /openapi.json**: mounted API contract.

## Log handling

The FastAPI bootstrap configures standard application logging. Milk post-write monitoring errors are logged after a successful persisted milk write because derived monitoring must not block the primary fact.

### Diagnostic sequence

1. Capture the exact failing route and HTTP status.
2. Capture the server log entry and traceback.
3. Determine whether persistence succeeded before a derived observer failed.
4. Check PostgreSQL connectivity and migration/schema state.
5. Reproduce with the smallest valid request using a persisted system-generated Animal ID where required.

Never log passwords, authentication secrets, full connection strings or other credentials.`
            },
            {
                id: "technical-testing",
                title: "7. Testing and release gates",
                summary: "Use backend regression, compile checks and frontend production builds before release.",
                keywords: ["testing", "pytest", "compileall", "Vite", "npm", "CI", "release", "regression"],
                content: `## Required local gates

1. ` + "`pytest -q`" + ` `
 + ` for full Python regression.
2. ` + "`python -m compileall -q src`" + ` `
 + ` for Python syntax/import compilation.
3. ` + "`npm ci`" + ` `
 + ` followed by ` + "`npm run build`" + ` `
 + ` in ` + "`src/DairyOS.Web`" + `.

### CI expectations

CI should use explicit least-privilege workflow permissions, install all test dependencies used by the lifecycle and compose gates, and require the frontend build. Security audits should fail on known production dependency vulnerabilities rather than silently accepting them.`
            },
            {
                id: "technical-security",
                title: "8. Security hardening",
                summary: "Keep credentials external, API enforcement server-side, and destructive operations protected.",
                keywords: ["security", "secret", "password", "authentication", "authorisation", "RBAC", "permissions", "least privilege"],
                content: `## Security rules

- Do not commit `.env`, database dumps, SQLite files or backup artifacts.
- Do not use development default credentials in production.
- Treat frontend visibility as presentation only; enforce permissions in the API.
- Protect destructive reset operations before production deployment.
- Use explicit environment variables or secret management for credentials.
- Keep CI workflow permissions to the minimum required scope.
- Run dependency audits for Python and frontend production dependencies.

### Incident evidence

Preserve request timestamps, route, status code, application error, affected subsystem and relevant commit SHA. Redact secrets before sharing logs.`
            },
        ],
    },
];

export type ManualSearchResult = {
    manualId: ManualAudience;
    manualTitle: string;
    sectionId: string;
    sectionTitle: string;
    summary: string;
    score: number;
};

export const MANUAL_SEARCH_INDEX = MANUALS.flatMap((manual) =>
    manual.sections.map((section) => ({
        manualId: manual.id,
        manualTitle: manual.title,
        sectionId: section.id,
        sectionTitle: section.title,
        searchable: `${manual.title}\n${section.title}\n${section.summary}\n${section.keywords.join(" ")}\n${section.content}`.toLowerCase(),
        summary: section.summary,
    })),
);

export function searchManuals(query: string): ManualSearchResult[] {
    const tokens = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (tokens.length === 0) return [];

    return MANUAL_SEARCH_INDEX
        .map((entry) => {
            const score = tokens.reduce((total, token) => {
                if (entry.sectionTitle.toLowerCase().includes(token)) return total + 6;
                if (entry.searchable.includes(token)) return total + 2;
                return total;
            }, 0);
            return { ...entry, score };
        })
        .filter((entry) => entry.score > 0)
        .sort((a, b) => b.score - a.score || a.sectionTitle.localeCompare(b.sectionTitle))
        .slice(0, 12)
        .map(({ searchable: _searchable, ...result }) => result);
}
