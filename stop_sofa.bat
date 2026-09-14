@echo off
REM SOFA.vbs ile gizli baslatilan sunucuyu (ve varsa otomatik baslatilan
REM OmniRoute'u) durdurmak icin bu dosyayi cift tiklayin.

echo SOFA sunucusu durduruluyor (port 8000)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /T /PID %%p >nul 2>&1
)

netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if errorlevel 1 (
    echo Tamamlandi, SOFA durduruldu ^(veya zaten calismiyordu^).
) else (
    echo [UYARI] Port 8000 hala kullanimda gibi gorunuyor. Gorev Yoneticisi'nden
    echo         "python.exe" surecini elle sonlandirmaniz gerekebilir.
)

echo.
echo OmniRoute durduruluyor...

REM --- Yontem 1: komut satirinda "omniroute" gecen tum surecleri (cmd
REM     sarmalayicisi + alt node.exe sureci dahil) hedef alarak kapat.
REM     Bu, port'taki tek bir PID'i oldurmekten daha guvenilir - npm
REM     "omniroute" komutu genelde bir .cmd sarmalayicisidir ve gercek
REM     sunucu onun alt sureci (node.exe) olarak calisir.
powershell -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*omniroute*' -and $_.ProcessId -ne $PID }; if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Write-Host ('Kapatilan surec sayisi: ' + $procs.Count) } else { Write-Host 'Komut satirinda omniroute gecen surec bulunamadi.' }"

REM --- Yontem 2 (yedek): port 20128'i dinleyen PID kalmissa onu da vur ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :20128 ^| findstr LISTENING') do (
    taskkill /F /T /PID %%p >nul 2>&1
)

REM --- Dogrulama: port hala dinleniyor mu? ---
netstat -ano | findstr :20128 | findstr LISTENING >nul 2>&1
if errorlevel 1 (
    echo Tamamlandi, OmniRoute durduruldu.
) else (
    echo [UYARI] Port 20128 hala kullanimda gibi gorunuyor. Gorev Yoneticisi'nden
    echo         "node.exe" veya "cmd.exe" surecini elle sonlandirmaniz gerekebilir.
)

pause
