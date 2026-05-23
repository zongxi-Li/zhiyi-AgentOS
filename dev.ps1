# 知弈 Docker 开发环境 - Windows PowerShell
param(
    [ValidateSet("up", "down", "build", "restart", "logs", "clean")]
    [string]$Action = "up"
)

$composeArgsPrefix = @()
docker compose version *> $null
if ($LASTEXITCODE -eq 0) {
    $compose = "docker"
    $composeArgsPrefix = @("compose")
} elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $compose = "docker-compose"
} else {
    throw "Docker Compose is required. Install Docker Desktop or docker-compose."
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $compose @composeArgsPrefix @Args
}

switch ($Action) {
    "up" {
        Write-Host "Starting development environment..." -ForegroundColor Green
        Invoke-Compose up -d --build
        Write-Host "Services starting..." -ForegroundColor Cyan
        Write-Host "  Frontend : http://localhost:3000" -ForegroundColor Yellow
        Write-Host "  Backend  : http://localhost:8080" -ForegroundColor Yellow
        Write-Host "  AI       : http://localhost:8000" -ForegroundColor Yellow
        Write-Host "  Postgres : localhost:5432" -ForegroundColor Yellow
        Write-Host "  Redis    : localhost:6379" -ForegroundColor Yellow
        Write-Host "Use 'dev.ps1 logs' to view logs" -ForegroundColor Gray
    }
    "down" {
        Write-Host "Stopping development environment..." -ForegroundColor Green
        Invoke-Compose down
    }
    "build" {
        Write-Host "Building all services..." -ForegroundColor Green
        Invoke-Compose build --no-cache
    }
    "restart" {
        Write-Host "Restarting development environment..." -ForegroundColor Green
        Invoke-Compose down
        Invoke-Compose up -d --build
    }
    "logs" {
        Invoke-Compose logs -f --tail=100
    }
    "clean" {
        Write-Host "Cleaning up (stop + remove volumes)..." -ForegroundColor Red
        Invoke-Compose down -v
        Write-Host "Done. All data removed." -ForegroundColor Red
    }
}
