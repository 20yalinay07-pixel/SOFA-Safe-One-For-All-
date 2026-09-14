@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title SOFA - Kurulum

echo ================================================
echo   SOFA (Safe One For All) - Kurulum
echo ================================================
echo.

REM --- Python kontrolu ---
where python >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi.
    echo        Once https://python.org adresinden Python kurun ^(kurulum
    echo        sirasinda "Add python.exe to PATH" secenegini isaretleyin^),
    echo        sonra bu dosyayi tekrar calistirin.
    echo.
    pause
    exit /b 1
)

REM --- Sanal ortam ---
if not exist ".venv" (
    echo [1/4] Sanal ortam olusturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Sanal ortam zaten mevcut, atlaniyor.
)

call ".venv\Scripts\activate.bat"

REM --- Bagimliliklar ---
echo [2/4] Bagimliliklar kuruluyor, bu biraz surebilir...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [HATA] Bagimliliklar kurulamadi. Yukaridaki hatayi kontrol edin.
    pause
    exit /b 1
)

REM --- .env ---
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [3/4] .env dosyasi olusturuldu ^(.env.example'dan kopyalandi^).
) else (
    echo [3/4] .env dosyasi zaten mevcut, atlaniyor.
)

REM --- Masaustu kisayolu ---
echo [4/4] Masaustu kisayolu olusturuluyor...

set "SHORTCUT_VBS=%TEMP%\sofa_make_shortcut.vbs"
> "%SHORTCUT_VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>> "%SHORTCUT_VBS%" echo strDesktop = oWS.SpecialFolders("Desktop")
>> "%SHORTCUT_VBS%" echo Set oLink = oWS.CreateShortcut(strDesktop ^& "\SOFA AI.lnk")
>> "%SHORTCUT_VBS%" echo oLink.TargetPath = "%~dp0SOFA.vbs"
>> "%SHORTCUT_VBS%" echo oLink.WorkingDirectory = "%~dp0"
>> "%SHORTCUT_VBS%" echo oLink.Description = "SOFA - Safe One For All"
>> "%SHORTCUT_VBS%" echo oLink.Save

cscript //nologo "%SHORTCUT_VBS%"
if errorlevel 1 (
    echo [UYARI] Kisayol otomatik olusturulamadi. Elle olusturmak icin:
    echo         SOFA.vbs dosyasina sag tik yapip
    echo         "Gonder -^> Masaustu ^(kisayol olustur^)" secebilirsiniz.
) else (
    echo        Masaustunde "SOFA AI" kisayolu olusturuldu.
)
del "%SHORTCUT_VBS%" >nul 2>&1

echo.
echo ================================================
echo   Kurulum tamamlandi!
echo   Masaustundeki "SOFA AI" kisayoluna cift tiklayarak
echo   SOFA'yi acabilirsiniz ^(cmd penceresi gorunmeden calisir^).
echo.
echo   NOT: Sohbet/Medya ozelliklerinin calismasi icin
echo   OmniRoute veya FreeLLMAPI'nin ayrica kurulu ve calisir
echo   durumda olmasi gerekir.
echo ================================================
echo.
pause
