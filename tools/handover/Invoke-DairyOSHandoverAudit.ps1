[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [string]$OutputDirectory = "",
    [switch]$Strict,
    [switch]$IncludeUntrackedArtifacts
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Result {
    param(
        [string]$Id,
        [ValidateSet("PASS", "FAIL", "BLOCKING", "WARN")]
        [string]$Status,
        [string]$Message,
        [string]$Evidence = ""
    )

    return [pscustomobject]@{
        Id       = $Id
        Status   = $Status
        Message  = $Message
        Evidence = $Evidence
    }
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $RepoRoot "audit-results"
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$results = [System.Collections.Generic.List[object]]::new()

$requiredOsSignals = [ordered]@{
    "ISO-IMG-RAW build"       = @("*.iso", "*.img", "*.raw", "*.qcow2", "*.vmdk", "*iso*", "*image*", "*raw*")
    "Bootloader-EFI"          = @("*grub*", "*systemd-boot*", "*.efi", "loader.conf", "grub.cfg")
    "Installer-provisioning"  = @("*kickstart*", "*preseed*", "*cloud-init*", "*autoinstall*", "*installer*", "*provision*")
    "Partitioning"            = @("*partit*", "*sgdisk*", "*parted*", "*fdisk*", "*fstab*", "*wipefs*")
    "Kernel"                  = @("*kernel*", "vmlinuz*", "bzImage*", "initrd*", "initramfs*")
    "PXE-network-boot"        = @("*pxe*", "*ipxe*", "*dnsmasq*", "*tftp*", "*netboot*")
    "Teardown-rollback"       = @("*uninstall*", "*teardown*", "*rollback*", "*purge*")
}

$allFiles = @(
    Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force |
        Where-Object {
            $_.FullName -notmatch '[\\/]\.git[\\/]' -and
            $_.FullName -notmatch '[\\/]node_modules[\\/]' -and
            $_.FullName -notmatch '[\\/]\.venv[\\/]'
        }
)

foreach ($category in $requiredOsSignals.Keys) {
    $categoryMatches = [System.Collections.Generic.List[object]]::new()

    foreach ($pattern in $requiredOsSignals[$category]) {
        foreach ($file in $allFiles) {
            if (($file.Name -like $pattern) -or ($file.FullName -like $pattern)) {
                $categoryMatches.Add($file)
            }
        }
    }

    $uniqueMatches = @($categoryMatches | Sort-Object FullName -Unique)
    $id = "P0-$category"

    if ($uniqueMatches.Count -gt 0) {
        $evidence = (@($uniqueMatches | Select-Object -First 20 -ExpandProperty FullName) -join "; ")
        $results.Add((Write-Result $id "PASS" "$category evidence found." $evidence))
    }
    else {
        $results.Add((Write-Result $id "BLOCKING" "$category evidence not found in repository." "Phase 0 mandatory artifact inventory"))
    }
}

$sourceExtensions = @(
    ".ps1", ".psm1", ".sh", ".bash", ".yml", ".yaml", ".toml", ".ini",
    ".cfg", ".conf", ".service", ".md", ".txt", ".py", ".js", ".ts",
    ".tsx", ".json"
)
$sourceFiles = @($allFiles | Where-Object { $_.Extension -in $sourceExtensions })

$tokens = @(
    "grub", "systemd", "kickstart", "preseed", "cloud-init", "pxe", "ipxe",
    "mkfs", "sgdisk", "parted", "efibootmgr", "wipefs", "dracut", "initramfs"
)

foreach ($token in $tokens) {
    $hit = $false

    foreach ($file in $sourceFiles) {
        try {
            if (Select-String -LiteralPath $file.FullName -Pattern $token -SimpleMatch -Quiet -ErrorAction Stop) {
                $hit = $true
                break
            }
        }
        catch {
            # Binary or unreadable files are ignored by this text-only inspection.
        }
    }

    if ($hit) {
        $results.Add((Write-Result "P0-TOKEN-$token" "PASS" "Repository text references '$token'." "static source inspection"))
    }
    else {
        $results.Add((Write-Result "P0-TOKEN-$token" "BLOCKING" "No repository text reference to '$token'." "static source inspection"))
    }
}

$appLifecycleTest = Join-Path $RepoRoot "tests\platform\test_lifecycle_manager.py"
if (Test-Path -LiteralPath $appLifecycleTest) {
    $results.Add((Write-Result "P1-APP-LIFECYCLE" "PASS" "Application lifecycle test suite exists, but it is not an OS installer test." $appLifecycleTest))
}
else {
    $results.Add((Write-Result "P1-APP-LIFECYCLE" "WARN" "Application lifecycle test suite not located." $appLifecycleTest))
}

$dockerCompose = Join-Path $RepoRoot "docker-compose.yml"
if (Test-Path -LiteralPath $dockerCompose) {
    $results.Add((Write-Result "P1-CONTAINER-DEPLOYMENT" "PASS" "Container deployment definition exists." $dockerCompose))
}
else {
    $results.Add((Write-Result "P1-CONTAINER-DEPLOYMENT" "WARN" "Container deployment definition missing." $dockerCompose))
}

$hardwarePatterns = @(
    "rfid", "rs485", "serial", "plc", "parlor", "parlour", "touch", "hid",
    "usb", "ethernet", "modbus", "scale"
)

foreach ($pattern in $hardwarePatterns) {
    $hits = [System.Collections.Generic.List[object]]::new()

    foreach ($file in $sourceFiles) {
        try {
            $matches = @(Select-String -LiteralPath $file.FullName -Pattern $pattern -SimpleMatch -ErrorAction Stop | Select-Object -First 3)
            foreach ($match in $matches) {
                $hits.Add($match)
            }
        }
        catch {
            # Ignore binary or unreadable files during static inspection.
        }
    }

    if ($hits.Count -gt 0) {
        $results.Add((Write-Result "P2-HW-$pattern" "PASS" "Static repository references hardware term '$pattern'." "source search"))
    }
    else {
        $results.Add((Write-Result "P2-HW-$pattern" "WARN" "No static repository reference for hardware term '$pattern'." "source search"))
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$jsonPath = Join-Path $OutputDirectory "dairyos-os-handover-$timestamp.json"
$mdPath = Join-Path $OutputDirectory "dairyos-os-handover-$timestamp.md"

$blocking = @($results | Where-Object { $_.Status -eq "BLOCKING" })
$failed = @($results | Where-Object { $_.Status -eq "FAIL" })
$warned = @($results | Where-Object { $_.Status -eq "WARN" })
$passed = @($results | Where-Object { $_.Status -eq "PASS" })

$handoverGate = "BLOCKED"
if (($blocking.Count -eq 0) -and ($failed.Count -eq 0)) {
    $handoverGate = "ELIGIBLE_FOR_NEXT_PHASE"
}

$summary = [ordered]@{
    Repository = $RepoRoot
    Timestamp = (Get-Date).ToString("o")
    Pass = $passed.Count
    Warn = $warned.Count
    Fail = $failed.Count
    Blocking = $blocking.Count
    HandoverGate = $handoverGate
    Results = $results
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# DairyOS OS Handover Audit")
$lines.Add("")
$lines.Add("Generated: $($summary.Timestamp)")
$lines.Add("")
$lines.Add("| Status | Count |")
$lines.Add("|---|---:|")
$lines.Add("| PASS | $($passed.Count) |")
$lines.Add("| WARN | $($warned.Count) |")
$lines.Add("| FAIL | $($failed.Count) |")
$lines.Add("| BLOCKING | $($blocking.Count) |")
$lines.Add("")
$lines.Add("## Gate")
$lines.Add("")
$lines.Add("**$($summary.HandoverGate)**")
$lines.Add("")

foreach ($r in $results) {
    $lines.Add("### $($r.Id) - $($r.Status)")
    $lines.Add("")
    $lines.Add($r.Message)
    $lines.Add("")

    if (-not [string]::IsNullOrWhiteSpace($r.Evidence)) {
        $lines.Add("Evidence: $($r.Evidence)")
        $lines.Add("")
    }
}

$lines -join "`n" | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host ""
Write-Host "DairyOS OS Handover Audit" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
if ($blocking.Count -gt 0) {
    $gateColor = "Red"
}
else {
    $gateColor = "Green"
}
Write-Host "Gate: $($summary.HandoverGate)" -ForegroundColor $gateColor
Write-Host "PASS=$($passed.Count) WARN=$($warned.Count) FAIL=$($failed.Count) BLOCKING=$($blocking.Count)"
Write-Host "JSON : $jsonPath"
Write-Host "MD   : $mdPath"

if ($Strict -and (($blocking.Count -gt 0) -or ($failed.Count -gt 0))) {
    exit 2
}

exit 0
