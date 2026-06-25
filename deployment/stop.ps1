$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendPidFile = Join-Path $root "backend.pid"
$frontendPidFile = Join-Path $root "frontend.pid"

function Stop-TrackedProcess {
    param(
        [string]$PidFile,
        [string]$Name
    )

    if (-not (Test-Path $PidFile)) {
        Write-Host "$Name PID file not found."
        return
    }

    $processId = Get-Content $PidFile -ErrorAction SilentlyContinue
    if (-not $processId) {
        Write-Host "$Name PID file was empty."
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "Stopped $Name (PID $processId)."
    }
    catch {
        Write-Host "$Name process was already stopped."
    }

    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

Stop-TrackedProcess -PidFile $backendPidFile -Name "backend"
Stop-TrackedProcess -PidFile $frontendPidFile -Name "frontend"

Write-Host "Shutdown complete."
