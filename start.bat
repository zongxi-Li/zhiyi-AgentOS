@echo off
echo ========================================
echo Kinlin AI 系统启动脚本
echo ========================================
echo.

REM 检查Docker是否运行
echo [1/5] 检查Docker状态...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: Docker Desktop 未运行，请先启动Docker Desktop
    echo 然后运行: docker-compose -f docker/docker-compose.yml up -d postgres redis
    echo.
    pause
    exit /b 1
)

REM 启动数据库和Redis
echo [2/5] 启动PostgreSQL和Redis...
cd docker
docker-compose up -d postgres redis
if %errorlevel% neq 0 (
    echo 错误: 无法启动数据库服务
    pause
    exit /b 1
)
cd ..
echo 数据库服务已启动
timeout /t 3 /nobreak >nul
echo.

REM 启动Python AI服务
echo [3/5] 启动Python AI服务 (端口8000)...
start "Kinlin AI Service" cmd /k "cd agent && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo Python AI服务启动中...
echo.

REM 启动Spring Boot后端
echo [4/5] 启动Spring Boot后端 (端口8080)...
cd backend
start "Kinlin Backend" cmd /k "mvn spring-boot:run"
cd ..
timeout /t 5 /nobreak >nul
echo 后端服务启动中...
echo.

REM 启动Vue前端
echo [5/5] 启动Vue前端 (开发模式)...
cd frontend
start "Kinlin Frontend" cmd /k "npm run dev"
cd ..
echo 前端服务启动中...
echo.

echo ========================================
echo 所有服务正在启动中...
echo ========================================
echo.
echo 服务地址:
echo   - 前端: http://localhost:5173
echo   - 后端API: http://localhost:8080
echo   - AI服务: http://localhost:8000
echo   - 数据库: localhost:5432
echo   - Redis: localhost:6379
echo.
echo 注意: 各服务将在新窗口中运行
echo 关闭窗口即可停止对应服务
echo.
pause



