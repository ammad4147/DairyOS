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
        purpose: "A practical guide for daily herd, feed, milk, health, breeding, findings and finance work.",
        sections: [
            {
                id: "operator-start", title: "1. Getting started", summary: "Start each working period from the live operational picture.", keywords: ["login", "dashboard", "navigation", "settings"],
                content: `## Daily start

1. Open DairyOS and confirm **System** is healthy and **Farm** shows the expected operational state.
2. Check **Dashboard** for the current operational picture and decision/alert indicators.
3. Open **Animals** and confirm the herd and milking population are plausible.
4. Review **Alerts & Decisions** before starting repetitive work.
5. Use **Settings → Help & Documentation** whenever a workflow or field definition is unclear.

### Data-entry rule

Record what actually occurred. Do not use zero to mean a missed session and do not invent historical values to fill gaps. Persisted domain records are authoritative; higher-level views are derived from them.`
            },
            {
                id: "operator-animals", title: "2. Herd and animal management", summary: "Maintain one operational identity per animal and use the passport for detailed history.", keywords: ["animals", "herd", "milking", "dry", "heifer", "calf", "passport", "ear tag", "RFID"],
                content: `## Register an animal

1. Open **Animals** and select **Register Animal**.
2. Enter identity information such as ear tag/RFID, breed, sex, date of birth and group/location.
3. Choose **MILKING** or **NON-MILKING**.
4. For milking animals, select the governed **2-session** or **3-session** plan.
5. For non-milking animals, select a reason and document it.
6. Save and confirm the success result.

### Find an animal

Use the Animals search field for partial or exact matches across Animal ID, ear tag/RFID, name or alias, dam/sire, status, lifecycle, breed, sex, group and location.

### Animal passport

Click any animal row to open the full passport. Use it for identity, operational status, effective milking plan, record counts, milk/feed/health/breeding history and timeline.`
            },
            {
                id: "operator-milk", title: "3. Milk logging", summary: "Record actual milk outcomes against the effective session plan and production date.", keywords: ["milk", "milking", "session", "yield", "production date", "morning", "afternoon", "evening", "missed"],
                content: `## Record milk

1. Open **Milk** or choose **Record Milk** from an animal passport.
2. Select an existing animal.
3. Use the session presented for that animal's effective milking frequency.
4. Enter measured litres and operator attribution.
5. Confirm the production date and save.

### Completeness

Expected sessions come from the effective schedule. A missing session remains missing; it is not converted to zero. Analytics distinguish recorded, skipped/not-entered and missing outcomes.

### Reconciliation

Use **Milk Reconciliation** with an explicit production date. Produced litres must be complete before a day can be fully reconciled to dispositions. Unaccounted or over-accounted litres are exceptions, not values to be silently balanced by the UI.`
            },
            {
                id: "operator-feed", title: "4. Feed management", summary: "Record feed activity with quantity and operational attribution.", keywords: ["feed", "feeding", "silage", "TMR", "hay", "quantity", "kg", "ration"],
                content: `## Record feed activity

1. Open **Feeding**.
2. Select the feed type and observed quantity in kilograms.
3. Add group/pen or animal attribution when relevant.
4. Record the operator and save.

### Operating practice

Keep feed records dated to the actual feeding activity. Use persisted records for consumption and cost analysis. Where data is incomplete, leave the deficiency explicit instead of manufacturing an estimate.`
            },
            {
                id: "operator-health", title: "5. Health and treatment monitoring", summary: "Capture observations and treatments as attributable dated events.", keywords: ["health", "treatment", "observation", "symptom", "severity", "temperature", "critical"],
                content: `## Record a health observation

1. Open **Health**.
2. Select the animal.
3. Describe the observation and symptom.
4. Enter temperature when measured.
5. Assign severity.
6. Record the operator and save.

### Follow-up

High and critical observations can create operational attention. Resolve findings only after the underlying farm action is actually completed.`
            },
            {
                id: "operator-breeding", title: "6. Reproduction workflows", summary: "Record reproductive events chronologically and rely on the backend current-state authority.", keywords: ["breeding", "reproduction", "heat", "insemination", "pregnancy", "calving", "dry off", "abortion"],
                content: `## Record reproduction

1. Open **Breeding**.
2. Select the animal.
3. Choose the event type.
4. Enter technician, result, semen/bull and notes as applicable.
5. Record the operator and save.

### Chronology and current state

Historical reproductive facts remain persisted breeding records. Current reproductive state is resolved from chronology by the reproductive-state authority. Same-day calving is exposed as **CALVED** in the API vocabulary. Do not invent a different current state in the frontend.`
            },
            {
                id: "operator-alerts", title: "7. Alerts, findings and decisions", summary: "Treat findings as operational work, not display-only messages.", keywords: ["alerts", "findings", "decisions", "acknowledge", "resolve", "critical", "warning"],
                content: `## Work a finding

1. Open **Alerts & Decisions**.
2. Review source, animal/date context and recommended action.
3. Acknowledge when the responsible person has accepted the work.
4. Perform the farm action in the correct operational section.
5. Resolve only when the condition is actually addressed.

Severity indicates priority; it is not a substitute for underlying domain evidence.`
            },
            {
                id: "operator-finance", title: "8. Finance and sales records", summary: "Keep financial facts attributable and distinguish revenue, receipts and receivables.", keywords: ["finance", "sales", "revenue", "receipt", "receivable", "cash", "bank", "owner withdrawal", "CMP"],
                content: `## Financial transaction entry

Record transaction type, amount, transaction date, category, payment method, counterparty and operator.

### Milk sales

Milk sales originate from persisted milk dispositions. Recognised revenue, amount received and receivable outstanding are separate concepts. An unpaid invoice is not cash received.

### Cost of milk production

CMP scenarios distinguish actual persisted values from scenario assumptions. The backend CMP service remains authoritative for actual milk volume, eligible cost and cost per litre.`
            },
            {
                id: "operator-settings", title: "9. Settings and permissions", summary: "Manage identity, reset protection and documentation without bypassing server authority.", keywords: ["settings", "permissions", "roles", "password", "reset protection", "documentation", "help"],
                content: `## Settings

Use **Settings** to manage farm identity, Animal ID prefix, reset protection and CMP scenarios. Reset-test-data is destructive; use it only during controlled testing and enable protection before production use.

### Permissions

User permissions are governed by the server-side authentication and authorisation layer. Frontend visibility is not a security boundary; a user who must not perform an action must also be denied by the API.`
            },
            {
                id: "operator-troubleshooting", title: "10. Basic troubleshooting", summary: "Use evidence-first checks before escalating an operational problem.", keywords: ["troubleshooting", "offline", "error", "failed", "retry", "diagnostic", "health"],
                content: `## API unavailable

1. Confirm the API process is running.
2. Open **/health** and **/readiness**.
3. Confirm PostgreSQL is reachable.
4. Refresh the affected section.

## A record will not save

Check required fields, animal identity and the operational date/session. Read the returned API error instead of retrying blindly.

## Data looks missing

Check the selected date/period and completeness/data-status indications. DairyOS deliberately avoids turning absence into zero.

## Escalation package

Record time, page, operation, Animal ID if applicable, exact error, production date and last successful action. Never send credentials or secrets in a support report.`
            },
        ],
    },
    {
        id: "technical",
        title: "DairyOS Technical Manual",
        audience: "Technical administrators, developers, deployment and support staff",
        purpose: "A production-oriented reference for architecture, persistence, APIs, configuration, telemetry, diagnostics and release controls.",
        sections: [
            {
                id: "technical-architecture", title: "1. Architecture and authority", summary: "Layered modular architecture with persisted domain facts and backend-derived read models.", keywords: ["architecture", "Clean Architecture", "DDD", "SOLID", "domain", "service", "repository", "authority"],
                content: `## Runtime model

DairyOS uses a Python/FastAPI backend with SQLAlchemy persistence and a React/Vite operator application. The backend is organised around models, repositories, application/domain services and API routers. The web shell consumes backend-authoritative read contracts.

### Authority principle

Authoritative domain data is persisted once. Higher layers consume lower-layer truth and must not redefine it. Current operational state, effective milking schedule, milk completeness, reconciliation, dispositions and analytics each have explicit backend authorities.

### Main runtime surfaces

- **FastAPI:** API/runtime boundary.
- **SQLAlchemy:** PostgreSQL persistence boundary.
- **Repository layer:** persistence adapters and domain access.
- **Service layer:** business rules and derived intelligence.
- **React/Vite:** operator presentation and navigation.
- **Settings documentation:** bundled static help with no API dependency.`
            },
            {
                id: "technical-api", title: "2. API contract map", summary: "Explicit operational routes with date-scoped analytics contracts.", keywords: ["API", "FastAPI", "OpenAPI", "routes", "analytics", "reconciliation", "settings", "passport"],
                content: `## Key operational routes

- Dashboard: GET /dashboard
- Settings: GET/PUT /settings
- Animals: GET/POST /farm/animals
- Animal passport: GET /farm/animals/{animal_id}/passport
- Effective milking schedule: GET /farm/animals/{animal_id}/milking-frequency/history
- Milk entry: POST /farm/milk
- Milk analytics: GET /farm/milk/analytics
- Milk production summary: GET /farm/milk/production-summary
- Milk reconciliation: GET /farm/milk/reconciliation?production_date=YYYY-MM-DD
- Milk dispositions: GET /farm/milk/dispositions
- Analytics catalog: GET /farm/analytics/catalog
- Analytics implementation contract: GET /farm/analytics/implementation-contract
- CMP scenarios: GET/POST /farm/cmp/scenarios
- Heat-stress intelligence: GET /farm/heat-stress/intelligence
- Findings: GET /farm/findings
- Health observations: GET /farm/health-observations
- Breeding: GET/POST /farm/breeding
- Feed: GET/POST /farm/feed
- Finance: GET/POST /farm/financial

The generated **/openapi.json** is the application-level route contract. Date-scoped analytics should reject an omitted required date rather than silently guessing one.`
            },
            {
                id: "technical-database", title: "3. PostgreSQL and persistence", summary: "PostgreSQL is authoritative with environment-driven SQLAlchemy configuration.", keywords: ["PostgreSQL", "SQLAlchemy", "psycopg", "DATABASE_URL", "migration", "backup", "restore", "schema"],
                content: `## Connection configuration

The database session module resolves **DAIRYOS_DATABASE_URL** first, then DAIRYOS_DB_HOST/PORT/NAME/USER/PASSWORD. SQLAlchemy uses the **postgresql+psycopg** dialect.

Production startup refuses to fall back to the well-known development password when an explicit production password is absent.

## Schema and migrations

ORM models are registered at the database initialization boundary. Schema evolution belongs to the migration layer; runtime create_all is an initialization boundary, not a substitute for controlled production migrations.

## Backup

Use the database_backup.py utility for PostgreSQL dumps and verification. The utility normalizes SQLAlchemy PostgreSQL URLs to a libpq-compatible target and does not place the database password in the command-line target. Prefer a disposable restore target for acceptance testing.`
            },
            {
                id: "technical-configuration", title: "4. Deployment configuration", summary: "Use explicit environment configuration for development and production deployments.", keywords: ["deployment", "Docker", "Compose", "environment", "production", "frontend", "port", "CORS"],
                content: `## Local development

Typical local configuration uses PostgreSQL on localhost:5432. The web application defaults to http://127.0.0.1:8000 unless an explicit frontend API URL is supplied.

## Docker Compose

Production compose supplies explicit PostgreSQL credentials and an authentication secret through environment variables. The API waits for a healthy database service before starting.

## Frontend build

Run npm ci followed by npm run build in src/DairyOS.Web. TypeScript checking must pass before Vite emits production assets.

## CORS

Browser origins are intentionally constrained to the reviewed local operator-development port range. Production deployments should set an explicit frontend origin policy.`
            },
            {
                id: "technical-device", title: "5. Sensors and device integration", summary: "Device protocols feed persisted dated observations and do not become a second source of truth.", keywords: ["sensor", "telemetry", "device", "IoT", "THI", "environment", "protocol", "observation"],
                content: `## Integration pattern

Device or telemetry adapters should submit observed facts with explicit observation date/time, source identifier and attributable payload. Validate the payload at the integration boundary before persistence.

### Environmental telemetry

Heat-stress intelligence consumes persisted environmental observations and governed milk production dates. Correlation should only be reported when both source populations have sufficient coverage.

### Recommended message envelope

Use fields equivalent to source_id, observed_at, measurement_type, value, unit and quality/status.

Do not embed dashboard-only calculations in devices. Store measurements; derive farm intelligence in the backend.`
            },
            {
                id: "technical-diagnostics", title: "6. Diagnostics, errors and logs", summary: "Diagnose from the runtime boundary inward and preserve exact error evidence.", keywords: ["diagnostics", "logs", "logging", "error", "traceback", "health", "readiness", "CI"],
                content: `## Runtime checks

- **GET /health**: service health.
- **GET /readiness**: readiness including database/runtime state.
- **GET /openapi.json**: mounted API contract.

## Diagnostic sequence

1. Capture the failing route and HTTP status.
2. Capture the server log entry and traceback.
3. Determine whether persistence succeeded before a derived observer failed.
4. Check PostgreSQL connectivity and migration/schema state.
5. Reproduce with the smallest valid request.

Never log passwords, authentication secrets, full connection strings or other credentials.`
            },
            {
                id: "technical-testing", title: "7. Testing and release gates", summary: "Use backend regression, compile checks and frontend production builds before release.", keywords: ["testing", "pytest", "compileall", "Vite", "npm", "CI", "release", "regression"],
                content: `## Required local gates

1. Run **pytest -q** for full Python regression.
2. Run **python -m compileall -q src** for Python compilation.
3. In **src/DairyOS.Web**, run **npm ci** then **npm run build**.

### CI expectations

CI should use least-privilege workflow permissions, install all test dependencies used by lifecycle and compose gates, require the frontend build and fail on known production dependency vulnerabilities.`
            },
            {
                id: "technical-security", title: "8. Security hardening", summary: "Keep credentials external, API enforcement server-side, and destructive operations protected.", keywords: ["security", "secret", "password", "authentication", "authorisation", "RBAC", "permissions", "least privilege"],
                content: `## Security rules

- Do not commit .env files, database dumps, SQLite files or backup artifacts.
- Do not use development default credentials in production.
- Treat frontend visibility as presentation only; enforce permissions in the API.
- Protect destructive reset operations before production deployment.
- Use explicit environment variables or secret management for credentials.
- Keep CI workflow permissions to the minimum required scope.
- Run dependency audits for Python and frontend production dependencies.

### Incident evidence

Preserve timestamps, route, status code, application error, affected subsystem and relevant commit SHA. Redact secrets before sharing logs.`
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
