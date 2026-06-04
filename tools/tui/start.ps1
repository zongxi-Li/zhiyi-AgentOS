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
$REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$COMPOSE_FILE = Join-Path $REPO_ROOT "docker\docker-compose.prod.yml"
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

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " ZhiYi AgentOS TUI Launcher" -ForegroundColor Cyan
Write-Host " Role: $Role  |  API: http://127.0.0.1:$($Port)/ai" -ForegroundColor Cyan
Write-Host " Mode: Docker shared backend" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1/2] Starting Docker ai-service..." -ForegroundColor Yellow
if (Test-Path $COMPOSE_FILE) {
    docker compose -f $COMPOSE_FILE up -d ai-service 2>&1
} else {
    docker compose up -d ai-service 2>&1
}

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
    Write-Host "       Check: docker compose -f $COMPOSE_FILE ps" -ForegroundColor Red
    exit 1
}

Write-Host "[2/2] Starting TUI..." -ForegroundColor Yellow
$env:AGENTOS_API_URL = "http://127.0.0.1:$Port/ai"
& $PYTHON -m kinlin_tui.app os --role $Role

Write-Host "Done." -ForegroundColor Green
