# Security Policy

## Supported branch

The active implementation line is `post-dashboard-reconciliation`.

## Reporting a vulnerability

Do not open a public GitHub issue for a suspected security vulnerability.

Report privately through the repository owner's GitHub contact channel and include:

- affected component or route;
- reproducible steps or proof of concept;
- impact assessment;
- relevant logs or screenshots with secrets removed;
- the first known affected commit, when available.

Do not include passwords, API tokens, database credentials, or other secrets in reports.

## Credential handling

DairyOS configuration supports environment-based database credentials and production startup requires an explicit PostgreSQL password or database URL. Local `.env` files and generated database backups are excluded from version control.

## Release hardening

Before a production release, verify that:

1. required CI checks are green;
2. the production database password and authentication secret are supplied outside source control;
3. database backups are created and independently verified;
4. the deployed image is rebuilt from the reviewed commit;
5. no new high-severity production dependency vulnerability is accepted without an explicit risk decision.
