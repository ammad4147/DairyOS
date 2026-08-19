#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$remote = "origin/audit/os-handover-2026-08-19"
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"

$root = Join-Path $PWD ".dairyo-reconciliation"
$out  = Join-Path $root "os-handover-inspection-$stamp"

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Remote OS Handover Forensic Inspection" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

git fetch origin --prune

$remoteHead = (git rev-parse $remote).Trim()
$remoteTree = (git rev-parse "$remote^{tree}").Trim()

Write-Host "Remote ref : $remote"
Write-Host "Remote HEAD: $remoteHead"
Write-Host "Remote tree: $remoteTree"
Write-Host ""

# ------------------------------------------------------------
# 1. Complete tracked-file inventory
# ------------------------------------------------------------

Write-Host "=== COMPLETE REMOTE FILE INVENTORY ===" -ForegroundColor Cyan

$allFiles = @(
    git ls-tree -r --name-only $remote
)

$allFiles |
    Sort-Object |
    Set-Content `
        -LiteralPath (Join-Path $out "remote-complete-file-inventory.txt") `
        -Encoding UTF8

Write-Host "Remote tracked files: $($allFiles.Count)"

# ------------------------------------------------------------
# 2. Handover / installation / deployment candidates
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE HANDOVER / INSTALLATION FILES ===" -ForegroundColor Cyan

$handoverFiles = @(
    $allFiles |
        Where-Object {
            $_ -match '(?i)(install|uninstall|handover|bootstrap|first.?boot|rollback|recovery|image|iso|mirror|offline|air.?gap|uefi|grub|systemd|partition|disk|deployment)'
        }
)

