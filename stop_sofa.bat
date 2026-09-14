@echo off
REM SOFA.vbs ile gizli baslatilan sunucuyu durdurmak icin bu dosyayi
REM cift tiklayin (port 8000'i dinleyen sureci sonlandirir).

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

pause
