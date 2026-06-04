#!/usr/bin/env pwsh
param(
    [ValidateSet("lawyer", "teacher", "programmer", "writer")]
    [string]$Role = "lawyer",
    [int]$Port = 8000,
    [switch]$Docker
)

$ErrorActionPreference = "Stop"
$PYTHON = "C:/Users/LZX/AppData/Local/Programs/Python/Python314/python.exe"
$TUI_SRC = Join-Path $PSScriptRoot "src"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$TUI_SRC;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $TUI_SRC
}

function Test-HttpHealth {
    param([int]$HealthPort)

    $client = [System.Net.Http.HttpClient]::new()
    try {
        $client.Timeout = [TimeSpan]::FromSeconds(2)
        $url = "http://127.0.0.1:$HealthPort/health"
        $response = $client.GetAsync(
            $url,
            [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead
        ).GetAwaiter().GetResult()
        try {
            return $response.IsSuccessStatusCode
        } finally {
            $response.Dispose()
        }
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Test-PortAvailable {
    param([int]$CandidatePort)

    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Parse("127.0.0.1"),
        $CandidatePort
    )
    try {
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        $listener.Stop()
    }
}

function Find-AvailablePort {
    param([int]$StartPort)

    $candidates = @()
    for ($p = $StartPort; $p -lt ($StartPort + 50); $p++) {
        $candidates += $p
    }
    for ($p = 8765; $p -lt 8790; $p++) {
        if ($candidates -notcontains $p) {
            $candidates += $p
        }
    }

    foreach ($candidate in $candidates) {
        if (Test-PortAvailable $candidate) {
            return $candidate
        }
    }

    throw "No available local port found for AgentOS backend."
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ZhiYi AgentOS TUI Launcher" -ForegroundColor Cyan
Write-Host " Role: $Role  |  API: http://127.0.0.1:$($Port)/ai" -ForegroundColor Cyan
if ($Docker) { Write-Host " Mode: Docker" -ForegroundColor Magenta }
Write-Host "============================================" -ForegroundColor Cyan

if ($Docker) {
    Write-Host ""
    Write-Host "[1/2] Starting Docker services..." -ForegroundColor Yellow
    docker compose up -d ai-service 2>&1

    Write-Host "       Waiting for ai-service..." -NoNewline
    $ok = $false
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Milliseconds 2000
        if (Test-HttpHealth $Port) {
            Write-Host " OK" -ForegroundColor Green
            $ok = $true
            break
        } else {
            Write-Host "." -NoNewline
        }
    }
    if (-not $ok) {
        Write-Host " TIMEOUT" -ForegroundColor Red
        Write-Host "       Check: docker compose ps" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "[1/2] Starting local backend..." -ForegroundColor Yellow
    $AGENT = "$PSScriptRoot\..\..\agent"
    $job = $null

    if (Test-HttpHealth $Port) {
        Write-Host "       Reusing healthy backend on port $Port" -ForegroundColor Green
    } else {
        if (-not (Test-PortAvailable $Port)) {
            $oldPort = $Port
            $Port = Find-AvailablePort ($Port + 1)
            Write-Host "       Port $oldPort is busy but unhealthy; using $Port instead." -ForegroundColor Yellow
        }

        $job = Start-Process -FilePath $PYTHON `
          -ArgumentList "-X", "utf8", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port" `
          -WorkingDirectory $AGENT -WindowStyle Hidden -PassThru
    }

    Write-Host "       Waiting for backend..." -NoNewline
    $ok = $false
    for ($i = 0; $i -lt 180; $i++) {
        Start-Sleep -Milliseconds 1000
        if (Test-HttpHealth $Port) {
            Write-Host " OK" -ForegroundColor Green
            $ok = $true
            break
        } else {
            Write-Host "." -NoNewline
        }
    }
    if (-not $ok) {
        Write-Host " TIMEOUT" -ForegroundColor Red
        if ($null -ne $job) {
            Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
        }
        exit 1
    }
}

Write-Host "[2/2] Starting TUI..." -ForegroundColor Yellow
$env:AGENTOS_API_URL = "http://127.0.0.1:$Port/ai"
& $PYTHON -m kinlin_tui.app os --role $Role

if ((-not $Docker) -and ($null -ne $job)) {
    Write-Host "Shutting down backend..." -ForegroundColor Yellow
    Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
}
Write-Host "Done." -ForegroundColor Green
