<#
.SYNOPSIS
    RETIRED — historical DairyOS forensic-remediation handover artefact.
.DESCRIPTION
    This script is preserved only as historical audit evidence.

    It is NOT an authorized DairyOS deployment, rollback, recovery, or
    remediation mechanism and must never modify the certified working tree.

    Current DairyOS changes are governed through Git main, exact-SHA
    certification, migrations, regression tests, and the documented recovery
    procedures. Historical handover scripts must not restore old source files
    over a certified baseline.
#>

[CmdletBinding()]
param(
    [switch]$Rollback,
    [string]$BackupDir = ""
)

$ErrorActionPreference = "Stop"

throw @"
RETIRED DAIRYOS HANDOVER ARTEFACT — NO ACTION PERFORMED.

tools/handover/Deploy-DairyOS-ForensicRemediation.ps1 is preserved only for
historical audit traceability. It is intentionally non-operational.

Do not use this file to deploy, roll back, restore, or modify DairyOS source.
Use the current certified main branch and approved DairyOS recovery/deployment
procedures instead.
"@
