# Kinlin AI 系统启动脚本 (PowerShell版本)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kinlin AI 系统启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否运行
Write-Host "[1/5] 检查Docker状态..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "Docker 运行正常" -ForegroundColor Green
} catch {
    Write-Host "警告: Docker Desktop 未运行，请先启动Docker Desktop" -ForegroundColor Red
    Write-Host "然后运行: docker-compose -f docker/docker-compose.yml up -d postgres redis" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 启动数据库和Redis
Write-Host "[2/5] 启动PostgreSQL和Redis..." -ForegroundColor Yellow
Set-Location docker
docker-compose up -d postgres redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法启动数据库服务" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Set-Location ..
Write-Host "数据库服务已启动" -ForegroundColor Green
Start-Sleep -Seconds 3
Write-Host ""

# 启动Python AI服务
Write-Host "[3/5] 启动Python AI服务 (端口8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\agent'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "Python AI服务启动中..." -ForegroundColor Green
Write-Host ""

# 启动Spring Boot后端
Write-Host "[4/5] 启动Spring Boot后端 (端口8080)..." -ForegroundColor Yellow
Set-Location backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; mvn spring-boot:run" -WindowStyle Normal
Set-Location ..
Start-Sleep -Seconds 5
Write-Host "后端服务启动中..." -ForegroundColor Green
Write-Host ""

# 启动Vue前端
Write-Host "[5/5] 启动Vue前端 (开发模式)..." -ForegroundColor Yellow
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal
Set-Location ..
Write-Host "前端服务启动中..." -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "所有服务正在启动中..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务地址:" -ForegroundColor Yellow
Write-Host "  - 前端: http://localhost:5173" -ForegroundColor White
Write-Host "  - 后端API: http://localhost:8080" -ForegroundColor White
Write-Host "  - AI服务: http://localhost:8000" -ForegroundColor White
Write-Host "  - 数据库: localhost:5432" -ForegroundColor White
Write-Host "  - Redis: localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "注意: 各服务将在新窗口中运行" -ForegroundColor Yellow
Write-Host "关闭窗口即可停止对应服务" -ForegroundColor Yellow
Write-Host ""
Read-Host "按Enter键退出"



