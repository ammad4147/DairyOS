# Workforce prerequisite — Tier 1d bootstrap

The first implementation slice replaces the static `/login` token with farm-scoped authenticated users.

## Required runtime configuration

- `DAIRYOS_AUTH_SECRET`: long random signing secret shared by API instances.
- `DAIRYOS_BOOTSTRAP_FARM_ID`: farm identifier for the first owner.
- `DAIRYOS_BOOTSTRAP_USERNAME`: first owner's login name.
- `DAIRYOS_BOOTSTRAP_PASSWORD`: first owner's password; minimum 12 characters.

All four values except the bootstrap settings are required for normal authentication. Bootstrap variables are only used when the specified farm has no users.

## Authorization roles

These are authentication/authorization roles and are deliberately separate from the operational `workforce_roles` vocabulary:

- `owner`
- `manager`
- `milker`

An owner can create any of the three roles. A manager can create managers and milkers, but not owners. User creation is farm-scoped.

## Endpoints

- `POST /login` — authenticate with `farm_id`, `username`, `password`.
- `GET /me` — resolve the signed bearer token to the current persisted identity.
- `POST /users` — owner/manager creates a farm user.

`POST /farm/workforce` now requires authentication and ignores caller-supplied worker identity. The persisted activity records the authenticated user ID, display name, authorization role and farm ID.

## Security notes

Passwords are stored as PBKDF2-SHA256 hashes with per-password random salts. Tokens are signed HMAC-SHA256 bearer tokens with an eight-hour lifetime. The current user is reloaded from the database on every authenticated request, so deactivation takes effect without waiting for token expiry.
