[CmdletBinding()]
param(
    [string]$ProjectName = "dairyos",
    [int]$WebPort = 0,
    [switch]$NoBrowser,
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$compose = @("compose", "--project-directory", $repoRoot, "--project-name", $ProjectName)
$requiredSecrets = @("POSTGRES_PASSWORD", "DAIRYOS_AUTH_SECRET", "DAIRYOS_EMAIL_SECRET")

function Read-DotEnv {
    param([string[]]$Lines)
    $values = @{}
    foreach ($line in $Lines) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $value = $Matches[2]
            if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $values[$Matches[1]] = $value
        }
    }
    return $values
}

function Write-RestrictedDotEnv {
    param([string[]]$Lines)
    [IO.File]::WriteAllLines($envFile, $Lines, [Text.UTF8Encoding]::new($false))
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $aclArgs = @(
        $envFile,
        "/inheritance:r",
        "/grant:r",
        ("*{0}:(F)" -f $sid),
        "*S-1-5-18:(F)",
        "*S-1-5-32-544:(F)"
    )
    & icacls.exe @aclArgs *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Windows could not restrict access to DairyOS deployment settings. No services were started."
    }
}

function New-SecretValue {
    param([ValidateSet("database", "auth", "email")][string]$Kind)
    if ($Kind -eq "email") {
        return [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).Replace('+', '-').Replace('/', '_')
    }
    $byteCount = if ($Kind -eq "auth") { 48 } else { 32 }
    return [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes($byteCount))
}

function Resolve-DeploymentSettings {
    & git -C $repoRoot check-ignore --quiet .env
    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS safeguards require .env to be ignored by Git before secrets can be stored. No secret file was created."
    }

    $lines = if (Test-Path -LiteralPath $envFile -PathType Leaf) {
        [IO.File]::ReadAllLines($envFile)
    } else {
        @()
    }
    $values = Read-DotEnv -Lines $lines
    $pgVolume = "{0}_dairyos_postgres_data" -f $ProjectName
    & docker volume inspect $pgVolume *> $null
    $hasExistingDatabase = $LASTEXITCODE -eq 0
    $kinds = @{
        POSTGRES_PASSWORD = "database"
        DAIRYOS_AUTH_SECRET = "auth"
        DAIRYOS_EMAIL_SECRET = "email"
    }

    foreach ($name in $requiredSecrets) {
        if ($values.ContainsKey($name) -and -not [string]::IsNullOrWhiteSpace($values[$name])) {
            continue
        }
        $value = [Environment]::GetEnvironmentVariable($name, "Process")
        if ([string]::IsNullOrWhiteSpace($value)) {
            $value = [Environment]::GetEnvironmentVariable($name, "User")
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            if ($hasExistingDatabase) {
                throw "A saved DairyOS database exists but $name is missing. To protect existing records, DairyOS will not replace it automatically; contact your DairyOS administrator."
            }
            $value = New-SecretValue -Kind $kinds[$name]
        }
        $values[$name] = $value
    }

    # Persist values obtained from per-user settings too: a fresh Compose
    # process cannot inherit values set in a terminal opened before them.
    $lines = @($lines | Where-Object { $_ -notmatch '^\s*(POSTGRES_PASSWORD|DAIRYOS_AUTH_SECRET|DAIRYOS_EMAIL_SECRET)\s*=' })
    foreach ($name in $requiredSecrets) {
        $lines += "${name}=$($values[$name])"
        [Environment]::SetEnvironmentVariable($name, $values[$name], "Process")
    }

    if ($WebPort -gt 0) {
        $env:DAIRYOS_WEB_PORT = "$WebPort"
        $values.DAIRYOS_WEB_PORT = "$WebPort"
    } elseif ($values.ContainsKey("DAIRYOS_WEB_PORT")) {
        $env:DAIRYOS_WEB_PORT = $values.DAIRYOS_WEB_PORT
    }
    if (-not $values.ContainsKey("POSTGRES_DB")) { $values.POSTGRES_DB = "dairyos" }
    if (-not $values.ContainsKey("POSTGRES_USER")) { $values.POSTGRES_USER = "dairyos" }
    foreach ($name in @("POSTGRES_DB", "POSTGRES_USER")) {
        if ($values[$name] -notmatch '^[A-Za-z0-9_-]+$') {
            throw "The configured $name is not supported by the guided DairyOS starter. Contact your DairyOS administrator."
        }
        [Environment]::SetEnvironmentVariable($name, $values[$name], "Process")
    }
    if (-not $env:DAIRYOS_WEB_PORT) { $env:DAIRYOS_WEB_PORT = "8000" }

    # This confirmation is intentionally transient and never retained in .env.
    $lines = @($lines | Where-Object { $_ -notmatch '^\s*DAIRYOS_HOSTED_BOOTSTRAP_DATABASE\s*=' })
    Write-RestrictedDotEnv -Lines $lines
    return $values
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)
    & docker @compose @Arguments *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS could not start its local web service. Your saved farm data was not removed. Close this window and try again; if it repeats, contact support."
    }
}

