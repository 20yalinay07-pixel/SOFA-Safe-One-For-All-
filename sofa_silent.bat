@echo off
REM Bu betik, gizli (pencere gostermeyen) baslatma icindir.
REM Elle calistirmayin - hata mesajlarini gormek icin start_sofa.bat kullanin.
REM Bu betik SOFA.vbs tarafindan cagrilir.

setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist ".venv" (
    python -m venv .venv >> sofa_launch.log 2>&1
)

call ".venv\Scripts\activate.bat" >> sofa_launch.log 2>&1

python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    pip install -r requirements.txt >> sofa_launch.log 2>&1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
)

start "" http://127.0.0.1:8000

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >> sofa_launch.log 2>&1
