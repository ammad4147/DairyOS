$ErrorActionPreference = "Stop"

$repo = "D:\DairyOS"
Set-Location $repo

$buildRoot = Join-Path $repo "build\DairyOS-Portable"
$distRoot = Join-Path $repo "dist\DairyOS-Portable"

Write-Host "Cleaning previous portable build..."

Remove-Item $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $distRoot -Recurse -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null

Write-Host "Building React frontend..."

npm --prefix "$repo\src\DairyOS.Web" run build

if ($LASTEXITCODE -ne 0) {
    throw "React production build failed with exit code $LASTEXITCODE"
}

$frontendIndex = Join-Path $repo "src\DairyOS.Web\dist\index.html"

if (-not (Test-Path -LiteralPath $frontendIndex -PathType Leaf)) {
    throw "React production build completed without dist/index.html"
}

Write-Host "Building DairyOS portable executable..."

python -m PyInstaller `
    --clean `
    --noconfirm `
    --onedir `
    --windowed `
    --name DairyOS `
    --distpath $distRoot `
    --workpath "$repo\build\pyinstaller-portable" `
    --collect-submodules dairyos `
    --collect-submodules alembic `
    --collect-submodules sqlalchemy `
    --collect-all webview `
    --add-data "$repo\alembic.ini;." `
    --add-data "$repo\db_migrations;db_migrations" `
    --add-data "$repo\src\DairyOS.Web\dist;src/DairyOS.Web/dist" `
    "$repo\src\dairyos\windows\supervisor.py"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

$bundle = Join-Path $distRoot "DairyOS"
$portableExe = Join-Path $bundle "DairyOS.exe"

if (-not (Test-Path -LiteralPath $portableExe -PathType Leaf)) {
    throw "PyInstaller reported success but portable DairyOS.exe was not produced: $portableExe"
}

Write-Host "Copying private PostgreSQL runtime..."

$targetRuntime = Join-Path $bundle "runtime\PostgreSQL"
$postgresSource = Join-Path $repo "runtime\PostgreSQL"

if (-not (Test-Path -LiteralPath $postgresSource -PathType Container)) {
    throw "Bundled PostgreSQL runtime not found: $postgresSource"
}

New-Item -ItemType Directory -Path $targetRuntime -Force | Out-Null

robocopy `
    $postgresSource `
    $targetRuntime `
    /E `
    /NFL `
    /NDL `
    /NJH `
    /NJS `
    /NP `
    /XD `
        (Join-Path $postgresSource "pgAdmin 4") `
        (Join-Path $postgresSource "StackBuilder") `
        (Join-Path $postgresSource "lib\pgxs\src\test")

if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

$versionSource = Join-Path $repo "runtime\postgresql.version"
$versionTarget = Join-Path $bundle "runtime\postgresql.version"

if (-not (Test-Path -LiteralPath $versionSource -PathType Leaf)) {
    throw "PostgreSQL version marker not found: $versionSource"
}

Copy-Item `
    $versionSource `
    $versionTarget `
    -Force

New-Item -ItemType Directory `
    -Path (Join-Path $bundle "data") `
    -Force | Out-Null

New-Item -ItemType Directory `
    -Path (Join-Path $bundle "logs") `
    -Force | Out-Null

$bundledPostgres = Join-Path $targetRuntime "bin\postgres.exe"
$bundledInitdb = Join-Path $targetRuntime "bin\initdb.exe"
$bundledPgctl = Join-Path $targetRuntime "bin\pg_ctl.exe"
$bundledCreatedb = Join-Path $targetRuntime "bin\createdb.exe"
$bundledPsql = Join-Path $targetRuntime "bin\psql.exe"
$bundledFrontend = Join-Path $bundle "_internal\src\DairyOS.Web\dist\index.html"

foreach ($required in @(
    $portableExe,
    $bundledPostgres,
    $bundledInitdb,
    $bundledPgctl,
    $bundledCreatedb,
    $bundledPsql,
    $versionTarget,
    $bundledFrontend
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Portable bundle validation failed; required file is missing: $required"
    }
}

Write-Host ""
Write-Host "Portable bundle created successfully:"
Write-Host $bundle
Write-Host "Executable:"
Write-Host $portableExe