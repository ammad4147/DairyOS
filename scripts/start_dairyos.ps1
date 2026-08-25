<#
    DairyOS one-click launcher.

    Starts the backend (FastAPI/uvicorn, port 8000) and the frontend
    (Vite dev server, port 5173) each in their own visible PowerShell
    window, waits for both to come up, then opens the operator UI.

    Python environment policy:
      - Prefer D:\DairyOS\.venv\Scripts\python.exe when that runtime exists.
      - Otherwise use the configured system Python (python on PATH).
      - Never call Activate.ps1. The launcher invokes Python directly.

    Safe to re-run: any stale process already listening on port 8000 or
    5173 is stopped first, but ONLY if it looks like a DairyOS process
    (python/uvicorn/node). An unrelated process is left alone and reported.
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backendPort = 8000
$frontendPort = 5173
$frontendRoot = Join-Path $root "src\DairyOS.Web"
$sourceRoot = Join-Path $root "src"

function Stop-StalePortOwner {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $proc = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        if (-not $proc) { continue }

        if ($proc.ProcessName -match "python|uvicorn|node") {
            Write-Host "Stopping stale $($proc.ProcessName) (PID $($proc.Id)) on port $Port" -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        } else {
            Write-Warning "Port $Port is already in use by '$($proc.ProcessName)' (PID $($proc.Id)), which doesn't look like a DairyOS process. Leaving it alone."
        }
    }
}

function Wait-ForHttp {
    param([string]$Url, [int]$TimeoutSeconds)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -lt 500) { return $true }
        } catch {
            # Not up yet -- keep polling.
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Resolve-DairyOSPython {
    $venvPython = Join-Path $root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython -PathType Leaf) {
        return $venvPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python -and $python.Source) {
        return $python.Source
    }

    throw "No Python interpreter was found. Install/configure Python 3.12+ and ensure 'python' is available on PATH."
}

if (-not (Test-Path $frontendRoot -PathType Container)) {
    throw "DairyOS frontend directory was not found: $frontendRoot"
}

if (-not (Test-Path (Join-Path $frontendRoot "package.json") -PathType Leaf)) {
    throw "DairyOS frontend package.json was not found: $frontendRoot\package.json"
}

$pythonExe = Resolve-DairyOSPython

Write-Host "== DairyOS launcher ==" -ForegroundColor Green
Write-Host "Python: $pythonExe" -ForegroundColor DarkGray
Write-Host "Frontend: $frontendRoot" -ForegroundColor DarkGray

Stop-StalePortOwner -Port $backendPort
Stop-StalePortOwner -Port $frontendPort
Start-Sleep -Seconds 1

Write-Host "Starting backend (uvicorn) on port $backendPort ..."
$backendCommand = "Set-Location '$root'; `$env:PYTHONPATH='$sourceRoot'; & '$pythonExe' -m uvicorn dairyos.app:app --reload --port $backendPort"
Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand
)

Write-Host "Starting frontend (vite) on port $frontendPort ..."
$frontendCommand = "Set-Location '$frontendRoot'; npm run dev -- --host localhost --port $frontendPort --strictPort"
Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand
)

Write-Host "Waiting for the backend to respond..."
$backendUp = Wait-ForHttp -Url "http://127.0.0.1:$backendPort/docs" -TimeoutSeconds 60
if (-not $backendUp) {
    Write-Warning "Backend did not respond within 60s -- check its PowerShell window for errors."
}

Write-Host "Waiting for the frontend to respond..."
$frontendUp = Wait-ForHttp -Url "http://localhost:$frontendPort" -TimeoutSeconds 60
if (-not $frontendUp) {
    Write-Warning "Frontend did not respond within 60s -- check its PowerShell window for errors."
}

if ($frontendUp) {
    Start-Process "http://localhost:$frontendPort"
    Write-Host "DairyOS operator UI opened at http://localhost:$frontendPort" -ForegroundColor Green
} else {
    Write-Warning "DairyOS backend may be running, but the operator UI was not opened because Vite did not respond."
}

Write-Host "Close the two DairyOS PowerShell windows (or press Ctrl+C in each) to stop the development runtime." -ForegroundColor DarkGray
