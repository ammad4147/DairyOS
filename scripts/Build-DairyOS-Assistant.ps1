[CmdletBinding()]
param(
    [string]$OutputRoot = "dist\DairyOS-Assistant-Release"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$head = (@(& git rev-parse HEAD) -join "").Trim()
$tree = (@(& git rev-parse "$head^{tree}") -join "").Trim()
if ($head -notmatch '^[0-9a-f]{40}$' -or $tree -notmatch '^[0-9a-f]{40}$') {
    throw "Assistant package requires an exact Git source commit and tree."
}
if ((@(& git status --porcelain) -join "`n").Trim()) {
    throw "Assistant package builds require a clean worktree."
}

& (Join-Path $PSScriptRoot "Get-AssistantRuntime.ps1")
$root = [IO.Path]::GetFullPath((Join-Path $repo $OutputRoot))
$staging = Join-Path $root "staging"
$package = Join-Path $root "DairyOS-Assistant-Pack.zip"
Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $staging -Force | Out-Null

python -m PyInstaller --noconfirm --clean --distpath $staging --workpath (Join-Path $repo "build\DairyOS-Assistant-Release") (Join-Path $repo "DairyOS-Assistant.spec")
if ($LASTEXITCODE -ne 0) { throw "Assistant PyInstaller build failed." }

$packRoot = Join-Path $staging "DairyOS-Assistant-Pack"
$manifest = [ordered]@{
    manifest_version = 1
    package_id = "dairyos-assistant"
    assistant_version = "0.1.0"
    compatible_core = ">=0.1.0 <0.2.0"
    model_identity = "Qwen3-1.7B-Q4_K_M"
    runtime_identity = "llama-server"
    source_commit = $head
    source_tree = $tree
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $packRoot "assistant-manifest.json") -Encoding utf8
Compress-Archive -Path (Join-Path $packRoot "*") -DestinationPath $package -CompressionLevel Optimal
$hash = (Get-FileHash $package -Algorithm SHA256).Hash.ToLowerInvariant()
$size = (Get-Item $package).Length
$manifest.package_size_bytes = $size
$manifest.sha256 = $hash
$hash | Set-Content ($package + ".sha256") -Encoding ascii
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $root "DairyOS-Assistant.release.json") -Encoding utf8
Write-Host "DAIRYOS ASSISTANT PACKAGE BUILD: PASS" -ForegroundColor Green
Get-Item $package | Select-Object FullName,Length
Get-FileHash $package -Algorithm SHA256
