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
$package = Join-Path $root "DairyOS-Assistant.dairyassistant"
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
$corpusManifestPath = Join-Path $packRoot "_internal\assistant-knowledge\manifest.json"
if (-not (Test-Path $corpusManifestPath -PathType Leaf)) { throw "Assistant corpus manifest is missing from the frozen package." }
$corpusManifest = Get-Content $corpusManifestPath -Raw | ConvertFrom-Json
if ([string]$corpusManifest.dairyos_source_commit -notmatch '^[0-9a-f]{40}$') {
    throw "Assistant corpus manifest has no exact source commit."
}
$manifest.corpus_source_commit = [string]$corpusManifest.dairyos_source_commit
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $packRoot "assistant-manifest.json") -Encoding utf8
$integrityFiles = [ordered]@{}
Get-ChildItem -LiteralPath $packRoot -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($packRoot.Length + 1).Replace('\', '/')
    $integrityFiles[$relative] = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
@{ format = "dairyassistant-integrity-v1"; files = $integrityFiles } |
    ConvertTo-Json -Depth 8 | Set-Content (Join-Path $packRoot "assistant-package-integrity.json") -Encoding utf8
$archive = Join-Path $root "DairyOS-Assistant.zip"
Compress-Archive -Path (Join-Path $packRoot "*") -DestinationPath $archive -CompressionLevel Optimal
Move-Item -LiteralPath $archive -Destination $package -Force
$hash = (Get-FileHash $package -Algorithm SHA256).Hash.ToLowerInvariant()
$size = (Get-Item $package).Length
$manifest.package_size_bytes = $size
$manifest.sha256 = $hash
$hash | Set-Content ($package + ".sha256") -Encoding ascii
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $root "DairyOS-Assistant.release.json") -Encoding utf8
Write-Host "DAIRYOS ASSISTANT PACKAGE BUILD: PASS" -ForegroundColor Green
Get-Item $package | Select-Object FullName,Length
Get-FileHash $package -Algorithm SHA256
