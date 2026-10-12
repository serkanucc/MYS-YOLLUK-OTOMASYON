@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title MYS Yolluk Otomasyon Merkezi
rem Eski paneli yalnızca otomasyon boşta ve port bu projeye aitse güvenle yenile.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0restart-panel.ps1"
if errorlevel 1 (
  echo Panel güvenli biçimde yenilenemedi. Yukarıdaki mesajı kontrol edin.
  pause
  exit /b 1
)

rem Proje sanal ortamı varsa paneli aynı bağımlılıklarla başlat; yoksa sistem Python'unu kullan.
if exist ".venv\Scripts\python.exe" (
  set "PANEL_PYTHON=.venv\Scripts\python.exe"
) else (
  set "PANEL_PYTHON=python"
)

rem Sunucu hazır olana kadar bekle; tarayıcıya eski/yanıtsız panel açılmasın.
start "" /b "%PANEL_PYTHON%" scripts\yolluk-controller.py
for /l %%i in (1,1,20) do (
  curl.exe --silent --fail http://127.0.0.1:8765/api/status >nul 2>&1 && goto panel_ready
  timeout /t 1 /nobreak >nul
)
echo Panel 20 saniye içinde başlamadı. Python/bağımlılık çıktısını kontrol edin.
pause
exit /b 1

:panel_ready
echo Güncel panel hazır: http://127.0.0.1:8765
start "" http://127.0.0.1:8765
pause

