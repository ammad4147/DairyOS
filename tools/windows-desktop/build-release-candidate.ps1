$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repo

$buildRoot = Join-Path $repo 'build\DairyOS-Release'
$distRoot = Join-Path $repo 'dist\DairyOS-Release'

Remove-Item $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $distRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null

Write-Host '=== BUILDING REACT FRONTEND ==='
npm --prefix "$repo\src\DairyOS.Web" run build
if ($LASTEXITCODE -ne 0) { throw "React production build failed with exit code $LASTEXITCODE" }

$frontendIndex = Join-Path $repo 'src\DairyOS.Web\dist\index.html'
if (-not (Test-Path -LiteralPath $frontendIndex -PathType Leaf)) {
    throw 'React production build completed without dist/index.html'
}

Write-Host '=== BUILDING DAIRYOS ONEDIR APPLICATION ==='
python -m PyInstaller `
    --clean `
    --noconfirm `
    --onedir `
    --windowed `
    --name DairyOS `
    --distpath $distRoot `
    --workpath (Join-Path $repo 'build\pyinstaller-release') `
    --collect-submodules dairyos `
    --collect-submodules alembic `
    --collect-submodules sqlalchemy `
    --collect-all webview `
    --add-data "$repo\alembic.ini;." `
    --add-data "$repo\db_migrations;db_migrations" `
    --add-data "$repo\src\DairyOS.Web\dist;src/DairyOS.Web/dist" `
    "$repo\src\dairyos\windows\supervisor.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed with exit code $LASTEXITCODE" }

$bundle = Join-Path $distRoot 'DairyOS'
$exe = Join-Path $bundle 'DairyOS.exe'
if (-not (Test-Path $exe)) { throw "PyInstaller output missing: $exe" }

Write-Host '=== COPYING PRIVATE POSTGRESQL RUNTIME ==='
$targetRuntime = Join-Path $bundle 'runtime\PostgreSQL'
$postgresSource = Join-Path $repo 'runtime\PostgreSQL'
if (-not (Test-Path -LiteralPath $postgresSource -PathType Container)) {
    throw "Bundled PostgreSQL runtime not found: $postgresSource"
}
New-Item -ItemType Directory -Path $targetRuntime -Force | Out-Null
robocopy $postgresSource $targetRuntime /E /NFL /NDL /NJH /NJS /NP /XD (Join-Path $postgresSource 'pgAdmin 4') (Join-Path $postgresSource 'StackBuilder') (Join-Path $postgresSource 'lib\pgxs\src\test') | Out-Null
if ($LASTEXITCODE -gt 7) { throw "PostgreSQL runtime copy failed with exit code $LASTEXITCODE" }

$versionSource = Join-Path $repo 'runtime\postgresql.version'
$versionTarget = Join-Path $bundle 'runtime\postgresql.version'
if (-not (Test-Path $versionSource)) { throw "PostgreSQL version marker missing: $versionSource" }
Copy-Item $versionSource $versionTarget -Force

New-Item -ItemType Directory -Path (Join-Path $bundle 'data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $bundle 'logs') -Force | Out-Null

$required = @(
    $exe,
    (Join-Path $targetRuntime 'bin\postgres.exe'),
    (Join-Path $targetRuntime 'bin\pg_ctl.exe'),
    (Join-Path $targetRuntime 'bin\initdb.exe'),
    (Join-Path $targetRuntime 'bin\createdb.exe'),
    (Join-Path $targetRuntime 'bin\psql.exe'),
    $versionTarget,
    (Join-Path $bundle '_internal\src\DairyOS.Web\dist\index.html')
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Release bundle validation failed; missing required file: $path"
    }
}

Write-Host ''
Write-Host '=== RELEASE CANDIDATE BUNDLE ==='
Write-Host $bundle
Get-FileHash $exe -Algorithm SHA256

# robocopy returns 1 when files were copied successfully. Clear the native
# process exit code explicitly so callers can distinguish success from failure.
exit 0
