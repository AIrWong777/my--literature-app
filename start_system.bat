@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo ========================================
echo    AI Literature Management System
echo ========================================
echo.

echo [1/4] Checking environment...
if not exist "my-literature-app\package.json" (
    echo Error: Frontend project file not found
    pause
    exit /b 1
)

if not exist "run.py" (
    echo Error: Backend startup file not found
    pause
    exit /b 1
)

echo Environment check passed

echo.
echo [2/4] Checking conda environment...
call conda info --envs | findstr "lite" >nul
if errorlevel 1 (
    echo Error: conda environment 'lite' not found
    echo Please create conda environment: conda create -n lite python=3.10
    echo Please install dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)
echo Conda environment 'lite' check passed

echo.
echo [3/4] Starting backend service...
start "Backend Service - FastAPI" cmd /k "conda activate lite && python run.py"
timeout /t 3 >nul

echo.
echo [4/4] Starting frontend service...
cd my-literature-app
start "Frontend Service - Next.js" cmd /k "npm run dev"
cd ..

echo.
echo System startup completed!
echo.
echo Service URLs:
echo    Frontend: http://localhost:3000
echo    Backend: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo Tips:
echo    - Two service windows will open automatically
echo    - Backend service runs in conda environment 'lite'
echo    - Close windows to stop corresponding services
echo    - First startup may take a few seconds
echo.
pause