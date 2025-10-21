@echo off
REM =============================================================================
REM Windows Docker Deployment Script for ClinChat-RAG Fusion AI System
REM =============================================================================

setlocal enabledelayedexpansion

echo 🐳 ClinChat-RAG Docker Deployment (Windows)
echo ========================================

set PROJECT_NAME=clinchat-rag
set COMPOSE_FILE=docker-compose.yml
set ENV_FILE=.env

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not available. Please ensure Docker Desktop is running.
    exit /b 1
)

if "%1"=="start" goto start
if "%1"=="dev" goto dev
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="test" goto test
if "%1"=="migrate" goto migrate
if "%1"=="clean" goto clean
if "%1"=="build" goto build
goto help

:start
echo [INFO] Starting ClinChat-RAG in production mode...
call :setup_env
call :build_images
echo [INFO] Starting services...
docker-compose up -d
call :wait_for_services
call :migrate_db
call :test_deployment
call :show_status
echo [SUCCESS] 🚀 ClinChat-RAG Fusion AI deployment complete!
goto end

:dev
echo [INFO] Starting ClinChat-RAG in development mode...
call :setup_env
call :build_images
echo [INFO] Starting development services...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
call :wait_for_services
call :migrate_db
call :show_status
echo [SUCCESS] 🚀 ClinChat-RAG development environment ready!
goto end

:stop
echo [INFO] Stopping services...
docker-compose down
echo [SUCCESS] Services stopped
goto end

:restart
echo [INFO] Restarting services...
docker-compose restart
call :wait_for_services
echo [SUCCESS] Services restarted
goto end

:logs
if "%2"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %2
)
goto end

:status
call :show_status
goto end

:test
call :test_deployment
goto end

:migrate
call :migrate_db
goto end

:build
echo [INFO] Building Docker images...
docker-compose build --no-cache
echo [SUCCESS] Images built successfully
goto end

:clean
echo [INFO] Cleaning up...
docker-compose down -v
docker system prune -f
echo [SUCCESS] Cleanup completed
goto end

:help
echo ClinChat-RAG Docker Management Script (Windows)
echo.
echo Usage: %0 [command]
echo.
echo Commands:
echo   start     - Deploy production environment
echo   dev       - Start development environment
echo   stop      - Stop all services
echo   restart   - Restart all services
echo   logs      - Show logs (optionally specify service)
echo   status    - Show service status
echo   test      - Test deployment
echo   migrate   - Run database migration
echo   build     - Build Docker images
echo   clean     - Clean up containers and images
echo   help      - Show this help message
echo.
echo Examples:
echo   %0 start              # Deploy production
echo   %0 dev                # Start development
echo   %0 logs clinchat-rag  # Show specific service logs
goto end

REM Helper functions
:setup_env
echo [INFO] Setting up environment...
if not exist "%ENV_FILE%" (
    if exist ".env.docker" (
        copy ".env.docker" "%ENV_FILE%" >nul
        echo [INFO] Copied .env.docker to .env
    ) else (
        echo [WARNING] No .env file found. Please create one with your API keys.
        exit /b 1
    )
)
echo [SUCCESS] Environment setup complete
goto :eof

:build_images
echo [INFO] Building Docker images...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build images
    exit /b 1
)
echo [SUCCESS] Images built successfully
goto :eof

:wait_for_services
echo [INFO] Waiting for services to be healthy...
set /a attempts=0
set /a max_attempts=30

:wait_loop
set /a attempts+=1
echo [INFO] Health check attempt !attempts!/!max_attempts!

REM Check if main API is responding
curl -f -s http://localhost:8002/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Main API is healthy
    goto :eof
)

if !attempts! geq !max_attempts! (
    echo [ERROR] Services failed to become healthy
    exit /b 1
)

timeout /t 5 /nobreak >nul 2>&1
goto wait_loop

:migrate_db
echo [INFO] Running database migration...
docker-compose exec -T clinchat-rag python scripts/migrate_database.py
if %errorlevel% neq 0 (
    echo [WARNING] Database migration may have failed
) else (
    echo [SUCCESS] Database migration completed
)
goto :eof

:test_deployment
echo [INFO] Testing deployment...

REM Test health endpoint
curl -f -s http://localhost:8002/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Health check passed
) else (
    echo [ERROR] Health check failed
    exit /b 1
)

echo [SUCCESS] Deployment test completed
goto :eof

:show_status
echo [INFO] Service Status:
echo.
docker-compose ps
echo.
echo [INFO] Available endpoints:
echo - Main API: http://localhost:8002
echo - API Docs: http://localhost:8002/docs
echo - Health Check: http://localhost:8002/health
echo - Chroma Vector DB: http://localhost:8001
echo - Grafana Dashboard: http://localhost:3000
echo - Prometheus: http://localhost:9091
echo.
goto :eof

:end
pause