function Wait-ForDatabase {
    Invoke-DockerCompose -Arguments @("up", "-d", "db")
    $deadline = (Get-Date).AddMinutes(2)
    do {
        $dbId = & docker @compose ps -q db 2>$null
        if ($LASTEXITCODE -eq 0 -and $dbId) {
            $state = & docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $dbId 2>$null
            if ($state -eq "healthy") { return }
            if ($state -eq "unhealthy" -or $state -eq "exited") {
                throw "DairyOS storage could not start. Your saved farm data was not removed. Contact support if retrying does not help."
            }
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "DairyOS storage is taking too long to start. Your saved farm data was not removed. Try again in a few minutes."
}

function Test-DatabaseIsEmpty {
    param([hashtable]$Settings)
    $query = "SELECT NOT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname <> 'information_schema' AND n.nspname !~ '^pg_' AND c.relkind IN ('r','p','v','m','S','f'));"
    $result = & docker @compose exec -T db psql --username $Settings.POSTGRES_USER --dbname $Settings.POSTGRES_DB --tuples-only --no-align --command $query 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS could not safely inspect its database. No automatic bootstrap was attempted. Contact support."
    }
    return ([string]$result).Trim() -eq "t"
}

function Wait-ForDairyOS {
    $url = "http://127.0.0.1:$($env:DAIRYOS_WEB_PORT)"
    $deadline = (Get-Date).AddMinutes(3)
    do {
        try {
            $readiness = Invoke-RestMethod -Uri "$url/readiness" -TimeoutSec 3
            if ($readiness.status -eq "READY") { return $url }
        } catch {
            # API may still be migrating the schema or restarting after bootstrap.
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "DairyOS did not become ready. Existing farm data has not been deleted. Contact support before attempting database recovery."
}

try {
    if ([string]::IsNullOrWhiteSpace($ProjectName) -or $ProjectName -notmatch '^[a-z0-9][a-z0-9_-]*$') {
        throw "DairyOS could not validate its local service name. Contact support."
    }

    $dockerReady = $false
    & docker info --format '{{.ServerVersion}}' *> $null
    if ($LASTEXITCODE -eq 0) { $dockerReady = $true }
    if (-not $dockerReady) {
        $desktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
        if (Test-Path -LiteralPath $desktop -PathType Leaf) {
            Write-Host "Starting DairyOS services... Docker Desktop is opening for the first time."
            Start-Process -FilePath $desktop
            $deadline = (Get-Date).AddMinutes(2)
            do {
                Start-Sleep -Seconds 3
                & docker info --format '{{.ServerVersion}}' *> $null
                $dockerReady = $LASTEXITCODE -eq 0
            } while (-not $dockerReady -and (Get-Date) -lt $deadline)
        }
    }
    if (-not $dockerReady) {
        throw "DairyOS could not reach its service engine. Start Docker Desktop and wait until it says it is running, then double-click Start-DairyOS-Web again. Your farm data is unchanged."
    }

    $settings = Resolve-DeploymentSettings
    if (-not $env:DAIRYOS_WEB_PORT) { $env:DAIRYOS_WEB_PORT = "8000" }
    if ($ValidateOnly) {
        Invoke-DockerCompose -Arguments @("config", "--quiet")
        Write-Host "DairyOS setup is ready. Double-click Start-DairyOS-Web to open the application." -ForegroundColor Green
        exit 0
    }

    Write-Host "Starting DairyOS... please wait."
    Wait-ForDatabase
    $bootstrapRequired = Test-DatabaseIsEmpty -Settings $settings
    if ($bootstrapRequired) {
        $env:DAIRYOS_HOSTED_BOOTSTRAP_DATABASE = $settings.POSTGRES_DB
    } else {
        Remove-Item Env:\DAIRYOS_HOSTED_BOOTSTRAP_DATABASE -ErrorAction SilentlyContinue
    }
    try {
        Invoke-DockerCompose -Arguments @("up", "-d", "--build", "api")
    } finally {
        Remove-Item Env:\DAIRYOS_HOSTED_BOOTSTRAP_DATABASE -ErrorAction SilentlyContinue
    }

    $url = Wait-ForDairyOS
    if ($bootstrapRequired) {
        Invoke-DockerCompose -Arguments @("up", "-d", "--force-recreate", "--build", "api")
        $url = Wait-ForDairyOS
    }

    Write-Host "DairyOS is ready." -ForegroundColor Green
    if (-not $NoBrowser) { Start-Process $url }
    Write-Host "Open this PC's DairyOS at $url"
    Write-Host "For your privacy, phone/network access is not enabled by this local starter."
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
