@echo off
REM Talash Backend Startup Script for Windows

echo.
echo ====================================
echo  Talash CV Processing Backend
echo ====================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    call myvenv\Scripts\activate.bat
)

echo.
echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

cd talash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

pause
