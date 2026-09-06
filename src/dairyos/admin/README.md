# DairyOS Administration Tool

The Admin Tool is a standalone privileged lifecycle and recovery surface. It is not part of the nine-tab operational DairyOS UI and it never uses the PostgreSQL administrator password as the human administrator credential.

## Authentication lifecycle

- First launch requires creation of a DairyOS Admin password.
- Passwords are never stored in plaintext; only a salted PBKDF2-SHA256 verifier is persisted.
- Setup issues a high-entropy recovery key. Only its verifier is stored.
- Every password change or recovery rotates the recovery key and invalidates the previous one.
- Normal sessions require the Admin password.
- Restore, rollback, reset, purge and uninstall require fresh password re-entry.
- Reset and purge additionally retain the exact operation-specific confirmation phrases.
- Failed/successful authentication and lifecycle actions are written to the Admin audit log.
- There is no master password, developer bypass, or automatic recovery-key reset.

## Administrative operations

The GUI and CLI provide:
- Validate installation and database health
- Create verified backup
- Restore a verified snapshot
- Roll back to a verified snapshot
- Reset operational farm data
- Permanently purge the data root after external recovery backup
- Uninstall while retaining data
- Change administrator password
- Recover administrator password with the recovery key
- Review administrative audit history

## Safety boundary

The existing lifecycle safeguards remain authoritative. Reset requires a healthy configured database, a verified pre-reset backup, stopped operational runtime, external recovery copy, checksum validation, zero-state verification, and automatic rollback on failure.

The Admin Tool binds only to loopback addresses.
