@echo off
REM SOFA.vbs ile gizli baslatilan sunucuyu (ve varsa otomatik baslatilan
REM OmniRoute'u) durdurmak icin bu dosyayi cift tiklayin.

echo SOFA sunucusu durduruluyor (port 8000)...
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
    set FOUND=1
)

if "%FOUND%"=="1" (
    echo Tamamlandi, SOFA durduruldu.
) else (
    echo Port 8000'de calisan bir SOFA sureci bulunamadi.
)

echo.
echo OmniRoute durduruluyor (port 20128, kuruluysa)...
set FOUND2=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :20128 ^| findstr LISTENING') do (
    taskkill /F /PID %%p >nul 2>&1
    set FOUND2=1
)

if "%FOUND2%"=="1" (
    echo Tamamlandi, OmniRoute durduruldu.
) else (
    echo Port 20128'de calisan bir OmniRoute sureci bulunamadi.
)

pause
