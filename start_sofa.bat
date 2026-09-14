@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title SOFA - Safe One For All

echo ============================================
echo   SOFA - Safe One For All baslatiliyor...
echo ============================================
echo.

REM --- Sanal ortam yoksa olustur ---
if not exist ".venv" (
    echo [SOFA] Ilk calistirma: sanal ortam olusturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [HATA] Python bulunamadi. Once https://python.org adresinden
        echo        Python kurup "Add to PATH" secenegini isaretleyin.
        echo.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

REM --- Bagimliliklar kurulu mu kontrol et, degilse kur ---
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [SOFA] Bagimliliklar kuruluyor, bu biraz surebilir...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [HATA] Bagimliliklar kurulamadi. Yukaridaki hatayi kontrol edin.
        echo.
        pause
        exit /b 1
    )
)

REM --- .env yoksa ornekten olustur ---
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [SOFA] .env dosyasi olusturuldu (.env.example'dan kopyalandi).
    echo         Sohbet/Medya icin CHAT_PROVIDER ve anahtarlarinizi
    echo         .env dosyasindan duzenleyebilirsiniz.
)

echo.
echo [SOFA] NOT: Sohbet ve Medya ozelliklerinin calismasi icin
echo        OmniRoute veya FreeLLMAPI'nin ayrica calisiyor olmasi gerekir.
echo.
echo [SOFA] Sunucu baslatiliyor, tarayici birazdan otomatik acilacak...
echo        Kapatmak icin bu pencereyi kapatmaniz yeterli.
echo.

start "" http://127.0.0.1:8000

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
