; ===========================================================
; SOFA (Safe One For All) - Windows Installer (NSIS)
;
; Derlemek icin (Windows'ta NSIS kurulu olmali - https://nsis.sourceforge.io):
;   makensis installer\SOFA_Setup.nsi
; Cikti: installer\SOFA-Setup.exe
;
; Bu installer:
;   - Uygulama dosyalarini $LOCALAPPDATA\SOFA altina kopyalar (yonetici
;     yetkisi gerektirmez)
;   - Python sanal ortamini olusturup bagimliliklari kurar
;   - npm kuruluysa OmniRoute'u otomatik kurar (npm install -g omniroute)
;   - Masaustu + Baslat Menusu kisayollari olusturur (ozel SOFA ikonuyla)
;   - Bir kaldirici (uninstaller) ekler
; ===========================================================

Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"

Name "SOFA - Safe One For All"
OutFile "SOFA-Setup.exe"
InstallDir "$LOCALAPPDATA\SOFA"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!define MUI_ICON "..\SOFA.ico"
!define MUI_UNICON "..\SOFA.ico"
!define MUI_FINISHPAGE_RUN "$INSTDIR\SOFA.vbs"
!define MUI_FINISHPAGE_RUN_TEXT "SOFA'yi simdi baslat"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_TEXT "API anahtarlarimi eklemek icin .env dosyasini ac"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION OpenEnvFile

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Function OpenEnvFile
    Exec 'notepad.exe "$INSTDIR\.env"'
FunctionEnd

Section "SOFA" SecMain
    SetOutPath "$INSTDIR"

    File /r "..\app"
    File /r "..\static"
    File /r "..\templates"
    File "..\requirements.txt"
    File "..\.env.example"
    File "..\README.md"
    File "..\start_sofa.bat"
    File "..\sofa_silent.bat"
    File "..\stop_sofa.bat"
    File "..\SOFA.vbs"
    File "..\SOFA.ico"

    IfFileExists "$INSTDIR\.env" env_exists 0
        CopyFiles /SILENT "$INSTDIR\.env.example" "$INSTDIR\.env"
    env_exists:

    ; --- Python sanal ortami + bagimliliklar ---
    DetailPrint "Python kontrol ediliyor..."
    nsExec::ExecToLog 'cmd /c where python'
    Pop $0
    ${If} $0 == "0"
        DetailPrint "Sanal ortam olusturuluyor ve bagimliliklar kuruluyor (birkac dakika surebilir)..."
        nsExec::ExecToLog 'cmd /c cd /d "$INSTDIR" && python -m venv .venv && "$INSTDIR\.venv\Scripts\pip.exe" install -q -r requirements.txt'
        Pop $0
    ${Else}
        MessageBox MB_OK|MB_ICONEXCLAMATION "Python bulunamadi. Once https://python.org adresinden Python kurup 'Add to PATH' secenegini isaretleyin, sonra SOFA klasorundeki start_sofa.bat dosyasini calistirin."
    ${EndIf}

    ; --- OmniRoute (npm kuruluysa otomatik kurulur) ---
    DetailPrint "npm kontrol ediliyor (OmniRoute icin)..."
    nsExec::ExecToLog 'cmd /c where npm'
    Pop $1
    ${If} $1 == "0"
        DetailPrint "OmniRoute kuruluyor (npm install -g omniroute)..."
        nsExec::ExecToLog 'cmd /c npm install -g omniroute'
        Pop $1
    ${Else}
        DetailPrint "npm bulunamadi, OmniRoute kurulumu atlandi (Node.js kurduktan sonra elle kurabilirsiniz)."
    ${EndIf}

    ; --- Kisayollar (ozel SOFA ikonuyla) ---
    CreateDirectory "$SMPROGRAMS\SOFA"
    CreateShortCut "$SMPROGRAMS\SOFA\SOFA AI.lnk" "$INSTDIR\SOFA.vbs" "" "$INSTDIR\SOFA.ico" 0
    CreateShortCut "$SMPROGRAMS\SOFA\SOFA Durdur.lnk" "$INSTDIR\stop_sofa.bat" "" "$INSTDIR\SOFA.ico" 0
    CreateShortCut "$SMPROGRAMS\SOFA\Kaldir.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$DESKTOP\SOFA AI.lnk" "$INSTDIR\SOFA.vbs" "" "$INSTDIR\SOFA.ico" 0

    ; --- Kaldirici ---
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "DisplayName" "SOFA - Safe One For All"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "DisplayIcon" "$INSTDIR\SOFA.ico"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "Publisher" "SOFA"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA" "NoRepair" 1
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\SOFA AI.lnk"
    Delete "$SMPROGRAMS\SOFA\SOFA AI.lnk"
    Delete "$SMPROGRAMS\SOFA\SOFA Durdur.lnk"
    Delete "$SMPROGRAMS\SOFA\Kaldir.lnk"
    RMDir "$SMPROGRAMS\SOFA"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SOFA"
    RMDir /r "$INSTDIR"
SectionEnd
