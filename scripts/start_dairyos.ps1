<#
    DairyOS one-click launcher (2026-08-14).

    Starts the backend (FastAPI/uvicorn, port 8000) and the frontend
    (Vite dev server, port 5173) each in their own visible PowerShell
    window (so you can see their logs and Ctrl+C to stop), waits for
    both to come up, then opens the dashboard in your default browser.

    Safe to re-run: any stale process already listening on port 8000 or
    5173 is stopped first, but ONLY if it looks like a DairyOS process
    (python/uvicorn/node) -- an unrelated app on one of those ports is
    left alone and reported instead, so this never kills something that
    isn't ours.
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backendPort = 8000
$frontendPort = 5173

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
            Write-Warning "Port $Port is already in use by '$($proc.ProcessName)' (PID $($proc.Id)), which doesn't look like a DairyOS process. Leaving it alone -- close it manually if this launch fails."
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

Write-Host "== DairyOS launcher ==" -ForegroundColor Green

Stop-StalePortOwner -Port $backendPort
Stop-StalePortOwner -Port $frontendPort
Start-Sleep -Seconds 1

Write-Host "Starting backend (uvicorn) on port $backendPort ..."
Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit", "-Command",
    "cd `"$root`"; & `"$root\.venv\Scripts\Activate.ps1`"; python -m uvicorn dairyos.app:app --reload --port $backendPort"
)

Write-Host "Starting frontend (vite) on port $frontendPort ..."
Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit", "-Command",
    "cd `"$root\src\DairyOS.Web`"; npm run dev -- --port $frontendPort --strictPort"
)

Write-Host "Waiting for the backend to respond..."
$backendUp = Wait-ForHttp -Url "http://127.0.0.1:$backendPort/docs" -TimeoutSeconds 60
if (-not $backendUp) {
    Write-Warning "Backend did not respond within 60s -- check its PowerShell window for errors."
}

Write-Host "Waiting for the frontend to respond..."
# "localhost", not "127.0.0.1" -- confirmed on this machine that Vite's
# dev server only answers on whichever address "localhost" resolves to
# (observed to be the IPv6 loopback), not on the literal IPv4 127.0.0.1.
$frontendUp = Wait-ForHttp -Url "http://localhost:$frontendPort" -TimeoutSeconds 60
if (-not $frontendUp) {
    Write-Warning "Frontend did not respond within 60s -- check its PowerShell window for errors."
}

Start-Process "http://localhost:$frontendPort"
Write-Host "DairyOS should now be open in your browser." -ForegroundColor Green
Write-Host "Close the two new PowerShell windows (or Ctrl+C in each) to stop the backend and frontend."
