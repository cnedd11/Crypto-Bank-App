$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$serverDir = Join-Path $root "my-app/server"
$clientDir = Join-Path $root "my-app/client"
$venvDir = Join-Path $serverDir "venv"
$pythonExe = Join-Path $venvDir "Scripts/python.exe"
$backendPidFile = Join-Path $root "backend.pid"
$frontendPidFile = Join-Path $root "frontend.pid"
$logDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$backendOut = Join-Path $logDir "backend.out.log"
$backendErr = Join-Path $logDir "backend.err.log"
$frontendOut = Join-Path $logDir "frontend.out.log"
$frontendErr = Join-Path $logDir "frontend.err.log"
$script:FrontendPort = 3000
$script:FrontendUrl = "http://localhost:$script:FrontendPort"

function Get-FreePort {
    param(
        [int]$StartPort = 3000,
        [int]$EndPort = 3010
    )

    for ($port = $StartPort; $port -le $EndPort; $port++) {
        $listener = $null
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
            $listener.Start()
            return $port
        }
        catch {
        }
        finally {
            if ($listener) {
                $listener.Stop()
            }
        }
    }

    throw "No free port found between $StartPort and $EndPort."
}

function Ensure-Venv {
    if (-not (Test-Path $pythonExe)) {
        Write-Host "Creating Python virtual environment..."
        py -3 -m venv $venvDir
    }
}

function Ensure-PythonPackages {
    Write-Host "Installing backend packages..."
    & $pythonExe -m pip install --upgrade pip | Out-Null
    & $pythonExe -m pip install flask flask-cors flask-sqlalchemy | Out-Null
}

function Start-Backend {
    if (Test-Path $backendPidFile) {
        $existingPid = Get-Content $backendPidFile -ErrorAction SilentlyContinue
        if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
            Write-Host "Backend is already running with PID $existingPid."
            return
        }
        Remove-Item $backendPidFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Starting Flask backend..."
    $proc = Start-Process -FilePath $pythonExe -ArgumentList "app.py" -WorkingDirectory $serverDir -PassThru -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr
    $proc.Id | Set-Content $backendPidFile
    Write-Host "Backend running with PID $($proc.Id). Logs: $backendOut, $backendErr"
}

function Ensure-FrontendDependencies {
    if (-not (Test-Path (Join-Path $clientDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..."
        Push-Location $clientDir
        try {
            & npm.cmd install
        }
        finally {
            Pop-Location
        }
    }
}

function Start-Frontend {
    if (Test-Path $frontendPidFile) {
        $existingPid = Get-Content $frontendPidFile -ErrorAction SilentlyContinue
        if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
            Write-Host "Frontend is already running with PID $existingPid."
            return
        }
        Remove-Item $frontendPidFile -Force -ErrorAction SilentlyContinue
    }

    $script:FrontendPort = Get-FreePort
    $script:FrontendUrl = "http://localhost:$script:FrontendPort"
    $env:PORT = [string]$script:FrontendPort

    Write-Host "Starting React frontend on $script:FrontendUrl..."
    $proc = Start-Process -FilePath "npm.cmd" -ArgumentList "start" -WorkingDirectory $clientDir -PassThru -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr
    $proc.Id | Set-Content $frontendPidFile
    Write-Host "Frontend running with PID $($proc.Id). Logs: $frontendOut, $frontendErr"
}

function Open-Website {
    $deadline = (Get-Date).AddSeconds(45)

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $script:FrontendUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                break
            }
        }
        catch {
        }

        Start-Sleep -Seconds 2
    }

    Start-Process $script:FrontendUrl
    Write-Host "Opened $script:FrontendUrl in your default browser."
}

Ensure-Venv
Ensure-PythonPackages
Start-Backend
Ensure-FrontendDependencies
Start-Frontend
Open-Website

Write-Host ""
Write-Host "App is running."
Write-Host "Frontend: $script:FrontendUrl"
Write-Host "Backend: http://localhost:5000"
Write-Host "Use .\stop.ps1 to stop it."