$handoverFiles |
    Sort-Object |
    Tee-Object `
        -FilePath (Join-Path $out "remote-handover-files.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 3. Operational scripts
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE POWERSHELL / SHELL / SERVICE FILES ===" -ForegroundColor Cyan

$scriptFiles = @(
    $allFiles |
        Where-Object {
            $_ -match '(?i)\.(ps1|psm1|sh|bash|service|timer)$'
        }
)

$scriptFiles |
    Sort-Object |
    Tee-Object `
        -FilePath (Join-Path $out "remote-operational-scripts.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 4. Explicit install/uninstall candidates
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE INSTALL / UNINSTALL CANDIDATES ===" -ForegroundColor Cyan

$installCandidates = @(
    $allFiles |
        Where-Object {
            $_ -match '(?i)(^|[/\\])(install|installer|uninstall|uninstaller|remove|setup|deploy|provision|bootstrap|first.?boot|rollback|recovery)'
        }
)

$installCandidates |
    Sort-Object |
    Tee-Object `
        -FilePath (Join-Path $out "remote-install-uninstall-candidates.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 5. OS-related documentation
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE OS DOCUMENTATION ===" -ForegroundColor Cyan

$documentationFiles = @(
    $allFiles |
        Where-Object {
            $_ -match '(?i)\.(md|txt|rst)$' -and
            $_ -match '(?i)(handover|install|uninstall|deployment|offline|air.?gap|os|recovery|rollback|boot)'
        }
)

$documentationFiles |
    Sort-Object |
    Tee-Object `
        -FilePath (Join-Path $out "remote-os-documentation.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 6. Remote OS-related commit history
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE COMMITS RELATED TO OS HANDOVER ===" -ForegroundColor Cyan

$commitSubjects = @(
    git log --format="%H`t%ad`t%s" --date=iso-strict $remote
)

$focusedCommits = @(
    $commitSubjects |
        Where-Object {
            $_ -match '(?i)(install|uninstall|handover|bootstrap|first.?boot|rollback|recovery|mirror|offline|air.?gap|uefi|grub|os|bare.?metal|postgres)'
        }
)

if ($focusedCommits.Count -eq 0) {
    Write-Host "No matching commit subjects found." -ForegroundColor Yellow
}
else {
    $focusedCommits |
        Tee-Object `
            -FilePath (Join-Path $out "remote-os-related-commits.txt") |
        ForEach-Object {
            Write-Host $_
        }
}

# ------------------------------------------------------------
# 7. Top-level repository map
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE TOP-LEVEL DIRECTORY MAP ===" -ForegroundColor Cyan

$topLevel = @(
    $allFiles |
        ForEach-Object {
            ($_ -split '[\\/]') | Select-Object -First 1
        } |
        Sort-Object -Unique
)

$topLevel |
    Tee-Object `
        -FilePath (Join-Path $out "remote-top-level-map.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 8. FAST CONTENT SEARCH
#
# git grep searches the tree directly instead of repeatedly fetching
# every file with git show. This is the key performance correction.
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== CONTENT SEARCH FOR OS HANDOVER TERMS ===" -ForegroundColor Cyan

$searchTerms = @(
    "DAIRYOS_INSTALL",
    "DAIRYOS_UNINSTALL",
    "uninstall",
    "installer",
    "install",
    "rollback",
    "recovery",
    "air.gap",
    "offline",
    "local mirror",
    "Debian mirror",
    "first boot",
    "postgresql",
    "grub",
    "UEFI",
    "partition",
    "bare metal"
)

$searchResultsFile = Join-Path $out "remote-os-term-search.txt"

if (Test-Path $searchResultsFile) {
    Remove-Item -LiteralPath $searchResultsFile -Force
}

foreach ($term in $searchTerms) {

    Write-Host ""
    Write-Host "--- SEARCH: $term ---" -ForegroundColor Yellow

    # -I = ignore binary files
    # -n = line numbers
    # -i = case-insensitive
    # --fixed-strings = literal term rather than regex
    #
    # A pattern containing spaces is fine here because $term is passed
    # as a single argument.

    $matches = @(
        git grep `
            -I `
            -n `
            -i `
            --fixed-strings `
            -- "$term" `
            $remote
        2>$null
    )

    if ($matches.Count -eq 0) {
        Write-Host "No matches."
        continue
    }

    foreach ($match in $matches) {
        $line = "[{0}] {1}" -f $term, $match
        Add-Content -LiteralPath $searchResultsFile -Value $line -Encoding UTF8
        Write-Host $line
    }
}

# ------------------------------------------------------------
# 9. Boot / disk / persistence candidates
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== REMOTE BOOT / DISK / PERSISTENCE CANDIDATES ===" -ForegroundColor Cyan

$bootPersistenceFiles = @(
    $allFiles |
        Where-Object {
            $_ -match '(?i)(boot|uefi|grub|efi|partition|disk|mount|fstab|postgres|database|rollback|recovery|persistence|image|iso)'
        }
)

$bootPersistenceFiles |
    Sort-Object |
    Tee-Object `
        -FilePath (Join-Path $out "remote-boot-disk-persistence-files.txt") |
    ForEach-Object {
        Write-Host $_
    }

# ------------------------------------------------------------
# 10. Exact remote snapshots of selected high-value files
# ------------------------------------------------------------

Write-Host ""
Write-Host "=== SELECTED REMOTE FILE SNAPSHOTS ===" -ForegroundColor Cyan

$focusFiles = @(
    "tools/handover/Invoke-DairyOSAllTests.ps1",
    "src/dairyos/api/farm_planning.py",
    "src/dairyos/data/repositories/repository_factory.py",
    "src/dairyos/farm/operations/repositories/adapters/database_breeding_repository.py"
)

foreach ($file in $focusFiles) {

    Write-Host ""
    Write-Host "--- $file ---" -ForegroundColor Yellow

    git cat-file -e "$remote`:$file" 2>$null
    $exists = ($LASTEXITCODE -eq 0)

    if ($exists) {

        $safeName = $file -replace '[\\/:]', '__'
        $destination = Join-Path $out "$safeName.remote"

        git show "$remote`:$file" |
            Set-Content `
                -LiteralPath $destination `
                -Encoding UTF8

        Write-Host "Saved: $destination" -ForegroundColor Green
    }
    else {
        Write-Host "NOT PRESENT on remote." -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------
# 11. Final report
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INSPECTION COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Output directory:" -ForegroundColor Green
Write-Host $out -ForegroundColor Green
Write-Host ""

Write-Host "NO SOURCE FILE WAS MODIFIED."
Write-Host "NO CHECKOUT / RESET / MERGE / REBASE / CLEAN WAS PERFORMED."
Write-Host ""

