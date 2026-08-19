# DairyOS Operator Manual

**Audience:** Farm operators, supervisors and authorised users  
**Offline system location:** Settings → Help & Documentation

## 1. Getting started

### Daily start

1. Open DairyOS and confirm **System** is healthy and **Farm** shows the expected operational state.
2. Check **Dashboard** for the current operational picture and decision/alert indicators.
3. Open **Animals** and confirm the herd and milking population are plausible.
4. Review **Alerts & Decisions** before starting repetitive work.
5. Use **Settings → Help & Documentation** whenever a workflow or field definition is unclear.

### Data-entry rule

Record what actually occurred. Do not use zero to mean a missed session and do not invent historical values to fill gaps. Persisted domain records are authoritative; higher-level views are derived from them.

## 2. Herd and animal management

### Register an animal

1. Open **Animals** and select **Register Animal**.
2. Enter identity information such as ear tag/RFID, breed, sex, date of birth and group/location.
3. Choose **MILKING** or **NON-MILKING**.
4. For milking animals, select the governed **2-session** or **3-session** plan.
5. For non-milking animals, select a reason and document it.
6. Save and confirm the success result.

### Find an animal

Use the Animals search field for partial or exact matches across Animal ID, ear tag/RFID, name or alias, dam/sire, status, lifecycle, breed, sex, group and location.

### Animal passport

Click any animal row to open the full passport. Use it for identity, operational status, effective milking plan, record counts, milk/feed/health/breeding history and timeline.

## 3. Milk logging

### Record milk

1. Open **Milk** or choose **Record Milk** from an animal passport.
2. Select an existing animal.
3. Use the session presented for that animal's effective milking frequency.
4. Enter measured litres and operator attribution.
5. Confirm the production date and save.

### Completeness

Expected sessions come from the effective schedule. A missing session remains missing; it is not converted to zero. Analytics distinguish recorded, skipped/not-entered and missing outcomes.

### Reconciliation

Use **Milk Reconciliation** with an explicit production date. Produced litres must be complete before a day can be fully reconciled to dispositions. Unaccounted or over-accounted litres are exceptions, not values to be silently balanced by the UI.

## 4. Feed management

1. Open **Feeding**.
2. Select the feed type and observed quantity in kilograms.
3. Add group/pen or animal attribution when relevant.
4. Record the operator and save.

Keep feed records dated to the actual feeding activity. Use persisted records for consumption and cost analysis. Where data is incomplete, leave the deficiency explicit instead of manufacturing an estimate.

## 5. Health and treatment monitoring

1. Open **Health**.
2. Select the animal.
3. Describe the observation and symptom.
4. Enter temperature when measured.
5. Assign severity.
6. Record the operator and save.

High and critical observations can create operational attention. Resolve findings only after the underlying farm action is actually completed.

## 6. Reproduction workflows

1. Open **Breeding**.
2. Select the animal.
3. Choose the event type.
4. Enter technician, result, semen/bull and notes as applicable.
5. Record the operator and save.

Historical reproductive facts remain persisted breeding records. Current reproductive state is resolved from chronology by the reproductive-state authority. Same-day calving is exposed as **CALVED** in the API vocabulary. Do not invent a different current state in the frontend.

## 7. Alerts, findings and decisions

1. Open **Alerts & Decisions**.
2. Review source, animal/date context and recommended action.
3. Acknowledge when the responsible person has accepted the work.
4. Perform the farm action in the correct operational section.
5. Resolve only when the condition is actually addressed.

Severity indicates priority; it is not a substitute for underlying domain evidence.

## 8. Finance and sales records

Record transaction type, amount, transaction date, category, payment method, counterparty and operator.

### Milk sales

Milk sales originate from persisted milk dispositions. Recognised revenue, amount received and receivable outstanding are separate concepts. An unpaid invoice is not cash received.

### Cost of milk production

CMP scenarios distinguish actual persisted values from scenario assumptions. The backend CMP service remains authoritative for actual milk volume, eligible cost and cost per litre.

## 9. Settings and permissions

Use **Settings** to manage farm identity, Animal ID prefix, reset protection and CMP scenarios.

Reset-test-data is destructive. Use it only during controlled testing and enable protection before production use.

User permissions are governed by the server-side authentication and authorisation layer. Frontend visibility is not a security boundary; a user who must not perform an action must also be denied by the API.

## 10. Basic troubleshooting

### API unavailable

1. Confirm the API process is running.
2. Open **/health** and **/readiness**.
3. Confirm PostgreSQL is reachable.
4. Refresh the affected section.

### A record will not save

Check required fields, animal identity and the operational date/session. Read the returned API error instead of retrying blindly.

### Data looks missing

Check the selected date/period and completeness/data-status indications. DairyOS deliberately avoids turning absence into zero.

### Escalation package

Record time, page, operation, Animal ID if applicable, exact error, production date and last successful action. Never send credentials or secrets in a support report.

## 11. Quick operational reference

| Task | Primary view | Important rule |
| --- | --- | --- |
| Register animal | Animals | Choose current MILKING/NON-MILKING state |
| Review history | Animal Passport | Use the backend passport chronology |
| Enter milk | Milk | Use the governed session and production date |
| Reconcile milk | Milk Reconciliation | Supply an explicit production date |
| Enter feed | Feeding | Record actual quantity and date |
| Enter health | Health | Attribute the observation and severity |
| Enter breeding | Breeding | Preserve event chronology |
| Work findings | Alerts & Decisions | Resolve only after action |
| Manage settings | Settings | Protect destructive reset before production |
| Get help | Settings / Help | Search locally with Help or Ctrl+K |
