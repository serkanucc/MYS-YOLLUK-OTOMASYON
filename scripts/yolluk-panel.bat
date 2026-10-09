@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title MYS Yolluk Otomasyon Merkezi
netstat -ano | findstr /r /c:":8765 .*LISTENING" >nul && (
  echo Panel zaten çalışıyor: http://127.0.0.1:8765
  start "" http://127.0.0.1:8765
  pause
  exit /b
)
start "" http://127.0.0.1:8765
python scripts\yolluk-controller.py


