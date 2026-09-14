' SOFA (Safe One For All) - Sessiz baslatici
' Masaustu kisayolunu bu dosyaya baglayin: cift tikladiginizda
' hicbir siyah cmd penceresi gorunmeden SOFA arka planda baslar
' ve taraytciniz otomatik acilir.
'
' Sorun giderme icin (hata mesajlarini gormek istiyorsaniz):
'   start_sofa.bat dosyasini dogrudan cift tiklayin (pencereli calisir).

Set WshShell = CreateObject("WScript.Shell")
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
WshShell.Run """" & scriptDir & "sofa_silent.bat" & """", 0, False
Set WshShell = Nothing
