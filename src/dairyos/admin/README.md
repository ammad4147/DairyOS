# DairyOS Administration Tool

The administrative tool is a separate operator surface for privileged lifecycle and recovery operations. It is not part of the nine-tab DairyOS operational UI.

## Boundary

The operational application does not provide an administrative password gate. Privileged actions are performed from this standalone tool and delegated to the canonical `dairyos.lifecycle` services.

## Entry point

`dairyos-admin` starts the standalone local administration UI.

The lifecycle CLI remains available as a low-level automation interface through `dairyos-lifecycle`.

## Safety rules

- Never call the operational `/settings/reset` endpoint for administrative reset.
- Destructive operations require explicit operation-specific confirmation tokens.
- Reset must create and verify a recovery artifact before mutation.
- Purge uses the existing external-backup boundary so the recovery artifact survives data-root deletion.
- Restore must verify snapshot file hashes before restoring.
- Database dumps must gain independent SHA-256 recording and restore verification before release clearance.
